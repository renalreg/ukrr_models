import argparse
import traceback
from sqlalchemy import text
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.elements import TextClause
from rr_common.rr_general_utils import rr_sqldata
from rr_database.sqlserver import SQLServerDatabase
from ukrr_models.rr_models import UKRRPatient, UKRR_Deleted_Patient
from sqlalchemy import (
    select,
    update,
    bindparam,
    Table,
    MetaData,
    and_,
    insert,
    delete,
    cast,
    Date,
)


class DeletePatientError(Exception):
    pass


class MergePatientError(Exception):
    pass


def row_to_str(rrno, keys, values) -> str:
    """Format a row as a string."""
    # Add RR_NO to the start
    keys = ["RR_NO"] + keys
    values = [rrno] + values

    return ", ".join(["%s=%s" % (k, v) for k, v in zip(keys, values)])


def get_deleted_patients(session: Session, rrno):
    """Get deleted patient records for a given RR_NO."""
    statement = select(UKRR_Deleted_Patient).where(UKRR_Deleted_Patient.rr_no == rrno)
    result = session.execute(statement)
    return result.scalars().all()


def restore(
    session: Session,
    ouf,
    table_name,
    audit_data,
    audit_desc,
    main_definition,
    keep_rrno,
    update=False,
    audit_hosp_centre="",
):
    """Copy back data from the AUDIT_{TABLE} to the {TABLE} ie. undelete."""
    main_desc = main_definition.description
    main_keys = main_definition.key_columns
    main_list = []
    unique_audit_data = []

    if table_name != "PATIENTS": 
        for record in audit_data:
            if record not in unique_audit_data:
                unique_audit_data.append(record)
            else:
                print("Duplicate audit record found and removed", table_name, record)
                ouf.write(
                    "Duplicate audit record found and removed "
                    + table_name
                    + " "
                    + str(record)
                    + "\n"
                )
    else: # If table is PATIENT, restore only the most recent row to preserve the PKs
        unique_audit_data = [audit_data[0]] 

    main_list = [column.name for column in main_desc]
    audit_list = [column for column in audit_desc]
    for record in unique_audit_data:
        values = {}

        for field in main_list:
            # position of this field in the audit record
            audit_order = audit_list.index(field)
            value = record[audit_order]

            if field == "HOSP_CENTRE" and (value is None or value == ""):
                if audit_hosp_centre != "":
                    value = audit_hosp_centre
                else:
                    value = "XXX"

            values[field] = value

        schema = None
        metadata = MetaData()
        table = Table(
            table_name,
            metadata,
            schema=schema,
            autoload_with=session.get_bind(),
        )

        insert_statement = insert(table).values(**values)
        session.execute(insert_statement)

        if update:
            session.commit()
        else:
            session.rollback()

        # Now work out if the record we have just undeleted
        if keep_rrno and table != "PATIENTS":
            audit_position = {name: i for i, name in enumerate(audit_list)}

            conditions = []
            for key in main_keys:
                if key == "RR_NO":
                    value = keep_rrno
                else:
                    value = record[audit_position[key]]

                conditions.append(table.c[key] == value)

            select_statement = select(table).where(and_(*conditions))

            result = session.execute(select_statement)
            data = result.fetchall()
            if len(data) > 0:
                ouf.write(
                    "Merged patient keys match in "
                    + table_name
                    + " where "
                    + str(conditions)
                    + "will be deleted if data identical\n"
                )
                # Now check that it's identical
                merged_record = data[0]
                same = True
                for order, field in enumerate(main_list):
                    # Find the postion of the data in the audit record
                    # for the merged data field
                    audit_order = audit_list.index(field)
                    if rr_sqldata(merged_record[order]) != rr_sqldata(
                        record[audit_order]
                    ):
                        same = False
                        break
                if same:
                    statement = delete(table).where(and_(*conditions))
                    ouf.write(str(statement) + "\n")
                    session.execute(statement)
                    if update:
                        session.commit()
                    else:
                        session.rollback()


