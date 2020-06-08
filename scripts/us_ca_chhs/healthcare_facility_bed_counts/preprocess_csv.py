# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import csv
import os
from preprocess_csv_helper import preserve_leading_zero
from preprocess_csv_helper import generate_dcid_for_county

# Read two datasets
df1 = pd.read_excel('https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/0997fa8e-ef7c-43f2-8b9a-94672935fa60/download/healthcare_facility_beds.xlsx',
                    converters={'FACID': lambda x: str(x)})

df2 = pd.read_excel(
    'https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/d6599aac-ff5e-4693-a295-9f9d646a1f06/download/ca_county_gach_bed_counts.xlsx',
    sheet_name='CA_COUNTY_GACH_BED_COUNTS')

# Generate a dictionary from CA county name to geoId.
counties = df2['COUNTY_NAME'].unique()
county_to_geoID = generate_dcid_for_county(counties)

# Preprocess for dataset 1 and output tmcf file.
df1.to_csv('temp_data.csv')
new_columns_1 = ['GeoId', 'CACountyName', 'CALicensedHealthcareFacilityBedFACID', 'CALicensedHealthcareFacilityName',
                 'CALicensedHealthcareFacilityType', 'CALicensedHealthcareFacilityBedType',
                 'CALicensedHealthcareFacilityBedCapacity']

FDR_to_type = {
    'SKILLED NURSING FACILITY': 'SkilledNursingFacility',
    'INTERMEDIATE CARE FACILITY-DD/H/N/CN/IID': 'IntermediateCareFacility',
    'CONGREGATE LIVING HEALTH FACILITY': 'CongregateLivingHealthFacility',
    'INTERMEDIATE CARE FACILITY': 'IntermediateCareFacility',
    'HOSPICE FACILITY': 'HospiceFacility',
    'GENERAL ACUTE CARE HOSPITAL': 'GeneralAcuteCareFacility',
    'ACUTE PSYCHIATRIC HOSPITAL': 'AcutePsychiatricFacility',
    'HOSPICE': 'HospiceFacility',
    'PEDIATRIC DAY HEALTH & RESPITE CARE FACILITY': 'PediatricDayHealth&RespiteCareFacility',
    'CHRONIC DIALYSIS CLINIC': 'ChronicDialysisFacility',
    'CHEMICAL DEPENDENCY RECOVERY HOSPITAL': 'ChemicalDependencyRecoveryFacility',
    'CORRECTIONAL TREATMENT CENTER': 'CorrectionalTreatmentCenterFacility'
}

