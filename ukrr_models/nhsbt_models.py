"""SQLAlchemy models for NHSBT"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Boolean

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class UKTPatient(Base):
    __tablename__ = "UKT_PATIENTS"

    UKTSSA_NO = Column(Integer, primary_key=True, autoincrement=False)
    SURNAME = Column(String(50))
    FORENAME = Column(String(50))
    SEX = Column(String(1))
    POST_CODE = Column(String(10))
    NEW_NHS_NO = Column(Integer)
    CHI_NO = Column(Integer)
    HSC_NO = Column(Integer)
    RR_NO = Column(Integer)
    UKT_DATE_DEATH = Column(DateTime)
    UKT_DATE_BIRTH = Column(DateTime)


class UKTTransplant(Base):
    __tablename__ = "UKT_TRANSPLANTS"

    REGISTRATION_ID = Column(String(12), primary_key=True)
    UKTSSA_NO = Column(Integer)
    TRANSPLANT_ID = Column(Integer)
    TRANSPLANT_TYPE = Column(String(10))
    TRANSPLANT_ORGAN = Column(String(50))
    TRANSPLANT_UNIT = Column(String(50))
    RR_NO = Column(Integer)
    TRANSPLANT_DATE = Column(DateTime)
    UKT_FAIL_DATE = Column(DateTime)
    REGISTRATION_DATE = Column(DateTime)
    REGISTRATION_DATE_TYPE = Column(String(12))
    REGISTRATION_END_DATE = Column(DateTime)
    REGISTRATION_END_STATUS = Column(String(12))
    TRANSPLANT_CONSIDERATION = Column(String(20))
    TRANSPLANT_DIALYSIS = Column(String(12))
    TRANSPLANT_RELATIONSHIP = Column(String(20))
    TRANSPLANT_SEX = Column(String(12))
    CAUSE_OF_FAILURE = Column(String(10))
    CAUSE_OF_FAILURE_TEXT = Column(String(500))
    CIT_MINS = Column(String(10))
    HLA_MISMATCH = Column(String(10))
    UKT_SUSPENSION = Column(Boolean)


class UKTSites(Base):
    __tablename__ = "UKT_SITES"

    SITE_NAME = Column(String(50), primary_key=True)
    RR_CODE = Column(String(8))
