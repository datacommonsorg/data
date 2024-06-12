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
"""Change the description
This script generates the import artefacts for the prevalence of asthma in adults and children at a county-level in the United States.

The dataset is extracted from the Interactive Maps of States and District of Columbia Visualizing Six-Level Urban-Rural Classification of
Counties and County-Equivalents with Corresponding Current Asthma Prevalence, 2016–2018 report.
"""
import re
import os
import sys
import difflib
import string
import pandas as pd
from absl import app, flags

from .config import _PV_MAP


# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

_DISEASE_DCID_DF = pd.read_csv('./data/annual_tables_disease_mapping.csv')
FLAGS = flags.FLAGS

#TODO: Some of the functions defined here can be used while processing the annual tables and hence making the common functions as a module is preferred.

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

def rename_columns(df_column_list):
    for idx in range(len(df_column_list)):
        if df_column_list[idx] == 'Disease;Disease':
            df_column_list[idx] = 'Disease'
        else:
            column = df_column_list[idx]
            if ';No.' in column:
                df_column_list[idx] = column.replace(';No.', '')

            if 'No.;' in column:
                df_column_list[idx] = column.replace('No.;', '')

    return df_column_list


def make_name_str(column_components, disease_match, dcid):
    pv_str = []
    age_pv = ''
    # collect all pvs
    for component in column_components:
        if component != disease_match:
            if '<' not in component or '≥65 yrs' not in component:
                pv_str.append(component)
            elif '≥65 yrs' in component:
                age_pv = f', age 65 or more years'
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
    name = (name + disease_match +
            ' incidents ') if len(disease_match) > 0 else name
    name = (name + age_pv + '\"') if len(age_pv) > 0 else (name.strip() + '\"')

    # fix the casing in serotypes
    if 'Serotype b' in name:
        name = name.replace('Serotype b', 'Serotype B')

    if 'Non-b' in name:
        name = name.replace('Non-b', 'Non-B')

    if 'serotype' in name:
        name = name.replace('serotype', 'Serotype')

    # drop all ages, all serotypes, all serogroups
    name = name.replace('All serogroups', '')
    name = name.replace('All serotypes', '')
    name = name.replace('All ages', '')
    name = name.replace('all Serotypes', '')
    name = name.replace('all Serogroups', '')
    name = name.replace('≥65 yrs', '65 or more years')

    # remove empty spaces
    name = name.replace('  ', ' ')
    name = name.replace(' , ', ', ')
    name = name.rstrip()
    return name


def map_pvs_from_column_name(row):
    row['sv_dcid'] = ''
    row['sv_dict'] = {}
    if row['ignore_label'] == 'X':
        return row

    sv_dict = {}
    # initialize the base dict
    sv_dict['Node'] = ''
    sv_dict['populationType'] = 'dcs:MedicalConditionIncident'
    sv_dict['typeOf'] = 'dcs:StatisticalVariable'
    sv_dict['statType'] = 'dcs:measuredValue'
    sv_dict['measuredProperty'] = 'dcs:count'
    # add other pvs
    column_components = row['variable'].split(';')
    for component in column_components:
        if component.lower() in _PV_MAP.keys():
            pv_dict = _PV_MAP[component.lower()]
            for p, v in pv_dict.items():
                #if property exists, concat the value with __
                if p in sv_dict.keys():
                    sv_dict[p] = sv_dict[p] + "__" + v[4:]
                else:
                    sv_dict[p] = v

    # add the medical condition
    if 'medicalCondition' in sv_dict.keys():
        sv_dict['medicalCondition'] = sv_dict['medicalCondition'] + "__" + row[
            'dcid']
    else:
        sv_dict['medicalCondition'] = 'dcs:' + row['dcid']

    # generate the name and dcid for the sv_dict
    dcid = get_statvar_dcid(sv_dict, ignore_props=['Node'])
    # remove Or from the dcid
    dcid = dcid.replace('Or', '_')
    # remove AllSerogroups and AllSerotypes from the dcid
    dcid = dcid.replace('_AllSerogroups', '')
    dcid = dcid.replace('_AllSerotypes', '')
    # update the Node key of the dict with the statvar dcid
    sv_dict['Node'] = 'dcid:' + dcid
    # generate the name for the statvar
    sv_dict['name'] = make_name_str(column_components, row['name'], dcid)

    # update the dcid_pv_map
    row['sv_dcid'] = 'dcs:' + dcid
    row['sv_dict'] = sv_dict
    return row


