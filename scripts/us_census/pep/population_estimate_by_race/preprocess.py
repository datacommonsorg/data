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
    from the datasets in provided local path.
    Typical usage:
    1. python3 preprocess.py
    2. python3 preprocess.py -i input_data
"""
import os
import re
import sys

import pandas as pd
from absl import app
from absl import flags
from state_to_geoid import USSTATE_MAP
from states_to_shortform import get_states

pd.set_option("display.max_columns", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_data"

if ("ip_path" in sys.argv and len(sys.argv) > 2):
    default_input_path = sys.argv[2]
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def add_geo_id(df: pd.DataFrame) -> pd.DataFrame:
    short_forms = get_states()
    df['Short_Form'] = df['Geographic Area'].str.replace(
        " ", "").apply(lambda row: short_forms.get(row, row))
    df['geo_ID'] = df['Short_Form'].apply(
        lambda rec: USSTATE_MAP.get(rec, pd.NA))
    df = df.dropna(subset=['Geographic Area'])
    return df


def _clean_xls_file(df: pd.DataFrame, file: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    #index=0
    if "2020" in file:
        df.drop(df[df['ORIGIN'] != 0].index, inplace=True)
        df.drop(df[df['SEX'] != 0].index, inplace=True)
        df = df.drop(['STATE','DIVISION','SUMLEV','SEX','ORIGIN'\
            ,'AGE','REGION','ESTIMATESBASE2010','CENSUS2010POP'\
            ,'POPESTIMATE042020'],axis=1)
    else:
        df = df.drop(['STATE','DIVISION','REGION','ESTIMATESBASE2000',\
            'CENSUS2010POP','POPESTIMATE2010'],axis=1)
    df = df.groupby(['NAME', 'RACE']).sum().transpose().stack(0).reset_index()
    if "2020" in file:
        df[0] = df[1] + df[2] + df[3] + df[4] + df[5] + df[6]
    df['0'] = df[0]
    df['1'] = df[1]
    df['2'] = df[2]
    df['3'] = df[3]
    df['4'] = df[4]
    df['5'] = df[5]
    df['6'] = df[6]
    df['Year'] = df['level_0'].str[-4:]
    df = df.drop(['level_0', 0, 1, 2, 3, 4, 5, 6], axis=1)
    df.columns = df.columns.str.replace('NAME', 'Geographic Area')
    df.columns = df.columns.str.replace('0', 'Total')
    df.columns = df.columns.str.replace('1', 'White Alone')
    df.columns = df.columns.str.replace('2', 'Black or African American Alone')
    df.columns = df.columns.str.replace('3',\
        'American Indian or Alaska Native Alone')
    df.columns = df.columns.str.replace('4', 'Asian Alone')
    df.columns = df.columns.str.replace('5',\
        'Native Hawaiian and Other Pacific Islander Alone')
    df.columns = df.columns.str.replace('6', 'Two or more Races')
    print(df.columns)
    return df


def _clean_xlsx_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    df = df.drop(['Census', 'Estimates Base', 2010], axis=1)
    df = df.drop([1], axis=0)
    df.drop(df.index[7:], inplace=True)
    #print(df.columns)
    df['Unnamed: 0'] = df['Unnamed: 0'].str.replace(".", "")
    df['Geographic Area'] = 'United States'
    df = df.groupby(['Geographic Area','Unnamed: 0']).sum()\
        .transpose().stack(0).reset_index()

    df.columns = df.columns.str.replace('level_0', 'Year')
    df.columns = df.columns.str.replace('White', 'White Alone')
    df.columns = df.columns.str.replace('TOTAL POPULATION', 'Total')
    df.columns = df.columns.str.replace('Black or African American', \
        'Black or African American Alone')
    df.columns = df.columns.str.replace(
        'Native Hawaiian and Other Pacific\
         Islander', 'Native Hawaiian and Other Pacific Islander Alone')
    df.columns = df.columns.str.replace('Asian', 'Asian Alone')

    df['Total'] = pd.to_numeric(df['Total'])
    #print(df)
    return df


def _clean_county_70_xls_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    df['Total People']=df[1]+df[2]+df[3]+df[4]+df[5]+df[6]+df[7]\
        +df[8]+df[9]+df[10]+df[11]+df[12]+df[13]+df[14]+df[15]+\
        df[16]+df[17]+df[18]
    df['FIPS'] = [f'{x:05}' for x in df['FIPS']]
    df['Info'] = df['Year'].astype(str) + '-' + df['FIPS'].astype(str)
    df.drop(columns=['Year','FIPS',1,2,3,4,5,6,7,8,9,10,11,12,\
        13,14,15,16,17,18],inplace=True)
    df = df.groupby(['Info','Race/Sex']).sum().transpose().\
        stack(0).reset_index()
    df['Year'] = df['Info'].str.split('-', expand=True)[0]
    df['geo_ID'] = "geoID/" + df['Info'].str.split('-', expand=True)[1]
    df['Total'] = df[1] + df[2] + df[3] + df[4] + df[5] + df[6]
    df['White Alone'] = df[1] + df[2]
    df['Black or African American Alone'] = df[3] + df[4]
    df.drop(columns=['Info', 'level_0', 1, 2, 3, 4, 5, 6], inplace=True)
    return df


def _clean_county_80_xls_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    df['Total People']=df[1]+df[2]+df[3]+df[4]+df[5]+df[6]+df[7]+\
        df[8]+df[9]+df[10]+df[11]+df[12]+df[13]+df[14]+df[15]+\
        df[16]+df[17]+df[18]
    df['FIPS'] = [f'{x:05}' for x in df['FIPS']]
    df['Info'] = df['Year'].astype(str) + '-' + df['FIPS'].astype(str)
    df.drop(columns=['Year','FIPS',1,2,3,4,5,6,7,8,9,10,11,12,13,14\
        ,15,16,17,18],inplace=True)
    df = df.groupby(['Info','Race/Sex']).sum().transpose().\
        stack(0).reset_index()
    df['Year'] = df['Info'].str.split('-', expand=True)[0]
    df['geo_ID'] = "geoID/" + df['Info'].str.split('-', expand=True)[1]
    df['Total']=df['White male']+df['White female']+df['Black male']\
        +df['Black female']+df['Other races male']+df['Other races female']
    df['White Alone'] = df['White male'] + df['White female']
    df['Black or African American Alone'] = df['Black male'] + \
        df['Black female']
    df.drop(columns=['Info','level_0','White male','White female','Black male'\
        ,'Black female','Other races male','Other races female'],inplace=True)
    return df


def _clean_xls2_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a xls file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of xls dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for xls dataset.
    """
    df['Race'] = (df['Race/Sex Indicator'].str.replace(" female", ""))
    df['Race'] = (df['Race'].str.replace(" male", ""))
    df = df.drop(['Race/Sex Indicator'], axis=1)
    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(",", "")
    extras = ['Year of Estimate', 'FIPS State Code', 'State Name', 'Race']
    cols = df.columns.drop(extras)
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    df['count']=df['Under 5 years']+df['5 to 9 years']+df['10 to 14 years']\
        +df['15 to 19 years']+df['20 to 24 years']+df['25 to 29 years']+\
        df['30 to 34 years']+df['35 to 39 years'] +df['40 to 44 years']	\
        +df['45 to 49 years'] +df['50 to 54 years'] +df['55 to 59 years']\
        +df['60 to 64 years'] +df['65 to 69 years'] +df['70 to 74 years']\
        +df['75 to 79 years'] +df['80 to 84 years'] +df['85 years and over']
    df = df.drop(['Under 5 years','5 to 9 years','10 to 14 years',\
        '15 to 19 years','20 to 24 years','25 to 29 years',\
        '30 to 34 years','35 to 39 years','40 to 44 years',\
        '45 to 49 years','50 to 54 years','55 to 59 years',\
        '60 to 64 years','65 to 69 years','70 to 74 years','75 to 79 years',\
        '80 to 84 years','85 years and over'],axis=1)
    df['locationyear'] = df['Year of Estimate'] + "-" + df['State Name']
    df = df.drop(['Year of Estimate', 'State Name'], axis=1)
    df = df.groupby(['locationyear','Race']).sum().transpose().\
        stack(0).reset_index()
    df['Year'] = df['locationyear'].str.split('-', expand=True)[0]
    df['Geographic Area'] = df['locationyear'].str.split('-', expand=True)[1]
    df['Total'] = df["White"] + df["Black"] + df['Other races']
    df = df.drop(['locationyear', 'level_0', 'Other races'], axis=1)

    df.columns = df.columns.str.replace('White', 'White Alone')
    df.columns = df.columns.str.replace('Black', 'Black Alone')

    return df


