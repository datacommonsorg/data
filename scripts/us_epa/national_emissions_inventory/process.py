# Copyright 2025 Google LLC
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
import time
# import shutil
# import tempfile
import concurrent.futures
from absl import app, flags, logging
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(
    1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

from util.statvar_dcid_generator import get_statvar_dcid

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

from config import *

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'gcs_output')
flags.DEFINE_string("intermediate_path",
                    os.path.join(default_input_path, "intermediate_output"),
                    "Path to save intermediate files.")

flags.DEFINE_string("input_path", os.path.join(default_input_path,
                                               "input_files"),
                    "Import Data File's List")
flags.DEFINE_string("output_path",
                    os.path.join(default_input_path, "output_files"),
                    "Path to save output files.")

_MCF_TEMPLATE = ("Node: dcid:{statvar}\n"
                 "name: \"Annual Amount Emissions {statvar_name}\"\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Emissions\n"
                 "measurementQualifier: dcs:Annual{scc}"
                 "{pollutant}{emission_type}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:amount\n")

_TMCF_TEMPLATE = ("Node: E:national_emissions->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: C:national_emissions->SV\n"
                  "measurementMethod: C:national_emissions->"
                  "Measurement_Method\n"
                  "observationAbout: C:national_emissions->geo_Id\n"
                  "observationDate: C:national_emissions->year\n"
                  "unit: Ton\n"
                  "observationPeriod: \"P1Y\"\n"
                  "value: C:national_emissions->observation\n")

TRIBAL_GEOCODE_START_RANGE = 80000
MAX_WORKERS = os.cpu_count()


