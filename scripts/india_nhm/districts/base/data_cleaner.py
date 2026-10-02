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
import difflib

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: dcs:AdministrativeArea2
lgdCode: C:{dataset_name}->lgdCode
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

MCF_NODES = """Node: dcid:{statvar}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: schema:Person
measuredProperty: dcid:{statvar}
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

    def __init__(self, data_folder, dataset_name, cols_dict, clean_names,
                 final_csv_path, module_dir):
        """
        Constructor
        """
        self.data_folder = data_folder
        self.dataset_name = dataset_name
        self.cols_dict = cols_dict
        self.clean_names = clean_names
        self.final_csv_path = final_csv_path
        self.module_dir = module_dir

        self.raw_df = None
        self.missing_dists = []

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

        lgd_file = os.path.join(self.module_dir, '../data/lgd_table.csv')
        self.dist_code = pd.read_csv(lgd_file, dtype={'DistrictCode': str})

        # Loop through each year file
        for file in os.listdir(self.data_folder):
            fname, fext = os.path.splitext(
                file)  # fname contains year of the file
            date = ''.join(['20', fname[-2:],
                            '-03'])  # date is set as March of every year

            if fext == '.xlsx':
                # Reading .xls file as html and preprocessing multiindex

                self.raw_df = pd.read_excel(os.path.join(
                    self.data_folder, file))
                # self.raw_df.columns = self.raw_df.columns.droplevel()

                cleaned_df = pd.DataFrame()
                cleaned_df['District'] = self.raw_df[
                    'Unnamed: 2']  # Unnamed:2 column has district names
                cleaned_df['Date'] = date

                # If no columns specified, extract all except first two (index and state name)
                if not self.cols_to_extract:
                    self.cols_to_extract = list(
                        set(self.raw_df.columns.droplevel(-1)[2:]))

                # Extract specified columns from raw dataframe if it exists
                for col in self.cols_to_extract:
                    if col in self.raw_df.columns:
                        cleaned_df[col] = self.raw_df[col].iloc[1:]
                    else:
                        continue

                df_full = pd.concat([df_full, cleaned_df], ignore_index=True)

        # Mapping District Names to corresponding LGD Codes
        df_full['DistrictCode'] = df_full.apply(
            lambda row: self._get_district_code(row), axis=1)

        # Reverse mapping LGD codes to District names to remove
        # spelling variations in names
        df_full['District'] = df_full.apply(
            lambda row: self._get_district_name(row), axis=1)

        # Converting column names according to schema and saving it as csv
        df_full.columns = df_full.columns.map(self.cols_dict)
        df_full = df_full.groupby(
            level=0).first()  # merging columns with same names

        # Dropping unwanted rows
        df_full = self._drop_unwanted_rows(df_full)

        df_full.iloc[2:].to_csv(self.final_csv_path, index=False)

    def create_mcf_tmcf(self):
        """
        Class method to generate MCF and TMCF files for the current dataset.
        
        """
        tmcf_file = os.path.join(self.module_dir,
                                 "{}.tmcf".format(self.dataset_name))

        mcf_file = os.path.join(self.module_dir,
                                "{}.mcf".format(self.dataset_name))

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
                            description=self.clean_names[variable]))

                    statvars_written.append(self.cols_dict[variable])

    def _get_district_code(self, row):
        """
        Class method to get a complete match or partial match to district names.
        For example, this function can identify 'Nilgiris' and 'The Niligris' as same name
        
        Cutoff = 0.8 captures all of the variations in the same district name
        
        """
        # if there is a close match for district name,
        # return district code from Local Govt. Directory (LGD)
        # else return None
        if pd.notna(row['District']):
            close_match = difflib.get_close_matches(
                row['District'].upper(),
                self.dist_code['DistrictName(InEnglish)'],
                n=1,
                cutoff=0.8)
            if close_match:
                lgd = self.dist_code[self.dist_code['DistrictName(InEnglish)']
                                     ==
                                     close_match[0]]['DistrictCode'].values[0]
                return str(lgd).zfill(3)
            else:
                close_match = difflib.get_close_matches(
                    row['District'].upper(),
                    self.dist_code['AlternateLabel'].astype(str),
                    n=1,
                    cutoff=0.8)
                if close_match:
                    lgd = self.dist_code[
                        self.dist_code['AlternateLabel'] ==
                        close_match[0]]['DistrictCode'].values[0]

                    return str(lgd).zfill(3)

            return None

    def _get_district_name(self, row):
        df = self.dist_code[self.dist_code['DistrictCode'] ==
                            row['DistrictCode']]
        try:
            return df['DistrictName(InEnglish)'].unique()[0].capitalize()
        except IndexError:
            return None

    def _drop_unwanted_rows(self, df):
        """
        Class method to drop unwanted rows from dataset.
        This method will drop rows with empty District names and rows with
        'Indicators.1' string (this is one of the headers from dataset)
        """

        unwanted_values = ['Indicators.1']
        df = df[df['District'].isin(unwanted_values) == False]
        df = df[df['District'].isna() == False]
        df = df.drop_duplicates(subset=['Date', 'District', 'lgdCode'],
                                keep=False)

        return df
