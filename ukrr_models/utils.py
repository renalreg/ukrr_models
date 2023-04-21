import uuid
import pyxb


from sqlalchemy.orm.session import object_session


from rr.nhs import get_organization, OrganizationType, valid_number
#from ukrdc.services.exceptions import PatientIdentifierNotFoundError
#from ukrdc.services.ukrdc_models import NAMESPACE
#from ukrdc.services.utils import customdate, 
from ukrdc_schema import ukrdc_schema
from ukrr_models.rr_models import Patient_Demographics, UKRRPatient
from ukrdc.database.utils import get_xml_datetime

NAMESPACE = uuid.UUID("59508627-0d06-44f5-bc32-ab5ff14de653")

# Historic Note.
# "SQLAlchemy sends 'proper case' items to Oracle in speech
# marks implying Case Sensitivity - which then doesn't match.
# This requires overriding the Table/Column Names"
# This isn't required now, nor does the code below reflect this but
# I (GS) seem to recall this caused me a lot of hassle so I'm going to
# preserve the comment just incase we fall through a portal to the past.

QUA_OBSERVATION_ITEMS = [
    ("QUA40", "QUA01", "PRE", "Systolic BP"),
    ("QUA41", "QUA01", "PRE", "Diastolic BP"),
    ("QUA42", "QUA01", None, "Weight"),
    ("QUA44", "QUA01", "POST", "Post-Systolic BP"),
    ("QUA45", "QUA01", "POST", "Post-Diastolic BP"),
]

QUA_RESULT_ITEMS = [
    ("QUA10", "QUA01", None, "Creatinine"),
    ("QUA11", "QUA01", None, "Urea"),
    ( "QUA21", "QUA01", None, "Haemoglobin"),
    ("QUA22", "QUA01", None, "Ferretin"),
    ("QUA23", "QUA01", None, "Albumin"),
    ("QUA24", "QUA01", None, "HbA1c"),
    ("QUA25", "QUA01", None, "Aluminium"),
    ("QUA26", "QUA01", None, "Cholesterol"),
    ("QUA27", "QUA01", None, "Parathyroid Hormone"),
    ("QUA30", "QUA01", None, "Uncorrected Calcium"),
    ("QUA31", "QUA01", None, "Corrected Calcium"),
    ("QUA32", "QUA01", None, "Phosphate"),
    ("QUA33", "QUA01", None, "Bicarbonate"),
    ("QUA34", "QUA01", None, "Sodium"),
    ("QUA50", "QUA01", None, "Urea Reduction Ratio"),
]

QBL_RESULT_ITEMS = [
    ("QBLB9", "QBLBA", None, "Parathyroid Hormone"),
    ("QBLB3", "QBLBB", None, "Calcium"),
    ("QBLB4", "QBLBC", None, "Corrected Calcium"),
    ("QBLB1", "QBLB2", None, "Phosphate"),
    ("QBLA9", "QBLAA", None, "Potassium"),
    ("QBLG9", "QBLGA", None, "Urea Reduction Ratio"),
    ("QBLGG", "QBLGH", None, "KT/V"),
    ("QBLE1", "QBLEB", None, "Haemoglobin"),
    ("QBLB7", "QBLB8", None, "Albumin"),
    ("QBLA6", "QBLA7", None, "Sodium"),
    ("QBLB5", "QBLB6", None, "Alkaline Phosphatase"),
    # No 25-Hydroxyvitamin D ?
]

def custom_date(datetime):
    print(datetime)
    return get_xml_datetime(datetime)

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


def get_data_definition(cursor):
    sql_string = """
    SELECT
        UPLOAD_KEY,
        FIELD_NAME
    FROM
        RR_DATA_DEFINITION
    """

    cursor.execute(sql_string)
    results = cursor.fetchall()

    data_definition = dict()

    for row in results:
        data_definition[row[0]] = row[1]

    return data_definition


