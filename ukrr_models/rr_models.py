from sqlalchemy import Column, Date, ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, relationship, declarative_base, synonym

from typing import List

Base = declarative_base()


class UKRRPatient(Base):
    __tablename__ = "PATIENTS"

    HOSP_CENTRE = Column(String)
    hosp_centre: Column = synonym("HOSP_CENTRE")

    RR_NO = Column(Integer, primary_key=True)
    rr_no: Column = synonym("RR_NO")

    SURNAME = Column(String)
    surname: Column = synonym("SURNAME")

    FORENAME = Column(String)
    forename: Column = synonym("FORENAME")

    SEX = Column(String)
    sex: Column = synonym("SEX")

    NHS_NO = Column("NEW_NHS_NO", Integer)
    nhs_no: Column = synonym("NHS_NO")

    CHI_NO = Column(Integer)
    chi_no: Column = synonym("CHI_NO")

    HSC_NO = Column(Integer)
    hsc_no: Column = synonym("HSC_NO")

    UKTSSA_NO = Column(Integer)
    uk_tssa_no: Column = synonym("UKTSSA_NO")

    DATE_BIRTH = Column(Date)
    date_birth: Column = synonym("DATE_BIRTH")

    DATE_DEATH = Column(Date)
    date_death: Column = synonym("DATE_DEATH")

    ETHNICITY = Column("ETHGR_CODE", String)
    ethnicity: Column = synonym("ETHNICITY")

    BLOOD_GROUP = Column(String)
    blood_group: Column = synonym("BLOOD_GROUP")

    BLOOD_RHESUS = Column("BLOOD_GROUP_RHESUS", String)
    blood_rhesus: Column = synonym("BLOOD_RHESUS")

    COD_READ = Column(String)
    cod_read: Column = synonym("COD_READ")

    COD_EDTA1 = Column(Integer)
    cod_edta1: Column = synonym("COD_EDTA1")

    COD_EDTA2 = Column(Integer)
    cod_edta2: Column = synonym("COD_EDTA2")

    COD_TEXT = Column(String)
    cod_text: Column = synonym("COD_TEXT")

    DATE_REGISTERED = Column(Date)
    date_registered: Column = synonym("DATE_REGISTERED")

    FIRST_SEEN_DATE = Column(Date)
    first_seen_date: Column = synonym("FIRST_SEEN_DATE")

    OPT_OUT_FLAG = Column(String)
    opt_out_flag: Column = synonym("OPT_OUT_FLAG")

    PATIENT_DEMOGRAPHICS: Mapped[List["Patient_Demographics"]] = relationship(
        back_populates="UKRR_PATIENT"
    )


class Patient_Demographics(Base):
    __tablename__ = "PATIENT_DEMOG"

    RR_NO = Column(Integer, ForeignKey("PATIENTS.RR_NO"), primary_key=True)
    rr_no: Column = synonym("RR_NO")

    HOSP_CENTRE = Column(String, primary_key=True)
    hosp_centre: Column = synonym("HOSP_CENTRE")

    SURNAME = Column(String)
    surname: Column = synonym("SURNAME")

    FORENAME = Column(String)
    forename: Column = synonym("FORENAME")

    BIRTH_NAME = Column(String)
    birth_name: Column = synonym("BIRTH_NAME")

    ALIAS_NAME = Column(String)
    alias_name: Column = synonym("ALIAS_NAME")

    DATE_BIRTH = Column(Date)
    date_birth: Column = synonym("DATE_BIRTH")

    DATE_DEATH = Column(Date)
    date_death: Column = synonym("DATE_DEATH")

    NHS_NO = Column("NEW_NHS_NO", Integer)
    nhs_no: Column = synonym("NHS_NO")

    CHI_NO = Column(Integer)
    chi_no: Column = synonym("CHI_NO")

    HSC_NO = Column(Integer)
    hsc_no: Column = synonym("HSC_NO")

    UKTSSA_NO = Column(Integer)
    uk_tssa_no: Column = synonym("UKTSSA_NO")

    LOCAL_HOSP_NO = Column(String)
    local_hosp_no: Column = synonym("LOCAL_HOSP_NO")

    FIRST_SEEN_DATE = Column(Date)
    first_seen_date: Column = synonym("FIRST_SEEN_DATE")

    UKRR_PATIENT: Mapped["UKRRPatient"] = relationship(
        back_populates="PATIENT_DEMOGRAPHICS"
    )


