# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file.
"""

import os
import sys
import pandas as pd

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

_SOURCE_GROUPS = {
    'FuelCombustionElectricUtility': 'StationaryFuelCombustion',
    'FuelCombustionIndustrial': 'StationaryFuelCombustion',
    'EPA_FuelCombustionOther': 'StationaryFuelCombustion',
    'ChemicalAndAlliedProductManufacturing': 'IndustrialAndOtherProcesses',
    'MetalsProcessing': 'IndustrialAndOtherProcesses',
    'PetroleumAndRelatedIndustries': 'IndustrialAndOtherProcesses',
    'EPA_OtherIndustrialProcesses': 'IndustrialAndOtherProcesses',
    'SolventUtilization': 'IndustrialAndOtherProcesses',
    'StorageAndTransport': 'IndustrialAndOtherProcesses',
    'WasteDisposalAndRecycling': 'IndustrialAndOtherProcesses',
    'OnRoadVehicles': 'Transportation',
    'NonRoadEnginesAndVehicles': 'Transportation'
}


class USAirPollutionEmissionTrends:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    _mcf_template = ''
    _tmcf_template = ''

    def __init__(self,
                 input_files: list,
                 csv_file_path: str = None,
                 mcf_file_path: str = None,
                 tmcf_file_path: str = None) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._final_df = pd.DataFrame(columns=[
            'geo_Id', 'year', 'SV_TEMP', 'observation', 'Measurement_Method'
        ])

    def set_cleaned_csv_file_path(self, cleaned_csv_file_path: str) -> None:
        self._cleaned_csv_file_path = cleaned_csv_file_path

    def set_mcf_file_path(self, mcf_file_path: str) -> None:
        self._mcf_file_path = mcf_file_path

    def set_tmcf_file_path(self, tmcf_file_path: str) -> None:
        self._tmcf_file_path = tmcf_file_path

    def aggregate_columns(self, df: pd.DataFrame, filter_values: list,
                          measurement_method: str) -> pd.DataFrame:
        """
        Aggregates the columns based on SV

        Args: 
            df (pd.DataFrame): df as the input, to aggregate values

        Returns:
            df (pd.DataFrame): modified df as output
        """
        for i in filter_values:
            df = df.drop(df[(df['SV_TEMP'].str.contains(i))].index)

        # Replacing the columns for grouping as per
        # StationaryFuelCombustion -    FuelCombustionElectricUtility
        #                               FuelCombustionIndustrial
        #                               EPA_FuelCombustionOther
        # IndustrialAndOtherProcesses - ChemicalAndAlliedProductManufacturing
        #                               MetalsProcessing
        #                               PetroleumAndRelatedIndustries
        #                               EPA_OtherIndustrialProcesses
        #                               SolventUtilization
        #                               StorageAndTransport
        #                               WasteDisposalAndRecycling
        # Transportation -              OnRoadVehicles
        #                               NonRoadEnginesAndVehicles

        df.loc[:, ('SV_TEMP')] = df['SV_TEMP'].replace(_SOURCE_GROUPS,
                                                       regex=True)
        df = df.groupby(['year', 'geo_Id', 'SV_TEMP']).sum().reset_index()
        df['Measurement_Method'] = measurement_method
        return df

    def data_standardize(self, df: pd.DataFrame, column_name: str,
                         standardize_values: dict) -> pd.DataFrame:
        """
        Replaces values of a single column into true values
        from metadata.

        Args:
            df (pd.DataFrame): df as the input, to change column values

        Returns:
            df (pd.DataFrame): modified df as output
        """
        df = df.replace({column_name: standardize_values})
        return df

    def _parse_source_files(self):
        pass

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(self._tmcf_template.rstrip('\n'))

    def generate_mcf(self, df: pd.DataFrame = None):
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df_cols (list) : List of DataFrame Columns

        Returns:
            sv_replacement (dict) : Dictionary to replace SV names 
                                    with SV generator names
        """
        if df is not None:
            self._final_df = df

        mcf_df = self._final_df.drop_duplicates(subset=['SV_TEMP']).reset_index(
            drop=True).sort_values(by=['SV_TEMP'])

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write("".join(mcf_df['mcf'].to_list()))

    def generate_csv(self):
        """
        This method generates CSV file w.r.t
        final df generated.

        Args:
            None

        Returns:
            None
        """
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        self._parse_source_files()

        self._final_df[[
            'geo_Id', 'year', 'SV', 'observation', 'Measurement_Method'
        ]].to_csv(self._cleaned_csv_file_path, index=False)

        return self._final_df
