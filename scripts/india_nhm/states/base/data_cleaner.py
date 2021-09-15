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
import pandas as pd

INDIA_ISO_CODES = {
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

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: schema:Place
isoCode: C:{dataset_name}->isoCode
"""

TMCF_NODES = """
Node: E:{dataset_name}->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:indianNHM/{statvar}
measurementMethod: dcs:NHM_HealthInformationManagementSystem
observationAbout: C:{dataset_name}->E0
observationDate: C:{dataset_name}->Date
observationPeriod: "P1Y"
value: C:{dataset_name}->{statvar}
"""

MCF_NODES = """Node: dcid:indianNHM/{statvar}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
measuredProperty: dcs:indianNHM/{statvar}
statType: dcs:measuredValue
"""


class NHMDataLoaderBase(object):
    """
    An object to clean .xls files under 'data/' folder and convert it to csv
    
    Attributes:
        data_folder: folder containing all the data files
        dataset_name: name given to the dataset
        cols_dict: dictionary containing column names in the data files mapped to StatVars
                    (keys contain column names and values contains StatVar names)
    """
    def __init__(self, data_folder, dataset_name, cols_dict, final_csv_path):
        """
        Constructor
        """
        self.data_folder = data_folder
        self.dataset_name = dataset_name
        self.cols_dict = cols_dict
        self.final_csv_path = final_csv_path

        self.raw_df = None

        # Ignoring the first 3 elements (State, isoCode, Date) in the dictionary map
        self.cols_to_extract = list(self.cols_dict.keys())[3:]

    def generate_csv(self):
        """
        Class method to preprocess the data file for each available year, extract t
        he columns and map the columns to schema.
        
        The dataframe is saved as a csv file in current directory.
        Returns:
            pandas dataframe: Cleaned dataframe.
        """
        df_full = pd.DataFrame(columns=list(self.cols_dict.keys()))

        # Loop through each year file
        for file in os.listdir(self.data_folder):
            fname, fext = os.path.splitext(
                file)  # fname contains year of the file
            date = ''.join(['20', fname[-2:],
                            '-03'])  # date is set as March of every year

            if fext == '.xls':
                # Reading .xls file as html and preprocessing multiindex
                self.raw_df = pd.read_html(os.path.join(
                    self.data_folder, file))[0]
                self.raw_df.columns = self.raw_df.columns.droplevel()

                cleaned_df = pd.DataFrame()
                cleaned_df['State'] = self.raw_df['Indicators']['Indicators.1']
                cleaned_df['isoCode'] = cleaned_df['State'].map(
                    INDIA_ISO_CODES)
                cleaned_df['Date'] = date

                # If no columns specified, extract all except first two (index and state name)
                if not self.cols_to_extract:
                    self.cols_to_extract = list(
                        set(self.raw_df.columns.droplevel(-1)[2:]))

                # Extract specified columns from raw dataframe if it exists
                for col in self.cols_to_extract:
                    if col in self.raw_df.columns:
                        cleaned_df[col] = self.raw_df[col][fname]
                    else:
                        continue

                df_full = df_full.append(cleaned_df, ignore_index=True)

        # Converting column names according to schema and saving it as csv
        df_full.columns = df_full.columns.map(self.cols_dict)
        df_full.to_csv(self.final_csv_path, index=False)

        return df_full

    def create_mcf_tmcf(self):
        """
        Class method to generate MCF and TMCF files for the current dataset.
        
        """
        tmcf_file = "{}.tmcf".format(self.dataset_name)
        mcf_file = "{}.mcf".format(self.dataset_name)

        with open(tmcf_file, 'w+') as tmcf, open(mcf_file, 'w+') as mcf:
            # Writing isoCODE entity
            tmcf.write(TMCF_ISOCODE.format(dataset_name=self.dataset_name))

            # Keeping track of written StatVars
            # Some columns in NHM_FamilyPlanning have same StatVar for multiple cols
            statvars_written = []

            # Writing nodes for each StatVar
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
                            description=str(variable).capitalize()))

                    statvars_written.append(self.cols_dict[variable])