def get_observations(cursor, data_definition, rr_no) -> list:
    # function to get observations and append them to the patient record.

    observations = []
    for value_item, date_item, prepost, description in QUA_OBSERVATION_ITEMS:
        sql_string = (
            """
        SELECT
            """
            + data_definition[value_item]
            + """,
            """
            + data_definition[date_item]
            + """
            FROM
                QUARTERLY_TREATMENT
            WHERE
                """
            + data_definition[value_item]
            + """ IS NOT NULL AND
                """
            + data_definition[date_item]
            + """ IS NOT NULL AND
                RR_NO = ?"""
        )

        cursor.execute(sql_string, (rr_no,))
        results = cursor.fetchall()

        for row in results:
            xml_observation = ukrdc_schema.Observation()
            xml_observation.ObservationTime = row[1]
            xml_observation.ObservationCode = pyxb.BIND()
            xml_observation.ObservationCode.Code = value_item
            xml_observation.ObservationCode.CodingStandard = "UKRR"
            xml_observation.ObservationCode.Description = description
            xml_observation.ObservationValue = str(row[0])
            xml_observation.PrePost = prepost

            observations.append(xml_observation)

    return observations


def get_laborders(cursor, data_definition, rr_no) -> list:
    sql_string = """
    SELECT *
    FROM
        QUARTERLY_TREATMENT
    WHERE
        RR_NO = ?
    """

    cursor.execute(sql_string, (rr_no,))
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    lab_orders = []
    if len(results) > 0:
        for row in results:
            xml_laborder = ukrdc_schema.LabOrder()
            xml_laborder.PlacerId = "XXX"
            xml_laborder.ReceivingLocation = ukrdc_schema.Location()
            xml_laborder.ReceivingLocation.Code = row["HOSP_CENTRE"]
            xml_laborder.OrderItem = ukrdc_schema.CodedField()
            xml_laborder.OrderItem.Code = "QUA"
            xml_laborder.OrderItem.CodingStandard = "UKRR"
            xml_laborder.SpecimenCollectedTime = row["DATE_END"]

            xml_laborder.ResultItems = ukrdc_schema.ResultItems()

            for value_item, date_item, prepost, description in QUA_RESULT_ITEMS:
                value_field = data_definition[value_item]
                date_field = data_definition[date_item]

                if row[value_field]:
                    xml_resultitem = ukrdc_schema.ResultItem()
                    xml_resultitem.PrePost = prepost
                    xml_resultitem.ServiceId = ukrdc_schema.ServiceId()
                    xml_resultitem.ServiceId.CodingStandard = "UKRR"
                    xml_resultitem.ServiceId.Code = value_item
                    xml_resultitem.ServiceId.Description = description
                    xml_resultitem.ResultValue = str(row[value_field])
                    xml_resultitem.ObservationTime = row[date_field]

                    xml_laborder.ResultItems.append(xml_resultitem)

            lab_orders.append(xml_laborder)

    sql_string = """
    SELECT *
    FROM
        MONTHLY_TREATMENT
    WHERE
        RR_NO = ?
    """

    cursor.execute(sql_string, (rr_no,))
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    if len(results) > 0 and not lab_orders:
        for row in results:
            xml_laborder = ukrdc_schema.LabOrder()
            xml_laborder.PlacerId = "XXX"
            xml_laborder.ReceivingLocation = ukrdc_schema.Location()
            xml_laborder.ReceivingLocation.Code = row["HOSP_CENTRE"]
            xml_laborder.OrderItem = ukrdc_schema.CodedField()
            xml_laborder.OrderItem.Code = "QBL"
            xml_laborder.OrderItem.CodingStandard = "UKRR"
            xml_laborder.SpecimenCollectedTime = row["DATE_END"]

            xml_laborder.ResultItems = ukrdc_schema.ResultItems()

            for value_item, date_item, prepost, description in QBL_RESULT_ITEMS:
                value_field = data_definition[value_item]
                date_field = data_definition[date_item]

                if row[value_field]:
                    xml_resultitem = ukrdc_schema.ResultItem()
                    xml_resultitem.PrePost = prepost
                    xml_resultitem.ServiceId = ukrdc_schema.ServiceId()
                    xml_resultitem.ServiceId.CodingStandard = "UKRR"
                    xml_resultitem.ServiceId.Code = value_item
                    xml_resultitem.ServiceId.Description = description
                    xml_resultitem.ResultValue = row[value_field]
                    xml_resultitem.ObservationTime = row[date_field]

                    xml_laborder.ResultItems.append(xml_resultitem)

            lab_orders.append(xml_laborder)
    return lab_orders