# start process dataset and also add one new column called 'ALicensedHealthcareFacilityCountyId'.
with open('CA_Licensed_Healthcare_Facility_Types_And_Counts.csv', 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=new_columns_1, lineterminator='\n')
    with open('temp_data.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        writer.writeheader()

        for row_dict in reader:
            processed_dict = {
                'GeoId': county_to_geoID[row_dict['COUNTY_NAME']],
                'CACountyName': row_dict['COUNTY_NAME'],
                'CALicensedHealthcareFacilityBedFACID': 'ELMS/' + preserve_leading_zero(row_dict['FACID']),
                'CALicensedHealthcareFacilityName': row_dict['FACNAME'],
                'CALicensedHealthcareFacilityType': FDR_to_type[row_dict['FAC_FDR']],
                'CALicensedHealthcareFacilityBedType': row_dict['BED_CAPACITY_TYPE'],
                'CALicensedHealthcareFacilityBedCapacity': row_dict['BED_CAPACITY']
            }

            writer.writerow(processed_dict)

os.remove('temp_data.csv')

# Output as a tmcf file.
# county node
TEMPLATE_MCF_GEO_1 = """
# CA county node
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E0
typeOf: schema:County
dcid: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->GeoId
"""

# facility type
TEMPLATE_MCF_FAC_TYPE_1 = """
# facilityType node.
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E1
typeOf: dcs:MedicalFacilityTypeEnum
dcid: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityType
"""

# Facility
# facility containedIn a county
TEMPLATE_MCF_FAC_1 = """
# facility node, containedIn County.
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E2
healthcareFacilityName: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityName
typeOf: schema:Hospital
dcid: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityBedFACID
healthcareFacilityType: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E1
containedIn: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E0
"""

# observation node, observationAbout facility
TEMPLATE_MCF_TEMPLATE_1 = """
# StatVarObservation node, observationAbout facility.
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E3
typeOf: StatVarObservation
variableMeasured: HealthcareFacilityBedCount
observationDate: "2020-06-01"
observationAbout: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E2
healthcareFacilityBedType: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityBedType
value: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityBedCapacity
"""

with open('CA_Licensed_Healthcare_Facility_Types_And_Counts.tmcf', 'w', newline='') as f_out:
    f_out.write(TEMPLATE_MCF_GEO_1)
    f_out.write(TEMPLATE_MCF_FAC_TYPE_1)
    f_out.write(TEMPLATE_MCF_FAC_1)
    f_out.write(TEMPLATE_MCF_TEMPLATE_1)


# Proprocess for dataset2 and output tmcf file.

tempDF2 = pd.read_excel(
    'https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/d6599aac-ff5e-4693-a295-9f9d646a1f06/download/ca_county_gach_bed_counts.xlsx',
    sheet_name='CA_COUNTY_GACH_BED_COUNTS')
tempDF2.to_csv('temp_data2.csv')

new_columns_2 = ['GeoId', 'CACountyName', 'CALicensedHealthcareFacilityType',
                 'HospitalCount', 'GeneralAcuteCareHospitalBedCount',
                 'GeneralAcuteCareHospitalAcutePsychiatricCareBedCount',
                 'GeneralAcuteCareHospitalAcuteRespiratoryCareBedCount',
                 'GeneralAcuteCareHospitalBURNBedCount',
                 'GeneralAcuteCareHospitalChemicalDependencyRecoveryBedCount',
                 'GeneralAcuteCareHospitalCoronaryCareBedCount',
                 'GeneralAcuteCareHospitalIntensiveCareBedCount',
                 'GeneralAcuteCareHospitalIntensiveCareNewbornNurseryBedCount',
                 'GeneralAcuteCareHospitalIntermediateCareBedCount',
                 'GeneralAcuteCareHospitalLaborAndDeliveryBedCount',
                 'GeneralAcuteCareHospitalPediatricBedCount',
                 'GeneralAcuteCareHospitalPediatricIntensiveCareUnitBedCount',
                 'GeneralAcuteCareHospitalPerinatalBedCount',
                 'GeneralAcuteCareHospitalRehabilitationBedCount',
                 'GeneralAcuteCareHospitalRenalTransplantBedCount',
                 'GeneralAcuteCareHospitalUnspecifiedGeneralAcuteCareBedCount']

# start process dataset and also add one new column called 'ALicensedHealthcareFacilityCountyId'.
with open('CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.csv', 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=new_columns_2, lineterminator='\n')
    with open('temp_data2.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        writer.writeheader()

        for row_dict in reader:
            processed_dict = {
                'GeoId': county_to_geoID[row_dict['COUNTY_NAME']],
                'CACountyName': row_dict['COUNTY_NAME'],
                'CALicensedHealthcareFacilityType': FDR_to_type[row_dict['FAC_FDR']],
                'HospitalCount': row_dict['FACILITY_COUNT'],
                'GeneralAcuteCareHospitalBedCount': row_dict['BED_CAPACITY'],
                'GeneralAcuteCareHospitalAcutePsychiatricCareBedCount': row_dict['ACUTE PSYCHIATRIC CARE'],
                'GeneralAcuteCareHospitalAcuteRespiratoryCareBedCount': row_dict['ACUTE RESPIRATORY CARE'],
                'GeneralAcuteCareHospitalBURNBedCount': row_dict['BURN'],
                'GeneralAcuteCareHospitalChemicalDependencyRecoveryBedCount': row_dict['CHEMICAL DEPENDENCY RECOVERY'],
                'GeneralAcuteCareHospitalCoronaryCareBedCount': row_dict['CORONARY CARE'],
                'GeneralAcuteCareHospitalIntensiveCareBedCount': row_dict['INTENSIVE CARE'],
                'GeneralAcuteCareHospitalIntensiveCareNewbornNurseryBedCount': row_dict['INTENSIVE CARE NEWBORN NURSERY'],
                'GeneralAcuteCareHospitalIntermediateCareBedCount': row_dict['INTERMEDIATE CARE'],
                'GeneralAcuteCareHospitalLaborAndDeliveryBedCount': row_dict['LABOR AND DELIVERY'],
                'GeneralAcuteCareHospitalPediatricBedCount': row_dict['PEDIATRIC'],
                'GeneralAcuteCareHospitalPediatricIntensiveCareUnitBedCount': row_dict['PEDIATRIC INTENSIVE CARE UNIT'],
                'GeneralAcuteCareHospitalPerinatalBedCount': row_dict['PERINATAL'],
                'GeneralAcuteCareHospitalRehabilitationBedCount': row_dict['REHABILITATION'],
                'GeneralAcuteCareHospitalRenalTransplantBedCount': row_dict['RENAL TRANSPLANT'],
                'GeneralAcuteCareHospitalUnspecifiedGeneralAcuteCareBedCount': row_dict['UNSPECIFIED GENERAL ACUTE CARE']
            }

            writer.writerow(processed_dict)

os.remove('temp_data2.csv')

TEMPLATE_MCF_GEO_2 = """
# County node.
Node: E:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->E0
typeOf: schema:County
dcid: C:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->GeoId
"""

TEMPLATE_MCF_TEMPLATE_2 = """
Node: E:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationDate: "2020-04-13"
observationAbout: E:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->E0
value: C:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->{stat_var}
"""

stat_vars = new_columns_2[3:5]

with open('CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.tmcf', 'w', newline='') as f_out:
    f_out.write(TEMPLATE_MCF_GEO_2)
    for i in range(len(stat_vars)):
        f_out.write(TEMPLATE_MCF_TEMPLATE_2.format_map({'index': i + 1, 'stat_var':stat_vars[i]}))