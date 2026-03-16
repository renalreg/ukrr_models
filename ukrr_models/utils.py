import argparse
from sqlalchemy import select
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, cast, Date, text
from rr_database.sqlserver import SQLServerDatabase

from ukrr_models.rr_models import UKRRPatient, UKRR_Deleted_Patient


def audit_date_expression():
    return cast(func.getdate(), Date)


def audit_time_expression():
    """
    Return time in format 1945 (for 19:45) or 0705 (for 07:05)
    """
    return text(
        "RIGHT('0' + CAST(DATEPART(hour, GETDATE()) AS VARCHAR(2)), 2) + "
        "RIGHT('0' + CAST(DATEPART(minute, GETDATE()) AS VARCHAR(2)), 2)"
    )


class DeletePatientError(Exception):
    pass


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

    database = SQLServerDatabase.connect(data_source="RR-SQL-Test", database="renalreg")
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
