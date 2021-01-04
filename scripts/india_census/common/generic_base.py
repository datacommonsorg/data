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
import json
import csv
import copy
import pandas as pd

CENSUS_DATA_COLUMN_START = 7


class CensusGenericDataLoaderBase(object):
    GENERIC_TEMPLATE_STAT_VAR = """Node: dcid:indianCensus/{name}
description: "{description}"
typeOf: dcs:StatisticalVariable
populationType: schema:Thing
measuredProperty: dcs:indianCensus/{name}

"""

    GENERIC_TEMPLATE_TMCF = """Node: E:IndiaCensus{year}_{dataset_name}->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:IndiaCensus{year}_{dataset_name}->StatisticalVariable
observationDate: C:IndiaCensus{year}_{dataset_name}->Year
observationAbout: E:IndiaCensus{year}_{dataset_name}->E1
value: C:IndiaCensus{year}_{dataset_name}->Value

Node: E:IndiaCensus{year}_{dataset_name}->E1
typeOf: schema:Place
indianCensusAreaCode{year}: C:IndiaCensus{year}_{dataset_name}->census_location_id"""
    """An object that represents Census Data and its variables.
    
    Attributes:
        census_columns (list): It will have all the data column names of a dataset
        census_year : Census year
        csv_file_path : Path where cleaned csv file will be saved
        data_file_path : Input XLS file from Census of India. Can be url or local path.
        dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        existing_stat_var (list): List of existing stat vars that we don't need to generate
        mcf (list): Description
        mcf_file_path : Description
        metadata_file_path : Description
        raw_df : Raw census data as dataframe
        stat_var_index (dict): local storage for census column name and corresponding statvar
        tmcf_file_path : Path where generated tmcf file will be saved
    """

    def __init__(self, data_file_path, metadata_file_path, mcf_file_path,
                 tmcf_file_path, csv_file_path, existing_stat_var, census_year,
                 dataset_name):
        """
        Constructor
        
        Args:
            data_file_path :  Input XLS file from Census of India. Can be url or local path
            metadata_file_path : Meta data csv file which has attribute details
            mcf_file_path : Path where generated mcf file will be saved
            tmcf_file_path : Path where generated tmcf file will be saved
            csv_file_path : Path where cleaned csv file will be saved
            existing_stat_var : List of existing stat vars that we don't need to generate
            census_year : Census Year
            dataset_name : Census dataset name. Eg:Primary_Abstract_Data
        """
        self.data_file_path = data_file_path
        self.metadata_file_path = metadata_file_path
        self.mcf_file_path = mcf_file_path
        self.csv_file_path = csv_file_path
        self.tmcf_file_path = tmcf_file_path
        self.existing_stat_var = existing_stat_var
        self.census_year = census_year
        self.dataset_name = dataset_name
        self.raw_df = None
        self.stat_var_index = {}
        self.census_columns = []

    def _download_and_standardize(self):
        dtype = {
            'State': str,
            'District': str,
            'Subdistt': str,
            "Town/Village": str
        }
        self.raw_df = pd.read_excel(self.data_file_path, dtype=dtype)
        self.census_columns = self.raw_df.columns[CENSUS_DATA_COLUMN_START:]

    def _format_location(self, row):
        #In this specific format there is no Level defined.
        #A non zero location code from the lowest administration area
        #takes the precedence.
        if row["Town/Village"] != "000000":
            return row["Town/Village"]

        elif row["Subdistt"] != "00000":
            return row["Subdistt"]

        elif row["District"] != "000":
            return row["Subdistt"]

        elif row["State"] != "00":
            return row["State"]
        else:
            #This is india level location
            return "0"

    def _format_data(self):
        #This function is overridden in the child class
        pass

    def _get_base_name(self, row):
        #This function is overridden in the child class
        name = "Count_"
        return name

    def _create_variable(self, data_row, **kwargs):
        #This function is overridden in the child class
        pass

    def _create_mcf(self):
        #This function is overridden in the child class
        pass

    def _create_tmcf(self):
        with open(self.tmcf_file_path, 'w+', newline='') as f_out:
            f_out.write(
                self.GENERIC_TEMPLATE_TMCF.format(
                    year=self.census_year, dataset_name=self.dataset_name))

    def process(self):
        self._download_and_standardize()
        self._create_mcf()
        self._create_tmcf()
        self._format_data()
