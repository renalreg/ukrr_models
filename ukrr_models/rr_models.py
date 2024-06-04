from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, relationship

Base = declarative_base()


class UKRRPatient(Base):
    __tablename__ = "patients"

    # This is (probably) the last centre for which a file was
    # loaded and not neccesarily the latest/main unit they
    # attend.
    hosp_centre = Column(String)

    rr_no = Column(Integer, primary_key=True)
    surname = Column(String)
    forename = Column(String)
    sex = Column(String)

    nhs_no = Column("new_nhs_no", Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    uktssa_no = Column(Integer)

    date_birth = Column(Date)
    date_death = Column(Date)

    ethnicity = Column("ethgr_code", String)

    blood_group = Column(String)
    blood_rhesus = Column("blood_group_rhesus", String)

    cod_read = Column(String)
    # TODO: [GIT-18] These should be updated to String in the DB.
    cod_edta1 = Column(Integer)
    cod_edta2 = Column(Integer)
    cod_text = Column(String)

    # This is the date the patient was
    # first loaded into the UKRR database
    date_registered = Column(Date)

    first_seen_date = Column(Date)

    patient_demographics: Mapped["Patient_Demographics"] = relationship(
        "Patient_Demographics", back_populates="ukrr_patient"
    )


class Patient_Demographics(Base):
    __tablename__ = "patient_demog"

    rr_no = Column(Integer, ForeignKey("patients.rr_no"), primary_key=True)
    hosp_centre = Column(String, primary_key=True)

    surname = Column(String)
    forename = Column(String)
    birth_name = Column(String)
    alias_name = Column(String)
    date_birth = Column(Date)
    date_death = Column(Date)

    nhs_no = Column("new_nhs_no", Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    uktssa_no = Column(Integer)
    local_hosp_no = Column(String)

    first_seen_date = Column(Date)

    ukrr_patient: Mapped["UKRRPatient"] = relationship(
        "UKRRPatient", back_populates="patient_demographics"
    )


class UKRR_Deleted_Patient(Base):
    __tablename__ = "deleted_patients"

    rr_no = Column(Integer, primary_key=True)
    surname = Column(String)
    forename = Column(String)
    sex = Column(String)

    nhs_no = Column("new_nhs_no", Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    uktssa_no = Column(Integer)

    local_hosp_no = Column(String)

    date_birth = Column(Date)
    date_death = Column(Date)
