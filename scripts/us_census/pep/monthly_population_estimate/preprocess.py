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
""" A Script to process USA Census PEP monthly population data
    from the datasets in the provided local path.
    Typical usage:
    1. python3 preprocess.py
    2. python3 preprocess.py -mode='download'
    3. python3 preprocess.py -mode='process'
"""
from dataclasses import replace
import os
import re
import warnings
import requests
import numpy as np
import time
import json
import sys
from datetime import datetime as dt

warnings.filterwarnings('ignore')
import pandas as pd
from absl import app
from absl import flags
from absl import logging

pd.set_option("display.max_columns", None)

FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, 'input_files')
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
_HEADER = 1
_SCALING_FACTOR_TXT_FILE = 1000

#Creating folder to store the raw data from source
raw_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "raw_data")
if not os.path.exists(raw_data_path):
    os.mkdir(raw_data_path)

_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n"
                 "{xtra_pvs}\n")

_TMCF_TEMPLATE = ("Node: E:USA_Population_Count->E{}\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: dcs:{}\n"
                  "measurementMethod: dcs:{}\n"
                  "observationAbout: C:USA_Population_Count->Location\n"
                  "observationDate: C:USA_Population_Count->Date\n"
                  "observationPeriod: \"P1M\"\n"
                  "value: C:USA_Population_Count->{}\n")


def _extract_year(val: str) -> tuple:
    """
    This Methods returns true,year from the value contains year.
    Otherwise false,''

    Arguments:
        val (str) : A string value contains data below format
                    yyyy or yyyy [1] or .MM 1
    Returns:
        res (tuple) : Tuple with boolean value and year value or None
    """
    # Extracting 0th index value from the val.
    # val contains yyyy or yyyy [1] or .MM 1
    val = str(val).strip().split(' ', maxsplit=1)[0]
    if val.isnumeric() and len(val) == 4:
        return True, val
    # Exceptional Case: val contains 20091
    # 2009 is year and 1 is Date.
    # Extracting just year from above format
    if val.isnumeric() and len(val) == 5:
        return True, val[:4]
    return False, None


def _return_year(col: str) -> str:
    """
    This Methods returns year value if col contains year.
    Otherwise pandas NA value.

    Arguments:
        col (str) : A string value contains data below format
                    yyyy or yyyy [1] or .MM 1
    Returns:
        res (str) : String value with year yyyy or pandas NA value
    """
    res, out = _extract_year(col)
    if res:
        return out
    return pd.NA


def _return_month(col: str) -> str:
    """
    This Methods returns month and date value if col contains month, date.
    Otherwise pandas NA value.

    Arguments:
        col (str) : A string value contains data below format
                    yyyy or yyyy [1] or .MM 1
    Returns:
        res (str) : String value with month mm or pandas NA value
    """
    res = _extract_year(col)
    if res[0]:
        return pd.NA
    return col


def _year_range(col: pd.Series) -> str:
    """
    This method returns year range from the dataframe
    column.
    Example:
    col(input):
    2000-04
    2000-05
    2000-06
    2000-07
    2000-08
    ...   
    2010-08
    2010-09
    2010-10
    2010-11
    2010-12
    output:
    "2010-2000"

    Arguments:
        col (Series) : DataFrame Column of dtype str

    Returns:
        year_range (str) : String of Concatenated max and min year values
    """
    year_range = None
    max_year = max(pd.to_datetime(col, errors='coerce').dt.year)
    min_year = min(pd.to_datetime(col, errors='coerce').dt.year)
    year_range = str(max_year) + '-' + str(min_year)
    return year_range


def _replace_name(final_cols: list) -> list:
    """
    List provided inorder to change the name as required by output.

    Arguments:
        final_cols (list) : List of dtype str

    Returns:
        final_cols (list) : List of dtype str
    """
    final_cols = [
        "Count_Person_" + (col.replace("Population ", "").replace(
            "Population", "").replace(" Plus ", "Or").replace(
                "Armed Forces Overseas", "InUSArmedForcesOverseas").replace(
                    "Household", "ResidesInHousehold").replace(
                        "Resident", "USResident").replace(
                            "Noninstitutionalized",
                            "NonInstitutionalized").strip().replace(
                                " ", "_").replace("__", "_"))
        for col in final_cols
    ]

    return final_cols


