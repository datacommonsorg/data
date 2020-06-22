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


# process dataset 1
df1 = pd.read_excel('https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/0997fa8e-ef7c-43f2-8b9a-94672935fa60/download/healthcare_facility_beds.xlsx',
                    converters={'FACID': lambda x: str(x)})

new_columns = ['GeoId',
               'CALicensedHealthcareFacilityBedFACID',
               'CALicensedHealthcareFacilityName',
               'CALicensedHealthcareFacilityType',
               'Count_HospitalBed_SkilledNursingBed',
               'Count_HospitalBed_SpecialTreatmentProgramBed',
               'Count_HospitalBed_IntermediateCareHabilitativeBed',
               'Count_HospitalBed_IntermediateCareNursingBed',
               'Count_HospitalBed_CongregateLivingHealthFacilityBed',
               'Count_HospitalBed_IntermediateCareBed',
               'Count_HospitalBed_CoronaryCareBed',
               'Count_HospitalBed_IntensiveCareBed',
               'Count_HospitalBed_IntensiveCareNewbornNurseryBed',
               'Count_HospitalBed_PerinatalBed',
               'Count_HospitalBed_UnspecifiedGeneralAcuteCareBed',
               'Count_HospitalBed_BurnBed',
               'Count_HospitalBed_PediatricBed',
               'Count_HospitalBed_RenalTransplantBed',
               'Count_HospitalBed_RehabilitationBed',
               'Count_HospitalBed_AcuteRespiratoryCareBed',
               'Count_HospitalBed_AcutePsychiatricCareBed',
               'Count_HospitalBed_ChemicalDependencyRecoveryBed',
               'Count_HospitalBed_PediatricIntensiveCareUnitBed',
               'Count_HospitalBed_LaborAndDeliveryBed',
               'Count_HospitalBed_IntermediateCareDevelopmentallyDisabledBed',
               'Count_HospitalBed_PsychiatricHealthBed',
               'Count_HospitalBed_PediatricDayAndRespiteCareBed',
               'Count_HospitalBed_DialysisStationsBed',
               'Count_HospitalBed_CorrectionalTreatmentCenterBed']

new_df = pd.DataFrame(columns=new_columns)

FDR_to_type = {
    'SKILLED NURSING FACILITY': 'SkilledNursingFacility',
    'INTERMEDIATE CARE FACILITY-DD/H/N/CN/IID': 'IntermediateCareFacility',
    'CONGREGATE LIVING HEALTH FACILITY': 'CongregateLivingHealthFacility',
    'INTERMEDIATE CARE FACILITY': 'IntermediateCareFacility',
    'HOSPICE FACILITY': 'HospiceFacility',
    'GENERAL ACUTE CARE HOSPITAL': 'GeneralAcuteCareFacility',
    'ACUTE PSYCHIATRIC HOSPITAL': 'AcutePsychiatricFacility',
    'HOSPICE': 'HospiceFacility',
    'PEDIATRIC DAY HEALTH & RESPITE CARE FACILITY': 'PediatricDayHealthAndRespiteCareFacility',
    'CHRONIC DIALYSIS CLINIC': 'ChronicDialysisFacility',
    'CHEMICAL DEPENDENCY RECOVERY HOSPITAL': 'ChemicalDependencyRecoveryFacility',
    'CORRECTIONAL TREATMENT CENTER': 'CorrectionalTreatmentCenterFacility'
}

