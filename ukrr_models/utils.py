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
