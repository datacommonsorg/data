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
    'IPD (Number)':
        'Count_Inpatient',
    'OPD (Number)':
        'Count_Outpatient',
    'OPD (Allopathic)':
        'Count_Outpatient',
    'Number of Major Operations':
        'Count_SurgicalProcedure_Major',
    'Number of Minor Operations':
        'Count_SurgicalProcedure_Minor',
    '% Inpatient Deaths to Total IPD':
        'Count_Inpatient_Deceased_AsFractionOf_Count_Inpatient',
    'Ayush OPD (Number)':
        'Count_Outpatient_Ayush',
}

clean_names = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'IPD (Number)':
        'Number of Inpatients',
    'OPD (Number)':
        'Number of Outpatients',
    'OPD (Allopathic)':
        'Number of Outpatients',
    'Number of Major Operations':
        'Number of Major Surgeries',
    'Number of Minor Operations':
        'Number of Minor Surgeries',
    '% Inpatient Deaths to Total IPD':
        'Percent of Inpatient Deaths to Total Inpatients',
    'Ayush OPD (Number)':
        'Number of Outpatients - AYUSH (Ayurveda, Yoga and Naturopathy, Unani, Siddha and Homeopathy)',
}

module_dir = os.path.dirname(__file__)

if __name__ == '__main__':
    dataset_name = "NHM_GeneralStats"
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
                           dataset_description="General Health Statistics Data",
                           data_level="State level",
                           cols_dict=cols_to_nodes,
                           clean_names=clean_names,
                           module_dir=module_dir)
    readme_gen.gen_readme()