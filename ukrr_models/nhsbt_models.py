"""SQLAlchemy models for NHSBT"""

from sqlalchemy import Boolean, DateTime, Integer, MetaData, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, synonym

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class UKTPatient(Base):
    __tablename__ = "UKT_PATIENTS"

    UKTSSA_NO: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    uktssa_no: Mapped[int] = synonym("UKTSSA_NO")

    SURNAME: Mapped[Optional[str]] = mapped_column(String(50))
    surname: Mapped[Optional[str]] = synonym("SURNAME")

    FORENAME: Mapped[Optional[str]] = mapped_column(String(50))
    forename: Mapped[Optional[str]] = synonym("FORENAME")

    SEX: Mapped[Optional[str]] = mapped_column(String(1))
    sex: Mapped[Optional[str]] = synonym("SEX")

    POST_CODE: Mapped[Optional[str]] = mapped_column(String(10))
    post_code: Mapped[Optional[str]] = synonym("POST_CODE")

    NEW_NHS_NO: Mapped[Optional[int]] = mapped_column(Integer)
    new_nhs_no: Mapped[Optional[int]] = synonym("NEW_NHS_NO")

    CHI_NO: Mapped[Optional[int]] = mapped_column(Integer)
    chi_no: Mapped[Optional[int]] = synonym("CHI_NO")

    HSC_NO: Mapped[Optional[int]] = mapped_column(Integer)
    hsc_no: Mapped[Optional[int]] = synonym("HSC_NO")

    RR_NO: Mapped[Optional[int]] = mapped_column(Integer)
    rr_no: Mapped[Optional[int]] = synonym("RR_NO")

    UKT_DATE_DEATH: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    ukt_date_death: Mapped[Optional[DateTime]] = synonym("UKT_DATE_DEATH")

    UKT_DATE_BIRTH: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    ukt_date_birth: Mapped[Optional[DateTime]] = synonym("UKT_DATE_BIRTH")


class UKTTransplant(Base):
    __tablename__ = "UKT_TRANSPLANTS"

    REGISTRATION_ID: Mapped[str] = mapped_column(String(12), primary_key=True)
    registration_id: Mapped[str] = synonym("REGISTRATION_ID")

    UKTSSA_NO: Mapped[int] = mapped_column(Integer)
    uktssa_no: Mapped[int] = synonym("UKTSSA_NO")

    TRANSPLANT_ID: Mapped[Optional[int]] = mapped_column(Integer)
    transplant_id: Mapped[Optional[int]] = synonym("TRANSPLANT_ID")

    TRANSPLANT_TYPE: Mapped[Optional[str]] = mapped_column(String(10))
    transplant_type: Mapped[Optional[str]] = synonym("TRANSPLANT_TYPE")

    TRANSPLANT_ORGAN: Mapped[Optional[str]] = mapped_column(String(50))
    transplant_organ: Mapped[Optional[str]] = synonym("TRANSPLANT_ORGAN")

    TRANSPLANT_UNIT: Mapped[Optional[str]] = mapped_column(String(50))
    transplant_unit: Mapped[Optional[str]] = synonym("TRANSPLANT_UNIT")

    RR_NO: Mapped[Optional[int]] = mapped_column(Integer)
    rr_no: Mapped[Optional[int]] = synonym("RR_NO")

    TRANSPLANT_DATE: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    transplant_date: Mapped[Optional[DateTime]] = synonym("TRANSPLANT_DATE")

    UKT_FAIL_DATE: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    ukt_fail_date: Mapped[Optional[DateTime]] = synonym("UKT_FAIL_DATE")

    REGISTRATION_DATE: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    registration_date: Mapped[Optional[DateTime]] = synonym("REGISTRATION_DATE")

    REGISTRATION_DATE_TYPE: Mapped[Optional[str]] = mapped_column(String(12))
    registration_date_type: Mapped[Optional[str]] = synonym("REGISTRATION_DATE_TYPE")

    REGISTRATION_END_DATE: Mapped[Optional[DateTime]] = mapped_column(DateTime)
    registration_end_date: Mapped[Optional[DateTime]] = synonym("REGISTRATION_END_DATE")

    REGISTRATION_END_STATUS: Mapped[Optional[str]] = mapped_column(String(12))
    registration_end_status: Mapped[Optional[str]] = synonym("REGISTRATION_END_STATUS")

    TRANSPLANT_CONSIDERATION: Mapped[Optional[str]] = mapped_column(String(20))
    transplant_consideration: Mapped[Optional[str]] = synonym("TRANSPLANT_CONSIDERATION")

    TRANSPLANT_DIALYSIS: Mapped[Optional[str]] = mapped_column(String(12))
    transplant_dialysis: Mapped[Optional[str]] = synonym("TRANSPLANT_DIALYSIS")

    TRANSPLANT_RELATIONSHIP: Mapped[Optional[str]] = mapped_column(String(20))
    transplant_relationship: Mapped[Optional[str]] = synonym("TRANSPLANT_RELATIONSHIP")

    TRANSPLANT_SEX: Mapped[Optional[str]] = mapped_column(String(12))
    transplant_sex: Mapped[Optional[str]] = synonym("TRANSPLANT_SEX")

    CAUSE_OF_FAILURE: Mapped[Optional[str]] = mapped_column(String(10))
    cause_of_failure: Mapped[Optional[str]] = synonym("CAUSE_OF_FAILURE")

    CAUSE_OF_FAILURE_TEXT: Mapped[Optional[str]] = mapped_column(String(500))
    cause_of_failure_text: Mapped[Optional[str]] = synonym("CAUSE_OF_FAILURE_TEXT")

    CIT_MINS: Mapped[Optional[str]] = mapped_column(String(10))
    cit_mins: Mapped[Optional[str]] = synonym("CIT_MINS")

    HLA_MISMATCH: Mapped[Optional[str]] = mapped_column(String(10))
    hla_mismatch: Mapped[Optional[str]] = synonym("HLA_MISMATCH")

    UKT_SUSPENSION: Mapped[Optional[bool]] = mapped_column(Boolean)
    ukt_suspension: Mapped[Optional[bool]] = synonym("UKT_SUSPENSION")


class UKTSites(Base):
    __tablename__ = "UKT_SITES"

    SITE_NAME: Mapped[str] = mapped_column(String(50), primary_key=True)
    site_name: Mapped[str] = synonym("SITE_NAME")

    RR_CODE: Mapped[str] = mapped_column(String(8))
    rr_code: Mapped[str] = synonym("RR_CODE")
