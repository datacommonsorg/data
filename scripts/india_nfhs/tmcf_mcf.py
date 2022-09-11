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

import csv
import pandas as pd
import os
import json
import re

dict_isoCode = {
    "Andhra Pradesh": "IN-AP",
    "Andhra Pradesh Old": "IN-AP",
    "Arunachal Pradesh": "IN-AR",
    "Assam": "IN-AS",
    "Bihar": "IN-BR",
    "Chattisgarh": "IN-CT",
    "Chhattisgarh": "IN-CT",
    "Goa": "IN-GA",
    "Gujarat": "IN-GJ",
    "Haryana": "IN-HR",
    "Himachal Pradesh": "IN-HP",
    "Jharkhand": "IN-JH",
    "Jharkhand#": "IN-JH",
    "Karnataka": "IN-KA",
    "Kerala": "IN-KL",
    "Madhya Pradesh": "IN-MP",
    "Madhya Pradesh#": "IN-MP",
    "Maharashtra": "IN-MH",
    "Manipur": "IN-MN",
    "Meghalaya": "IN-ML",
    "Mizoram": "IN-MZ",
    "Nagaland": "IN-NL",
    "Nagaland#": "IN-NL",
    "Odisha": "IN-OR",
    "Punjab": "IN-PB",
    "Rajasthan": "IN-RJ",
    "Sikkim": "IN-SK",
    "Tamil Nadu": "IN-TN",
    "Tamilnadu": "IN-TN",
    "Telengana": "IN-TG",
    "Telangana": "IN-TG",
    "Tripura": "IN-TR",
    "Uttarakhand": "IN-UT",
    "Uttar Pradesh": "IN-UP",
    "West Bengal": "IN-WB",
    "Andaman and Nicobar Islands": "IN-AN",
    "Andaman & Nicobar Islands": "IN-AN",
    "Andaman & N. Island": "IN-AN",
    "A & N Islands": "IN-AN",
    "Chandigarh": "IN-CH",
    "Dadra and Nagar Haveli": "IN-DN",
    "Dadra & Nagar Haveli": "IN-DN",
    "Dadar Nagar Haveli": "IN-DN",
    "Daman and Diu": "IN-DD",
    "Daman & Diu": "IN-DD",
    "Delhi": "IN-DL",
    "Jammu and Kashmir": "IN-JK",
    "Jammu & Kashmir": "IN-JK",
    "Ladakh": "IN-LA",
    "Lakshadweep": "IN-LD",
    "Lakshwadeep": "IN-LD",
    "Pondicherry": "IN-PY",
    "Puducherry": "IN-PY",
    "Puduchery": "IN-PY",
    "Dadra and Nagar Haveli and Daman and Diu": "IN-DN_DD",
    "all India": "IN",
    "all-India": "IN",
    "All India": "IN"
}

csv_path = "data/6821/6821_source_data.csv"

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: schema:Place
isoCode: C:{dataset_name}->isoCode
"""

TMCF_NODES = """
Node: E:{dataset_name}->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statvar}
measurementMethod: dcs:NHM_HealthInformationManagementSystem
observationAbout: E:{dataset_name}->E0
observationDate: C:{dataset_name}->Date
observationPeriod: "P1Y"
value: C:{dataset_name}->{statvar}
"""

MCF_NODES = """
Node: dcid:{statvar}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
measuredProperty: dcs:{statvar}
statType: dcs:measuredValue
"""

with open('india_nfhs.json') as json_file:
    cols_to_nodes = json.load(json_file)

module_dir = os.path.dirname(__file__)

class NFHSDataLoaderBase(object):
    """
    An object to clean .xls files under 'data/' folder and convert it to csv
    
    Attributes:
        data_folder: folder containing all the data files
        dataset_name: name given to the dataset
        cols_dict: dictionary containing column names in the data files mapped to StatVars
                    (keys contain column names and values contains StatVar names)
    """

    def __init__(self, data_folder, dataset_name, cols_dict, module_dir):
        """
        Constructor
        """
        self.data_folder = data_folder
        self.dataset_name = dataset_name
        self.cols_dict = cols_dict
        self.module_dir = module_dir

        self.raw_df = None
        self.cols_to_extract = list(self.cols_dict.keys())[3:]

    def generate_csv(self):
        df = pd.read_csv(csv_path)
        for i in df['srcStateName']:
            # print(i)
            for j in dict_isoCode.keys():
                state = i.lower()
                if i.lower() == j.lower():
                    df['srcStateName'] = df['srcStateName'].str.replace(i, dict_isoCode[j])

        for i in df['Year']:
            if i == '2019-20':
                df['Year'] = df['Year'].str.replace(i, '2020')
            else:
                df['Year'] = df['Year'].str.replace(i, '2016')
        
        df.rename(columns=cols_to_nodes,inplace=True)
        df.to_csv('DataComplete.csv', index=False)

    def create_mcf_tmcf(self):
        """
        Class method to generate MCF and TMCF files for the current dataset.
        
        """
        tmcf_file = os.path.join(self.module_dir,
                                 "{}.tmcf".format(self.dataset_name))

        mcf_file = os.path.join(self.module_dir,
                                "{}.mcf".format(self.dataset_name))

        with open(tmcf_file, 'w+') as tmcf, open(mcf_file, 'w+') as mcf:
            tmcf.write(TMCF_ISOCODE.format(dataset_name=self.dataset_name))

            statvars_written = []

            for idx, variable in enumerate(self.cols_to_extract):
                if self.cols_dict[variable] not in statvars_written:
                    # Writing TMCF
                    tmcf.write(
                        TMCF_NODES.format(dataset_name=self.dataset_name,
                                          index=idx + 1,
                                          statvar=self.cols_dict[variable]))
                    # Writing MCF
                    mcf.write(
                        MCF_NODES.format(
                            statvar=self.cols_dict[variable],
                            # descript=self.cols_dict[variable].replace('_', ' '),
                            description = re.sub(r"(\w)([A-Z])", r"\1 \2", self.cols_dict[variable].replace('_', ' '))))

                    statvars_written.append(self.cols_dict[variable])

if __name__ == '__main__':
    dataset_name = "NFHS_Health"
    data_folder = os.path.join(module_dir, '../data/')
    loader = NFHSDataLoaderBase(data_folder=data_folder,
                               dataset_name=dataset_name,
                               cols_dict=cols_to_nodes,
                               module_dir=module_dir)

    loader.create_mcf_tmcf()
    # loader.generate_csv()