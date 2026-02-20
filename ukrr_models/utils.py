import argparse
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from sqlalchemy.exc import SQLAlchemyError
from rr_database.sqlserver import SQLServerDatabase

from ukrr_models.rr_models import UKRRPatient, UKRR_Deleted_Patient


def audit_date_expression():
    return cast(func.getdate(), Date)


def audit_time_expression():
    return func.concat(
        func.datepart("hour", func.getdate()),
        func.datepart("minute", func.getdate()),
    )

def row_to_str(rrno, keys, values) -> str:
    """Format a row as a string."""
    # Add RR_NO to the start
    keys = ["RR_NO"] + keys
    values = [rrno] + values

    return ", ".join(["%s=%s" % (k, v) for k, v in zip(keys, values)])

class DeletePatientError(Exception):
    pass

class MergePatientError(Exception):
    pass


def merge_patient(
    session: Session,
    table_desc,
    source_rrno: str,
    destination_rrno: str,
):
    print("Merging %s to %s..." % (source_rrno, destination_rrno))
    for table in table_desc:
        print("Merging %s table..." % table)
        if table == "PATIENT_XREF":
            continue
        
        key_columns = list(table_desc[table].key_columns)
        
        if "RR_NO" in key_columns:
            # We ignore the RR_NO column when comparing rows
            key_columns.remove("RR_NO")
        else:
            # Skip tables that don't contain patient data (i.e. no RR_NO column)
            continue
        
        # Skip tables where the RR_NO is the only key
        # e.g. PATIENTS, EXTERNAL_COMM
        if len(key_columns) == 0:
            continue
        
        sql = "SELECT {columns} FROM {table} WHERE RR_NO = :RR_NO".format(
            table=table,
            columns=", ".join(key_columns),
        )
        
        print(f"Getting source data from {table}...")
        # Get data for source patient
        session.execute(sql, {"RR_NO": source_rrno})
        # Convert to a python list for row equality checking
        src_rows = [list(x) for x in session.fetchall()]
        
        print(f"Getting destination data from {table}...")

        # Get data for destination patient
        session.execute(sql, {"RR_NO": destination_rrno})
        dest_rows = [list(x) for x in session.fetchall()]
        
        update_sql = "UPDATE {table} SET RR_NO = :DEST_RR_NO WHERE RR_NO = :SRC_RR_NO {conditions}".format(
            table=table,
            conditions=" ".join("AND {0} = :{0}".format(x) for x in key_columns),
        )

        print(f"Updating {table}...")
        
        for src_row in src_rows:
            # Skip ESRF rows that were automatically created by the
            # validation (HOSP_CENTRE is set to 999)
            if table == "ESRF" and src_row[0] == "999":
                continue

            # Check if destination patient already has a row matching
            # this one (comparing the keys)
            if src_row in dest_rows:
                # Skip update
                continue

            # Move the row from the source patient to the destination patient
            params = {
                "SRC_RR_NO": source_rrno,
                "DEST_RR_NO": destination_rrno,
            }
            params.update(dict(list(zip(key_columns, src_row))))

            try:
                session.execute(update_sql, params)
            except Exception:
                # Print the exception
                import traceback

                traceback.print_exc()

                raise MergePatientError(
                    "Error updating {table} ({row})".format(
                        table=table,
                        row=row_to_str(source_rrno, key_columns, src_row),
                    )
                )

            if session.cursor.rowcount != 1:
                msg = (
                    "Expected to update 1 row from {table} "
                    "({row}) but actually updated {count} rows"
                )
                raise MergePatientError(
                    msg.format(
                        table=table,
                        row=row_to_str(source_rrno, key_columns, src_row),
                        count=session.cursor.rowcount,
                    )
                )

            print(
                "Moved {table} ({row}) from {src_rrno} to {dest_rrno}".format(
                    table=table,
                    row=row_to_str(source_rrno, key_columns, src_row),
                    src_rrno=source_rrno,
                    dest_rrno=destination_rrno,
                )
            )

def delete_patient(
    session: Session,
    rrno: str,
    username: str,
    authorised_by: str,
    reason: str,
    duplicate_rrno: Optional[str] = None,
):
    """Delete a patient."""
    print(f"Deleting {rrno}...")

    patient = session.scalar(select(UKRRPatient).where(UKRRPatient.rr_no == rrno))

    if patient is None:
        raise DeletePatientError(f"Patient (RR_NO={rrno}) not found")

    # Find list of columns we need to copy from PATIENTS to DELETED_PATIENTS
    patient_columns = {c.key for c in UKRRPatient.__table__.columns}
    deleted_patient_columns = {c.key for c in UKRR_Deleted_Patient.__table__.columns}
    shared_cols = patient_columns & deleted_patient_columns

    print("Adding %s to DELETED_PATIENTS..." % rrno)

    patinet_params: dict[str, object] = {
        col: getattr(patient, col) for col in shared_cols
    }

    patinet_params.update(
        {
            "USERNAME": username,
            "AUTHORISED_BY": authorised_by,
            "DESCRIPTION": reason,
            "DUPLICATE_RR_NO": duplicate_rrno,
        }
    )

    deleted_patient_params = {
        key: value
        for key, value in patinet_params.items()
        if key in deleted_patient_columns
    }

    deleted_patient = UKRR_Deleted_Patient(**deleted_patient_params)
    deleted_patient.audit_date = audit_date_expression()
    deleted_patient.audit_time = audit_time_expression()

    try:
        session.add(deleted_patient)
        session.delete(patient)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise DeletePatientError(
            f"Error adding patient (RR_NO={rrno}) to DELETED_PATIENTS"
        )

    print(f"Deleted {rrno}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--rrno", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--authorised-by", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--duplicate-rrno", required=False)

    args = parser.parse_args()

    database = SQLServerDatabase.connect(server="RR-SQL-Live", database="renalreg")
    table_desc = database.table_definitions()
    with database.session as session:
        print(
            f"Deleting patient {args.rrno}, authorised by {args.authorised_by} for reason {args.reason}"
        )
        delete_patient(
            session=session,
            rrno=args.rrno,
            username=args.username,
            authorised_by=args.authorised_by,
            reason=args.reason,
            duplicate_rrno=args.duplicate_rrno,
        )
