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

import os
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
    'Estimated Number of Annual Pregnancies #':
        'Count_PregnancyEvent',
    'Total number of pregnant women Registered for ANC':
        'Count_PregnantWomen_RegisteredForAntenatalCare',
    'Number of Pregnant women registered within first trimester':
        'Count_PregnantWomen_RegisteredForAntenatalCareWithinFirstTrimester',
    'Total reported deliveries':
        'Count_ChildDeliveryEvent',
    'Institutional deliveries (Public Insts.+Pvt. Insts.)':
        'Count_ChildDeliveryEvent_InAnInstitution',
    'Deliveries Conducted at Public Institutions':
        'Count_ChildDeliveryEvent_InPublicInstitution',
    'Number of Home deliveries':
        'Count_ChildDeliveryEvent_AtHome',
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/Auxillary Nurse Midwife)':
        'Count_ChildDeliveryEvent_AtHome_WithStandbyAssist',
    '% Safe deliveries to Total Reported Deliveries':
        'Count_DeliveryEvent_Safe_AsFractionOf_Count_DeliveryEvent'
}

clean_names = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'Estimated Number of Annual Pregnancies #':
        'Total number of Annual Pregnancies',
    'Total number of pregnant women Registered for ANC':
        'Total number of pregnant women registered for Antenatal Care',
    'Number of Pregnant women registered within first trimester':
        'Number of pregnant women registered for Antenatal Care within first trimester',
    'Total reported deliveries':
        'Total reported child deliveries',
    'Institutional deliveries (Public Insts.+Pvt. Insts.)':
        'Institutional deliveries (includes public and private institutions)',
    'Deliveries Conducted at Public Institutions':
        'Deliveries conducted at public institutions',
    'Number of Home deliveries':
        'Number of home deliveries',
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/Auxillary Nurse Midwife)':
        'Number of home deliveries attended by StandbyAssist (Doctor/Nurse/Auxillary Nurse Midwife)',
    '% Safe deliveries to Total Reported Deliveries':
        'Percentage of safe deliveries to total reported deliveries'
}

module_dir = os.path.dirname(__file__)

if __name__ == '__main__':
    dataset_name = "NHM_MaternalHealth"
    data_folder = os.path.join(module_dir, '../data/')
    csv_path = os.path.join(module_dir, "{}.csv".format(dataset_name))

    # Preprocess files; Generate CSV; Generate TMCF file
    loader = NHMDataLoaderBase(data_folder=data_folder,
                               dataset_name=dataset_name,
                               cols_dict=cols_to_nodes,
                               clean_names=clean_names,
                               final_csv_path=csv_path,
                               module_dir=module_dir)
    loader.generate_csv()
    loader.create_mcf_tmcf()

    # Write README file
    readme_gen = ReadMeGen(dataset_name=dataset_name,
                           dataset_description="Maternal Health Data",
                           data_level="State level",
                           cols_dict=cols_to_nodes,
                           clean_names=clean_names,
                           module_dir=module_dir)
    readme_gen.gen_readme()
