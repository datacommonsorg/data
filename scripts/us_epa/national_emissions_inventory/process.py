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

import gc
import os
import shutil
import sys
import time
import traceback
import uuid
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
MAX_WORKERS = min(8, os.cpu_count() or 1)


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
                df['emissions type code'] = ''
            elif 'process' in file_path:
                df = df.dropna(subset=['fips code'])
                df['emissions type code'] = ''
            if '2008' in file_path:
                df['year'] = '2008'
            else:
                df['year'] = '2011'
        elif '2017' in file_path:
            if 'Event' in file_path:
                df['pollutant type(s)'] = 'nan'
            elif 'point_' in os.path.basename(
                    file_path) or 'facility_process' in file_path:
                df.rename(columns=replacement_point_17, inplace=True)
                df['emissions type code'] = ''
            elif 'nonpoint' in file_path:
                df['emissions type code'] = ''
            df['year'] = '2017'
        elif '2020' in file_path:
            if 'Event' in file_path:
                df['pollutant type(s)'] = 'nan'
            elif 'point_' in os.path.basename(
                    file_path) or 'facility_process' in file_path:
                df.rename(columns=replacement_20, inplace=True)
                df['emissions type code'] = ''
            elif 'nonpoint' in file_path:
                df['emissions type code'] = ''
            df['year'] = '2020'
        elif 'tribes' in file_path:
            if 'fips code' not in df.columns and 'tribal name' in df.columns:
                df.rename(columns=replacement_tribes, inplace=True)
                df = self._data_standardize(df, 'fips code')
            else:
                df.rename(columns=replacement_14, inplace=True)
                if 'event' in file_path or 'process' in file_path:
                    df['emissions type code'] = ''
            df['pollutant type(s)'] = 'nan'
            df['year'] = '2014'
        elif '2014' in file_path:
            df.rename(columns=replacement_14, inplace=True)
            if 'event' in file_path or 'process' in file_path:
                df['emissions type code'] = ''
            df['pollutant type(s)'] = 'nan'
            df['year'] = '2014'
        else:
            raise ValueError(
                f"Unhandled file path or unexpected survey year in: {file_path}"
            )

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
        logging.info(f"Processing file: {file_path}")
        df = pd.read_csv(file_path, header=0, low_memory=False)

        pd.set_option('display.max_columns', 14)
        df = self._regularize_columns(df, file_path)
        df['pollutant code'] = df['pollutant code'].astype(str)

        # Convert fips code to numeric, filter out invalid/tribal codes, and format as 5-digit string
        df['fips_num'] = pd.to_numeric(df['fips code'], errors='coerce')
        df = df.dropna(subset=['fips_num'])
        df = df[(df['fips_num'] > 0) &
                (df['fips_num'] <= TRIBAL_GEOCODE_START_RANGE)]
        df['geo_Id'] = 'geoId/' + df['fips_num'].astype(int).astype(
            str).str.zfill(5)
        df = df.drop(columns=['fips_num'])

        # Strip trailing .0 from float-parsed SCC codes before extracting level 1
        df['scc'] = df['scc'].astype(str).str.replace(
            r'\.0$', '', regex=True).str.strip()
        df['scc'] = np.where(df['scc'].str.len() == 10, df['scc'].str[0:2],
                             df['scc'].str[0])
        df.rename(columns=replacement_17, inplace=True)
        df_pollutants = df[df['pollutant code'].isin(pollutants)]
        df_pollutants = self._data_standardize(df_pollutants, 'pollutant code')
        df['pollutant code'] = ''
        df = pd.concat([df, df_pollutants], ignore_index=True)
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
        # safely turn any non-numeric values into NaN and drop them
        df['observation'] = pd.to_numeric(df['observation'], errors='coerce')
        df = df.dropna(subset=['observation'])
        return df

    def _process_file(self, file_path: str) -> None:
        """
        Process a single file and save the intermediate result.
        """
        try:
            df = self._national_emissions(file_path)
            if df is not None and not df.empty:
                df = df.sort_values(
                    by=['geo_Id', 'year', 'SV', 'Measurement_Method', 'observation'])
                df.dropna(subset=['observation'], inplace=True)
                df['observation'] = np.where(
                    df['unit'] == 'Pound',
                    df['observation'] / 2000, df['observation'])
                df['unit'] = "Ton"
                if 'scc_name' in df.columns:
                    df = df.drop(columns=['scc_name'])
                df = df.groupby(
                    ['geo_Id', 'year', 'Measurement_Method', 'SV'],
                    as_index=False)['observation'].sum()
                df['unit'] = "Ton"
                intermediate_file_path = os.path.join(
                    self.temp_dir,
                    f"{uuid.uuid4().hex}_{os.path.basename(file_path)}.pkl"
                )
                df.to_pickle(intermediate_file_path)
                logging.info(
                    f"Saved intermediate file at : {intermediate_file_path}")
        except Exception as e:
            logging.exception(f"Error processing file {file_path}: {e}")
            raise

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

    def _process(self) -> None:
        """
        This Method processes the input files to generate
        the final df.
        Args:
            None
        Returns:
            None
        """
        logging.info("Starting data processing across all input files.")
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if self.temp_dir:
            os.makedirs(self.temp_dir, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_WORKERS) as executor:
            list(executor.map(self._process_file, self._input_files))

        logging.info("Consolidating intermediate files.")
        intermediate_files = [
            os.path.join(self.temp_dir, f) for f in os.listdir(self.temp_dir)
            if not f.startswith('.')
        ]
        if not intermediate_files:
            logging.fatal("No intermediate files found to concatenate. Exiting.")
            raise FileNotFoundError(
                "No intermediate files found to concatenate.")

        chunk_size = 10
        chunk_dfs = []
        for i in range(0, len(intermediate_files), chunk_size):
            batch = intermediate_files[i:i + chunk_size]
            batch_dfs = []
            for f in batch:
                try:
                    df = pd.read_pickle(f) if f.endswith('.pkl') else pd.read_csv(f, low_memory=False)
                    batch_dfs.append(df)
                    logging.info(f"Appending {f}")
                except Exception as e:
                    logging.fatal(
                        f"Error reading intermediate file {f}: {e}\n{traceback.format_exc()}"
                    )
                    raise
            if batch_dfs:
                batch_concat = pd.concat(batch_dfs, ignore_index=True)
                del batch_dfs
                batch_concat = batch_concat.sort_values(
                    by=['geo_Id', 'year', 'SV', 'Measurement_Method', 'observation'])
                batch_concat.dropna(subset=['observation'], inplace=True)
                batch_concat['observation'] = np.where(
                    batch_concat['unit'] == 'Pound',
                    batch_concat['observation'] / 2000,
                    batch_concat['observation'])
                if 'scc_name' in batch_concat.columns:
                    batch_concat = batch_concat.drop(columns=['scc_name'])
                batch_concat = batch_concat.groupby(
                    ['geo_Id', 'year', 'Measurement_Method', 'SV'],
                    as_index=False)['observation'].sum()
                batch_concat['unit'] = "Ton"
                chunk_dfs.append(batch_concat)
                del batch_concat
                gc.collect()

        if not chunk_dfs:
            logging.fatal("No dataframes to concatenate. Exiting.")
            raise RuntimeError(
                "No dataframes to concatenate after processing intermediate files."
            )

        self.final_df = pd.concat(chunk_dfs, ignore_index=True)
        del chunk_dfs
        gc.collect()

        self.final_df = self.final_df.sort_values(
            by=['geo_Id', 'year', 'SV', 'Measurement_Method', 'observation'])
        self.final_df.dropna(subset=['observation'], inplace=True)
        self.final_df['observation'] = np.where(
            self.final_df['unit'] == 'Pound',
            self.final_df['observation'] / 2000, self.final_df['observation'])
        if 'scc_name' in self.final_df.columns:
            self.final_df = self.final_df.drop(columns=['scc_name'])
        self.final_df = self.final_df.groupby(
            ['geo_Id', 'year', 'Measurement_Method', 'SV'],
            as_index=False)['observation'].sum()
        self.final_df['unit'] = "Ton"
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
            f"Error finding input files: {e}. Run the download script first.\n{traceback.format_exc()}"
        )
        raise

    # Defining Output Files
    logging.info(
        f"input_path {input_path} and output_file_path {output_file_path}")
    csv_name = "national_emissions.csv"
    mcf_name = "national_emissions.mcf"
    tmcf_name = "national_emissions.tmcf"
    cleaned_csv_path = os.path.join(output_file_path, csv_name)
    if os.path.exists(intermediate_path):
        shutil.rmtree(intermediate_path)
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
        logging.fatal(
            f"An unexpected error occurred: {e}\n{traceback.format_exc()}")
        raise


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
