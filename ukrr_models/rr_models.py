import uuid

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session

import pyxb

from rr.nhs import get_organization, OrganizationType, valid_number
from ukrdc.services.exceptions import PatientIdentifierNotFoundError
from ukrdc.services.ukrdc_models import NAMESPACE
from ukrdc.services.utils import get_xml_datetime, customdate
from ukrdc_schema import ukrdc_schema

Base = declarative_base()

# Historic Note.
# "SQLAlchemy sends 'proper case' items to Oracle in speech
# marks implying Case Sensitivity - which then doens't match.
# This requires overriding the Table/Column Names"
# This isn't required now, nor does the code below reflect this but
# I (GS) seem to recall this caused me a lot of hassle so I'm going to
# preserve the comment just incase we fall through a portal to the past.


class UKRR_Patient(Base):

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
    # TODO: These should be updated to String in the DB.
    cod_edta1 = Column(Integer)
    cod_edta2 = Column(Integer)
    cod_text = Column(String)

    # This is the date the patient was
    # first loaded into the UKRR database
    date_registered = Column(Date)

    first_seen_date = Column(Date)

    patient_demographics = relationship(
        "Patient_Demographics", backref="patient", lazy="dynamic"
    )

    def create_temp_treatments(cursor):

        try:
            sql_string = """
            CREATE TABLE TEMP_TREATMENTS (
                RR_NO INT,
                FROM_TIME DATETIME,
                ADMITREASONCODE VARCHAR(3),
                HEALTHCAREFACILITYCODE VARCHAR(10),
                TO_TIME DATETIME,
                DISCHARGEREASONCODE VARCHAR(3),
                DISCHARGELOCATION VARCHAR(10)
            ) """
            cursor.execute(sql_string)
        except:
            print("TEMP_TREATMENTS table already exists")

        sql_string = """TRUNCATE TABLE TEMP_TREATMENTS"""
        cursor.execute(sql_string)

        # NOTE: If you don't do this the uncomitted DDL
        # locks everything up. This also applies if using
        # temporary tables.
        cursor.connection.commit()

        sql_string = """
        INSERT INTO TEMP_TREATMENTS
        SELECT
            A.RR_NO,
            A.DATE_START AS FROM_TIME,
            CASE
                WHEN C.EQUIV_MODALITY IS NOT NULL
                    THEN C.EQUIV_MODALITY
                ELSE
                    A.TREATMENT_MODALITY
            END AS ADMITREASONCODE,
            A.TREATMENT_CENTRE AS HEALTHCAREFACILITYCODE,
            B.DATE_START AS TO_TIME,
            B.TREATMENT_MODALITY AS DISCHARGEREASONCODE,
            B.TREATMENT_CENTRE AS DISCHARGELOCATION
        FROM
        (
        SELECT
            RR_NO,
            DATE_START,
            DATE_END,
            YEAR_END_SEQ,
            TREATMENT_MODALITY,
            HOSP_CENTRE,
            TREATMENT_CENTRE,
            ROW_NUMBER() OVER (PARTITION BY RR_NO ORDER BY DATE_START ASC, YEAR_END_SEQ ASC) AS ROWNUMBER
        FROM
            TREATMENT
        ) A
        LEFT JOIN
        (
        SELECT
            RR_NO,
            DATE_START,
            DATE_END,
            YEAR_END_SEQ,
            TREATMENT_MODALITY,
            HOSP_CENTRE,
            TREATMENT_CENTRE,
            ROW_NUMBER() OVER (PARTITION BY RR_NO ORDER BY DATE_START ASC, YEAR_END_SEQ ASC) AS ROWNUMBER
        FROM
            TREATMENT
        ) B
            ON
                A.RR_NO = B.RR_NO AND
                A.ROWNUMBER = B.ROWNUMBER - 1 AND
                A.HOSP_CENTRE = B.HOSP_CENTRE
        LEFT JOIN MODALITY_CODES C ON C.REGISTRY_CODE = A.TREATMENT_MODALITY
        LEFT JOIN MODALITY_CODES D ON D.REGISTRY_CODE = B.TREATMENT_MODALITY
        WHERE
            C.TRANSFER_OUT = 0 AND
            C.REGISTRY_CODE_TYPE <> 'X'
        ORDER BY
            A.RR_NO,
            A.DATE_START,
            A.YEAR_END_SEQ
        """

        cursor.execute(sql_string)

        # Apparently the same with this.
        cursor.connection.commit()

    def as_pyxb_xml(
        self,
        # If sending_facility is supplied we assume only
        # one set of data returned.
        sending_facility: str = "UKRR",
        sending_extract: str = "UKRR",
        full_patient_record: bool = True,
        treatment_cache: bool = False,
    ):

        # TODO: We need to handle Refused Consent Patients

        if sending_facility == "UKRR":
            full_patient_record = False

        patient_record = ukrdc_schema.PatientRecord()
        patient_record.SendingFacility = sending_facility
        patient_record.SendingExtract = sending_extract
        patient_record.Patient = ukrdc_schema.Patient()
        patient_record.Patient.BirthTime = get_xml_datetime(self.date_birth)
        patient_record.Patient.DeathTime = get_xml_datetime(self.date_death)

        if self.sex:
            patient_record.Patient.Gender = self.sex

        patient_record.Patient.PatientNumbers = pyxb.BIND()

        if sending_facility == "UKRR":
            xml_identifier = ukrdc_schema.PatientNumber()
            xml_identifier.Number = str(self.rr_no)
            # TODO: This may not pass validation.
            # More significantly a value other than LOCALHOSP may
            # be a problem with the EMPI logic.
            xml_identifier.Organization = "UKRR"
            xml_identifier.NumberType = "MRN"
            patient_record.Patient.PatientNumbers.append(xml_identifier)

            surname = self.surname
            forename = self.forename

        else:
            patient_demographics = self.patient_demographics.filter(
                Patient_Demographics.hosp_centre == sending_facility
            ).first()

            if patient_demographics:
                surname = patient_demographics.surname
                forename = patient_demographics.forename
                local_hosp_no = patient_demographics.local_hosp_no

                xml_identifier = ukrdc_schema.PatientNumber()
                xml_identifier.Number = str(local_hosp_no)
                xml_identifier.Organization = "LOCALHOSP"
                xml_identifier.NumberType = "MRN"
                patient_record.Patient.PatientNumbers.append(xml_identifier)
            else:
                for nhs_identifier in (self.nhs_no, self.chi_no, self.hsc_no):
                    organization = get_organization(nhs_identifier)
                    if organization == OrganizationType.UNK or not valid_number(
                        nhs_identifier, organization
                    ):
                        continue

                    xml_identifier = ukrdc_schema.PatientNumber()
                    xml_identifier.Number = str(nhs_identifier)
                    xml_identifier.Organization = organization.name
                    xml_identifier.NumberType = "MRN"

                    patient_record.Patient.PatientNumbers.append(xml_identifier)

                    # Once we've got one quit.
                    break

                surname = self.surname
                forename = self.forename

        patient_record.Patient.Names = pyxb.BIND(
            pyxb.BIND(use="L", Family=surname, Given=forename)
        )

        # National Identifiers
        for nhs_identifier in (self.nhs_no, self.chi_no, self.hsc_no):

            if nhs_identifier:
                xml_identifier = ukrdc_schema.PatientNumber()

                xml_identifier.Number = str(nhs_identifier)

                organization = get_organization(nhs_identifier)
                if organization == OrganizationType.UNK or not valid_number(
                    nhs_identifier, organization
                ):
                    raise PatientIdentifierNotFoundError("Invalid NHS Number Supplied")

                xml_identifier.Organization = organization.name
                xml_identifier.NumberType = "NI"

                patient_record.Patient.PatientNumbers.append(xml_identifier)

        # RR National Identifier
        xml_identifier = ukrdc_schema.PatientNumber()
        xml_identifier.Number = str(self.rr_no)
        xml_identifier.Organization = "UKRR"
        xml_identifier.NumberType = "NI"

        patient_record.Patient.PatientNumbers.append(xml_identifier)

        if sending_facility == "UKRR":
            # RR Program Membership
            patient_record.ProgramMemberships = pyxb.BIND()
            xml_program_membership = ukrdc_schema.ProgramMembership()
            xml_program_membership.ProgramName = "UKRR"
            reg_date, _ = get_xml_datetime(self.date_registered).split("T")
            xml_program_membership.FromTime = customdate(reg_date)
            yhs_external_id = uuid.uuid5(NAMESPACE, str(nhs_identifier) + "UKRR").hex
            xml_program_membership.ExternalId = yhs_external_id

            patient_record.ProgramMemberships.append(xml_program_membership)

        if full_patient_record:
            # TODO: Extract the other stuff here

            # Ethnicity
            if self.ethnicity:
                if len(self.ethnicity) == 1:
                    # TODO: We need a conversion for the READ ethnicity codes
                    ethnicity = ukrdc_schema.EthnicGroup()
                    ethnicity.Code = self.ethnicity
                    ethnicity.CodingStandard = "NHS_DATA_DICTIONARY"
                    patient_record.Patient.EthnicGroup = ethnicity

            # TODO: First Seen Height/Weight/Creatinine
            # These would need creating but using "First Seen Date"
            # As the date of the results/observations

            # TODO: Adult Height
            # Not sure what we can do about this as there's no date
            # Could set it to be the same as their 18th Birthday but
            # That seems a bit random. Needs discussion.

            # Cause of Death

            # TODO: COD_READ

            patient_record.Diagnoses = pyxb.BIND()

            if self.cod_edta1:
                cause_of_death = ukrdc_schema.CauseOfDeath()
                diagnosis = ukrdc_schema.CF_EDTA_COD()
                # TODO: The str() can be removed once the DB field is changed.
                diagnosis.Code = str(self.cod_edta1)
                diagnosis.CodingStandard = "EDTA_COD"
                cause_of_death.Diagnosis = diagnosis
                cause_of_death.Description = self.cod_text

                patient_record.Diagnoses.append(cause_of_death)

            # TODO: COD_EDTA1

            # Blood Type
            # TODO: Need to check UKRR codes match
            if self.blood_group:
                patient_record.Patient.BloodGroup = self.blood_group
            if self.blood_rhesus:
                patient_record.Patient.BloodRhesus = self.blood_rhesus

            # TODO: Family Doctor

            # TODO: Other IDs - NHSBT, SCOT_REG, UKRR_UID etc. - Needs discussion.

            # TODO: BIRTH_NAME / ALIAS_NAME

            # Treatments

            # TODO: The 'X' Codes need Reviewing. In particular
            # Acute Episode without RRT which may qualify as something akin
            # to Conservative Management.

            try:
                # I suspect this can fail if you create an object
                # outside of a session

                if treatment_cache:
                    sql_string = """
                    SELECT
                        RR_NO,
                        FROM_TIME,
                        ADMITREASONCODE,
                        HEALTHCAREFACILITYCODE,
                        TO_TIME,
                        DISCHARGEREASONCODE,
                        DISCHARGELOCATION
                    FROM
                        TEMP_TREATMENTS
                    WHERE
                        RR_NO = :rr_no AND
                        HEALTHCAREFACILITYCODE = :hosp_centre
                    ORDER BY
                        FROM_TIME"""
                else:
                    sql_string = """
                    SELECT
                        A.RR_NO,
                        A.DATE_START AS FROM_TIME,
                        CASE
                            WHEN C.EQUIV_MODALITY IS NOT NULL
                                THEN C.EQUIV_MODALITY
                            ELSE
                                A.TREATMENT_MODALITY
                        END AS ADMITREASONCODE,
                        A.TREATMENT_CENTRE AS HEALTHCAREFACILITYCODE,
                        B.DATE_START AS TO_TIME,
                        B.TREATMENT_MODALITY AS DISCHARGEREASONCODE,
                        B.TREATMENT_CENTRE AS DISCHARGELOCATION
                    FROM
                    (
                    SELECT
                        RR_NO,
                        DATE_START,
                        DATE_END,
                        YEAR_END_SEQ,
                        TREATMENT_MODALITY,
                        HOSP_CENTRE,
                        TREATMENT_CENTRE,
                        ROW_NUMBER() OVER (PARTITION BY RR_NO ORDER BY DATE_START ASC, YEAR_END_SEQ ASC) AS ROWNUMBER
                    FROM
                        TREATMENT
                    WHERE
                        RR_NO = :rr_no
                    ) A
                    LEFT JOIN
                    (
                    SELECT
                        RR_NO,
                        DATE_START,
                        DATE_END,
                        YEAR_END_SEQ,
                        TREATMENT_MODALITY,
                        HOSP_CENTRE,
                        TREATMENT_CENTRE,
                        ROW_NUMBER() OVER (PARTITION BY RR_NO ORDER BY DATE_START ASC, YEAR_END_SEQ ASC) AS ROWNUMBER
                    FROM
                        TREATMENT
                    WHERE
                        RR_NO = :rr_no
                    ) B
                        ON
                            A.RR_NO = B.RR_NO AND
                            A.ROWNUMBER = B.ROWNUMBER - 1 AND
                            A.HOSP_CENTRE = B.HOSP_CENTRE
                    LEFT JOIN MODALITY_CODES C ON C.REGISTRY_CODE = A.TREATMENT_MODALITY
                    LEFT JOIN MODALITY_CODES D ON D.REGISTRY_CODE = B.TREATMENT_MODALITY
                    WHERE
                        A.RR_NO = :rr_no AND
                        C.TRANSFER_OUT = 0 AND
                        C.REGISTRY_CODE_TYPE <> 'X' AND
                        A.HOSP_CENTRE = :hosp_centre
                    ORDER BY
                        A.RR_NO,
                        A.DATE_START,
                        A.YEAR_END_SEQ
                    """

                cursor = (
                    object_session(self)
                    .execute(
                        sql_string,
                        {"rr_no": self.rr_no, "hosp_centre": sending_facility},
                    )
                    .cursor
                )
                results = cursor.fetchall()

                if results:
                    patient_record.Encounters = pyxb.BIND()

                for row in results:

                    from_time = row[1]
                    admitreasoncode = row[2]
                    healthcarefacilitycode = row[3]
                    to_time = row[4]
                    dischargereason = row[5]
                    dischargelocation = row[6]

                    treatment = ukrdc_schema.Treatment()

                    treatment.FromTime = from_time
                    treatment.ToTime = to_time

                    if healthcarefacilitycode:
                        treatment.HealthCareFacility = ukrdc_schema.Location()
                        treatment.HealthCareFacility.Code = healthcarefacilitycode
                        treatment.HealthCareFacility.CodingStandard = "RR1+"

                    if admitreasoncode:

                        # TODO: This needs an updated ukrdc_schema to fix a typo.
                        # for now we'll use a more generic TX code.
                        if admitreasoncode == "77":
                            admitreasoncode = "23"

                        treatment.AdmitReason = ukrdc_schema.CF_RR7_TREATMENT()
                        treatment.AdmitReason.Code = admitreasoncode
                        treatment.AdmitReason.CodingStandard = "CF_RR7_TREATMENT"

                    # TODO: This needs to be a lookup to MODALITY_CODES
                    # Or, I wonder if you can get it out of the PyXB Model?
                    if dischargereason in (
                        "30",
                        "38",
                        "84",
                        "85",
                        "86",
                        "90",
                        "91",
                        "92",
                        "95",
                    ):
                        treatment.DischargeReason = ukrdc_schema.CF_RR7_DISCHARGE()
                        treatment.DischargeReason.Code = dischargereason
                        treatment.DischargeReason.CodingStandard = "CF_RR7_DISCHARGE"

                        # Only output the location if we have a reason.
                        if dischargelocation:
                            treatment.DischargeLocation = ukrdc_schema.Location()
                            treatment.DischargeLocation.Code = dischargelocation
                            treatment.DischargeLocation.CodingStandard = "RR1+"

                    patient_record.Encounters.append(treatment)
            except Exception:
                raise
        return patient_record.toDOM().toprettyxml()


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