def get_transplants(cursor, facility, rr_no) -> list:
    # NHS B&T Transplants (Waiting List)
    sqlstring = """
    SELECT
        A.RR_NO,
        REGISTRATION_DATE,
        REGISTRATION_END_DATE,
        REGISTRATION_ID,
        TRANSPLANT_CONSIDERATION,
        C.RR_CODE,
        REGISTRATION_END_STATUS
    FROM
        UKT_TRANSPLANTS A
    LEFT JOIN UKT_SITES C ON A.TRANSPLANT_UNIT = C.SITE_NAME
    WHERE
        A.RR_NO = ? AND
        C.RR_CODE = ?
    """

    cursor.execute(sqlstring, (rr_no, facility))
    results = cursor.fetchall()

    # line removed because I don't really understand how it fits in
    transplants = []
    for row in results:
        transplant_list = ukrdc_schema.TransplantList()
        transplant_list.EncounterNumber = row[3]
        transplant_list.EncounterType = "P"

        transplant_list.FromTime = row[1]
        transplant_list.ToTime = row[2]

        admit_reason = ukrdc_schema.CodedField()
        admit_reason.Code = row[4]
        transplant_list.AdmitReason = admit_reason

        discharge_reason = ukrdc_schema.CodedField()
        discharge_reason.Code = row[6]
        transplant_list.DischargeReason = discharge_reason

        transplants.append(transplant_list)
    return transplants


