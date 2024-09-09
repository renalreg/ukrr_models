"""SQLAlchemy models for NHSBT"""

from sqlalchemy.orm import declarative_base, synonym
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Boolean

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class UKTPatient(Base):
    __tablename__ = "UKT_PATIENTS"

    UKTSSA_NO = Column(Integer, primary_key=True, autoincrement=False)
    uktssa_no = synonym("UKTSSA_NO")

    SURNAME = Column(String(50))
    surname = synonym("SURNAME")

    FORENAME = Column(String(50))
    forename = synonym("FORENAME")

    SEX = Column(String(1))
    sex = synonym("SEX")

    POST_CODE = Column(String(10))
    post_code = synonym("POST_CODE")

    NEW_NHS_NO = Column(Integer)
    new_nhs_no = synonym("NEW_NHS_NO")

    CHI_NO = Column(Integer)
    chi_no = synonym("CHI_NO")

    HSC_NO = Column(Integer)
    hsc_no = synonym("HSC_NO")

    RR_NO = Column(Integer)
    rr_no = synonym("RR_NO")

    UKT_DATE_DEATH = Column(DateTime)
    ukt_date_death = synonym("UKT_DATE_DEATH")

    UKT_DATE_BIRTH = Column(DateTime)
    ukt_date_birth = synonym("UKT_DATE_BIRTH")


class UKTTransplant(Base):
    __tablename__ = "UKT_TRANSPLANTS"

    REGISTRATION_ID = Column(String(12), primary_key=True)
    registration_id = synonym("REGISTRATION_ID")

    UKTSSA_NO = Column(Integer)
    uktssa_no = synonym("UKTSSA_NO")

    TRANSPLANT_ID = Column(Integer)
    transplant_id = synonym("TRANSPLANT_ID")

    TRANSPLANT_TYPE = Column(String(10))
    transplant_type = synonym("TRANSPLANT_TYPE")

    TRANSPLANT_ORGAN = Column(String(50))
    transplant_organ = synonym("TRANSPLANT_ORGAN")

    TRANSPLANT_UNIT = Column(String(50))
    transplant_unit = synonym("TRANSPLANT_UNIT")

    RR_NO = Column(Integer)
    rr_no = synonym("RR_NO")

    TRANSPLANT_DATE = Column(DateTime)
    transplant_date = synonym("TRANSPLANT_DATE")

    UKT_FAIL_DATE = Column(DateTime)
    ukt_fail_date = synonym("UKT_FAIL_DATE")

    REGISTRATION_DATE = Column(DateTime)
    registration_date = synonym("REGISTRATION_DATE")

    REGISTRATION_DATE_TYPE = Column(String(12))
    registration_date_type = synonym("REGISTRATION_DATE_TYPE")

    REGISTRATION_END_DATE = Column(DateTime)
    registration_end_date = synonym("REGISTRATION_END_DATE")

    REGISTRATION_END_STATUS = Column(String(12))
    registration_end_status = synonym("REGISTRATION_END_STATUS")

    TRANSPLANT_CONSIDERATION = Column(String(20))
    transplant_consideration = synonym("TRANSPLANT_CONSIDERATION")

    TRANSPLANT_DIALYSIS = Column(String(12))
    transplant_dialysis = synonym("TRANSPLANT_DIALYSIS")

    TRANSPLANT_RELATIONSHIP = Column(String(20))
    transplant_relationship = synonym("TRANSPLANT_RELATIONSHIP")

    TRANSPLANT_SEX = Column(String(12))
    transplant_sex = synonym("TRANSPLANT_SEX")

    CAUSE_OF_FAILURE = Column(String(10))
    cause_of_failure = synonym("CAUSE_OF_FAILURE")

    CAUSE_OF_FAILURE_TEXT = Column(String(500))
    cause_of_failure_text = synonym("CAUSE_OF_FAILURE_TEXT")

    CIT_MINS = Column(String(10))
    cit_mins = synonym("CIT_MINS")

    HLA_MISMATCH = Column(String(10))
    hla_mismatch = synonym("HLA_MISMATCH")

    UKT_SUSPENSION = Column(Boolean)
    ukt_suspension = synonym("UKT_SUSPENSION")


class UKTSites(Base):
    __tablename__ = "UKT_SITES"

    SITE_NAME = Column(String(50), primary_key=True)
    site_name = synonym("SITE_NAME")

    RR_CODE = Column(String(8))
    rr_code = synonym("RR_CODE")
