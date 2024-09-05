from sqlalchemy import Column, Date, ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, relationship, declarative_base

from typing import List

Base = declarative_base()


class UKRRPatient(Base):
    __tablename__ = "PATIENTS"

    # This is (probably) the last centre for which a file was
    # loaded and not necessarily the latest/main unit they
    # attend.
    HOSP_CENTRE = Column(String)
    RR_NO = Column(Integer, primary_key=True)
    SURNAME = Column(String)
    FORENAME = Column(String)
    SEX = Column(String)

    NHS_NO = Column("NEW_NHS_NO", Integer)
    CHI_NO = Column(Integer)
    HSC_NO = Column(Integer)
    UKTSSA_NO = Column(Integer)

    DATE_BIRTH = Column(Date)
    DATE_DEATH = Column(Date)

    ETHNICITY = Column("ETHGR_CODE", String)

    BLOOD_GROUP = Column(String)
    BLOOD_RHESUS = Column("BLOOD_GROUP_RHESUS", String)

    COD_READ = Column(String)
    # TODO: [GIT-18] These should be updated to String in the DB.
    COD_EDTA1 = Column(Integer)
    COD_EDTA2 = Column(Integer)
    COD_TEXT = Column(String)

    # This is the date the patient was
    # first loaded into the UKRR database
    DATE_REGISTERED = Column(Date)
    FIRST_SEEN_DATE = Column(Date)
    OPT_OUT_FLAG = Column(String)

    PATIENT_DEMOGRAPHICS: Mapped[List["Patient_Demographics"]] = relationship(
        back_populates="UKRR_PATIENT"
    )


class Patient_Demographics(Base):
    __tablename__ = "PATIENT_DEMOG"

    RR_NO = Column(Integer, ForeignKey("PATIENTS.RR_NO"), primary_key=True)
    HOSP_CENTRE = Column(String, primary_key=True)

    SURNAME = Column(String)
    FORENAME = Column(String)
    BIRTH_NAME = Column(String)
    ALIAS_NAME = Column(String)
    DATE_BIRTH = Column(Date)
    DATE_DEATH = Column(Date)

    NHS_NO = Column("NEW_NHS_NO", Integer)
    CHI_NO = Column(Integer)
    HSC_NO = Column(Integer)
    UKTSSA_NO = Column(Integer)
    LOCAL_HOSP_NO = Column(String)

    FIRST_SEEN_DATE = Column(Date)

    UKRR_PATIENT: Mapped["UKRRPatient"] = relationship(
        back_populates="PATIENT_DEMOGRAPHICS"
    )


class UKRR_Deleted_Patient(Base):
    __tablename__ = "DELETED_PATIENTS"

    RR_NO = Column(Integer, primary_key=True)
    SURNAME = Column(String)
    FORENAME = Column(String)
    SEX = Column(String)

    NHS_NO = Column("NEW_NHS_NO", Integer)
    CHI_NO = Column(Integer)
    HSC_NO = Column(Integer)
    UKTSSA_NO = Column(Integer)

    LOCAL_HOSP_NO = Column(String)

    DATE_BIRTH = Column(Date)
    DATE_DEATH = Column(Date)


class QuarterlyTreatment(Base):
    __tablename__ = "QUARTERLY_TREATMENT"

    RR_NO = Column(Integer, primary_key=True)
    DATE_START = Column(DateTime, primary_key=True)
    TREATMENT_MODALITY = Column(String, primary_key=True)
    TREATMENT_CENTRE = Column(String, primary_key=True)
    HOSP_CENTRE = Column(String, primary_key=True)
    DATE_END = Column(DateTime)
    ADD_HAEMO_ON_PD = Column(String)
    CREATININE = Column(Numeric(38, 4))
    UREA = Column(Numeric(38, 4))
    HAEMOGLOBIN = Column(Numeric(38, 4))
    FERRETIN = Column(Numeric(38, 4))
    ALBUMIN = Column(Numeric(38, 4))
    ALUMINIUM = Column(Numeric(38, 4))
    HBA1C = Column(Numeric(38, 4))
    CHOLESTEROL = Column(Numeric(38, 4))
    IPTH = Column(Numeric(38, 4))
    CALCIUM_UNCORR = Column(Numeric(38, 4))
    CALCIUM_CORR = Column(Numeric(38, 4))
    PHOSPHATE = Column(Numeric(38, 4))
    BICARBONATE = Column(Numeric(38, 4))
    SYSTOLIC_BP = Column(Numeric(20, 0))
    DIASTOLIC_BP = Column(Numeric(20, 0))
    WEIGHT = Column(Numeric(38, 4))
    UREA_REDUCTION_RATIO = Column(Numeric(38, 4))
    EPO_USE = Column(String)
    HD_SUPERVISION = Column(String)
    DIALYSER_USED = Column(String)
    FLOW_RATE = Column(Numeric(20, 0))
    DIAL_REUSE = Column(String)
    TIMES_PER_WEEK = Column(Numeric(20, 0))
    DIAL_TIME = Column(Numeric(38, 4))
    BICARB_DIAL = Column(String)
    WEEKLY_FLUID_VOL = Column(Numeric(38, 4))
    BAG_SIZE = Column(Numeric(38, 4))
    CENTRE_PRI = Column(String)
    POST_SYSTOLIC_BP = Column(Numeric(20, 0))
    POST_DIASTOLIC_BP = Column(Numeric(20, 0))
    SODIUM = Column(Numeric(38, 4))
    PD_DIALYSATE_KTV = Column(Numeric(38, 4))
    PD_URINE_KTV = Column(Numeric(38, 4))
    PD_NPCR = Column(Numeric(38, 4))
    CRP = Column(Numeric(38, 4))
    LDL_CHOLESTEROL = Column(Numeric(38, 4))
    HDL_CHOLESTEROL = Column(Numeric(38, 4))
    TRIGLYCERIDES = Column(Numeric(38, 4))
    WAITING_LIST_STATUS = Column(String)
    CREATININE_FIRST_MONTH = Column(Numeric(38, 4))
    CREATININE_SECOND_MONTH = Column(Numeric(38, 4))
    PERCENT_HYPOCHROMIC = Column(Numeric(38, 4))
    MCH = Column(Numeric(38, 4))
    B12 = Column(Numeric(38, 4))
    RED_CELL_FOLATE = Column(Numeric(38, 4))
    TRANSFERRIN_SATURATION = Column(Numeric(38, 4))
    SERUM_POTASSIUM = Column(Numeric(38, 4))
    PROTEIN_CREATININE_RATIO = Column(Numeric(38, 4))
    ALBUMIN_CREATININE_RATIO = Column(Numeric(38, 4))
    SERUM_CELL_FOLATE = Column(Numeric(38, 4))
    ACE_INHIBITOR = Column(String)
    RENAGEL = Column(String)
    LANTHANUM = Column(String)
    CINACALCET = Column(String)
    CALCIUM_BASED_BINDER = Column(String)
    ALUCAPS = Column(String)
    SERUM_URATE = Column(Numeric(38, 4))
    STATIN_DRUG_USE = Column(String)
    HBA1C_MMOL = Column(Numeric(3, 0))
    ALKALINE_PHOSPHATASE = Column(Numeric(38, 4))
