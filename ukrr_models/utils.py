import datetime as dt
from typing import Optional, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from sqlalchemy.exc import SQLAlchemyError

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
    
    patient = session.scalar(
        select(UKRRPatient).where(UKRRPatient.rr_no == rrno)
    )
    
    if patient is None:
        raise DeletePatientError(f"Patient (RR_NO={rrno}) not found")
    
    # Find list of columns we need to copy from PATIENTS to DELETED_PATIENTS
    patient_columns = {c.key for c in UKRRPatient.__table__.columns}
    deleted_patient_columns = {c.key for c in UKRR_Deleted_Patient.__table__.columns}
    shared_cols = patient_columns & deleted_patient_columns
    
    print("Adding %s to DELETED_PATIENTS..." % rrno)
    
    patinet_params: dict[str, object] = {col: getattr(patient, col) for col in shared_cols}
    
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
    deleted_patient.AUDIT_DATE = audit_date_expression()
    delete_patient.AUDIT_TIME = audit_time_expression()
    
    try:
        session.add(deleted_patient)
        session.delete(patient)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise DeletePatientError(f"Error adding patient (RR_NO={rrno}) to DELETED_PATIENTS")
    
    print(f"Deleted {rrno}")