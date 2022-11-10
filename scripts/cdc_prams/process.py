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
The Python script loads the datasets,
cleans them and generates the cleaned CSV, MCF and TMCF file.
"""
import os
import sys
import re
from copy import deepcopy
import pandas as pd
import numpy as np
from absl import app, flags
import tabula as tb

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, _CODEDIR)
sys.path.insert(1, os.path.join(_CODEDIR, '../../util/'))
from statvar_dcid_generator import get_statvar_dcid
from state_division_to_dcid import _PLACE_MAP

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
from statvar import statvar_col
from constants import (_MCF_TEMPLATE, _TMCF_TEMPLATE, DEFAULT_SV_PROP, _PROP,
                       _TIME, _INSURANCE, _CIGARETTES, PV_PROP, _YEAR)

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")

flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
input_years = ["2016", "2017", "2018", "2019", "2020"]
flags.DEFINE_list("input_years", input_years, "Import Data File's List")


def _merging_multiline_sv(df, geo):
    '''
    StatVar column which are present in multiline format are converted into
    one single statvar
    Args: DataFrame, Flag
    Returns: df1: DataFrame
    '''
    multiline = [
        'Multivitamin use ≥4 times a week during the month before',
        'Heavy drinking (≥8 drinks a week) during the 3 months before',
        'Experienced IPV during pregnancy by a husband or partner'
    ]
    # Converting the multiline statistical variable into single line
    # statistical variable
    for line in multiline:
        for i in range(len(df)):
            if df.loc[i, 'statVar'] == line:
                df.loc[i,'statVar'] = \
                    f"{df.loc[i,'statVar']}{' '}{df.loc[i + 2,'statVar']}"
                for year in _FLAGS.input_years:
                    if year == "2016":
                        df.loc[i, year + '_sampleSize'] = df.loc[i + 1,
                                                                 'statVar']
                        df.loc[i, year + '_CI'] = df.loc[i + 1, year + '_CI']
                    else:
                        df.loc[i, year + '_sampleSize'] = df.loc[i + 1, year +
                                                                 '_sampleSize']
                        df.loc[i, year + '_CI'] = df.loc[i + 1, year + '_CI']
                if geo == "State":
                    df.loc[i, 'Overall_2020_CI'] = df.loc[i + 1,
                                                          'Overall_2020_CI']
                df.drop([i + 1, i + 2], inplace=True)
                df.reset_index(drop=True, inplace=True)
                break
    return df


def _split_statvar_value(df, geo):
    '''
    The values are seperated from the statvar and given into the next column
    Args: DataFrame, Flag
    Returns: df: DataFrame
    '''
    for i in range(len(df)):
        if df.loc[i, 'statVar'][-4:].strip().strip('§').isnumeric():
            if geo == "State":
                df.loc[i, '2016_sampleSize'] = df.loc[
                    i, 'statVar'][-4:].strip().strip('§')
            elif geo == "National":
                df.loc[i, '2016_sampleSize'] = df.loc[
                    i, 'statVar'][-5:].strip().strip('§')
            l1 = len(df.loc[i, 'statVar'])
            l2 = len(df.loc[i, '2016_sampleSize'])
            df.loc[i, 'statVar'] = df.loc[i, 'statVar'][:l1 - l2].strip()
        if re.match(r'^\d{1}\.\d{1} \(\d{1}.\d{1}-\d{1}\.\d{1}\)',
                    df.loc[i, 'statVar']):
            df.loc[i, 'Overall_2020_CI'] = df.loc[i, 'statVar'][:12]
            df.loc[i, 'statVar'] = df.loc[i, 'statVar'][13:]
    return df


national_columns = [
    'Geo', 'SV', '2016_sampleSize', '2016_CI', '2017_sampleSize', '2017_CI',
    '2018_sampleSize', '2018_CI', '2019_sampleSize', '2019_CI',
    '2020_sampleSize', '2020_CI', 'ScalingFactor'
]


def _cleaning_national_file(df, geo):
    '''
    There are certain rows in which specific values are not split as required
    Args: DataFrame, Flag
    Returns: df: DataFrame
    '''
    for i in range(len(df)):
        if df.loc[
                i,
                'statVar'] == 'Experienced IPV during the 12 months'+\
                    ' before pregnancy by a':
            if geo == "National":
                df.loc[i, 'statVar'] = df.loc[i,
                                              'statVar'].replace('a2.5 ', 'a')
                df.loc[i + 1, '2020_CI'] = 2.5
            df.loc[i + 1,
                   'statVar'] = df.loc[i, 'statVar'] + df.loc[i + 1, 'statVar']
            df.drop([i], inplace=True)
            df.reset_index(drop=True, inplace=True)
            break
    # The values are seperated from the statvar and given into the next
    # column in the national file.
    if geo == "National":
        for i in range(len(df)):
            if df.loc[
                    i,
                    'statVar'] == 'Teeth cleaned during pregnancy by'+\
                        ' a dentist or dental':
                df.loc[i + 1,
                       'statVar'] = df.loc[i + 1,
                                           'statVar'].replace('40.0 ', '')
                df.loc[i + 1, '2020_CI'] = 40.0
                df.loc[i + 1,
                       'statVar'] = df.loc[i, 'statVar'] + df.loc[i + 1,
                                                                  'statVar']
                df.drop([i], inplace=True)
                df.reset_index(drop=True, inplace=True)
                break
    return df


def _flatten_header_and_sub_header(df) -> pd.DataFrame:
    '''
    The source file has main headers, sub headers and statvar.
    All the headers and statvars are combined into one
    Args: DataFrame, Flag
    Returns: df: DataFrame
    '''
    main_header = [
        'Nutrition', 'Pre-pregnancy Weight', 'Substance Use',
        'Intimate Partner Violence (IPV)¥', 'Depression',
        'Health Care Services', 'Pregnancy Intention',
        'Postpartum†† Family Planning', 'Oral Health',
        'Health Insurance Status One Month Before Pregnancy¶',
        'Health Insurance Status One Month Before Pregnancy¶¶',
        'Health Insurance Status for Prenatal Care¶¶',
        'Health Insurance Status Postpartum††¶¶', 'Infant Sleep Practices',
        'Breastfeeding Practices'
    ]

    sub_header = [
        'Any cigarette smoking', 'Any e-cigarette use',
        'Highly effective contraceptive methods'
    ]

    df['main_header'] = np.where(df['statVar'].isin(main_header), df['statVar'],
                                 pd.NA)
    df['main_header_delete_flag'] = df['main_header']
    df['main_header_delete_flag'] = df['main_header_delete_flag'].fillna("")
    df['main_header'] = df['main_header'].fillna(method='ffill')

    df['sub_header'] = np.where(df['statVar'].isin(sub_header), df['statVar'],
                                pd.NA)
    df['sub_header_delete_flag'] = df['sub_header']
    df['sub_header_delete_flag'] = df['sub_header_delete_flag'].fillna("")
    df['sub_header'] = df['sub_header'].fillna(method='ffill', limit=2)
    index = df[df['statVar'] == 'Postpartum'].index.values[0]
    df.loc[index, 'sub_header'] = "Any cigarette smoking"
    df['sub_header'] = df['sub_header'].fillna("")

    df['newStatVar'] = df['main_header'] + "_" + df['sub_header'] + "_" + df[
        'statVar']
    df = df.loc[(df['main_header_delete_flag'] == '')]
    df = df.loc[(df['sub_header_delete_flag'] == '')]
    df = df.drop(columns=[
        'statVar', 'main_header_delete_flag', 'sub_header', 'main_header',
        'sub_header_delete_flag'
    ])
    df['SV'] = df['newStatVar']
    # Replacing statvar with proper statvar from the dictionary
    df = df.replace({'SV': statvar_col})
    # Resolving geoId using util folder.
    df = df.replace({'Geo': _PLACE_MAP})
    df = df.reset_index(drop=True)
    # Creating a new column named as 'ScalingFactor'
    df.insert(1, 'ScalingFactor', np.NaN)
    return df


state_columns = [
    'Geo', 'SV', '2016_sampleSize', '2017_sampleSize', '2018_sampleSize',
    '2019_sampleSize', '2020_sampleSize', '2016_CI_PERCENT', '2016_CI_LOWER',
    '2016_CI_UPPER', '2017_CI_PERCENT', '2017_CI_LOWER', '2017_CI_UPPER',
    '2018_CI_PERCENT', '2018_CI_LOWER', '2018_CI_UPPER', '2019_CI_PERCENT',
    '2019_CI_LOWER', '2019_CI_UPPER', '2020_CI_PERCENT', '2020_CI_LOWER',
    '2020_CI_UPPER', 'ScalingFactor'
]


def _splitting_ci_columns(df, geo):
    '''
    The CI has percent, lower confidence and upper confidence values
    within one column. This method is used to seperated into three
    different columns for State. Ex: 39.3 (36.4-42.2)
    Args: DataFrame, Flag
    Returns: df: DataFrame
    '''
    if geo == "State":
        split_col = ['2016_CI', '2017_CI', '2018_CI', '2019_CI', '2020_CI']
        for i in split_col:
            df[i] = df[i].fillna(pd.NA)
            # Splitting the column based on space and "-"
            df_split = df[i].str.split(r"\s+|-", expand=True)
            # determinign the size of the column after splitting it.
            siz = df_split.shape[1]
            # If the column is empty the size is 1 it is spit and
            # the columns remain empty
            if siz == 1:
                df_split = df_split.rename(
                    columns={df_split.columns[0]: i + '_PERCENT'})
                df_split[i + '_LOWER'] = ""
                df_split[i + '_UPPER'] = ""
            # If the column size is 3, it is split into 3 different columns.
            elif siz == 3:
                df_split = df_split.rename(
                    columns={
                        df_split.columns[0]: i + '_PERCENT',
                        df_split.columns[1]: i + '_LOWER',
                        df_split.columns[2]: i + '_UPPER'
                    })
                # Removing unwanted characters.
                df_split[i + '_LOWER'] = df_split[i + '_LOWER'].str.replace(
                    '(', '', regex=False)
                df_split[i + '_UPPER'] = df_split[i + '_UPPER'].str.replace(
                    ')', '', regex=False)
            df = pd.concat([df, df_split], axis=1)
        df = df.drop(columns=[
            'newStatVar', '2016_CI', '2017_CI', '2018_CI', '2019_CI', '2020_CI',
            'Overall_2020_CI'
        ])
        # Redifining columns
    if geo == "National":
        df = df[national_columns]
    elif geo == "State":
        df = df[state_columns]
        # The Distric of Columbia has characters : (.-.)
        df['2018_CI_UPPER'] = df['2018_CI_UPPER'].replace('.', '0.0')
        df['2018_CI_LOWER'] = df['2018_CI_LOWER'].replace('.', '0.0')
    return df


def _stat_var(df, geo):
    '''
        Creating dummy statvars to generate properties
        Args: DataFrame, Flag
        Returns: df_all: DataFrame
    '''
    df_all = pd.DataFrame([])
    sv_columns = ['sample_size', 'percent_sv', 'lower_level', 'upper_level']

    for col in sv_columns:
        temp_df = df.copy()

        drop_columns = []
        if col == "sample_size":
            temp_df['SV'] = 'SampleSize_Count' + temp_df['SV']
            if geo == "National":
                for year in range(2016, 2021):
                    drop_columns.append(str(year) + '_CI')
                temp_df = temp_df.drop(columns=drop_columns)
            elif geo == "State":
                for year in range(2016, 2021):
                    for col in ['_CI_PERCENT', '_CI_LOWER', '_CI_UPPER']:
                        drop_columns.append(str(year) + col)
                temp_df = temp_df.drop(columns=drop_columns)

            temp_df = temp_df.melt(id_vars=['Geo', 'SV', 'ScalingFactor'],
                                   var_name='Year',
                                   value_name='Observation')

        elif col == "percent_sv":
            temp_df['SV'] = 'Percent' + temp_df['SV']
            temp_df['ScalingFactor'] = 100

            if geo == "National":
                for year in range(2016, 2021):
                    drop_columns.append(str(year) + '_sampleSize')
                temp_df = temp_df.drop(columns=drop_columns)
            elif geo == "State":
                for year in range(2016, 2021):
                    for col in ['_sampleSize', '_CI_LOWER', '_CI_UPPER']:
                        drop_columns.append(str(year) + col)
                temp_df = temp_df.drop(columns=drop_columns)

            temp_df = temp_df.melt(id_vars=['Geo', 'SV', 'ScalingFactor'],
                                   var_name='Year',
                                   value_name='Observation')

        elif col == "lower_level":
            if geo == "National":
                continue
            elif geo == "State":
                temp_df[
                    'SV'] = 'ConfidenceIntervalLowerLimit_Count' + temp_df['SV']
                for year in range(2016, 2021):
                    for col in ['_sampleSize', '_CI_UPPER', '_CI_PERCENT']:
                        drop_columns.append(str(year) + col)
                temp_df = temp_df.drop(columns=drop_columns)

                temp_df = temp_df.melt(id_vars=['Geo', 'SV', 'ScalingFactor'],
                                       var_name='Year',
                                       value_name='Observation')

        elif col == "upper_level":
            if geo == "National":
                continue
            elif geo == "State":
                temp_df[
                    'SV'] = 'ConfidenceIntervalUpperLimit_Count' + temp_df['SV']
                for year in range(2016, 2021):
                    for col in ['_sampleSize', '_CI_LOWER', '_CI_PERCENT']:
                        drop_columns.append(str(year) + col)
                temp_df = temp_df.drop(columns=drop_columns)
                temp_df = temp_df.melt(id_vars=['Geo', 'SV', 'ScalingFactor'],
                                       var_name='Year',
                                       value_name='Observation')

        df_all = pd.concat([df_all, temp_df], axis=0)
        df_all = df_all[['Geo', 'SV', 'Year', 'Observation', 'ScalingFactor']]
    return df_all


def prams(input_url: list) -> pd.DataFrame:
    '''
        Cleans the files for concatenation in Final CSV
         Args:
            input_url (list) : List of input urls
        Returns:
            df_all : DataFrame
    '''
    final_df = pd.DataFrame()
    # Creatd flag as the format for state and national file are different and
    # requires different modifications.
    for file in input_url:
        geo = "State"
        if "All-Sites" in file:
            geo = "National"
        data = tb.read_pdf(file, pages='all')
        df = pd.concat(data)
        file_name = os.path.basename(file)
        # creating geoId column in the dataframe and resolving geoId value for
        # District of Columbia, New York City and National file.
        df['Geo'] = file_name.replace('-PRAMS-MCH-Indicators-508.pdf','').\
        replace('-',' ').replace('District Columbia','District of Columbia')\
        .replace('New York City','geoId/3651000')\
            .replace('All Sites','country/USA')
        df.reset_index(drop=True, inplace=True)
        if geo == "State":
            # dropping unwanted columns
            df = df.drop([
                'Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3',
                'Unnamed: 4'
            ],
                         axis=1)
            df.columns = [
                'statVar', '2016_CI', '2017_sampleSize', '2017_CI',
                '2018_sampleSize', '2018_CI', '2019_sampleSize', '2019_CI',
                '2020_sampleSize', '2020_CI', 'Overall_2020_CI', 'Geo'
            ]
        elif geo == "National":
            df.columns = [
                'statVar', '2016_CI', '2017_sampleSize', '2017_Nan', '2017_CI',
                '2018_sampleSize', '2018_Nan', '2018_CI', '2019_sampleSize',
                '2019_Nan', '2019_CI', '2020_sampleSize', '2020_Nan', '2020_CI',
                'Geo'
            ]
            # dropping unwanted columns
            df = df.drop(['2017_Nan', '2018_Nan', '2019_Nan', '2020_Nan'],
                         axis=1)
        # inserting an extra column so that the first column
        df.insert(1, '2016_sampleSize', np.NaN)
        # Removing unwanted charaters
        df['statVar'] = df['statVar'].str.replace('• ', '')
        df = _merging_multiline_sv(df, geo)
        df = _split_statvar_value(df, geo)
        df = _cleaning_national_file(df, geo)
        df = _flatten_header_and_sub_header(df)
        df = _splitting_ci_columns(df, geo)
        df = _stat_var(df, geo)
        final_df = pd.concat([final_df, df], axis=0)
        # Replacing Year column with the correct Values.
        for old, new in _YEAR.items():
            final_df['Year'] = final_df['Year'].replace(old, new)
        final_df.reset_index(drop=True, inplace=True)
        final_df = final_df.sort_values(by=['Geo'], kind="stable")
    return final_df


class USPrams:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Arguments:
            None
        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding="UTF-8") as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def _generate_mcf(self, sv_names: list, mcf_file_path: str) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_names (list): List of Statistical Variables
            mcf_file_path (str): Output MCF File Path
        """
        # pylint: disable=W1309
        # pylint: disable=R0912
        # pylint: disable=R0915
        mcf_nodes = []
        dcid_nodes = {}
        for sv in sv_names:
            pvs = []
            dcid = sv
            sv_prop = [prop.strip() for prop in sv.split(" ")]
            # Using statistical variable template
            # deepcopy follows the template and keeps adding the properties.
            sv_pvs = deepcopy(DEFAULT_SV_PROP)
            # Created dictionaries to replace with correct values
            for prop in sv_prop:
                statVar = insurance = time = cigarettes = prop_val = prop
                for old, new in _PROP.items():
                    statVar = statVar.replace(old, new)
                for old, new in _INSURANCE.items():
                    insurance = insurance.replace(old, new)
                for old, new in _TIME.items():
                    time = time.replace(old, new)
                for old, new in _CIGARETTES.items():
                    cigarettes = cigarettes.replace(old, new)
                for old, new in PV_PROP.items():
                    prop_val = prop_val.replace(old, new)

                if "SampleSize" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:count"
                    sv_pvs["statType"] = f"dcs:sampleSize"
                    pvs.append(f"measuredProperty: dcs:count")
                    pvs.append(f"statType: dcs:sampleSize")

                if "Percent" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    sv_pvs["statType"] = f"dcs:measuredValue"
                    sv_pvs[
                        "measurementDenominator"] = f"dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    pvs.append(f"measuredProperty: dcs:count")
                    pvs.append(f"statType: dcs:measuredValue")
                    pvs.append(
                        f"measurementDenominator: dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    )

                if "ConfidenceIntervalLowerLimit" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    sv_pvs["statType"] = f"dcs:confidenceIntervalLowerLimit"
                    sv_pvs[
                        "measurementDenominator"] = f"dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    pvs.append(f"measuredProperty: dcs:count")
                    pvs.append(f"statType: dcs:confidenceIntervalLowerLimit")
                    pvs.append(
                        f"measurementDenominator: dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    )

                if "ConfidenceIntervalUpperLimit" in prop:
                    sv_pvs["measuredProperty"] = f"dcs:percent"
                    sv_pvs["statType"] = f"dcs:confidenceIntervalUpperLimit"
                    sv_pvs[
                        "measurementDenominator"] = f"dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    pvs.append(f"measuredProperty: dcs:count")
                    pvs.append(f"statType: dcs:confidenceIntervalUpperLimit")
                    pvs.append(
                        f"measurementDenominator: dcs:Count_BirthEvent"+\
                            "_LiveBirth"
                    )

                if "MultivitaminUseMoreThan4TimesAWeek" in prop:
                    prop = prop[0].lower() + prop[1:]
                    sv_pvs["mothersHealthPrevention"] = f"dcs:{statVar}"
                    sv_pvs["healthPreventionActionFrequency"] = f"dcs:{time}"
                    pvs.append(f"mothersHealthPrevention: dcs:{statVar}")
                    pvs.append(f"healthPreventionActionFrequency: dcs:{time}")

                if "Underweight" in prop or "Overweight" in prop or\
                    "Obese" in prop:
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{statVar}"
                    pvs.append(f"mothersHealthBehavior: dcs:{statVar}")

                if "HealthCareVisit12MonthsBeforePregnancy"in prop or\
                        "PrenatalCareInFirstTrimester" in prop or\
                        "FluShot12MonthsBeforeDelivery"in prop or\
                        "MaternalCheckupPostpartum" in prop or\
                        "TeethCleanedByDentistOrHygienist" in prop:
                    prop = prop[0].lower() + prop[1:]
                    sv_pvs["mothersHealthPrevention"] = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{time}"
                    pvs.append(f"mothersHealthPrevention: dcs:{statVar}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "CigaretteSmoking3MonthsBeforePregnancy" in prop or\
                    "CigaretteSmokingLast3MonthsOfPregnancy"in prop or \
                    "CigaretteSmokingPostpartum" in prop or\
                    "ECigaretteSmoking3MonthsBeforePregnancy" in prop or\
                    "ECigaretteSmokingLast3MonthsOfPregnancy" in prop:
                    sv_pvs["tobaccoUsageType"] = f"dcs:{cigarettes}"
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{time}"
                    pvs.append(f"tobaccoUsageType: dcs:{cigarettes}")
                    pvs.append(f"mothersHealthBehavior: dcs:{statVar}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "HookahInLast2Years" in prop or\
                     "HeavyDrinking3MonthsBeforePregnancy" in prop:
                    sv_pvs["mothersHealthBehavior"] = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{time}"
                    pvs.append(f"mothersHealthBehavior: dcs:{statVar}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "IntimatePartnerViolenceByCurrentOrExPartnerOr"+\
                    "CurrentOrExHusband" in prop:
                    sv_pvs["intimatePartnerViolence"] = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"{time}"
                    pvs.append(f"intimatePartnerViolence: dcs:{statVar}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "MistimedPregnancy" in prop or\
                    "UnwantedPregnancy" in prop or\
                    "UnsureIfWantedPregnancy" in prop or\
                     "IntendedPregnancy" in prop :
                    sv_pvs["pregnancyIntention"] = f"dcs:{cigarettes}"
                    pvs.append(f"pregnancyIntention: dcs:{cigarettes}")

                elif "AnyPostpartumFamilyPlanning"in prop or\
                    "MaleOrFemaleSterilization"in prop or\
                    "LongActingReversibleContraceptiveMethods" in prop or\
                    "ModeratelyEffectiveContraceptiveMethods"in prop or\
                    "LeastEffectiveContraceptiveMethods"in prop:
                    sv_pvs["postpartumFamilyPlanning"] = f"dcs:{cigarettes}"
                    pvs.append(f"postpartumFamilyPlanning: dcs:{cigarettes}")

                elif "CDC_SelfReportedDepression3MonthsBeforePregnancy" in prop\
                     or "CDC_SelfReportedDepressionDuringPregnancy" in prop or\
                    "CDC_SelfReportedDepressionPostpartum" in prop:
                    sv_pvs["mothersHealthCondition"] = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{time}"
                    pvs.append(f"mothersHealthCondition: dcs:{statVar}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "healthInsuranceStatusOneMonthBeforePregnancy"+\
                    "PrivateInsurance"in prop or\
                    "healthInsuranceStatusOneMonthBeforePregnancy"+\
                        "Medicaid" in prop or\
                    "healthInsuranceStatusOneMonthBeforePregnancy"+\
                        "NoInsurance" in prop :
                    sv_pvs["healthInsuranceStatusOneMonthBeforePregnancy"]\
                    = f"dcs:{statVar}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{time}"
                    pvs.append(
                        f"healthInsuranceStatusOneMonthBeforePregnancy: dcs:{statVar}"
                    )
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "healthInsuranceStatusForPrenatalCare"+\
                    "PrivateInsurance"in prop or\
                    "healthInsuranceStatusForPrenatalCareMedicaid" in prop or\
                    "healthInsuranceStatusForPrenatalCareNoInsurance" in prop:
                    sv_pvs[
                        "healthInsuranceStatusForPrenatalCare"] = f"dcs:{statVar}"
                    pvs.append(
                        f"healthInsuranceStatusForPrenatalCare: dcs:{statVar}")

                elif "healthInsuranceStatusPostpartumPrivateInsurance" in prop\
                    or "healthInsuranceStatusPostpartumMedicaid" in prop or\
                    "healthInsuranceStatusPostpartumNoInsurance" in prop:
                    sv_pvs[
                        "healthInsuranceStatusPostpartum"] = f"dcs:{insurance}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{time}"
                    pvs.append(
                        f"healthInsuranceStatusPostpartum: dcs:{insurance}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

                elif "BabyMostOftenLaidOnBackToSleep" in prop:
                    sv_pvs["infantSleepPractice"] = f"dcs:{cigarettes}"
                    pvs.append(f"infantSleepPractice: dcs:{cigarettes}")

                elif "EverBreastfed" in prop:
                    sv_pvs["breastFeedingPractice"] = f"dcs:{cigarettes}"
                    pvs.append(f"breastFeedingPractice: dcs:{cigarettes}")

                elif "AnyBreastfeedingAt8Weeks" in prop:
                    sv_pvs["breastFeedingPractice"] = f"dcs:{cigarettes}"
                    sv_pvs["timePeriodRelativeToPregnancy"] = f"dcs:{time}"
                    pvs.append(f"breastFeedingPractice: dcs:{cigarettes}")
                    pvs.append(f"timePeriodRelativeToPregnancy: dcs:{time}")

            resolved_dcid = get_statvar_dcid(sv_pvs)
            dcid_nodes[dcid] = resolved_dcid
            mcf_nodes.append(
                _MCF_TEMPLATE.format(dcid=resolved_dcid,
                                     xtra_pvs='\n'.join(pvs)))
        mcf = '\n'.join(mcf_nodes)
        # Writing Genereated MCF to local path.
        with open(mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(mcf.rstrip('\n'))
        return dcid_nodes
        # pylint: enable=W1309
        # pylint: enable=R0912
        # pylint: enable=R0915

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        Arguments: None
        Returns: None
        """
        df = prams(self.input_files)
        sv_names = df.SV.unique().tolist()
        sv_names.sort()

        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        updated_sv = self._generate_mcf(sv_names, self.mcf_file_path)
        # Replacing dummy statvars with the Statistical variables generated from
        # dcid_generator
        df["SV"] = df["SV"].map(updated_sv)
        self._generate_tmcf()
        df["Observation"] = df["Observation"].replace(to_replace={'': pd.NA})
        df = df.dropna(subset=['Observation'])
        df.to_csv(self.cleaned_csv_file_path, index=False)


def main(_):
    input_path = FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [os.path.join(input_path, file) for file in ip_files]
    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    csv_name = "PRAMS.csv"
    mcf_name = "PRAMS.mcf"
    tmcf_name = "PRAMS.tmcf"
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    loader = USPrams(ip_files, cleaned_csv_path, mcf_path, tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)