def as_pyxb_xml(
    Patient: UKRRPatient,
    # If sending_facility is supplied we assume only
    # one set of data returned.
    sending_facility: str = "UKRR",
    sending_extract: str = "UKRR",
    full_patient_record: bool = True,
    treatment_cache: bool = False,
    transplant: bool = False,
):
    # Function split out from the main UKRR_patient class
    # TODO: We need to handle Refused Consent Patients

    if sending_facility == "UKRR":
        full_patient_record = False

    patient_record = ukrdc_schema.PatientRecord()
    if transplant:
        patient_record.SendingFacility = "NHSBT"
    else:
        patient_record.SendingFacility = sending_facility

    patient_record.SendingExtract = sending_extract
    patient_record.Patient = ukrdc_schema.Patient()
    print()
    patient_record.Patient.BirthTime = get_xml_datetime(Patient.date_birth)
    patient_record.Patient.DeathTime = get_xml_datetime(Patient.date_death)

    if Patient.sex:
        patient_record.Patient.Gender = Patient.sex

    patient_record.Patient.PatientNumbers = pyxb.BIND()

    # create
    if sending_facility == "UKRR":
        xml_identifier = ukrdc_schema.PatientNumber()
        xml_identifier.Number = str(Patient.rr_no)
        # TODO: This may not pass validation.
        # More significantly a value other than LOCALHOSP may
        # be a problem with the EMPI logic.
        xml_identifier.Organization = "UKRR"
        xml_identifier.NumberType = "MRN"
        patient_record.Patient.PatientNumbers.append(xml_identifier)

        surname = Patient.surname
        forename = Patient.forename

    else:
        patient_demographics = Patient.patient_demographics.filter(
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
            for nhs_identifier in (Patient.nhs_no, Patient.chi_no, Patient.hsc_no):
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

            surname = Patient.surname
            forename = Patient.forename

    patient_record.Patient.Names = pyxb.BIND(
        pyxb.BIND(use="L", Family=surname, Given=forename)
    )



    # National Identifiers
    for nhs_identifier in (Patient.nhs_no, Patient.chi_no, Patient.hsc_no):
        if nhs_identifier:
            xml_identifier = ukrdc_schema.PatientNumber()

            xml_identifier.Number = str(nhs_identifier)

            organization = get_organization(nhs_identifier)
            if organization == OrganizationType.UNK or not valid_number(
                nhs_identifier, organization
            ):
                raise Exception("Invalid NHS Number Supplied")

            xml_identifier.Organization = organization.name
            xml_identifier.NumberType = "NI"

            patient_record.Patient.PatientNumbers.append(xml_identifier)

        # RR National Identifier
    xml_identifier = ukrdc_schema.PatientNumber()
    xml_identifier.Number = str(Patient.rr_no)
    xml_identifier.Organization = "UKRR"
    xml_identifier.NumberType = "NI"

    patient_record.Patient.PatientNumbers.append(xml_identifier)

    if sending_facility == "UKRR":
        # RR Program Membership
        patient_record.ProgramMemberships = pyxb.BIND()
        xml_program_membership = ukrdc_schema.ProgramMembership()
        xml_program_membership.ProgramName = "UKRR"
        reg_date, _ = get_xml_datetime(Patient.date_registered).split("T")
        xml_program_membership.FromTime = customdate(reg_date)
        yhs_external_id = uuid.uuid5(NAMESPACE, str(nhs_identifier) + "UKRR").hex
        xml_program_membership.ExternalId = yhs_external_id

        patient_record.ProgramMemberships.append(xml_program_membership)

    if full_patient_record:
        # TODO: Extract the other stuff here

        # Ethnicity
        if Patient.ethnicity:
            if len(Patient.ethnicity) == 1:
                # TODO: We need a conversion for the READ ethnicity codes
                ethnicity = ukrdc_schema.EthnicGroup()
                ethnicity.Code = Patient.ethnicity
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

        if Patient.cod_edta1:
            cause_of_death = ukrdc_schema.CauseOfDeath()
            diagnosis = ukrdc_schema.CF_EDTA_COD()
            # TODO: The str() can be removed once the DB field is changed.
            diagnosis.Code = str(Patient.cod_edta1)
            diagnosis.CodingStandard = "EDTA_COD"
            cause_of_death.Diagnosis = diagnosis
            cause_of_death.Description = Patient.cod_text

            patient_record.Diagnoses.append(cause_of_death)

        # TODO: COD_EDTA1

        # Blood Type
        # TODO: Need to check UKRR codes match
        if Patient.blood_group:
            patient_record.Patient.BloodGroup = Patient.blood_group
        if Patient.blood_rhesus:
            patient_record.Patient.BloodRhesus = Patient.blood_rhesus

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
                object_session(Patient)
                .execute(
                    sql_string,
                    {"rr_no": Patient.rr_no, "hosp_centre": sending_facility},
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

            data_definition = get_data_definition(cursor)

            #  Add observations
            observations = get_observations(cursor, data_definition, Patient.rr_no)
            if observations:
                patient_record.Observations = pyxb.BIND()
                for observation in observations:
                    patient_record.Observations.append(observation)

            # Add lab orders/results
            lab_orders = get_laborders(cursor, data_definition, Patient.rr_no)
            if lab_orders:
                patient_record.LabOrders = pyxb.BIND()
                for order in lab_orders:
                    patient_record.LabOrders.append(order)

        except Exception:
            raise

        if transplant:
            """
            include transplants
            """
            transplants = get_transplants(cursor, sending_facility, Patient.rr_no)
            if transplants:
                if not patient_record.Encounters:
                    patient_record.Encounters = pyxb.BIND()
                for tran in transplants:
                    patient_record.Encounters.append(tran)

    return patient_record.toDOM().toprettyxml()