class CensusUSACountryPopulation:
    """
    CensusUSACountryPopulation class provides methods
    to load the data into dataframes, process, cleans
    dataframes and finally creates single cleaned csv
    file.
    Also provides methods to generate MCF and TMCF
    Files using pre-defined templates.
    """

    def __init__(self, input_path: str, csv_file_path: str, mcf_file_path: str,
                 tmcf_file_path: str) -> None:
        self.input_path = input_path  #added
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._df = None
        self._file_name = None
        self._scaling_factor = 1
        # Finding the Dir Path
        if not os.path.exists(os.path.dirname(self._cleaned_csv_file_path)):
            os.mkdir(os.path.dirname(self._cleaned_csv_file_path))

    def _load_data(self, file: str) -> pd.DataFrame:
        """
        This Methods loads the data into pandas Dataframe
        using the provided file path and Returns the Dataframe.

        Arguments:
            file (str) : String of Dataset File Path
        Returns:
            df (DataFrame) : DataFrame with loaded dataset
        """
        df = None
        self._file_name = os.path.basename(file)
        if ".xls" in file:
            df = pd.read_excel(file)
        return df

    def _transform_df(self, df: pd.DataFrame, file: str) -> pd.DataFrame:
        """
        This method transforms Dataframe into cleaned DF.
        Also, It Creates new columns, remove duplicates,
        Standaradize headers to SV's, Mulitply with
        scaling factor.

        Arguments:
            df (DataFrame) : DataFrame

        Returns:
            df (DataFrame) : DataFrame.
        """
        final_cols = [col for col in df.columns if 'year' not in col.lower()]
        # _return_year("1999") or _return_year("1999 [1]"): 1999
        # _return_year(".07 1"): pd.NA
        df['Year'] = df['Year and Month'].apply(_return_year).fillna(
            method='ffill', limit=12)
        # _return_year("1999") or _return_year("1999 [1]"): pd.NA
        # _return_year(".07 1"): 07
        df['Month'] = df['Year and Month'].apply(_return_month)
        df.dropna(subset=['Year', 'Month'], inplace=True)

        # Creating new Date Column and Final Date format is yyyy-mm
        df['Date'] = df['Year'] + df['Month']
        df['Date'] = df['Date'].str.replace(".", "").str.replace(
            " ", "").str.replace("*", "")
        df['Date'] = pd.to_datetime(df['Date'],
                                    format='%Y%B%d',
                                    errors="coerce")
        # dropping 2010, 2020 overlapping values from different files
        # dropping < 2000 files having some text in the value column

        if 'nat-total.xlsx' in file:
            df = df[df['Resident Population Plus Armed Forces Overseas'] !=
                    'with']
        if 'na-est2009-01.xlsx' in file:
            df = df[df['Date'] < dt(2010, 4, 1)]
        if 'na-est2019-01.xlsx' in file:
            df = df[df['Date'] < dt(2020, 4, 1)]
        df.dropna(subset=['Date'], inplace=True)
        df['Date'] = df['Date'].dt.strftime('%Y-%m')
        df.drop_duplicates(subset=['Date'], inplace=True)

        # Deriving new SV Count_Person_InArmedForcesOverseas as
        # subtracting Resident Population from
        # Resident Population Plus Armed Forces Overseas
        df['Count_Person_InUSArmedForcesOverseas'] = df[
            'Resident Population Plus Armed Forces Overseas'].astype(
                'int') - df['Resident Population'].astype('int')
        computed_cols = ["Date", "Count_Person_InUSArmedForcesOverseas"]

        # Selecting Computed and Final Columns from the DF.
        df = df[computed_cols + final_cols]

        # Renaming DF Headers with ref to SV's Naming Standards.
        final_cols_list = _replace_name(final_cols)

        final_cols_list = computed_cols + final_cols_list
        df.columns = final_cols_list

        # Creating Location column with default value country/USA.
        # as the dataset is all about USA country level only.
        df.insert(1, "Location", "country/USA", True)
        df.insert(0, 'date_range', _year_range(df['Date']), True)
        return df

    def _transform_data(self, df: pd.DataFrame, file: str) -> None:
        """
        This method calls the required functions to transform
        the dataframe and saves the final cleaned data in
        CSV file format.

        Arguments:
        df (DataFrame): Input DataFrame containing the raw data to be transformed.

        Returns:
        bool: Returns True if the transformation and file saving are successful, 
              False if an error occurs during processing.
        """

        try:
            df = self._transform_df(df, file)

            if self._df is None:
                self._df = df
            else:
                self._df = pd.concat([self._df, df], ignore_index=True)

            self._df.sort_values(by=['Date', 'date_range'],
                                 ascending=False,
                                 inplace=True)
            # Data for 2020 exists in two sources, causing overlap. We'll eliminate duplicates
            #self._df.drop_duplicates("Date", keep="last", inplace=True)
            self._df.drop(['date_range'], axis=1, inplace=True)
            float_col = self._df.select_dtypes(include=['float64'])
            for col in float_col.columns.values:
                try:
                    self._df[col] = self._df[col].astype('int64')
                except:
                    pass
            self._df.to_csv(self._cleaned_csv_file_path, index=False)
        except Exception as e:
            logging.fatal(f'Error when processing file:-{e}')
        return True

    def _generate_mcf(self, df_cols: list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        try:
            mcf_nodes = []
            for col in df_cols:
                pvs = []
                residence = ""
                status = ""
                armedf = ""
                if col.lower() in ["date", "location"]:
                    continue
                if re.findall('Resident', col):
                    if re.findall('InUSArmedForcesOverseas', col):
                        status = "USResident__InUSArmedForcesOverseas"
                    else:
                        status = "USResident"
                    residence = "residentStatus: dcs:" + status
                    pvs.append(residence)
                elif re.findall('ArmedForces', col):
                    residence = "residentStatus: dcs:" + "InUSArmedForcesOverseas"
                    pvs.append(residence)
                if re.findall('Resides', col):
                    if re.findall('Household', col):
                        residence = "residenceType: dcs:" + "Household"
                        pvs.append(residence)
                if re.findall('Civilian', col):
                    armedf = "armedForcesStatus: dcs:Civilian"
                    pvs.append(armedf)
                    if re.findall('NonInstitutionalized', col):
                        residence = ("institutionalization: dcs:" +
                                     "USC_NonInstitutionalized")
                        pvs.append(residence)
                if re.findall('Count_Person_InUSArmedForcesOverseas', col):
                    armedf = "armedForcesStatus: dcs:InArmedForces"
                    pvs.append(armedf)
                node = _MCF_TEMPLATE.format(dcid=col, xtra_pvs='\n'.join(pvs))
                mcf_nodes.append(node)

                mcf = '\n'.join(mcf_nodes)

            # Writing Genereated MCF to local path.
            with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
                f_out.write(mcf.rstrip('\n'))
        except Exception as e:
            logging.fatal(f'Error when Generating MCF file:-{e}')

    def _generate_tmcf(self, df_cols: list) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """

        i = 0
        measure = ""
        tmcf = ""
        for col in df_cols:
            if col.lower() in ["date", "location"]:
                continue
            if re.findall('Count_Person_InUSArmedForcesOverseas', col):
                measure = "dcAggregate/CensusPEPSurvey"
            else:
                measure = "CensusPEPSurvey"
            tmcf = tmcf + _TMCF_TEMPLATE.format(i, col, measure, col) + "\n"
            i = i + 1

        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))

    def process(self):
        """
        This is main method to iterate on each file,
        calls defined methods to clean, generate final
        cleaned CSV file, MCF file and TMCF file.
        """
        #input_path = FLAGS.input_path
        ip_files = os.listdir(self.input_path)
        self.input_files = [
            self.input_path + os.sep + file for file in ip_files
        ]
        if len(self.input_files) == 0:
            logging.info("No files to process")
            return
        processed_count = 0
        total_files_to_process = len(self.input_files)
        logging.info(f"No of files to be processed {len(self.input_files)}")
        for file in self.input_files:
            logging.info(f"Processing file: {file}")
            df = self._load_data(file)
            result = self._transform_data(df, file)
            if result:
                processed_count += 1
            else:
                logging.fatal(f'Failed to process {file}')
        logging.info(f"No of files processed {processed_count}")
        if total_files_to_process > 0 & (processed_count
                                         == total_files_to_process):
            self._generate_mcf(self._df.columns)
            self._generate_tmcf(self._df.columns)
        else:
            logging.fatal(
                "Aborting output files as no of files to process not matching processed files"
            )


def add_future_year_urls():
    """
    This method scans the download URLs for future years.
    """
    global _FILES_TO_DOWNLOAD
    with open(os.path.join(_MODULE_DIR, 'input_url.json'), 'r') as inpit_file:
        _FILES_TO_DOWNLOAD = json.load(inpit_file)
    urls_to_scan = [
        "https://www2.census.gov/programs-surveys/popest/tables/2020-{YEAR}/national/totals/NA-EST{YEAR}-POP.xlsx"
    ]
    # This method checks for URLs from 2030 down to 2021. If a valid URL is found for any year, the method stops and adds it to the download URL.
    #
    for url in urls_to_scan:
        for future_year in range(2030, 2021, -1):
            YEAR = future_year

            url_to_check = url.format(YEAR=YEAR)
            try:
                check_url = requests.head(url_to_check)
                if check_url.status_code == 200:
                    _FILES_TO_DOWNLOAD.append({"download_path": url_to_check})
                    break

            except:
                logging.error(f"URL is not accessable {url_to_check}")


def _clean_csv_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Args:
        df (DataFrame) : DataFrame of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    # Removal of file description and headers in the initial lines of the input
    #
    # Input Data:
    # table with row headers in column A and column headers in rows 3 through 5 (leading dots indicate sub-parts)
    # Table 1. Monthly Population Estimates for the United States:  April 1, 2000 to December 1, 2010
    # Year and Month    Resident Population     Resident Population Plus Armed Forces Overseas   Civilian Population	Civilian Noninstitutionalized Population
    # 2000
    # .April 1	28,14,24,602	28,16,52,670	28,02,00,922	27,61,62,490
    # .May 1	28,16,46,806	28,18,76,634	28,04,28,534	27,63,89,920
    #
    # Output Data:
    # (Made Headers) Year and Month    Resident Population     Resident Population Plus Armed Forces Overseas   Civilian Population    Civilian Noninstitutionalized Population
    # 2000
    # .April 1	28,14,24,602	28,16,52,670	28,02,00,922	27,61,62,490
    # .May 1	28,16,46,806	28,18,76,634	28,04,28,534	27,63,89,920

    idx = df[df[0] == "Year and Month"].index
    df = df.iloc[idx.values[0] + 1:][:]
    df = df.dropna(axis=1, how='all')
    cols = [
        "Year and Month", "Resident Population",
        "Resident Population Plus Armed Forces Overseas", "Civilian Population",
        "Civilian NonInstitutionalized Population"
    ]
    df.columns = cols
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")
    return df


def _clean_txt_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame): DataFrame representing the loaded TXT dataset.
    
    Returns:
        DataFrame: Transformed DataFrame after cleaning operations.
    """
    df['Year and Month'] = df[['Year and Month', 'Date']]\
                                    .apply(_concat_cols, axis=1)
    df.drop(columns=['Date'], inplace=True)
    for col in df.columns:
        df[col] = df[col].str.replace(",", "")

    # The index numbers alotted as per where the columns are present to
    # move the columns left
    resident_population = 1
    resident_population_plus_armed_forces_overseas = 2
    civilian_population = 3
    civilian_noninstitutionalized_population = 4
    # Moving the row data left upto one index value.
    # As the text file has (census) mentioned in some rows and it makes the
    # other column's data shift by one place, we need to shift it back to the
    # original place.
    idx = df[df['Resident Population'] == "(census)"].index
    df.iloc[idx, resident_population] = df.iloc[idx][
        "Resident Population Plus Armed Forces Overseas"]
    df.iloc[idx, resident_population_plus_armed_forces_overseas] = df.iloc[idx][
        "Civilian Population"]
    df.iloc[idx, civilian_population] = df.iloc[idx][
        "Civilian NonInstitutionalized Population"]
    df.iloc[idx, civilian_noninstitutionalized_population] = np.NAN
    return df


def _mulitply_scaling_factor(col: pd.Series) -> pd.Series:
    """
    This method multiply dataframe column with scaling factor.

    Arguments:
        col (Series): A DataFrame column of dtype int, containing the values to be scaled.

    Returns:
        Series: A DataFrame column with values multiplied by the scaling factor.
    """
    res = col
    if col not in [None, np.NAN]:
        if col.isdigit():
            res = int(col) * _SCALING_FACTOR_TXT_FILE
    return res


def _concat_cols(col: pd.Series) -> pd.Series:
    """
    This method concats two DataFrame column values
    with space in-between.

    Args:
        col (Series): A pandas Series containing two values from the DataFrame.

    Returns:
        res (Series) : Concatenated DataFrame Columns
    """
    res = col[0]
    if col[1] is None:
        return res
    res = col[0] + ' ' + col[1]
    return res


def download_files():
    """
    This method allows to download the input files.
    """
    global _FILES_TO_DOWNLOAD
    session = requests.session()
    max_retry = 5
    for file_to_dowload in _FILES_TO_DOWNLOAD:
        file_name = None
        url = file_to_dowload['download_path']
        if 'file_name' in file_to_dowload and len(
                file_to_dowload['file_name'] > 5):
            file_name = file_to_dowload['file_name']
        else:
            file_name = url.split('/')[-1]
        retry_number = 0

        is_file_downloaded = False
        while is_file_downloaded == False:
            try:
                df = None
                file_name = url.split("/")[-1]

                if ".xls" in url:
                    df = pd.read_excel(url, header=_HEADER)
                    df.to_excel(os.path.join(raw_data_path, file_name),
                                index=False,
                                header=False,
                                engine='xlsxwriter')
                    df.to_excel(os.path.join(_INPUT_FILE_PATH, file_name),
                                index=False,
                                header=False,
                                engine='xlsxwriter')
                elif ".csv" in url:
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        if response.status_code == 200:
                            with open(os.path.join(raw_data_path, file_name),
                                      'wb') as f:
                                f.write(response.content)
                    file_name = file_name.replace(".csv", ".xlsx")
                    df = pd.read_csv(url, header=None)
                    df = _clean_csv_file(df)
                    df.to_excel(os.path.join(_INPUT_FILE_PATH, file_name),
                                index=False,
                                engine='xlsxwriter')
                elif ".txt" in url:
                    with requests.get(url, stream=True) as response:
                        response.raise_for_status()
                        if response.status_code == 200:
                            with open(os.path.join(raw_data_path, file_name),
                                      'wb') as f:
                                f.write(response.content)
                    file_name = file_name.replace(".txt", ".xlsx")
                    cols = [
                        "Year and Month", "Date", "Resident Population",
                        "Resident Population Plus Armed Forces Overseas",
                        "Civilian Population",
                        "Civilian NonInstitutionalized Population"
                    ]
                    df = pd.read_table(url,
                                       index_col=False,
                                       delim_whitespace=True,
                                       engine='python',
                                       skiprows=17,
                                       names=cols)
                    # Skipping 17 rows as the initial 17 rows contains the information about
                    # the file being used, heading files spread accross multiple lines and
                    # other irrelevant information like source/contact details.
                    df = _clean_txt_file(df)
                    # Multiplying the data with scaling factor 1000.
                    for col in df.columns:
                        if "year" not in col.lower():
                            df[col] = df[col].apply(_mulitply_scaling_factor)
                    df.to_excel(os.path.join(_INPUT_FILE_PATH, file_name),
                                index=False,
                                engine='xlsxwriter')

                is_file_downloaded = True
                logging.info(f"Downloaded file : {url}")

            except Exception as e:
                logging.error(f"Retry file download {url} - {e}")
                time.sleep(5)
                retry_number += 1
                if retry_number > max_retry:
                    logging.fatal(f"Error downloading {url}")
                    logging.error("Exit from script")
                    sys.exit(1)
    return True


def main(_):
    mode = FLAGS.mode
    # Defining Output file names
    output_path = os.path.join(_MODULE_DIR, "output")
    input_path = os.path.join(_MODULE_DIR, "input_files")
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    cleaned_csv_path = os.path.join(output_path, "USA_Population_Count.csv")
    mcf_path = os.path.join(output_path, "USA_Population_Count.mcf")
    tmcf_path = os.path.join(output_path, "USA_Population_Count.tmcf")
    download_status = True
    if mode == "" or mode == "download":
        add_future_year_urls()
        download_status = download_files()
    if download_status and (mode == "" or mode == "process"):
        loader = CensusUSACountryPopulation(FLAGS.input_path, cleaned_csv_path,
                                            mcf_path, tmcf_path)
        loader.process()


if __name__ == "__main__":
    app.run(main)
