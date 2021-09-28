from sqlalchemy.orm import relationship
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.ext.declarative import declarative_base

import pyxb

from ukrdc_schema import ukrdc_schema
from ukrdc.services.utils import get_xml_datetime

Base = declarative_base()

# Historic Note.
# "SQLAlchemy sends 'proper case' items to Oracle in speech
# marks implying Case Sensitivity - which then doens't match.
# This requires overriding the Table/Column Names"
# This isn't required now, nor does the code below reflect this but
# I (GS) seem to recall this caused me a lot of hassle so I'm going to
# preserve the comment just incase we fall through a portal to the past.


class UKRR_Patient(Base):

    __tablename__ = 'patients'

    rr_no = Column(Integer, primary_key=True)
    surname = Column(String)
    forename = Column(String)
    sex = Column(String)

    nhs_no = Column('new_nhs_no', Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    uktssa_no = Column(Integer)

    date_birth = Column(Date)
    date_death = Column(Date)

    # This is the date the patient was
    # first loaded into the UKRR database
    date_registered = Column(Date)

    first_seen_date = Column(Date)

    patient_demographics = relationship("Patient_Demographics", backref="patient")

    def as_pyxb_xml(
        self,
        # If sending_facility is supplied we assume only
        # one set of data returned.
        sending_facility: str = 'UKRR',
        # TODO: UKRR is not a valid value for SendingExtract yet.
        sending_extract: str = 'UKRDC',
        full_patient_record: bool = True
    ):

        patient_record = ukrdc_schema.PatientRecord()
        patient_record.SendingFacility = sending_facility
        patient_record.SendingExtract = sending_extract

        patient_record.Patient = ukrdc_schema.Patient()

        patient_record.Patient.BirthTime = get_xml_datetime(self.date_birth)

        if self.sex:
            patient_record.Patient.Gender = self.sex

        patient_record.Patient.PatientNumbers = pyxb.BIND()

        if sending_facility == 'UKRR':
            patient_record.Patient.Names = pyxb.BIND(
                pyxb.BIND(use="L", Family=self.surname, Given=self.forename)
            )

            xml_identifier = ukrdc_schema.PatientNumber()
            xml_identifier.Number = str(self.rr_no)
            # TODO: This may not pass validation.
            # More significantly a value other than LOCALHOSP may
            # be a problem with the EMPI logic.
            xml_identifier.Organization = "UKRR"
            xml_identifier.NumberType = "MRN"
            patient_record.Patient.PatientNumbers.append(xml_identifier)

        else:
            patient_demographics = self.patient_demographics.filter(hosp_centre==sending_facility).first()

            patient_record.Patient.Names = pyxb.BIND(
                pyxb.BIND(use="L", Family=patient_demographics.surname, Given=patient_demographics.forename)
            )

            for nhs_identifier in (self.nhs_no, self.chi_no, self.hsc_no):
                if nhs_identifier:
                    xml_identifier = ukrdc_schema.PatientNumber()

                    xml_identifier.Number = str(nhs_identifier)
                    # TODO: Work this out
                    xml_identifier.Organization = "NHS"
                    xml_identifier.NumberType = "MRN"

                    patient_record.Patient.PatientNumbers.append(xml_identifier)

                    # Once we've got one quit.
                    break

        # National Identifiers
        for nhs_identifier in (self.nhs_no, self.chi_no, self.hsc_no):

            if nhs_identifier:
                xml_identifier = ukrdc_schema.PatientNumber()

                xml_identifier.Number = str(nhs_identifier)
                # TODO: Find the actual organization.
                xml_identifier.Organization = 'NHS'
                xml_identifier.NumberType = "NI"

                patient_record.Patient.PatientNumbers.append(xml_identifier)

        # RR National Identifier
        xml_identifier = ukrdc_schema.PatientNumber()

        xml_identifier.Number = str(self.rr_no)
        # TODO: Find the actual organization.
        xml_identifier.Organization = 'UKRR'
        xml_identifier.NumberType = "NI"

        patient_record.Patient.PatientNumbers.append(xml_identifier)
        
        if sending_facility == 'UKRR':
            # TODO: Create a Program Membership Here
            pass

        if full_patient_record:
            # TODO: Extract the other stuff here
            pass

        return patient_record.toDOM().toprettyxml()


class Patient_Demographics(Base):

    __tablename__ = 'patient_demog'

    rr_no = Column(Integer, ForeignKey("patients.rr_no"), primary_key=True)
    hosp_centre = Column(String, primary_key=True)

    surname = Column(String)
    forename = Column(String)
    birth_name = Column(String)
    alias_name = Column(String)
    date_birth = Column(Date)
    date_death = Column(Date)

    nhs_no = Column('new_nhs_no', Integer)
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

    nhs_no = Column('new_nhs_no', Integer)
    chi_no = Column(Integer)
    hsc_no = Column(Integer)
    uktssa_no = Column(Integer)

    date_birth = Column(Date)
    date_death = Column(Date)