def undelete_patient(
    session: Session,
    table_desc,
    rrno: str,
    output_dir: str,
    audit_date: str,
    keep_rrno: str = "",
    update: bool = False,
    audit_hosp_centre: str = "",
):
    """Take a deleted patient and "undelete" it using data in audit_* tables"""
    print("Undeleting %s..." % rrno)
    tables = list(table_desc.keys())

    # Make sure patients first
    del tables[tables.index("PATIENTS")]
    tables.insert(0, "PATIENTS")
    # Remove the Deleted Patients table as this isn't used (Audit_Patients is used instead).
    tables.remove("DELETED_PATIENTS")

    ouf = open(
        output_dir + "registry_resurrect_" + str(rrno) + ".txt",
        "w",
    )
    tables = ["PATIENTS"]
    for table_name in tables:
        audit_table_name = "AUDIT_" + table_name
        schema = None
        metadata = MetaData()

        audit_table = Table(
            audit_table_name,
            metadata,
            schema=schema,
            autoload_with=session.get_bind(),
        )

        statement = select(audit_table).where(
            and_(
                audit_table.c.RR_NO == bindparam("RR_NO"),
                audit_table.c.AUDIT_STATUS == "D",
                cast(audit_table.c.AUDIT_DATE, Date)
                == cast(bindparam("AUDIT_DATE"), Date),
            )
        )
        try:
            result = session.execute(
                statement,
                {
                    "RR_NO": rrno,
                    "AUDIT_DATE": audit_date,
                },
            )
            rows = result.fetchall()
        except Exception:
            print("Problem querying", audit_table)
            raise

        if len(rows) >= 0:  # type: ignore[attr-defined]
            print("Status=D", audit_table, len(rows))
            ouf.write(
                "Status=D "
                + audit_table_name
                + " audit records="
                + str(len(rows))
                + "\n"
            )

            restore(
                session=session,
                ouf=ouf,
                table_name=table_name,
                audit_data=rows,
                audit_desc=result.keys(),
                main_definition=table_desc[table_name],
                keep_rrno=keep_rrno,
                update=update,
                audit_hosp_centre=audit_hosp_centre,
            )

    delete_statement = delete(UKRR_Deleted_Patient).where(
        UKRR_Deleted_Patient.rr_no == rrno
    )
    ouf.write(f"{delete_statement}\n")
    session.execute(delete_statement)
    if update:
        print(f"Deleted patient {rrno} from DELETED_PATIENTS")
        session.commit()
    else:
        session.rollback()


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
            .where(*(table.c[c] == bindparam(f"w_{c}") for c in key_columns))
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
            params.update(
                {f"w_{col}": value for col, value in zip(key_columns, src_row)}
            )
            try:
                result = session.execute(update_statement, params)
                session.commit()
            except Exception:
                session.rollback()
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
                        count=result.rowcount,  # type: ignore[attr-defined]
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
    audit_date: Optional[TextClause] = None,
    audit_time: Optional[TextClause] = None,
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
    # SQLA is able to send an SQL expression into INSERT statement
    deleted_patient.audit_date = audit_date  # type: ignore[assignment]
    deleted_patient.audit_time = audit_time  # type: ignore[assignment]

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

    # Undelete-specific args
    parser.add_argument("--undelete", action="store_true")
    parser.add_argument("--update", action="store_true")

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

            print(f"Merging patient {args.rrno} into {args.destination_rrno}")
            merge_patient(
                session=session,
                table_desc=table_desc,
                source_rrno=args.rrno,
                destination_rrno=args.destination_rrno,
            )
        elif args.undelete:
            if not args.rrno:
                parser.error("--undelete requires --rrno")

            print(f"Undeleting patient {args.rrno}")
            deleted_patient = get_deleted_patients(session, args.rrno)[0]
            audit_surname = deleted_patient.surname
            audit_forename = deleted_patient.forename
            audit_dob = deleted_patient.date_birth
            audit_hosp_centre = deleted_patient.hosp_centre
            description = deleted_patient.description
            audit_date = deleted_patient.audit_date
            duplicate_rrno = deleted_patient.duplicate_rr_no

            if duplicate_rrno:
                keep_rrno = str(duplicate_rrno)
            else:
                keep_rrno = description[description.rfind(" ") + 1 :].replace("/", "")
                if len(keep_rrno) != 9 or not keep_rrno.isdigit():
                    keep_rrno = ""

            undelete_patient(
                session=session,
                table_desc=table_desc,
                rrno=args.rrno,
                output_dir="output/",
                audit_date=audit_date,
                keep_rrno=keep_rrno,
                update=args.update,
                audit_hosp_centre=audit_hosp_centre,
            )
        else:
            if (
                not args.rrno
                or not args.username
                or not args.authorised_by
                or not args.reason
            ):
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
