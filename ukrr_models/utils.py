import argparse
import traceback
from sqlalchemy import text
from sqlalchemy import select
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rr_database.sqlserver import SQLServerDatabase
from ukrr_models.rr_models import UKRRPatient, UKRR_Deleted_Patient


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
    for table_name in table_desc:
        print("Merging %s table..." % table_name)
        if table_name == "PATIENT_XREF":
            continue

        key_columns = list(table_desc[table_name].key_columns)

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

        schema = None
        metadata = MetaData()
        table = Table(
            table_name,
            metadata,
            schema=schema,
            autoload_with=session.get_bind(),
        )

        columns = [table.c[c] for c in key_columns]
        statement = select(*columns).where(table.c.RR_NO == bindparam("RR_NO"))

        print(f"Getting source data from {table}...")
        # Get data for source patient
        result = session.execute(statement, {"RR_NO": source_rrno})
        src_rows = [list(row) for row in result.all()]

        print(f"Getting destination data from {table}...")

        # Get data for destination patient
        result = session.execute(statement, {"RR_NO": destination_rrno})
        dest_rows = [list(row) for row in result.all()]

        update_statement = (
            update(table)
            .where(table.c.RR_NO == bindparam("SRC_RR_NO"))
            .where(*(table.c[c] == bindparam(c) for c in key_columns))
            .values(RR_NO=bindparam("DEST_RR_NO"))
        )

        print(f"Updating {table}...")

        for src_row in src_rows:
            # Skip ESRF rows that were automatically created by the
            # validation (HOSP_CENTRE is set to 999)
            if table_name == "ESRF" and src_row[0] == "999":
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
                result = session.execute(update_statement, params)
            except Exception:
                traceback.print_exc()

                raise MergePatientError(
                    "Error updating {table} ({row})".format(
                        table=table,
                        row=row_to_str(source_rrno, key_columns, src_row),
                    )
                )

            if result.rowcount != 1:  # type: ignore[attr-defined]
                msg = (
                    "Expected to update 1 row from {table} "
                    "({row}) but actually updated {count} rows"
                )
                raise MergePatientError(
                    msg.format(
                        table=table,
                        row=row_to_str(source_rrno, key_columns, src_row),
                        count=result.rowcount,
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
    audit_date: Optional[str] = None,
    audit_time: Optional[str] = None,
):
    """Delete a patient."""
    print(f"Deleting {rrno}...")

    patient = session.scalar(select(UKRRPatient).where(UKRRPatient.rr_no == rrno))

    if patient is None:
        raise DeletePatientError(f"Patient (RR_NO={rrno}) not found")

    # Column is called NHS_NO in the model, but NEW_NHS_NO in the DB
    rename_map = {
        "NEW_NHS_NO": "NHS_NO",
    }

    # Find list of columns we need to copy from PATIENTS to DELETED_PATIENTS
    patient_columns = {c.key for c in UKRRPatient.__table__.columns}
    deleted_patient_columns = {c.key for c in UKRR_Deleted_Patient.__table__.columns}
    shared_cols = patient_columns & deleted_patient_columns

    print("Adding %s to DELETED_PATIENTS..." % rrno)

    patient_params: dict[str, object] = {
        rename_map.get(col, col): getattr(patient, rename_map.get(col, col))
        for col in shared_cols
    }

    patient_params.update(
        {
            "USERNAME": username,
            "AUTHORISED_BY": authorised_by,
            "DESCRIPTION": reason,
            "DUPLICATE_RR_NO": duplicate_rrno,
        }
    )

    deleted_patient_params: dict[str, Any] = {
        key: value
        for key, value in patient_params.items()
        if key in deleted_patient_columns
    }

    deleted_patient = UKRR_Deleted_Patient(**deleted_patient_params)
    deleted_patient.audit_date = audit_date
    deleted_patient.audit_time = audit_time

    try:
        session.add(deleted_patient)
        session.delete(patient)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        traceback.print_exc()
        raise DeletePatientError(
            f"Error adding patient (RR_NO={rrno}) to DELETED_PATIENTS"
        )

    print(f"Deleted {rrno}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--rrno", required=True)
    parser.add_argument("--username", required=False)
    parser.add_argument("--authorised-by", required=False)
    parser.add_argument("--reason", required=False)
    parser.add_argument("--duplicate-rrno", required=False)
    
    # Merge-specific args
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--destination-rrno", required=False)

    args = parser.parse_args()

    database = SQLServerDatabase.connect(data_source="RR-SQL-Test", database="renalreg")
    table_desc = database.table_definitions()
    
    # Audit datetime metadata
    audit_date = text(database.audit_date()) 
    audit_time = text(database.audit_time())
    with database.session as session:
        if args.merge:
            if not args.rrno or not args.destination_rrno:
                parser.error("--merge requires --rrno and --destination-rrno")

            print(
                f"Merging patient {args.rrno} into {args.destination_rrno}"
            )
            merge_patient(
                session=session,
                table_desc=table_desc,
                source_rrno=args.rrno,
                destination_rrno=args.destination_rrno,
            )
        else:
            if not args.rrno or not args.username or not args.authorised_by or not args.reason:
                parser.error(
                    "delete mode requires --rrno --username --authorised-by --reason --duplicate-rrno"
                )

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
                audit_date=audit_date,
                audit_time=audit_time,
            )