def _clean_csv_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(",", "")
    df['Total'] = pd.to_numeric(df['1'])
    df['White Alone'] = pd.to_numeric(df['4'])
    col = df.columns
    if len(col) >= 15:
        df['Black or African American Alone'] = pd.to_numeric(df['7'])
        df = df.drop(["10", "11", "12"], axis=1)
        df["American Indian or Alaska Native Alone"] = ""
        df["Asian Alone"] = ""
        df["Native Hawaiian and Other Pacific Islander Alone"] = ""
        df["Two or more Races"] = ""
        df["Total White"] = ""
        df["Total Black"] = ""
        df["Total American Indian & Alaska Native"] = ""
        df["Total Asian & Pacific Islander"] = ""
    df = df.drop(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], axis=1)
    return df


def _clean_county_20_csv_file(file_path: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        file_path (str) : File path of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    df = pd.read_csv(file_path, encoding="ISO-8859-1")
    final_cols = ["Year", "geo_ID", "Total","White Alone",\
        "Black or African American Alone",\
        "American Indian or Alaska Native Alone","Asian Alone",\
        "Native Hawaiian and Other Pacific Islander Alone",\
        "Two or more Races"]

    cols_dict = {
        "geo_ID": ["STATE", "COUNTY"],
        "Total": ["TOT_POP"],
        "White Alone": ["WA_MALE", "WA_FEMALE"],
        "Black or African American Alone": ["BA_MALE", "BA_FEMALE"],
        "American Indian or Alaska Native Alone": ["IA_MALE", "IA_FEMALE"],
        "Asian Alone": ["AA_MALE", "AA_FEMALE"],
        "Native Hawaiian and Other Pacific Islander Alone":      \
            ["NA_MALE", "NA_FEMALE"],
        "Two or more Races": ["TOM_MALE", "TOM_FEMALE"]
    }
    file_name = os.path.basename(file_path)
    start_yr, skip_yr1, skip_yr2, age_grp, initial_yr = 2, 12, 13, 99, 1998
    if "CC-EST2020-ALLDATA6" in file_name:
        start_yr, skip_yr1, skip_yr2, age_grp, initial_yr = 3, 13, 13, 0, 2007
    df = df[(df["YEAR"] >= start_yr) & (df["YEAR"] != skip_yr1) & (df["YEAR"] \
        != skip_yr2) & (df["AGEGRP"] == age_grp) ].reset_index().\
        drop(columns=["index"])
    df["YEAR"] = df["YEAR"].replace(skip_yr1 + 1, skip_yr1)
    df["STATE"] = df["STATE"].astype('str').str.pad\
        (width=2, side="left", fillchar="0")
    df["COUNTY"] = df["COUNTY"].astype('str').str.pad\
        (width=3, side="left", fillchar="0")
    final_df = pd.DataFrame()
    for col in final_cols:
        if col == "Year":
            final_df[col] = initial_yr + df["YEAR"]
        elif col == "geo_ID":
            final_df[col] = "geoId/" + df["STATE"] + df["COUNTY"]
        else:
            final_df[col] = df.loc[:, cols_dict[col]].sum(axis=1).astype('int')
    return final_df


def _clean_csv2_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a csv file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of csv dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for csv dataset.
    """
    df.drop(df.index[65:], inplace=True)
    df.drop(df.index[1:14], inplace=True)
    modify = [0, 30, 31, 32, 33, 34, 35, 40, 41, 42, 49]
    for j in modify:
        df.iloc[j]["Area"] = df.iloc[j]["Area"] + " " + df.iloc[j][1]
        for i in range(2, 10):
            df.iloc[j][i - 1] = df.iloc[j][i]
    df.iloc[9][
        "Area"] = df.iloc[9]["Area"] + " " + df.iloc[9][1] + " " + df.iloc[9][2]
    for i in range(3, 11):
        df.iloc[9][i - 2] = df.iloc[9][i]
    df.drop(columns=["3", "4", "8", "9", "10"], inplace=True)
    df.columns = df.columns.str.replace('Area', 'Geographic Area')
    df.columns = df.columns.str.replace('1', 'Total')
    df.columns = df.columns.str.replace('2', 'Total White')
    df.columns = df.columns.str.replace('5', 'Total Black')
    df.columns = df.columns.str.replace('6', \
        'Total American Indian & Alaska Native')
    df.columns = df.columns.str.replace('7', 'Total Asian & Pacific Islander')

    df["Geographic Area"] = [x.title() for x in df["Geographic Area"]]
    #print(df)
    return df


def _clean_txt_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of txt dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    df['1'] = df['1'].astype(str)
    df = df[df['1'].str.contains("999")]
    mask = df['1'].str[0] == '7'
    df = df.loc[mask]
    df['Geographic Area'] = "United States"
    df['Year'] = "19" + df['1'].str[1:3]
    df['Total'] = df['2']
    df['Total White'] = df['5'] + df['6']
    df['Total Black'] = df['7'] + df['8']
    df['Total American Indian & Alaska Native'] = df['9'] + df['10']
    df['Total Asian & Pacific Islander'] = df['11'] + df['12']
    df = df.drop([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"
    ],
                 axis=1)
    #print(df)
    return df


def _clean_txt2_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        df (DataFrame) : DataFrame of txt dataset

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    df['1'] = df['1'].astype(str)
    mask = df['1'].str.len() >= 6
    df = df.loc[mask]
    mask = df['2'] >= 50000
    df = df.loc[mask]
    mask = df['1'].str[0] == '7'
    df = df.loc[mask]
    #df = df[df['1'].str.contains("7")]
    df = df[df['1'].str.contains("999")]
    #print(df)
    df['Geographic Area'] = "United States"
    df['Year'] = df['1'].str[1:5]
    df['Total'] = df['2']
    df['Total White'] = df['5'] + df['6']
    df['Total Black'] = df['7'] + df['8']
    df['Total American Indian & Alaska Native'] = df['9'] + df['10']
    df['Total Asian & Pacific Islander'] = df['11'] + df['12']
    df = df.drop([
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"
    ],
                 axis=1)
    return df


def _clean_county_90_txt_file(file: str) -> pd.DataFrame:
    """
    This method cleans the dataframe loaded from a txt file format.
    Also, Performs transformations on the data.

    Arguments:
        file (str) : Address of the file in system.

    Returns:
        df (DataFrame) : Transformed DataFrame for txt dataset.
    """
    df=pd.DataFrame(columns=["FIPS","Total","Total White",1,2,"Total Black",\
        "Total American Indian & Alaska Native",\
        "Total Asian & Pacific Islander",3])
    with open(file, encoding="ISO-8859-1") as inp:
        filter_list = ["1", "2", "3", "4", "5", "0"]
        for line in inp.readlines():
            if line.strip().startswith(tuple(filter_list)):
                list2 = (" ".join(line.strip('\n').split()).split())
                list1 = []
                for x in list2:
                    if x.isnumeric():
                        list1.append(x)
                df.loc[len(df.index)] = list1
    df["geo_ID"] = "geoID/" + df["FIPS"]
    df.drop(columns=["FIPS", 1, 2, 3], inplace=True)
    df["Year"] = "19" + file[-6:-4]
    return df


def _transform_df(df: pd.DataFrame) -> pd.DataFrame:
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
    # Deriving new SV Count_Person_NonWhite as
    # subtracting White Alone from
    # Total

    if 'Geographic Area' in df.columns:
        final_cols = [
            col for col in df.columns if 'year' not in col.lower() and
            'geographic area' not in col.lower()
        ]
        missing_cols = ['Geographic Area', 'Year']
    else:
        final_cols = [
            col for col in df.columns
            if 'year' not in col.lower() and 'geo_id' not in col.lower()
        ]
        missing_cols = ['geo_ID', 'Year']

    if 'White Alone' in df.columns:
        df['Count_Person_NonWhite'] = df['Total'].astype(
            'int') - df['White Alone'].astype('int')
        computed_cols = ['Count_Person_NonWhite']
    else:
        computed_cols = []
    df = df[missing_cols + final_cols + computed_cols]

    # Renaming DF Headers with ref to SV's Naming Standards.
    final_cols_list = ["Count_Person_" + col\
                    .replace("Asian Alone", "AsianAlone")\
                    .replace("White Alone", "WhiteAlone")\
                    .replace\
                        ("Native Hawaiian and Other Pacific Islander Alone"\
                        ,"NativeHawaiianAndOtherPacificIslanderAlone")\
                    .replace("Black or African American Alone",\
                        "BlackOrAfricanAmericanAlone")\
                    .replace("Two or more Races",\
                            "TwoOrMoreRaces")\
                    .replace("American Indian or Alaska Native Alone",\
                        "AmericanIndianAndAlaskaNativeAlone")
                    .replace("Asian and Pacific Islander",\
                        "AsianAndPacificIslander")\
                    .replace("Total White",\
                        "WhiteAloneOrInCombinationWithOneOrMoreOtherRaces")\
                    .replace("Total Black",\
                        "BlackOrAfricanAmericanAloneOrInCombination"+\
                            "WithOneOrMoreOtherRaces")\
                    .replace("Total American Indian & Alaska Native",\
                        "AmericanIndianAndAlaskaNativeAloneOrInCombin"\
                            +"ationWithOneOrMoreOtherRaces")\
                    .replace("Total Asian & Pacific Islander",\
                        "AsianOrPacificIslander")\
                    .strip()\
                    .replace(" ", "_")\
                    for col in final_cols]

    final_cols_list = missing_cols + final_cols_list + computed_cols
    df.columns = final_cols_list
    return df


class CensusUSAPopulationByRace:
    """
    CensusUSAPopulationByRace class provides methods
    to load the data into dataframes, process, cleans
    dataframes and finally creates single cleaned csv
    file.
    Also provides methods to generate MCF and TMCF
    Files using pre-defined templates.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path
        self.df = None
        self.file_name = None
        self.scaling_factor = 1

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
        self.file_name = os.path.basename(file)
        print(file)
        if ".xls" in file:
            if "pe-19" in file:
                df = pd.read_excel(file)
                df = _clean_xls2_file(df)
            elif "nc-est" in file:
                df = pd.read_excel(file)
                df = _clean_xlsx_file(df)
            elif "co-asr-7079" in file:
                df = pd.read_excel(file)
                df = _clean_county_70_xls_file(df)
            elif "pe-02" in file:
                df = pd.read_excel(file)
                df = _clean_county_80_xls_file(df)
            else:
                df = pd.read_excel(file)
                df = _clean_xls_file(df, file)
        elif ".csv" in file:
            if "srh" in file:
                df = pd.read_csv(file)
                df["Year"] = "19" + file[-6:-4]
                df = _clean_csv2_file(df)
            elif "co-est00" in file or "CC-EST2020" in file:
                df = _clean_county_20_csv_file(file)
            else:
                df = pd.read_csv(file)
                df = _clean_csv_file(df)
        elif ".TXT" in file or ".txt" in file:
            if "USCounty" in file:
                df = _clean_county_90_txt_file(file)
            else:
                cols = ["0", "1", "2", "3", "4", "5", "6", "7",\
                    "8", "9", "10", "11","12", "13", "14", "15",\
                    "16", "17", "18", "19", "20", "21", "22"]
                df = pd.read_table(file,
                                   index_col=False,
                                   delim_whitespace=True,
                                   engine='python',
                                   names=cols)
                if "CQI" in file:
                    df = _clean_txt_file(df)
                elif "for" in file:
                    df = _clean_txt2_file(df)
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
        # Finding the Dir Path
        file_dir = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        df = _transform_df(df)
        if 'geo_ID' not in df.columns:
            df = add_geo_id(df)
        if self.df is None:
            self.df = pd.DataFrame(columns=["Year","geo_ID",\
                "Count_Person_USAllRaces","Count_Person_WhiteAlone",\
                "Count_Person_BlackOrAfricanAmericanAlone",\
                "Count_Person_AmericanIndianAndAlaskaNativeAlone",\
                "Count_Person_AsianAlone"\
                ,"Count_Person_NativeHawaiianAndOtherPacificIslanderAlone",\
                "Count_Person_WhiteAloneOrInCombinationWithOne"+\
                    "OrMoreOtherRaces",\
                "Count_Person_BlackOrAfricanAmericanAloneOrInCombination"+\
                    "WithOneOrMoreOtherRaces",\
                "Count_Person_AsianOrPacificIslander",\
                "Count_Person_AmericanIndianAndAlaskaNativeAloneOrIn"+\
                    "CombinationWithOneOrMoreOtherRaces",\
                "Count_Person_TwoOrMoreRaces","Count_Person_NonWhite"])
            self.df = self.df.append(df, ignore_index=True)

        else:
            self.df = self.df.append(df, ignore_index=True)
        self.df['Year'] = pd.to_numeric(self.df['Year'])
        self.df.sort_values(by=['Year', 'geo_ID'], ascending=True, inplace=True)
        self.df = self.df[["Year","geo_ID",
            "Count_Person_WhiteAlone",\
            "Count_Person_BlackOrAfricanAmericanAlone",\
            "Count_Person_AmericanIndianAndAlaskaNativeAlone",\
            "Count_Person_AsianAlone",\
            "Count_Person_NativeHawaiianAndOtherPacificIslanderAlone",\
            "Count_Person_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces",\
            "Count_Person_BlackOrAfricanAmericanAloneOrInCombination"+\
                "WithOneOrMoreOtherRaces",\
            "Count_Person_AsianOrPacificIslander",\
            "Count_Person_AmericanIndianAndAlaskaNativeAloneOrIn"+\
                "CombinationWithOneOrMoreOtherRaces",\
            "Count_Person_TwoOrMoreRaces","Count_Person_NonWhite"]]
        self.df.to_csv(self.cleaned_csv_file_path, index=False)

    def process(self):
        """
        This is main method to iterate on each file,
        calls defined methods to clean, generate final
        cleaned CSV file, MCF file and TMCF file.
        """
        for file in self.input_files:
            df = self._load_data(file)
            self._transform_data(df)
        self._generate_mcf(self.df.columns)
        self._generate_tmcf(self.df.columns)

    def _generate_mcf(self, df_cols: list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Arguments:
            df_cols (list) : List of DataFrame Columns

        Returns:
            None
        """
        mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
race: dcs:{}
"""
        mcf = ""
        for col in df_cols:
            race = ""
            if col.lower() in [
                    "geographic area", "year", "short_form", "geo_id"
            ]:
                continue
            if re.findall('WhiteAlone', col) and \
                re.findall('OrInCombination', col):
                race = "WhiteAloneOrInCombinationWithOneOrMoreOtherRaces"
            elif re.findall('White', col) and re.findall('Non', col):
                race = "NonWhite"
            elif re.findall('WhiteAlone', col):
                race = "WhiteAlone"
            if re.findall('Black', col) and \
                re.findall('OrInCombination', col):
                race = "BlackOrAfricanAmericanAloneOrInCombination"+\
                    "WithOneOrMoreOtherRaces"
            elif re.findall('Black', col):
                race = "BlackOrAfricanAmericanAlone"
            if re.findall('AmericanIndian', col):
                if re.findall('OrInCombination', col):
                    race = "AmericanIndianAndAlaskaNativeAloneOrIn"+\
                        "CombinationWithOneOrMoreOtherRaces"
                else:
                    race = "AmericanIndianAndAlaskaNativeAlone"
            if re.findall('AsianAlone', col):
                race = "AsianAlone"
            if re.findall('NativeHawaiianAndOtherPacificIslanderAlone', col):
                race = "NativeHawaiianAndOtherPacificIslanderAlone"
            if re.findall('TwoOrMoreRaces', col):
                race = "TwoOrMoreRaces"
            if re.findall('AsianOrPacificIslander', col):
                race = "AsianOrPacificIslander"
            mcf = mcf + mcf_template.format(col, race) + "\n"

        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
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
        tmcf_template = """Node: E:USA_Population_Count->E{}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{}
measurementMethod: dcs:{}
observationAbout: C:USA_Population_Count->geo_ID
observationDate: C:USA_Population_Count->Year
observationPeriod: \"P1Y\"
value: C:USA_Population_Count->{}  
"""
        i = 0
        measure = ""
        tmcf = ""
        for col in df_cols:
            if col.lower() in [
                    "geographic area", "year", "short_form", "geo_id"
            ]:
                continue
            if re.findall('NonWhite', col):
                measure = "dcAggregate/CensusPEPSurvey"
            else:
                measure = "CensusPEPSurvey"
            tmcf = tmcf + tmcf_template.format(i, col, measure, col) + "\n"
            i = i + 1

        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))


def main(_):
    input_path = FLAGS.input_path

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    # Defining Output file names
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    cleaned_csv_path = data_file_path + os.sep +\
        "USA_Population_Count_by_Race.csv"
    mcf_path = data_file_path + os.sep + "USA_Population_Count_by_Race.mcf"
    tmcf_path = data_file_path + os.sep + \
        "USA_Population_Count_by_Race.tmcf"

    loader = CensusUSAPopulationByRace(ip_files, cleaned_csv_path, mcf_path,
                                       tmcf_path)

    loader.process()


if __name__ == "__main__":
    app.run(main)
