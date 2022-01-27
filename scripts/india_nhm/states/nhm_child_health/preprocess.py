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

from india_nhm.states.base.data_cleaner import NHMDataLoaderBase
from india_nhm.states.base.readme_generator import ReadMeGen

# Mapping dictionary for data columns and StatVars
cols_to_nodes = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'Total Number of reported live births':
        'Count_BirthEvent_LiveBirth',
    'Total Number of reported Still Births':
        'Count_BirthEvent_StillBirth',
    '% Total Reported Live Births to Total Deliveries':
        'Count_BirthEvent_LiveBirth_AsFractionOf_Count_ChildDeliveryEvent',
    'Number of Infants given BCG':
        'Count_Infant_VaccineAdministered_BCG',
    'Number of Infants given OPV 0 (Birth Dose)':
        'Count_Infant_VaccineAdministered_OPV',
    'Number of Infants given DPT1':
        'Count_Infant_VaccineAdministered_DPTDose1',
    'Number of Infants given DPT2':
        'Count_Infant_VaccineAdministered_DPTDose2',
    'Number of Infants given DPT3':
        'Count_Infant_VaccineAdministered_DPTDose3',
    'Number of Infants given Measles':
        'Count_ChildVaccinationEvent_MMR',
    'Adverse Events Following Imunisation (Deaths)':
        'Count_Infant_VaccineSideEffect_Adverse_Deaths',
    'Adverse Events Following Imunisation (Others)':
        'Count_Infant_VaccineSideEffect_Adverse_Others',
    'Total Number of Infant Deaths reported':
        'Count_Death_Infant'
}
    
clean_names = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'Total Number of reported live births':
        'Total number of reported live births',
    'Total Number of reported Still Births':
        'Total number of reported still births',
    '% Total Reported Live Births to Total Deliveries':
        'Percent of total reported live births to total deliveries',
    'Number of Infants given BCG':
        'Number of infants given BCG vaccine',
    'Number of Infants given OPV 0 (Birth Dose)':
        'Number of infants given OPV 0 Vaccine (Birth Dose)',
    'Number of Infants given DPT1':
        'Number of infants given DPT Vaccine Dose 1',
    'Number of Infants given DPT2':
        'Number of infants given DPT Vaccine Dose 2',
    'Number of Infants given DPT3':
        'Number of infants given DPT Vaccine Dose 3',
    'Number of Infants given Measles':
        'Number of infants given MMR Vaccine',
    'Adverse Events Following Imunisation (Deaths)':
        'Adverse events following immunization (Deaths)',
    'Adverse Events Following Imunisation (Others)':
        'Adverse events following immunization (Others)',
    'Total Number of Infant Deaths reported':
        'Total number of infant deaths reported'
}

if __name__ == '__main__':
    dataset_name = "NHM_ChildHealth"

    # Preprocess files; Generate CSV; Generate TMCF file
    loader = NHMDataLoaderBase(data_folder='../data/',
                               dataset_name=dataset_name,
                               cols_dict=cols_to_nodes,
                               final_csv_path="{}.csv".format(dataset_name))
    loader.generate_csv()
    loader.create_mcf_tmcf()

    # Write README file
    readme_gen = ReadMeGen(dataset_name=dataset_name,
                           dataset_description="Child Health Data",
                           data_level="State level",
                           cols_dict=cols_to_nodes,
                           clean_names=clean_names)
    readme_gen.gen_readme()
