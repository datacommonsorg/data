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
    2. python3 preprocess.py -i input_data
"""
from dataclasses import replace
import os
import re

import pandas as pd
from absl import app
from absl import flags

pd.set_option("display.max_columns", None)

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_data")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

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

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
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

    def _transform_df(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def _transform_data(self, df: pd.DataFrame) -> None:
        """
        This method calls the required functions to transform
        the dataframe and saves the final cleaned data in
        CSV file format.

        Arguments:
            file (str) : Dataset File Path

        Returns:
            df (DataFrame) : DataFrame.
        """

        df = self._transform_df(df)

        if self._df is None:
            self._df = df
        else:
            self._df = self._df.append(df, ignore_index=True)

        self._df.sort_values(by=['Date', 'date_range'],
                             ascending=False,
                             inplace=True)
        self._df.drop_duplicates("Date", keep="first", inplace=True)
        self._df.drop(['date_range'], axis=1, inplace=True)
        float_col = self._df.select_dtypes(include=['float64'])
        for col in float_col.columns.values:
            self._df[col] = self._df[col].astype('int64')
        self._df.to_csv(self._cleaned_csv_file_path, index=False)

    def _generate_mcf(self, df_cols: list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """

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
        for file in self._input_files:
            df = self._load_data(file)
            self._transform_data(df)
        self._generate_mcf(self._df.columns)
        self._generate_tmcf(self._df.columns)


def main(_):
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output file names
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    cleaned_csv_path = os.path.join(data_file_path, "USA_Population_Count.csv")
    mcf_path = os.path.join(data_file_path, "USA_Population_Count.mcf")
    tmcf_path = os.path.join(data_file_path, "USA_Population_Count.tmcf")

    loader = CensusUSACountryPopulation(ip_files, cleaned_csv_path, mcf_path,
                                        tmcf_path)

    loader.process()


if __name__ == "__main__":
    app.run(main)