bed_type_dict = {
    'SKILLED NURSING': 'SkilledNursingBed',
    'SPECIAL TREATMENT PROGRAM': 'SpecialTreatmentProgramBed',
    'INTERMEDIATE CARE/DD HABILITATIVE': 'IntermediateCareHabilitativeBed',
    'INTERMEDIATE CARE/DD NURSING': 'IntermediateCareNursingBed',
    'CONGREGATE LIVING HEALTH FACILITY': 'CongregateLivingHealthFacilityBed',
    'INTERMEDIATE CARE': 'IntermediateCareBed',
    'HOSPICE': 'HospiceBed',
    'CORONARY CARE': 'CoronaryCareBed',
    'INTENSIVE CARE': 'IntensiveCareBed',
    'INTENSIVE CARE NEWBORN NURSERY': 'IntensiveCareNewbornNurseryBed',
    'PERINATAL': 'PerinatalBed',
    'UNSPECIFIED GENERAL ACUTE CARE': 'UnspecifiedGeneralAcuteCareBed',
    'BURN': 'BurnBed',
    'PEDIATRIC': 'PediatricBed',
    'RENAL TRANSPLANT': 'RenalTransplantBed',
    'REHABILITATION': 'RehabilitationBed',
    'ACUTE RESPIRATORY CARE': 'AcuteRespiratoryCareBed',
    'ACUTE PSYCHIATRIC CARE': 'AcutePsychiatricCareBed',
    'CHEMICAL DEPENDENCY RECOVERY': 'ChemicalDependencyRecoveryBed',
    'PEDIATRIC INTENSIVE CARE UNIT': 'PediatricIntensiveCareUnitBed',
    'LABOR AND DELIVERY': 'LaborAndDeliveryBed',
    'INTERMEDIATE CARE/DD': 'IntermediateCareDevelopmentallyDisabledBed',
    'PSYCHIATRIC HEALTH': 'PsychiatricHealthBed',
    'PEDI. DAY & RESPITE CARE': 'PediatricDayAndRespiteCareBed',
    'DIALYSIS STATIONS': 'DialysisStationsBed',
    'CORRECTIONAL TREATMENT CENTER': 'CorrectionalTreatmentCenterBed',
}

df2 = pd.read_excel(
    'https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/d6599aac-ff5e-4693-a295-9f9d646a1f06/download/ca_county_gach_bed_counts.xlsx',
    sheet_name='CA_COUNTY_GACH_BED_COUNTS')

# Generate a dictionary from CA county name to geoId.
counties = df2['COUNTY_NAME'].unique()
county_to_geoID = generate_dcid_for_county(counties)

elmsId_to_index = {}
real_index = 0
for index, row_dict in df1.iterrows():
    elmsId = preserve_leading_zero(row_dict['FACID'])
    stat_var = 'Count_HospitalBed_' + bed_type_dict[row_dict['BED_CAPACITY_TYPE']]
    if elmsId in elmsId_to_index:
        new_df.loc[elmsId_to_index[elmsId], stat_var] = row_dict['BED_CAPACITY']
    else:
        elmsId_to_index[elmsId] = real_index
        real_index = real_index + 1
        new_row = {
            'GeoId': 'dcid:' + county_to_geoID[row_dict['COUNTY_NAME']],
            'CALicensedHealthcareFacilityBedFACID': 'ELMS/' + elmsId,
            'CALicensedHealthcareFacilityName': row_dict['FACNAME'],
            'CALicensedHealthcareFacilityType': 'dcs:' + FDR_to_type[row_dict['FAC_FDR']],
            'Count_HospitalBed_SkilledNursingBed': None,
            'Count_HospitalBed_SpecialTreatmentProgramBed': None,
            'Count_HospitalBed_IntermediateCareHabilitativeBed': None,
            'Count_HospitalBed_IntermediateCareNursingBed': None,
            'Count_HospitalBed_CongregateLivingHealthFacilityBed': None,
            'Count_HospitalBed_IntermediateCareBed': None,
            'Count_HospitalBed_CoronaryCareBed': None,
            'Count_HospitalBed_IntensiveCareBed': None,
            'Count_HospitalBed_IntensiveCareNewbornNurseryBed': None,
            'Count_HospitalBed_PerinatalBed': None,
            'Count_HospitalBed_UnspecifiedGeneralAcuteCareBed': None,
            'Count_HospitalBed_BurnBed': None,
            'Count_HospitalBed_PediatricBed': None,
            'Count_HospitalBed_RenalTransplantBed': None,
            'Count_HospitalBed_RehabilitationBed': None,
            'Count_HospitalBed_AcuteRespiratoryCareBed': None,
            'Count_HospitalBed_AcutePsychiatricCareBed': None,
            'Count_HospitalBed_ChemicalDependencyRecoveryBed': None,
            'Count_HospitalBed_PediatricIntensiveCareUnitBed': None,
            'Count_HospitalBed_LaborAndDeliveryBed': None,
            'Count_HospitalBed_IntermediateCareDevelopmentallyDisabledBed': None,
            'Count_HospitalBed_PsychiatricHealthBed': None,
            'Count_HospitalBed_PediatricDayAndRespiteCareBed': None,
            'Count_HospitalBed_DialysisStationsBed': None,
            'Count_HospitalBed_CorrectionalTreatmentCenterBed': None
        }
        new_row[stat_var] = row_dict['BED_CAPACITY']
        new_df = new_df.append(new_row, ignore_index=True)