def clean_single_dataframe(df, year, table):

    # flatten multi-indexed columns
    df.columns = df.columns.to_flat_index().str.join(';')

    # get columns of interest
    column_list = [
        column for column in df.columns.tolist()
        if ((('No.' in column) and
             ('Total' not in column)) or ('Disease' in column))
    ]
    df = df[column_list]

    del column_list
    # fix the name of the columns
    df.columns = rename_columns(df.columns.tolist())

    # handle the empty values
    df = df.fillna('')

    diseases_map = _DISEASE_DCID_DF[(_DISEASE_DCID_DF['table'] == int(table)) &
                                    (_DISEASE_DCID_DF['year'] == int(year))]
    for col in df.columns.tolist():
        diseases_map[col] = df[col].values.tolist()
    del df

    diseases_map = diseases_map.melt(
        id_vars=diseases_map.columns.tolist()[:7],
        value_vars=diseases_map.columns.tolist()[7:],
        ignore_index=True)

    # add additional columns to resolve the disease name and dcid
    diseases_map = diseases_map.drop_duplicates(keep='first')
    diseases_map = diseases_map[diseases_map['Replacement'] != 'NAN']
    diseases_map = diseases_map.dropna(subset=['name', 'dcid'])
    diseases_map['variable'] = diseases_map['Replacement'] + ';' + diseases_map[
        'variable']
    diseases_map = diseases_map.drop(
        columns=['Disease', 'sameAs', 'table', 'Replacement'])

    # fix the value column based on the data notes mentioned in NNDSS
    diseases_map = diseases_map[diseases_map['value'].str.contains('\\d',
                                                                   regex=True)]

    diseases_map.rename(columns={'year': 'observationDate'}, inplace=True)
    diseases_map['observationAbout'] = 'country/USA'
    diseases_map['observationPeriod'] = 'P1Y'
    diseases_map['measurementMethod'] = 'dcs:CDC_NNDSS_Diseases_AnnualTables'

    if table == '4':

        diseases_map['ignore_label'] = diseases_map['variable'].apply(
            lambda e: 'X' if 'Age <5 years' in e else '')
    else:

        diseases_map['ignore_label'] = ''

    sv_df = diseases_map[['variable', 'name', 'dcid']]
    diseases_map = diseases_map[[
        col for col in diseases_map.columns.tolist()
        if col not in ['name', 'dcid']
    ]]
    sv_df = sv_df.drop_duplicates(keep='first')
    return diseases_map, sv_df


def process_table_4(file_list):
    """
    TABLE 4. Annual reported cases of notifiable diseases and rates, by age group, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table4_list = [s for s in os.listdir(file_list) if "table_4" in s]
    clean_dataframe = pd.DataFrame()
    full_sv_df = pd.DataFrame()
    for filename in table4_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]

        df = pd.read_csv(input_filepath, header=[0, 1])
        df, sv_df = clean_single_dataframe(df, year, '4')

        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
        full_sv_df = pd.concat([full_sv_df, sv_df], ignore_index=True)
    return clean_dataframe, full_sv_df


def process_table_5(file_list):
    """
    TABLE 5. Annual reported cases of notifiable diseases and rates, by sex, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table5_list = [s for s in os.listdir(file_list) if "table_5" in s]
    clean_dataframe = pd.DataFrame()
    full_sv_df = pd.DataFrame()
    for filename in table5_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]

        df = pd.read_csv(input_filepath, header=[0, 1])
        df, sv_df = clean_single_dataframe(df, year, '5')
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
        full_sv_df = pd.concat([full_sv_df, sv_df], ignore_index=True)
    return clean_dataframe, full_sv_df


