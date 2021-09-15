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

import os
from base.data_cleaner import NHMDataLoaderBase
from base.readme_generator import ReadMeGen

# Mapping dictionary for data columns and StatVars
cols_to_nodes = {
        "Total Number of reported live births": "Count_ChildBirthEvent_Live",
        "Total Number of reported Still Births" : "Count_ChildBirthEvent_Still",
        "% Live Births to Total Deliveries" : "Count_ChildBirthEvent_Live_AsFractionOf_Count_ChildDeliveryEvent",
        "Number of Infants given BCG" : "Count_ChildVaccinationEvent_BCG",
        "Number of Infants given OPV 0 (Birth Dose)" : "Count_ChildVaccinationEvent_OPV",
        "Number of Infants given DPT1" : "Count_ChildVaccinationEvent_DPT_FirstDose",
        "Number of Infants given DPT2" : "Count_ChildVaccinationEvent_DPT_SecondDose",
        "Number of Infants given DPT3" : "Count_ChildVaccinationEvent_DPT_ThirdDose",
        "Number of Infants given Measles" : "Count_ChildVaccinationEvent_Measles",
        "Adverse Events Following Immunisation" : "Count_ChildVaccinationEvent_AdverseEvents_Death",
        "Total Number of Infant Deaths reported" : "Count_ChildDeathEvent"
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
                           cols_dict=cols_to_nodes)
    readme_gen.gen_readme()
