"""SQLAlchemy models for NHSBT"""

from sqlalchemy.orm import declarative_base, synonym
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Boolean

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class UKTPatient(Base):
    __tablename__ = "UKT_PATIENTS"

    UKTSSA_NO = Column(Integer, primary_key=True, autoincrement=False)
    uktssa_no: Column = synonym("UKTSSA_NO")

    SURNAME = Column(String(50))
    surname: Column = synonym("SURNAME")

    FORENAME = Column(String(50))
    forename: Column = synonym("FORENAME")

    SEX = Column(String(1))
    sex: Column = synonym("SEX")

    POST_CODE = Column(String(10))
    post_code: Column = synonym("POST_CODE")

    NEW_NHS_NO = Column(Integer)
    new_nhs_no: Column = synonym("NEW_NHS_NO")

    CHI_NO = Column(Integer)
    chi_no: Column = synonym("CHI_NO")

    HSC_NO = Column(Integer)
    hsc_no: Column = synonym("HSC_NO")

    RR_NO = Column(Integer)
    rr_no: Column = synonym("RR_NO")

    UKT_DATE_DEATH = Column(DateTime)
    ukt_date_death: Column = synonym("UKT_DATE_DEATH")

    UKT_DATE_BIRTH = Column(DateTime)
    ukt_date_birth: Column = synonym("UKT_DATE_BIRTH")


class UKTTransplant(Base):
    __tablename__ = "UKT_TRANSPLANTS"

    REGISTRATION_ID = Column(String(12), primary_key=True)
    registration_id: Column = synonym("REGISTRATION_ID")

    UKTSSA_NO = Column(Integer)
    uktssa_no: Column = synonym("UKTSSA_NO")

    TRANSPLANT_ID = Column(Integer)
    transplant_id: Column = synonym("TRANSPLANT_ID")

    TRANSPLANT_TYPE = Column(String(10))
    transplant_type: Column = synonym("TRANSPLANT_TYPE")

    TRANSPLANT_ORGAN = Column(String(50))
    transplant_organ: Column = synonym("TRANSPLANT_ORGAN")

    TRANSPLANT_UNIT = Column(String(50))
    transplant_unit: Column = synonym("TRANSPLANT_UNIT")

    RR_NO = Column(Integer)
    rr_no: Column = synonym("RR_NO")

    TRANSPLANT_DATE = Column(DateTime)
    transplant_date: Column = synonym("TRANSPLANT_DATE")

    UKT_FAIL_DATE = Column(DateTime)
    ukt_fail_date: Column = synonym("UKT_FAIL_DATE")

    REGISTRATION_DATE = Column(DateTime)
    registration_date: Column = synonym("REGISTRATION_DATE")

    REGISTRATION_DATE_TYPE = Column(String(12))
    registration_date_type: Column = synonym("REGISTRATION_DATE_TYPE")

    REGISTRATION_END_DATE = Column(DateTime)
    registration_end_date: Column = synonym("REGISTRATION_END_DATE")

    REGISTRATION_END_STATUS = Column(String(12))
    registration_end_status: Column = synonym("REGISTRATION_END_STATUS")

    TRANSPLANT_CONSIDERATION = Column(String(20))
    transplant_consideration: Column = synonym("TRANSPLANT_CONSIDERATION")

    TRANSPLANT_DIALYSIS = Column(String(12))
    transplant_dialysis: Column = synonym("TRANSPLANT_DIALYSIS")

    TRANSPLANT_RELATIONSHIP = Column(String(20))
    transplant_relationship: Column = synonym("TRANSPLANT_RELATIONSHIP")

    TRANSPLANT_SEX = Column(String(12))
    transplant_sex: Column = synonym("TRANSPLANT_SEX")

    CAUSE_OF_FAILURE = Column(String(10))
    cause_of_failure: Column = synonym("CAUSE_OF_FAILURE")

    CAUSE_OF_FAILURE_TEXT = Column(String(500))
    cause_of_failure_text: Column = synonym("CAUSE_OF_FAILURE_TEXT")

    CIT_MINS = Column(String(10))
    cit_mins: Column = synonym("CIT_MINS")

    HLA_MISMATCH = Column(String(10))
    hla_mismatch: Column = synonym("HLA_MISMATCH")

    UKT_SUSPENSION = Column(Boolean)
    ukt_suspension: Column = synonym("UKT_SUSPENSION")


class UKTSites(Base):
    __tablename__ = "UKT_SITES"

    SITE_NAME = Column(String(50), primary_key=True)
    site_name: Column = synonym("SITE_NAME")

    RR_CODE = Column(String(8))
    rr_code: Column = synonym("RR_CODE")
