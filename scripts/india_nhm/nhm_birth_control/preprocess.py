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

import sys

sys.path.append("..")

from base.data_cleaner import NHMDataLoaderBase
from base.readme_generator import ReadMeGen

# Mapping dictionary for data columns and StatVars
# Mutiple keys for some same StatVar since column name is changed in recent datasets
cols_to_nodes = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'Number of Vasectomies Conducted (Public + Pvt.)':
        'Count_BirthControlEvent_Vasectomy',
    'Number of Vasectomies Conducted':
        'Count_BirthControlEvent_Vasectomy',
    'Number of Tubectomies Conducted (Public + Pvt.)':
        'Count_BirthControlEvent_Tubectomy',
    'Number of Tubectomies Conducted':
        'Count_BirthControlEvent_Tubectomy',
    'Total Sterilisation Conducted':
        'Count_BirthControlEvent_Sterilization',
    '% Male Sterlisation (Vasectomies) to Total sterilisation':
        'Count_BirthControlEvent_Vasectomy_AsFractionOf_Count_BirthControlEvent_Sterlization',
    'Total cases of deaths following Sterlisation ( Male + Female)':
        'Count_Death_BirthControlSterilization',
    'Total IUCD Insertions done(public+private)':
        'Count_BirthControlEvent_IUCDInsertion',
    'Total Interval IUCD Insertions done':
        'Count_BirthControlEvent_IUCDInsertion',
    '% IUCD insertions in public plus private institutions to all family planning methods ( IUCD plus permanent)':
        'Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent',
    '% IUCD insertions to all family planning methods ( IUCD plus permanent)':
        'Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent',
    'Oral Pills distributed':
        'Count_ContraceptiveDistribution_OralPill',
    'Combined Oral Pills distributed':
        'Count_ContraceptiveDistribution_OralPill',
    'Condom pieces distributed':
        'Count_ContraceptiveDistribution_Condom',
}

if __name__ == '__main__':
    dataset_name = "NHM_BirthControl"

    # Preprocess files; Generate CSV; Generate TMCF file
    loader = NHMDataLoaderBase(data_folder='../data/',
                               dataset_name=dataset_name,
                               cols_dict=cols_to_nodes,
                               final_csv_path="{}.csv".format(dataset_name))
    loader.generate_csv()
    loader.create_mcf_tmcf()

    # Write README file
    readme_gen = ReadMeGen(dataset_name=dataset_name,
                           dataset_description="Birth Control Data",
                           data_level="State level",
                           cols_dict=cols_to_nodes)
    readme_gen.gen_readme()
