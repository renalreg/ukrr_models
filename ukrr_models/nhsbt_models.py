""" SQLAlchemy models for NHSBT
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, MetaData

metadata = MetaData()
Base = declarative_base(metadata=metadata)

# http://docs.sqlalchemy.org/en/latest/dialects/oracle.html#identifier-casing


class UKTPatient(Base):
    __tablename__ = "ukt_patients"

    # Note - SQLAlchemy sends 'proper case' items to Oracle in speech marks implying Case 
    # Sensitivity - which then doesn't match.
    uktssa_no = Column(
        Integer,
        primary_key=True,
        doc="Test",
        info={"Test": "Blick"},
        autoincrement=False,
    )
    surname = Column(String)
    forename = Column(String)
    sex = Column(String)
    post_code = Column(String)
    new_nhs_no = Column(Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    rr_no = Column(Integer)
    ukt_date_death = Column(Date)
    ukt_date_birth = Column(Date)


class UKTTransplant(Base):
    __tablename__ = "ukt_transplants"

    transplant_id = Column(Integer)
    uktssa_no = Column(Integer)
    transplant_date = Column(Date)
    transplant_type = Column(String)
    transplant_organ = Column(String)
    transplant_unit = Column(String)
    ukt_fail_date = Column(Date)
    rr_no = Column(Integer)
    registration_id = Column(String, primary_key=True)
    registration_date = Column(Date)
    registration_date_type = Column(String)
    registration_end_date = Column(Date)
    registration_end_status = Column(String)
    transplant_consideration = Column(String)
    transplant_dialysis = Column(String)
    transplant_relationship = Column(String)
    transplant_sex = Column(String)
    cause_of_failure = Column(String)
    cause_of_failure_text = Column(String)
    cit_mins = Column(String)
    hla_mismatch = Column(String)
    ukt_suspension = Column(String)