def process_table_6(file_list):
    """
    TABLE 6. Annual reported cases of notifiable diseases and rates, by race*,†, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table6_list = [s for s in os.listdir(file_list) if "table_6" in s]
    clean_dataframe = pd.DataFrame()
    full_sv_df = pd.DataFrame()
    for filename in table6_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]

        df = pd.read_csv(input_filepath, header=[0, 1])
        df, sv_df = clean_single_dataframe(df, year, '6')
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
        full_sv_df = pd.concat([full_sv_df, sv_df], ignore_index=True)
    return clean_dataframe, full_sv_df


def process_table_7(file_list):
    """
    TABLE 7. Annual reported cases of notifiable diseases and rates, by ethnicity*, United States, excluding U.S. Territories and Non-U.S. Residents
    """
    table7_list = [s for s in os.listdir(file_list) if "table_7" in s]
    clean_dataframe = pd.DataFrame()
    full_sv_df = pd.DataFrame()
    for filename in table7_list:
        input_filepath = os.path.join(file_list, filename)
        year = filename.split('_')[2]

        df = pd.read_csv(input_filepath, header=[0, 1])
        df, sv_df = clean_single_dataframe(df, year, '7')
        # add processed dataframe to the clean_csv
        clean_dataframe = pd.concat([clean_dataframe, df], ignore_index=True)
        full_sv_df = pd.concat([full_sv_df, sv_df], ignore_index=True)
    return clean_dataframe, full_sv_df


def generate_statvars(full_sv_df):
    full_sv_df = full_sv_df.apply(map_pvs_from_column_name,
                                  axis=1,
                                  result_type='expand')
    return full_sv_df


def write_svdicts_to_file(dict_list, file_path):
    unique_dict = [dict(tup) for tup in {tuple(d.items()) for d in dict_list}]
    f = open(file_path, "w")
    for udict in unique_dict:
        for p, v in udict.items():
            if v == 'dcs:AllSerotypes' or v == 'dcs:AllSerogroups':
                f.write('#' + p + ": " + v + "\n")
            else:
                f.write(p + ": " + v + "\n")
        f.write('\n')
    f.close()


def main(_) -> None:
    flags.DEFINE_string(
        'input_path', './data/nndss_annual_data_all',
        'Path to the directory with weekly data scrapped from NNDSS')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')

    file_list = FLAGS.input_path
    output_path = FLAGS.output_path

    # process each table and clean the dataset
    sv4, tab4 = process_table_4(file_list)
    sv5, tab5 = process_table_5(file_list)
    sv6, tab6 = process_table_6(file_list)
    sv7, tab7 = process_table_7(file_list)
    tab5.to_csv('table_5.csv', index=False)
    # make a single dataframe of cleaned data and statvar pvs
    cleaned_dataframe = pd.concat([tab4, tab5, tab6, tab7], ignore_index=True)
    full_sv_df = pd.concat([sv4, sv5, sv6, sv7], ignore_index=True)
    full_sv_df = full_sv_df.drop_duplicates(keep='first')
    del tab4, tab5, tab6, tab7, sv4, sv5, sv6, sv7
    # associate the disease name and dcid to clean_dataframe
    cleaned_dataframe = pd.merge(cleaned_dataframe,
                                 full_sv_df,
                                 on='variable',
                                 how='left')
    del full_sv_df
    # statvar dataframe with all constraints
    full_sv_df = cleaned_dataframe[['ignore_label', 'variable', 'name', 'dcid']]
    full_sv_df = full_sv_df.drop_duplicates(keep='first')
    # generate statvars from full_sv_df
    full_sv_df = generate_statvars(full_sv_df)
    # merge statvar dcid with full df
    cleaned_dataframe = pd.merge(
        cleaned_dataframe,
        full_sv_df,
        on=['ignore_label', 'variable', 'name', 'dcid'],
        how='left')
    # filter rows that have a defined statvar dcid
    cleaned_dataframe = cleaned_dataframe[cleaned_dataframe['sv_dcid'] != '']
    obs_df = cleaned_dataframe[[
        'observationAbout', 'observationDate', 'sv_dcid', 'measurementMethod',
        'value', 'observationPeriod', 'variable'
    ]]
    obs_df.rename(columns={'sv_dcid': 'variableMeasured'}, inplace=True)
    # setup the output directory
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_prefix = 'cdc_nndss_annual_by_demographics'
    # write statvar_dct to mcf file
    sv_dict_list = cleaned_dataframe['sv_dict'].values.tolist()
    mcf_file_path = os.path.join(output_path, f'{file_prefix}.mcf')
    write_svdicts_to_file(sv_dict_list, mcf_file_path)

    # write outputs to file
    f = open(os.path.join(output_path, f'{file_prefix}.tmcf'), 'w')
    f.write(_TEMPLATE_MCF)
    f.close()

    # TODO: Write to csv + tmcf + sv mcf (can be global)
    obs_df.to_csv(os.path.join(output_path, f'{file_prefix}.csv'), index=False)


if __name__ == '__main__':
    app.run(main)
