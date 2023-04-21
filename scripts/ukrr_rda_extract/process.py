"""
Ported from: https://github.com/renalreg/ukrr_rda_extract 
This(These) scripts seem to be primarily what are using the pyxb utils so I have put it here to drive the models. 
"""

from datetime import datetime
import sys

import pyxb
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ukrdc.database import Connection
from ukrr_models.rr_models import UKRRPatient
from ukrr_models.utils import as_pyxb_xml, create_temp_treatments, get_xml_datetime 
import ukrdc.cohort_extract.ukrr_db as ukrr_db


OUTPUT_DIR = 'output/'

#renalreg_engine = Connection.get_engine_from_file(None, "ukrdc_rrsqllive")
url = Connection.get_engine_from_file(None, "ukrdc_rrsqllive").url
renalreg_engine = create_engine(url=url,use_setinputsizes=False)
renalreg_connection = renalreg_engine.raw_connection()
renalreg_cursor = renalreg_connection.cursor()
renalreg_sessionmaker = sessionmaker(bind=renalreg_engine)
renalreg_session = renalreg_sessionmaker()


print('START - Cache Treatments')
create_temp_treatments(renalreg_cursor)
print('END - Cache Treatments')

# TODO: In the future we will want to just want to identify patients with updated
# records. I am unsure if modifying the cohort_extract to add that as a criteria
# will be appropriate.
print('START - Get Cohort')
ukrr_patients = ukrr_db.process(start_date=datetime(2018, 1, 1), date_death=datetime(2018, 1, 1))
print('END - Get Cohort')

for row in ukrr_patients:

    # This is to try to handle the DB Connection dropping mid-query.
    while 1:
        rr_no = row[0]
        ukrr_patient = renalreg_session.query(UKRRPatient).filter(UKRRPatient.rr_no==rr_no).first()

        # TODO: Change this to sqlalchemy
        sql_string = """
            SELECT DISTINCT
                HOSP_CENTRE
            FROM
                QUARTERLY_TREATMENT
            WHERE
                RR_NO = :rr_no
        """
        
        results = renalreg_session.execute(text(sql_string), {"rr_no":rr_no} )
        #renalreg_cursor.execute(sql_string, rr_no)
        #results = renalreg_cursor.fetchall()
        
        for hosp_centre in [row[0] for row in results]:
            print(rr_no, hosp_centre)
            xml_string = as_pyxb_xml(ukrr_patient, sending_facility=hosp_centre, treatment_cache=True)
            output_file = open(OUTPUT_DIR + f"{hosp_centre}_{rr_no}.xml", 'w')
            output_file.write(xml_string)
            output_file.close()
            
        break