new_df.to_csv('CA_Licensed_Healthcare_Facility_Types_And_Counts.csv')

# Output as a tmcf file.
# Facility node, facility containedIn a county
TEMPLATE_MCF_FAC_1 = """
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E0
healthcareFacilityName: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityName
typeOf: schema:Hospital
dcid: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityBedFACID
healthcareFacilityType: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->CALicensedHealthcareFacilityType
containedIn: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->GeoId
"""

# observation node, observationAbout facility
TEMPLATE_MCF_TEMPLATE_1 = """
Node: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E{index}
typeOf: StatVarObservation
variableMeasured: {stat_var}
observationDate: "2020-06-01"
observationAbout: E:CA_Licensed_Healthcare_Facility_Types_And_Counts->E0
value: C:CA_Licensed_Healthcare_Facility_Types_And_Counts->{stat_var}
"""

with open('CA_Licensed_Healthcare_Facility_Types_And_Counts.tmcf', 'w', newline='') as f_out:
    f_out.write(TEMPLATE_MCF_FAC_1)

    stat_vars = new_columns[4:]
    for i in range(len(stat_vars)):
        f_out.write(TEMPLATE_MCF_TEMPLATE_1.format_map({'index': i + 1, 'stat_var': stat_vars[i]}))

# Proprocess for dataset2 and output tmcf file.

tempDF2 = pd.read_excel(
    'https://data.chhs.ca.gov/dataset/09b8ad0e-aca6-4147-b78d-bdaad872f30b/resource/d6599aac-ff5e-4693-a295-9f9d646a1f06/download/ca_county_gach_bed_counts.xlsx',
    sheet_name='CA_COUNTY_GACH_BED_COUNTS')
tempDF2.to_csv('temp_data2.csv')

new_columns_2 = ['GeoId', 'CACountyName', 'CALicensedHealthcareFacilityType',
                 'Count_Hosptital_GeneralAcuteCare',
                 'Count_HospitalBed_GeneralAcuteCare',
                 'Count_HospitalBed_GeneralAcuteCare_AcutePsychiatricCareBed',
                 'Count_HospitalBed_GeneralAcuteCare_AcuteRespiratoryCareBed',
                 'Count_HospitalBed_GeneralAcuteCare_BurnBed',
                 'Count_HospitalBed_GeneralAcuteCare_ChemicalDependencyRecoveryBed',
                 'Count_HospitalBed_GeneralAcuteCare_CoronaryCareBed',
                 'Count_HospitalBed_GeneralAcuteCare_IntensiveCareBed',
                 'Count_HospitalBed_GeneralAcuteCare_IntensiveCareNewbornNurseryBed',
                 'Count_HospitalBed_GeneralAcuteCare_IntermediateCareBed',
                 'Count_HospitalBed_GeneralAcuteCare_LaborAndDeliveryBed',
                 'Count_HospitalBed_GeneralAcuteCare_PediatricBed',
                 'Count_HospitalBed_GeneralAcuteCare_PediatricIntensiveCareUnitBed',
                 'Count_HospitalBed_GeneralAcuteCare_PerinatalBed',
                 'Count_HospitalBed_GeneralAcuteCare_RehabilitationBed',
                 'Count_HospitalBed_GeneralAcuteCare_RenalTransplantBed',
                 'Count_HospitalBed_GeneralAcuteCare_UnspecifiedGeneralAcuteCareBed']

