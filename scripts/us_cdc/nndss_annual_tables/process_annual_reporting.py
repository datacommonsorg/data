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
This script generates the clean csv, template and stat-var mcf files for the
NNDSS Annual tables based on Reporting Area
"""
import numpy as np
import os
import sys
import csv
import difflib
import re
import string
import datetime
import pandas as pd
from absl import app, flags, logging
from config import _PV_MAP
# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

from place_map import get_place_dcid

sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'weekly_nndss_input', './data/nndss_annual_data_all',
    'Path to the directory with weekly data scrapped from NNDSS')
flags.DEFINE_string(
    'weekly_nndss_output', './data/output',
    'Path to the directory where generated files are to be stored.')

_PREFIX = 'cdc_nndss_annual_by_reporting_area_tables'

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

#NOTE: At the moment, we are ignoring the non-integer value of reported disease incidents.
_FORMAT_UNREPORTED_CASES = {
    '-': '',
    'U': '',
    'N': '',
    'NN': '',
    'NP': '',
    'NC': '',
    'P': '',
    '\*\*': ''
}

#NOTE: A map for different
_PV_MAP = {
    'confirmed': {
        'medicalStatus': 'dcs:ConfirmedCase'
    },
    'probable': {
        'medicalStatus': 'dcs:ProbableCase'
    },
    'pediatric mortality': {
        'medicalStatus': 'dcs:PediatricMortality'
    },
    'deaths': {
        'medicalStatus': 'dcs:PatientDeceased'
    },
    'age <5': {
        'age': '[- 5 Years]'
    },
    'age < 5': {
        'age': '[- 5 Years]'
    },
    'age <5 years': {
        'age': '[- 5 Years]'
    },
    'age < 5 years': {
        'age': '[- 5 Years]'
    },
    'all serotypes': {
        'serotype': 'dcs:AllSerotypes'
    },
    'serotype b': {
        'serotype': 'dcs:SerotypeB'
    },
    'unknown serotype': {
        'serotype': 'dcs:UnknownSerotype'
    },
    'non-b serotype': {
        'serotype': 'dcs:NonSerotypeB'
    },
    'other serogroups': {
        'serogroup': 'dcs:OtherSerogroups'
    },
    'nontypeable': {
        'serogroup': 'dcs:OtherSerogroups'
    },
    'unknown serogroup': {
        'serogroup': 'dcs:UnknownSerogroups'
    },
    'all groups': {
        'serogroup': 'dcs:AllSerogroups'
    },
    'all serogroups': {
        'serogroup': 'dcs:AllSerogroups'
    },
    'serogroups acwy': {
        'serogroup': 'dcs:ACWYSerogroup'
    },
    'serogroup b': {
        'serogroup': 'dcs:SerogroupB'
    },
    'group a': {
        'serogroup': 'dcs:SerogroupA'
    },
    'perinatal infection': {
        'medicalCondition': 'dcs:PerinatalInfection'
    },
    'acute': {
        'medicalCondition': 'dcs:AcuteCondition'
    },
    'chronic': {
        'medicalCondition': 'dcs:ChronicCondition'
    },
    'imported': {
        'medicalStatus': 'dcs:ImportedCase'
    },
    'indigenous': {
        'medicalStatus': 'dcs:IndigenousCase'
    },
    'clinical': {
        'medicalStatus': 'dcs:ClinicalCase'
    },
    'neuroinvasive': {
        'medicalCondition': 'dcs:NeuroinvasiveDisease'
    },
    'non-neuroinvasive': {
        'medicalCondition': 'dcs:NonNeuroinvasiveDisease'
    },
    'congenital': {
        'medicalCondition': 'dcs:CongenitalDisease'
    },
    'non-congenital': {
        'medicalCondition': 'dcs:NonCongenitalDisease'
    },
    'drug resistant': {
        'medicalCondition': 'dcs:DrugResistantDisease'
    },
    'nondrug resistant': {
        'medicalCondition': 'dcs:NonDrugResistantDisease'
    },
    'invasive disease': {
        'medicalCondition': 'dcs:InvasiveDisease'
    },
    'post-diarrheal': {
        'medicalCondition': 'dcs:PostDiarrheal'
    }
}

#TODO: Resolve path based on the script path for tests
#TODO: Wrap this within the main function

_DISEASE_DCID_DF = pd.read_csv("./data/annual_tables_counts.csv")
print(_DISEASE_DCID_DF.head)
_DISEASE_DCID_DF = _DISEASE_DCID_DF[_DISEASE_DCID_DF['replacement'] != 'NAN']


def format_column_header(column_list):
    # for all other columns update using _DISEASE_DCID_DF
    try:
        # Log information about input data
        logging.info(f"Formatting column headers.")
        rename_map = {}

        # for some datasets the first column is poorly formatted
        rename_map[column_list[0]] = 'Reporting Area'

        for col in column_list[1:]:
            try:
                match = difflib.get_close_matches(
                    col, _DISEASE_DCID_DF['original'].astype(str),
                    cutoff=0.9)[0]
                rename_map[col] = _DISEASE_DCID_DF.loc[
                    _DISEASE_DCID_DF['original'] == match,
                    'replacement'].values[0]
            except IndexError:
                # Occurs for three columns which describe the species of the bacteria which is not captured in a statvar at the moment.
                continue
        return rename_map
    except Exception as e:
        logging.fatal(f"Error during column header formatting: {e}")


def concat_rows_with_column_headers(rows_with_col_names, df_column_list):
    try:
        logging.info(
            f"Concatenating rows with column headers.: {df_column_list}")

        # some rows have NaN as the first element, we replace it with ''
        rows_with_col_names = rows_with_col_names.fillna('')

        # works with table structure where column=0 is always the 'Reporting Area' and the the other columns are the case counts with different aggregations
        rows_with_col_names = rows_with_col_names.groupby(
            df_column_list[0])[df_column_list[1:]].agg(
                lambda d: ';'.join(d.drop_duplicates())).reset_index()

        ## some csvs do not have data and need will throw an exception when column names are flattened.
        try:
            ## flatten column names to list
            column_list = rows_with_col_names.loc[
                0, :].values.flatten().tolist()
            ## remove non-printable
            logging.info("Rows concatenated successfully.")
            return column_list
        except:
            # Dataframe does not have any data points and is pobably a note.
            return []
    except Exception as e:
        logging.fatal(f"Error during concatenation: {e}")


def process_nndss_current_weekly(input_filepath: str):
    try:
        logging.info(
            f"Reading NNDSS current weekly data from: {input_filepath}")

        ## from the csv files get the year, and week count
        filename = input_filepath.split('/')[-1]
        year = int(filename[10:14])

        df = pd.read_csv(input_filepath, header=None)

        ## fix the column names of the file - the head of the dataframe has all the rows that have the column name
        rows_with_col_names = df[(df[0] == 'Reporting Area') |
                                 (df[0] == 'Reporting  Area') |
                                 (df[0] == 'Reporting area') |
                                 (df[0] == 'Reporting  area')]
        column_list = concat_rows_with_column_headers(rows_with_col_names,
                                                      df.columns.tolist())
        # remove rows starting with 'Notes' or 'Total' or 'Notice'
        if df.shape[0] > 5:
            # some csv files have column indices as the first row, which need to be removed
            if df[0][0] == '0':
                df = df.drop([0], errors='ignore')

            # remove rows that had column names
            df = df[~df.isin(rows_with_col_names)].dropna()
            del rows_with_col_names
            # replace double spaces with a single space
            column_list = [c.replace('  ', ' ') for c in column_list]
            # update columns of the dataframe
            df.columns = column_list

            # format column names
            rename_map = format_column_header(column_list)
            df.rename(columns=rename_map, inplace=True)

            # select columns of interest i.e. current week statistics
            selected_cols = list(rename_map.values())

            # filter the dataframe to current week stat columns
            df = df[selected_cols]

            # un-pivot the dataframe to place, column, value
            df = df.melt(id_vars=['Reporting Area'],
                         value_vars=selected_cols,
                         var_name='variable',
                         value_name='value')

            # add the observation date to the dataframe
            df['observationDate'] = year

            # add the observation period based on the column names
            df['observationPeriod'] = 'P1Y'
            # convert the place names to geoIds
            df['observationAbout'] = df['Reporting Area'].apply(
                lambda x: get_place_dcid(x))

            # fix the value column based on the data notes mentioned in NNDSS
            df = df[df['value'].str.contains('\\d', regex=True)]
            logging.info("NNADS data processing completed.")
            return df
    except Exception as e:
        logging.fatal(f"Error during processing: {e}")


def make_name_str(column_components, dcid):
    try:
        logging.info(f"Creating name string for dcid: {dcid}")
        pv_str = []
        resident_status = ''
        age_pv = ''
        # collect all pvs
        for component in column_components:
            if '<' not in component:
                pv_str.append(component)
            else:
                # extract the age in years from column. Expected form is <{age}
                age_num = component.split('<')[1].split(' ')[0]
                age_pv = f', age {age_num} or less years'

        # Drop diseases from pv_str
        pv_str = ', '.join(pv_str)
        pv_str = pv_str.replace('disease', '')

        # construct the sv name
        name = "\"Count of "
        name = (name + pv_str + ' ') if len(pv_str) > 0 else name
        name = (name + 'incidents ')  #if len(disease_match) > 0 else name
        name = (name + resident_status +
                ' ') if len(resident_status) > 0 else name
        name = (name + age_pv + '\"') if len(age_pv) > 0 else (name.strip() +
                                                               '\"')
        # fix the casing in serotypes
        if 'Serotype b' in name:
            name = name.replace('Serotype b', 'Serotype B')

        if 'Non-b' in name:
            name = name.replace('Non-b', 'Non-B')

        if 'serotype' in name:
            name = name.replace('serotype', 'Serotype')

        # remove empty spaces
        name = name.replace('  ', ' ')
        name = name.replace(' , ', ', ')
        name = name.rstrip()
        return name
    except Exception as e:
        logging.error(
            f"Error creating name string for dcid: {dcid}. Error: {e}")


def generate_statvar_map_for_columns(column_list, place_list):
    try:
        logging.info(f"Generating StatVar map for columns and places.")
        sv_map = {}
        dcid_df = pd.DataFrame(
            columns=['Reporting Area', 'variable', 'variableMeasured'])
        for column in column_list:
            # initialize the statvar dict for the current column
            svdict = {}
            svdict['populationType'] = 'dcs:MedicalConditionIncident'
            svdict['typeOf'] = 'dcs:StatisticalVariable'
            svdict['statType'] = 'dcs:measuredValue'
            svdict['measuredProperty'] = 'dcs:count'

            # map to disease
            mapped_disease = _DISEASE_DCID_DF.loc[
                _DISEASE_DCID_DF['replacement'] == column, :]
            mapped_disease = mapped_disease.drop_duplicates(keep='first')

            # column names have multiple pvs which are joined with ';'
            column_components = column.split(';')

            # add pvs that are dependent on the place
            patterns_for_resident_pvs = {
                'U.S. Residents, excluding U.S. Territories': 'dcs:USResident',
                'US Residents': 'dcs:USResident',
                'Non-U.S. Residents': 'dcs:NonUSResident'
            }

            # when we have the best match i.e, only one row
            if mapped_disease.shape[0] >= 1:
                incidentType = 'dcs:' + str(mapped_disease['dcid'].values[0])
                disease = str(mapped_disease['diseases'].values[0])
                disease = '_'.join([e.title() for e in disease.split()])
                disease = disease.replace(',', '_')
                svdict['medicalCondition'] = incidentType

                # we need to add other non-disease pvs to the statvar
                for component in column_components:
                    if 'Current' not in component:
                        if component.lower() in _PV_MAP.keys():
                            pv_dict = _PV_MAP[component.lower()]
                            # if property exists, append the value to existing property, separated by a comma
                            for p, v in pv_dict.items():
                                if p in svdict.keys():
                                    svdict[p] = svdict[p] + "__" + v[4:]
                                else:
                                    svdict[p] = v

                # check if residentStatus property is applicable
                resident_status = ''
                for place in place_list:
                    resident_status_place = [
                        substr
                        for substr in list(patterns_for_resident_pvs.keys())
                        if substr in place
                    ]

                    if len(resident_status_place) > 0:
                        resident_status = patterns_for_resident_pvs[
                            resident_status_place[0]]

                    # add residentStatus pv to the svdict
                    if resident_status:
                        # add residentStatus pv to dict
                        svdict_tmp = svdict.copy()
                        svdict_tmp['residentStatus'] = resident_status
                        # get name and dcid
                        dcid = get_statvar_dcid(svdict_tmp)
                        # remove logical OR from dcid
                        dcid = dcid.replace('Or', '_')
                        # remove AllSerotypes and AllSerogroups from dcid
                        dcid = dcid.replace('_AllSerogroups', '')
                        dcid = dcid.replace('_AllSerotypes', '')

                        svdict_tmp['name'] = make_name_str(
                            column_components, dcid)
                        # add to column_map
                        key = 'Node: dcid:' + dcid
                        if key not in sv_map.keys():
                            sv_map[key] = svdict_tmp
                        dcid_df = dcid_df._append(
                            {
                                'Reporting Area': place,
                                'variable': column,
                                'variableMeasured': dcid
                            },
                            ignore_index=True)

                    else:
                        # get name and dcid
                        svdict_tmp = svdict.copy()
                        dcid = get_statvar_dcid(svdict_tmp)
                        # remove the logical Or from dcid
                        dcid = dcid.replace('Or', '_')
                        # remove AllSerotypes and AllSerogroups from dcid
                        dcid = dcid.replace('_AllSerogroups', '')
                        dcid = dcid.replace('_AllSerotypes', '')

                        svdict_tmp['name'] = make_name_str(
                            column_components, dcid)
                        # add to column_map
                        key = 'Node: dcid:' + dcid
                        if key not in sv_map.keys():
                            sv_map[key] = svdict_tmp
                        # print("type-----------",type(dcid_df))
                        dcid_df = dcid_df._append(
                            {
                                'Reporting Area': place,
                                'variable': column,
                                'variableMeasured': dcid
                            },
                            ignore_index=True)
        logging.info("StatVar map generation completed.")
        return sv_map, dcid_df

    except Exception as e:
        logging.fatal(f"Error in generate statvar map. {e}")


def generate_processed_csv(input_path):
    try:
        logging.info(f"Reading input file: {input_path}")
        processed_dataframe_list = []
        #TODO: Parallelize this step
        # for all files in the data directory process the files and append to a common dataframe
        file_list = [
            f for f in sorted(os.listdir(input_path)) if 'table_2' in f
        ]
        for filename in file_list:
            file_inputpath = os.path.join(input_path, filename)
            df = process_nndss_current_weekly(file_inputpath)
            processed_dataframe_list.append(df)

        # concat list of all processed data frames
        cleaned_dataframe = pd.concat(processed_dataframe_list,
                                      ignore_index=False)
        del processed_dataframe_list

        # set measurement method
        cleaned_dataframe[
            'measurementMethod'] = 'dcs:CDC_NNDSS_Diseases_AnnualTables'

        cleaned_dataframe['observationAbout'].replace('', np.nan, inplace=True)
        cleaned_dataframe['value'].replace('', np.nan, inplace=True)
        cleaned_dataframe.dropna(subset=['value', 'observationAbout'],
                                 inplace=True)

        cleaned_dataframe['value'] = cleaned_dataframe['value'].str.replace(
            ',', '')
        cleaned_dataframe['value'] = cleaned_dataframe['value'].astype(float)
        logging.info(f"Processing completed")
        return cleaned_dataframe
    except Exception as e:
        logging.fatal(f"An unexpected error occurred during processing: {e}")


def main(_) -> None:
    logging.info("Process annual reporting started")
    input_path = FLAGS.weekly_nndss_input
    output_path = FLAGS.weekly_nndss_output

    cleaned_dataframe = generate_processed_csv(input_path)

    # for each unique column generate the statvar with constraints
    unique_columns = cleaned_dataframe['variable'].unique().tolist()
    unique_places = cleaned_dataframe['Reporting Area'].unique().tolist()

    # column - statvar dictionary map
    sv_map, dcid_df = generate_statvar_map_for_columns(unique_columns,
                                                       unique_places)

    # map the statvars to column names
    cleaned_dataframe = pd.merge(cleaned_dataframe,
                                 dcid_df,
                                 on=['Reporting Area', 'variable'],
                                 how='left')

    #TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate

    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # write outputs to file
    f = open(os.path.join(output_path, f'{_PREFIX}.tmcf'), 'w')
    f.write(_TEMPLATE_MCF)
    f.close()

    # write statvar mcf file from col_map
    f = open(os.path.join(output_path, f'{_PREFIX}.mcf'), 'w')

    for dcid, pvdict in sv_map.items():
        f.write(dcid + '\n')
        for p, v in pvdict.items():
            if v == 'dcs:AllSerotypes' or v == 'dcs:AllSerogroups':
                f.write('#' + p + ": " + v + "\n")
            else:
                f.write(p + ": " + v + "\n")
        f.write("\n")
    f.close()

    # write csv
    cleaned_dataframe = cleaned_dataframe[[
        'observationAbout', 'observationDate', 'variableMeasured',
        'measurementMethod', 'value', 'observationPeriod', 'variable'
    ]]
    cleaned_dataframe.to_csv(os.path.join(output_path, f'{_PREFIX}.csv'),
                             index=False)


if __name__ == '__main__':
    app.run(main)