class USAirEmissionTrends:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str,
                 intermediate_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self.final_df = pd.DataFrame(columns=[
            'geo_Id', 'year', 'SV', 'observation', 'unit', 'Measurement_Method'
        ])
        self.final_mcf_template = ""
        self.temp_dir = intermediate_path
        logging.info("USAirEmissionTrends instance initialized.")

    def _data_standardize(self, df: pd.DataFrame,
                          column_name: str) -> pd.DataFrame:
        """
        Replaces values of a single column into true values
        from metadata and returns the DF.
        Args:
            df (pd.DataFrame): df as the input, to change column values,
            column_name (str): column_name as a string, which has to be changed
        Returns:
            df (pd.DataFrame): modified df as output
        """
        df = df.replace({column_name: replace_metadata})
        return df

    def _regularize_columns(self, df: pd.DataFrame,
                            file_path: str) -> pd.DataFrame:
        """
        Reads the file for national emissions data and regularizes the files into a
        single structure so that it can be processed at once. This includes dropping
        additional columns, renaming the columns and adding the columns with null if
        not present.
        Args:
            df (pd.DataFrame): provides the df as input
            file_path (str): path to excel file as the input
        Returns:
            df (pd.DataFrame): provides the regularized df as output
        """
        if '2008' in file_path or '2011' in file_path:
            df.rename(columns=replacement_08_11, inplace=True)
            df['pollutant type(s)'] = 'nan'
            if 'event' in file_path:
                df.loc[:, 'emissions type code'] = ''
            elif 'process' in file_path:
                df = df.dropna(subset=['fips code'])
                df.loc[:, 'emissions type code'] = ''
            if '2008' in file_path:
                df.loc[:, 'year'] = '2008'
            else:
                df.loc[:, 'year'] = '2011'
        elif '2017' in file_path:
            if 'Event' in file_path:
                df['pollutant type(s)'] = 'nan'
            elif 'point' in file_path:
                if 'unknown' in file_path or '678910' in file_path:
                    df.rename(columns=replacement_point_17, inplace=True)
                df.loc[:, 'emissions type code'] = ''
            df['year'] = '2017'
        elif '2020' in file_path:
            if 'Event' in file_path:
                df['pollutant type(s)'] = 'nan'
            elif 'point' in file_path:
                if 'unknown' in file_path:
                    df.rename(columns=replacement_20, inplace=True)
                df.loc[:, 'emissions type code'] = ''
            df['year'] = '2020'
        elif 'tribes' in file_path:
            df.rename(columns=replacement_tribes, inplace=True)
            df = self._data_standardize(df, 'fips code')
            df['pollutant type(s)'] = 'nan'
            df['year'] = '2014'
        else:
            df.rename(columns=replacement_14, inplace=True)
            if 'event' in file_path or 'process' in file_path:
                df.loc[:, 'emissions type code'] = ''
            df['pollutant type(s)'] = 'nan'
            df['year'] = '2014'

        # Ensure all expected columns exist before subsetting
        for col in df_columns:
            if col not in df.columns:
                df[col] = np.nan

        df = df[df_columns]
        return df

    def _national_emissions(self, file_path: str) -> pd.DataFrame:
        """
        Reads the file for national emissions data and cleans it for concatenation
        in Final CSV.
        Args:
            file_path (str): path to excel file as the input
        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        try:
            logging.info(f"Processing file: {file_path}")
            df = pd.read_csv(file_path, header=0, low_memory=False)

            pd.set_option('display.max_columns', 14)
            df = self._regularize_columns(df, file_path)
            df['pollutant code'] = df['pollutant code'].astype(str)
            df['geo_Id'] = ([f'{x:05}' for x in df['fips code']])

            # Convert geo_Id to numeric and filter based on range
            df['geo_Id'] = pd.to_numeric(
                df['geo_Id'], errors='coerce'
            )  # Convert to numeric, invalid parsing will be set as NaN
            df = df[df['geo_Id'] <= TRIBAL_GEOCODE_START_RANGE]

            # Remove if Tribal Details are needed
            df['geo_Id'] = df['geo_Id'].astype(float).astype(int)
            df = df.drop(df[df.geo_Id > TRIBAL_GEOCODE_START_RANGE].index)
            df['geo_Id'] = ([f'{x:05}' for x in df['geo_Id']])
            df['geo_Id'] = df['geo_Id'].astype(str)

            # Remove if Tribal Details are needed
            df['scc'] = df['scc'].astype(str)
            df['scc'] = np.where(df['scc'].str.len() == 10, df['scc'].str[0:2],
                                 df['scc'].str[0])
            df['geo_Id'] = 'geoId/' + df['geo_Id']
            df.rename(columns=replacement_17, inplace=True)
            df_pollutants = df[df['pollutant code'].isin(pollutants)]
            df_pollutants = self._data_standardize(df_pollutants,
                                                   'pollutant code')
            df['pollutant code'] = ''
            df = pd.concat([df, df_pollutants])
            df = self._data_standardize(df, 'unit')
            df['scc_name'] = df['scc'].astype(str)
            df = df.replace({'scc_name': replace_source_metadata})
            df['scc_name'] = df['scc_name'].str.replace(' ', '')
            df['SV'] = ('Annual_Amount_Emissions_' +
                        df['pollutant code'].astype(str) + '_SCC_' +
                        df['scc'].astype(str)) + '_' + df['scc_name']

            df['Measurement_Method'] = 'dcAggregate/EPA_NationalEmissionInventory'
            df['SV'] = df['SV'].str.replace('_nan', '').str.replace('__', '_')
            df = df.drop(columns=drop_df)
            df = df.drop(df[df['observation'] == '.'].index)
            # safely turn any non-numeric values into NaN
            df['observation'] = pd.to_numeric(df['observation'],
                                              errors='coerce')
            return df
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            return pd.DataFrame()

    def _process_file(self, file_path: str) -> None:
        """
        Process a single file and save the intermediate result.
        """
        try:
            df = self._national_emissions(file_path)
            if not df.empty:
                intermediate_file_path = os.path.join(
                    self.temp_dir,
                    f"{str(datetime.now().timestamp()).replace('.', '_')}_{os.path.basename(file_path)}"
                )
                df.to_csv(intermediate_file_path, index=False)
                logging.info(
                    f"Saved intermediate file at : {intermediate_file_path}")
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    def _mcf_property_generator(self) -> None:
        """
        This method generates mcf properties w.r.t
        the SVs present.
        Args:
            None
        Returns:
            None
        """
        logging.info(
            "Generating MCF properties based on unique Statistical Variables (SVs)."
        )
        sv_list = self.final_df["SV"].to_list()
        sv_list = list(set(sv_list))
        sv_list.sort()
        for sv in sv_list:
            pollutant = code = ''
            sv_property = sv.split("_")
            source = '\nepaSccCode: dcs:EPA_SCC/' + sv_property[-2]
            scc_name = sv_property[-1]
            scc_name = scc_name + " (" + sv_property[-2] + ")"
            pollutant_start = 3 if sv_property[3] != 'SCC' else None
            if sv_property[3] in ('Exhaust', 'Evaporation', 'Refueling',
                                  'BName', 'TName', 'Cruise', 'Maneuvering',
                                  'ReducedSpeedZone', 'Hotelling'):
                code = "emissionTypeCode: dcs:" + sv_property[3]
                scc_name = scc_name + ", " + sv_property[3]
                pollutant_start = 4 if sv_property[4] != 'SCC' else None

            pollutant_name = ''
            pollutant_value = ''
            if pollutant_start != None:
                for i in sv_property[pollutant_start:-3]:
                    pollutant = pollutant + i + '_'
                pollutant_value = '\nemittedThing: dcs:' + pollutant.rstrip('_')
                pollutant_name = replace_metadata[pollutant.rstrip('_')] + ", "
            self.final_mcf_template += _MCF_TEMPLATE.format(
                statvar=sv,
                scc=source,
                pollutant=pollutant_value,
                statvar_name=pollutant_name + scc_name,
                emission_type=code) + "\n"
        logging.info("MCF properties generation complete.")

    def _process(self):
        """
        This Method processes the input files to generate
        the final df.
        Args:
            None
        Returns:
            None
        """
        logging.info("Starting data processing across all input files.")
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS) as executor:
            executor.map(self._process_file, self._input_files)

        logging.info("Consolidating intermediate files.")
        intermediate_files = [
            os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir)
        ]
        dfs = []
        for f in intermediate_files:
            try:
                dfs.append(pd.read_csv(f, low_memory=False))
                logging.info(f"Appending {f}")
            except Exception as e:
                logging.error(f"Error reading intermediate file {f}: {e}")

        if not dfs:
            logging.error("No dataframes to concatenate. Exiting.")
            return

        self.final_df = pd.concat(dfs, ignore_index=True)

        self.final_df = self.final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'Measurement_Method', 'observation'])
        self.final_df['observation'].replace('', np.nan, inplace=True)
        self.final_df.dropna(subset=['observation'], inplace=True)
        self.final_df['observation'] = np.where(
            self.final_df['unit'] == 'Pound',
            self.final_df['observation'] / 2000, self.final_df['observation'])
        self.final_df = self.final_df.groupby(
            ['geo_Id', 'year', 'Measurement_Method', 'SV']).sum().reset_index()
        self.final_df['unit'] = "Ton"
        if 'scc_name' in self.final_df.columns:
            self.final_df = self.final_df.drop(columns=['scc_name'])
        logging.info("Data processing complete.")

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Args:
            None
        Returns:
            None
        """
        logging.info(f"Generating TMCF file: '{self._tmcf_file_path}'.")
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def generate_mcf(self) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            None
        Returns:
            None
        """
        logging.info(f"Generating MCF file: '{self._mcf_file_path}'.")
        self._mcf_property_generator()

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(self.final_mcf_template.rstrip('\n'))

    def generate_csv(self) -> None:
        """
        This method generates CSV file w.r.t
        input_files folder.
        Args:
            None
        Returns:
            None
        """
        logging.info(
            f"Generating cleaned CSV file: '{self._cleaned_csv_file_path}'.")
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        self._process()

        self.final_df.to_csv(self._cleaned_csv_file_path, index=False)


def process_files(input_path: str, output_file_path: str,
                  intermediate_path: str):
    """
    Processes the national emissions data.

    Args:
        input_path (str): The path to the input files.
        output_file_path (str): The path to save the output files.
        intermediate_path (str): The path to save intermediate files.
    """
    # Read all input files
    try:
        ip_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(input_path)
            for file in files
            if file.lower().endswith('.csv')
        ]
    except Exception as e:
        logging.fatal(
            f"Error finding input files: {e}. Run the download script first.\n")
        sys.exit(1)

    # Defining Output Files
    logging.info(
        f"input_path {input_path} and output_file_path {output_file_path}")
    csv_name = "national_emissions.csv"
    mcf_name = "national_emissions.mcf"
    tmcf_name = "national_emissions.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    if not os.path.exists(intermediate_path):
        os.makedirs(intermediate_path, exist_ok=True)
    mcf_path = os.path.join(output_file_path, mcf_name)
    tmcf_path = os.path.join(output_file_path, tmcf_name)

    loader = None
    try:
        loader = USAirEmissionTrends(ip_files, cleaned_csv_path, mcf_path,
                                     tmcf_path, intermediate_path)
        loader.generate_csv()
        loader.generate_mcf()
        loader.generate_tmcf()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def main(_):
    """
    The main function for the script.
    """
    logging.set_verbosity(1)
    logging.info("Started process script")
    start_time = time.time()
    process_files(FLAGS.input_path, FLAGS.output_path, FLAGS.intermediate_path)
    elapsed_time = time.time() - start_time
    logging.info(f"Total execution time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    app.run(main)
