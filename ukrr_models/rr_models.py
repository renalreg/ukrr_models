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

from ukrdc_schema import ukrdc_schema

from ukrdc.services.utils import get_xml_datetime, customdate
import uuid
from ukrdc.services.ukrdc_models import NAMESPACE
from rr.nhs import get_organization, OrganizationType, valid_number
from ukrdc.services.exceptions import PatientIdentifierNotFoundError

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

    # This is the date the patient was
    # first loaded into the UKRR database
    date_registered = Column(Date)

    first_seen_date = Column(Date)

    patient_demographics = relationship(
        "Patient_Demographics", backref="patient", lazy="dynamic"
    )

    def as_pyxb_xml(
        self,
        # If sending_facility is supplied we assume only
        # one set of data returned.
        sending_facility: str = "UKRR",
        # Sending extract change from UKRDC to UKRR
        sending_extract: str = "UKRR",
        full_patient_record: bool = True,
    ):
        surname = self.surname
        forename = self.forename

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

        else:
            patient_demographics = self.patient_demographics.filter(
                Patient_Demographics.hosp_centre == sending_facility
            ).first()

            if patient_demographics:
                surname = patient_demographics.surname
                forename = patient_demographics.forename

            for nhs_identifier in (self.nhs_no, self.chi_no, self.hsc_no):
                if nhs_identifier:

                    xml_identifier = ukrdc_schema.PatientNumber()
                    xml_identifier.Number = str(nhs_identifier)

                    organization = get_organization(nhs_identifier)
                    if organization == OrganizationType.UNK or not valid_number(
                        nhs_identifier, organization
                    ):
                        raise PatientIdentifierNotFoundError(
                            "Invalid NHS Number Supplied"
                        )
                    xml_identifier.Organization = organization.name
                    xml_identifier.NumberType = "MRN"

                    patient_record.Patient.PatientNumbers.append(xml_identifier)

                    # Once we've got one quit.
                    break

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

                # RR Program Membership
                patient_record.ProgramMemberships = pyxb.BIND()
                xml_program_membership = ukrdc_schema.ProgramMembership()
                xml_program_membership.ProgramName = "UKRR"
                reg_date, _ = get_xml_datetime(self.date_registered).split("T")
                xml_program_membership.FromTime = customdate(reg_date)
                yhs_external_id = uuid.uuid5(
                    NAMESPACE, str(nhs_identifier) + "UKRR"
                ).hex
                xml_program_membership.ExternalId = yhs_external_id

                patient_record.ProgramMemberships.append(xml_program_membership)

        # RR National Identifier
        xml_identifier = ukrdc_schema.PatientNumber()

        xml_identifier.Number = str(self.rr_no)
        # TODO: Find the actual organization.
        xml_identifier.Organization = "UKRR"
        xml_identifier.NumberType = "NI"

        patient_record.Patient.PatientNumbers.append(xml_identifier)

        if sending_facility == "UKRR":
            # TODO: Create a Program Membership Here
            pass

        if full_patient_record:
            # TODO: Extract the other stuff here

            # Treatments
            try:
                # I suspect this can fail if you create an object
                # outside of a session

                sql_string = """
                SELECT
                    A.RR_NO,
                    A.DATE_START AS FROM_TIME,
                    A.TREATMENT_MODALITY AS ADMITREASONCODE,
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
                    A.RR_NO = :rr_no AND
                    C.TRANSFER_OUT = 0 AND
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
                        treatment.HealthCareFacility.CodingStandard = "ODS"

                    if admitreasoncode:
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

    date_birth = Column(Date)
    date_death = Column(Date)