# start process dataset and also add one new column called 'ALicensedHealthcareFacilityCountyId'.
with open('CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.csv', 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=new_columns_2, lineterminator='\n')
    with open('temp_data2.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        writer.writeheader()

        for row_dict in reader:
            processed_dict = {
                'GeoId': 'dcid:' + county_to_geoID[row_dict['COUNTY_NAME']],
                'CACountyName': row_dict['COUNTY_NAME'],
                'CALicensedHealthcareFacilityType': FDR_to_type[row_dict['FAC_FDR']],
                'Count_Hosptital_GeneralAcuteCare': row_dict['FACILITY_COUNT'],
                'Count_HospitalBed_GeneralAcuteCare': row_dict['BED_CAPACITY'],
                'Count_HospitalBed_GeneralAcuteCare_AcutePsychiatricCareBed': row_dict['ACUTE PSYCHIATRIC CARE'],
                'Count_HospitalBed_GeneralAcuteCare_AcuteRespiratoryCareBed': row_dict['ACUTE RESPIRATORY CARE'],
                'Count_HospitalBed_GeneralAcuteCare_BurnBed': row_dict['BURN'],
                'Count_HospitalBed_GeneralAcuteCare_ChemicalDependencyRecoveryBed': row_dict['CHEMICAL DEPENDENCY RECOVERY'],
                'Count_HospitalBed_GeneralAcuteCare_CoronaryCareBed': row_dict['CORONARY CARE'],
                'Count_HospitalBed_GeneralAcuteCare_IntensiveCareBed': row_dict['INTENSIVE CARE'],
                'Count_HospitalBed_GeneralAcuteCare_IntensiveCareNewbornNurseryBed': row_dict['INTENSIVE CARE NEWBORN NURSERY'],
                'Count_HospitalBed_GeneralAcuteCare_IntermediateCareBed': row_dict['INTERMEDIATE CARE'],
                'Count_HospitalBed_GeneralAcuteCare_LaborAndDeliveryBed': row_dict['LABOR AND DELIVERY'],
                'Count_HospitalBed_GeneralAcuteCare_PediatricBed': row_dict['PEDIATRIC'],
                'Count_HospitalBed_GeneralAcuteCare_PediatricIntensiveCareUnitBed': row_dict['PEDIATRIC INTENSIVE CARE UNIT'],
                'Count_HospitalBed_GeneralAcuteCare_PerinatalBed': row_dict['PERINATAL'],
                'Count_HospitalBed_GeneralAcuteCare_RehabilitationBed': row_dict['REHABILITATION'],
                'Count_HospitalBed_GeneralAcuteCare_RenalTransplantBed': row_dict['RENAL TRANSPLANT'],
                'Count_HospitalBed_GeneralAcuteCare_UnspecifiedGeneralAcuteCareBed': row_dict['UNSPECIFIED GENERAL ACUTE CARE']
            }

            writer.writerow(processed_dict)

os.remove('temp_data2.csv')

TEMPLATE_MCF_TEMPLATE_2 = """
Node: E:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationDate: "2020-04-13"
observationAbout: C:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->GeoId
value: C:CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts->{stat_var}
"""

stat_vars = new_columns_2[3:]

with open('CA_County_General_Acute_Care_Hospitals_Bed_Types_And_Counts.tmcf', 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        f_out.write(TEMPLATE_MCF_TEMPLATE_2.format_map({'index': i, 'stat_var':stat_vars[i]}))