class UKRR_Deleted_Patient(Base):
    __tablename__ = "DELETED_PATIENTS"

    RR_NO = Column(Integer, primary_key=True)
    rr_no: Column = synonym("RR_NO")

    SURNAME = Column(String)
    surname: Column = synonym("SURNAME")

    FORENAME = Column(String)
    forename: Column = synonym("FORENAME")

    SEX = Column(String)
    sex: Column = synonym("SEX")

    NHS_NO = Column("NEW_NHS_NO", Integer)
    nhs_no: Column = synonym("NHS_NO")

    CHI_NO = Column(Integer)
    chi_no: Column = synonym("CHI_NO")

    HSC_NO = Column(Integer)
    hsc_no: Column = synonym("HSC_NO")

    UKTSSA_NO = Column(Integer)
    uk_tssa_no: Column = synonym("UKTSSA_NO")

    LOCAL_HOSP_NO = Column(String)
    local_hosp_no: Column = synonym("LOCAL_HOSP_NO")

    DATE_BIRTH = Column(Date)
    date_birth: Column = synonym("DATE_BIRTH")

    DATE_DEATH = Column(Date)
    date_death: Column = synonym("DATE_DEATH")


class QuarterlyTreatment(Base):
    __tablename__ = "QUARTERLY_TREATMENT"

    RR_NO = Column(Integer, primary_key=True)
    rr_no: Column = synonym("RR_NO")

    DATE_START = Column(DateTime, primary_key=True)
    date_start: Column = synonym("DATE_START")

    TREATMENT_MODALITY = Column(String, primary_key=True)
    treatment_modality: Column = synonym("TREATMENT_MODALITY")

    TREATMENT_CENTRE = Column(String, primary_key=True)
    treatment_centre: Column = synonym("TREATMENT_CENTRE")

    HOSP_CENTRE = Column(String, primary_key=True)
    hosp_centre: Column = synonym("HOSP_CENTRE")

    DATE_END = Column(DateTime)
    date_end: Column = synonym("DATE_END")

    ADD_HAEMO_ON_PD = Column(String)
    add_haemo_on_pd: Column = synonym("ADD_HAEMO_ON_PD")

    CREATININE = Column(Numeric(38, 4))
    creatinine: Column = synonym("CREATININE")

    UREA = Column(Numeric(38, 4))
    urea: Column = synonym("UREA")

    HAEMOGLOBIN = Column(Numeric(38, 4))
    haemoglobin: Column = synonym("HAEMOGLOBIN")

    FERRETIN = Column(Numeric(38, 4))
    ferretin: Column = synonym("FERRETIN")

    ALBUMIN = Column(Numeric(38, 4))
    albumin: Column = synonym("ALBUMIN")

    ALUMINIUM = Column(Numeric(38, 4))
    aluminium: Column = synonym("ALUMINIUM")

    HBA1C = Column(Numeric(38, 4))
    hba1c: Column = synonym("HBA1C")

    CHOLESTEROL = Column(Numeric(38, 4))
    cholesterol: Column = synonym("CHOLESTEROL")

    IPTH = Column(Numeric(38, 4))
    ipth: Column = synonym("IPTH")

    CALCIUM_UNCORR = Column(Numeric(38, 4))
    calcium_uncorr: Column = synonym("CALCIUM_UNCORR")

    CALCIUM_CORR = Column(Numeric(38, 4))
    calcium_corr: Column = synonym("CALCIUM_CORR")

    PHOSPHATE = Column(Numeric(38, 4))
    phosphate: Column = synonym("PHOSPHATE")

    BICARBONATE = Column(Numeric(38, 4))
    bicarbonate: Column = synonym("BICARBONATE")

    SYSTOLIC_BP = Column(Numeric(20, 0))
    systolic_bp: Column = synonym("SYSTOLIC_BP")

    DIASTOLIC_BP = Column(Numeric(20, 0))
    diastolic_bp: Column = synonym("DIASTOLIC_BP")

    WEIGHT = Column(Numeric(38, 4))
    weight: Column = synonym("WEIGHT")

    UREA_REDUCTION_RATIO = Column(Numeric(38, 4))
    urea_reduction_ratio: Column = synonym("UREA_REDUCTION_RATIO")

    EPO_USE = Column(String)
    epo_use: Column = synonym("EPO_USE")

    HD_SUPERVISION = Column(String)
    hd_supervision: Column = synonym("HD_SUPERVISION")

    DIALYSER_USED = Column(String)
    dialyser_used: Column = synonym("DIALYSER_USED")

    FLOW_RATE = Column(Numeric(20, 0))
    flow_rate: Column = synonym("FLOW_RATE")

    DIAL_REUSE = Column(String)
    dial_reuse: Column = synonym("DIAL_REUSE")

    TIMES_PER_WEEK = Column(Numeric(20, 0))
    times_per_week: Column = synonym("TIMES_PER_WEEK")

    DIAL_TIME = Column(Numeric(38, 4))
    dial_time: Column = synonym("DIAL_TIME")

    BICARB_DIAL = Column(String)
    bicarb_dial: Column = synonym("BICARB_DIAL")

    WEEKLY_FLUID_VOL = Column(Numeric(38, 4))
    weekly_fluid_vol: Column = synonym("WEEKLY_FLUID_VOL")

    BAG_SIZE = Column(Numeric(38, 4))
    bag_size: Column = synonym("BAG_SIZE")

    CENTRE_PRI = Column(String)
    centre_pri: Column = synonym("CENTRE_PRI")

    POST_SYSTOLIC_BP = Column(Numeric(20, 0))
    post_systolic_bp: Column = synonym("POST_SYSTOLIC_BP")

    POST_DIASTOLIC_BP = Column(Numeric(20, 0))
    post_diastolic_bp: Column = synonym("POST_DIASTOLIC_BP")

    SODIUM = Column(Numeric(38, 4))
    sodium: Column = synonym("SODIUM")

    PD_DIALYSATE_KTV = Column(Numeric(38, 4))
    pd_dialysate_ktv: Column = synonym("PD_DIALYSATE_KTV")

    PD_URINE_KTV = Column(Numeric(38, 4))
    pd_urine_ktv: Column = synonym("PD_URINE_KTV")

    PD_NPCR = Column(Numeric(38, 4))
    pd_npcr: Column = synonym("PD_NPCR")

    CRP = Column(Numeric(38, 4))
    crp: Column = synonym("CRP")

    LDL_CHOLESTEROL = Column(Numeric(38, 4))
    ldl_cholesterol: Column = synonym("LDL_CHOLESTEROL")

    HDL_CHOLESTEROL = Column(Numeric(38, 4))
    hdl_cholesterol: Column = synonym("HDL_CHOLESTEROL")

    TRIGLYCERIDES = Column(Numeric(38, 4))
    triglycerides: Column = synonym("TRIGLYCERIDES")

    WAITING_LIST_STATUS = Column(String)
    waiting_list_status: Column = synonym("WAITING_LIST_STATUS")

    CREATININE_FIRST_MONTH = Column(Numeric(38, 4))
    creatinine_first_month: Column = synonym("CREATININE_FIRST_MONTH")

    CREATININE_SECOND_MONTH = Column(Numeric(38, 4))
    creatinine_second_month: Column = synonym("CREATININE_SECOND_MONTH")

    PERCENT_HYPOCHROMIC = Column(Numeric(38, 4))
    percent_hypochromic: Column = synonym("PERCENT_HYPOCHROMIC")

    MCH = Column(Numeric(38, 4))
    mch: Column = synonym("MCH")

    B12 = Column(Numeric(38, 4))
    b12: Column = synonym("B12")

    RED_CELL_FOLATE = Column(Numeric(38, 4))
    red_cell_folate: Column = synonym("RED_CELL_FOLATE")

    TRANSFERRIN_SATURATION = Column(Numeric(38, 4))
    transferrin_saturation: Column = synonym("TRANSFERRIN_SATURATION")

    SERUM_POTASSIUM = Column(Numeric(38, 4))
    serum_potassium: Column = synonym("SERUM_POTASSIUM")

    PROTEIN_CREATININE_RATIO = Column(Numeric(38, 4))
    protein_creatinine_ratio: Column = synonym("PROTEIN_CREATININE_RATIO")

    ALBUMIN_CREATININE_RATIO = Column(Numeric(38, 4))
    albumin_creatinine_ratio: Column = synonym("ALBUMIN_CREATININE_RATIO")

    SERUM_CELL_FOLATE = Column(Numeric(38, 4))
    serum_cell_folate: Column = synonym("SERUM_CELL_FOLATE")

    ACE_INHIBITOR = Column(String)
    ace_inhibitor: Column = synonym("ACE_INHIBITOR")

    RENAGEL = Column(String)
    renagel: Column = synonym("RENAGEL")

    LANTHANUM = Column(String)
    lanthanum: Column = synonym("LANTHANUM")

    CINACALCET = Column(String)
    cinacalcet: Column = synonym("CINACALCET")

    CALCIUM_BASED_BINDER = Column(String)
    calcium_based_binder: Column = synonym("CALCIUM_BASED_BINDER")

    ALUCAPS = Column(String)
    alucaps: Column = synonym("ALUCAPS")

    SERUM_URATE = Column(Numeric(38, 4))
    serum_urate: Column = synonym("SERUM_URATE")

    STATIN_DRUG_USE = Column(String)
    statin_drug_use: Column = synonym("STATIN_DRUG_USE")

    HBA1C_MMOL = Column(Numeric(3, 0))
    hba1c_mmol: Column = synonym("HBA1C_MMOL")

    ALKALINE_PHOSPHATASE = Column(Numeric(38, 4))
    alkaline_phosphatase: Column = synonym("ALKALINE_PHOSPHATASE")
