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
#
"""Processing script for data downloaded from the NORS dashboard"""
import os
import sys
import json
import pandas as pd
from absl import app, flags, logging
from sodapy import Socrata
import requests

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for util modules
from statvar_dcid_generator import get_statvar_dcid
from state_division_to_dcid import get_place_dcid

FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

_MMETHOD = 'NORSNonInfectiousDisease'
_FILE_PREFIX = 'NORS_NonInfectious_Disease'

_STAT_COLS = ['Illnesses', 'Hospitalizations', 'Deaths']

_SV_BASE_MAP = {
    "Illnesses": {
        "Node": "",
        "populationType": "dcs:MedicalConditionIncident",
        "typeOf": "dcs:StatisticalVariable",
        "statType": "dcs:measuredValue",
        "measuredProperty": "dcs:count"
    },
    "Hospitalizations": {
        "Node": "",
        "populationType": "dcs:MedicalConditionIncident",
        "typeOf": "dcs:StatisticalVariable",
        "statType": "dcs:measuredValue",
        "medicalStatus": "PatientHospitalized",
        "measuredProperty": "dcs:count"
    },
    "Deaths": {
        "Node": "",
        "populationType": "dcs:MedicalConditionIncident",
        "typeOf": "dcs:StatisticalVariable",
        "statType": "dcs:measuredValue",
        "medicalStatus": "PatientDeceased",
        "measuredProperty": "dcs:count"
    }
}
dataset_id = "5xkq-dg7x"
domain = "data.cdc.gov"
client = Socrata(domain, None)
filename = "NationalOutbreakPublicDataTool.xlsx"
sheet_name = "Outbreak Data"
base_path = "./data"
schema_map_path = f"{base_path}/col_map_exc_food.json"
input_directory = f"{base_path}/input_files"
output_directory = f"{base_path}/output"
sheet_name = "Outbreak Data"
os.makedirs(input_directory, exist_ok=True)
os.makedirs(output_directory, exist_ok=True)
input_path = os.path.join(input_directory, filename)


def download_data_from_api(column_mapping=None):
    try:
        logging.info('Downloading starts')
        # Get the total number of records dynamically
        count_url = f"https://{domain}/resource/{dataset_id}.json?$select=count(*)"
        count_response = requests.get(count_url)

        if count_response.status_code == 200:
            total_records_data = count_response.json()
            if total_records_data and isinstance(
                    total_records_data,
                    list) and len(total_records_data
                                 ) > 0 and "count" in total_records_data[0]:
                total_records = int(total_records_data[0]["count"])
                logging.info(f"Total records available: {total_records}")
            else:
                logging.error(
                    "Could not retrieve the total number of records from the API."
                )
                return
        else:
            logging.fatal(
                f"Error fetching total record count: Received status code {count_response.status_code}"
            )
            return

        limit = 10000  # Set a reasonable limit for each request
        offset = 0
        all_data = []

        while offset < total_records:
            logging.info(f"Downloading records {offset} to {offset + limit}")
            results = client.get(dataset_id, limit=limit, offset=offset)
            if not results:
                logging.info("No more data available.")
                break
            all_data.extend(results)
            offset += limit
            logging.info(f"Retrieved {len(all_data)} rows so far...")

        results_df = pd.DataFrame.from_records(all_data)

        # Rename columns if column_mapping is provided
        if column_mapping:
            results_df = results_df.rename(columns=column_mapping)
        with pd.ExcelWriter(input_path,
                            engine='openpyxl') as writer:  # Requires openpyxl
            results_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logging.info(f"Data saved to {input_path}, sheet '{sheet_name}'")

    except Exception as e:
        logging.fatal(f"Error while downloading : {e}")


def fix_date_format(df: pd.DataFrame) -> pd.DataFrame:
    # Combine year, month columns to observationDate in YYYY-MM format
    try:
        logging.info(
            f'Combine year, month columns to observationDate in YYYY-MM format:'
        )
        df['Year'] = df['Year'].astype(str)
        df['Month'] = df['Month'].astype(str)
        df['Month'] = df['Month'].str.zfill(2)
        df['observationDate'] = df['Year'] + '-' + df['Month']
        df.drop(columns=['Year', 'Month'], inplace=True)
        return df
    except Exception as e:
        logging.error(f"Error while generating observationDate : {e}")


def generate_aggregates(df: pd.DataFrame,
                        groupby_cols: list = None) -> pd.DataFrame:
    # do not aggregate country-level stats
    """Generates aggregates from a DataFrame.

    Args:
        df: The input DataFrame.
        groupby_cols: A list of columns to group by. If None, aggregates are calculated for the entire DataFrame.

    Returns:
        A DataFrame containing the aggregates.
    """
    try:
        logging.info(f"Generating aggregates grouped by: {groupby_cols}")
        country_stat_df = df[df['observationAbout'].str.contains('country')]
        cols = groupby_cols + _STAT_COLS
        country_stat_df = country_stat_df[cols]
        country_stat_df = country_stat_df.groupby(groupby_cols,
                                                  as_index=False).agg({
                                                      'Illnesses': sum,
                                                      'Hospitalizations': sum,
                                                      'Deaths': sum
                                                  })

        # aggreagte stats for US states and territories
        aggregate_df = df[~(df['observationAbout'].str.contains('country'))]
        aggregate_df = aggregate_df.groupby(groupby_cols, as_index=False).agg({
            'Illnesses': sum,
            'Hospitalizations': sum,
            'Deaths': sum
        })

        # aggregate for US at country level
        country_group_by = [
            cols for cols in groupby_cols if cols != 'observationAbout'
        ]
        us_aggreagte_df = aggregate_df.groupby(country_group_by,
                                               as_index=False).agg({
                                                   'Illnesses': sum,
                                                   'Hospitalizations': sum,
                                                   'Deaths': sum
                                               })
        us_aggreagte_df['observationAbout'] = 'country/USA'

        # merge all aggregations
        aggregate_df = pd.concat(
            [aggregate_df, us_aggreagte_df, country_stat_df], ignore_index=True)
        # transform the dataframe to date, place, variable, value format
        aggregate_df = aggregate_df.melt(id_vars=groupby_cols,
                                         value_vars=_STAT_COLS)
        # add additional columns
        aggregate_df['observationPeriod'] = 'P1Y'
        aggregate_df['measurementMethod'] = f'dcAggregate/{_MMETHOD}'
        logging.info("Aggregates generated successfully.")
        return aggregate_df
    except Exception as e:
        logging.fatal(f"An error occurred during aggregate generation: {e}")


def make_stat_vars(row, PV_MAP):
    """Creates statistical variables based on the given row and PV_MAP.
    Args:
        row (pandas.Series): A row of data.
        PV_MAP (dict): A dictionary mapping variable names to possible values.

    Returns:
        dict: A dictionary of statistical variables.
    """
    try:
        logging.info(f"Generating Statvars.")
        row['variableMeasured'] = ''
        row['sv_dict'] = {}
        sv_dict = _SV_BASE_MAP[row['variable']].copy()

        # Add transmission mode
        if pd.notna(row['Primary Mode']) and row['Primary Mode'] != '':
            sv_dict.update(PV_MAP['Primary Mode'][row['Primary Mode']])
        #NOTE: Current import focuses on rows with only 1 Etiology
        if pd.notna(row['Etiology']) and row['Etiology'] != '':
            etiology_list = row['Etiology'].split(';')
            if len(etiology_list) == 1:
                for etiology in etiology_list:
                    if 'etiology' not in sv_dict.keys():
                        sv_dict.update(PV_MAP['Etiology'][etiology])
                    sv_dict['etiology'] = PV_MAP['Etiology'][etiology][
                        'etiology']

                if pd.notna(row['Etiology Status']):
                    etiology_status_list = row['Etiology Status'].split(';')
                    assert len(etiology_status_list) == len(
                        etiology_list
                    ), "Etiology and Etiology Status have varying length, please check."
                    for status in etiology_status_list:

                        if 'medicalStatus' not in sv_dict.keys():
                            sv_dict.update(PV_MAP['Etiology Status'][status])
                        else:
                            sv_dict['medicalStatus'] = sv_dict[
                                'medicalStatus'] + '__' + PV_MAP[
                                    'Etiology Status'][status]['medicalStatus']
        dcid = get_statvar_dcid(sv_dict, ignore_props=['Node'])
        dcid = dcid.replace(' ', '')
        dcid = dcid.replace('Or', '_')
        dcid = dcid.replace('-', '_')

        # update the Node key of the dict with the statvar dcid
        sv_dict['Node'] = 'dcid:' + dcid
        # prefix namespace
        sv_dict['transmissionMode'] = 'dcs:' + sv_dict['transmissionMode']
        try:
            sv_dict['etiology'] = 'dcs:' + sv_dict['etiology']
        except KeyError:
            pass  # Etiology is not part of the statvar dict
        try:
            sv_dict['medicalStatus'] = 'dcs:' + sv_dict['medicalStatus']
        except KeyError:
            pass  # Etiology Status is not found in the statvar dict

        # # update the dcid_pv_map
        row['variableMeasured'] = 'dcs:' + dcid
        row['sv_dict'] = sv_dict
        return row
    except Exception as e:
        logging.fatal(f"An error occurred, while generating statvar: {e}")


def write_svdicts_to_file(dict_list, file_path):
    """Writes a list of dictionaries to a file, one dictionary per line.

    Args:
        dict_list (list): A list of dictionaries, where each dictionary 
                           represents a set of statistical variables.
        file_path (str): The path to the file where the dictionaries will be written.
    """
    try:
        logging.info(f"writing svs in a file .. ")
        unique_dict = [
            dict(tup) for tup in {tuple(d.items()) for d in dict_list}
        ]
        f = open(file_path, "w")
        for udict in unique_dict:
            for p, v in udict.items():
                f.write(p + ": " + v + "\n")
            f.write('\n')
        f.close()

    except Exception as e:
        logging.fatal(f"An error occurred, while writing to file . : {e}")


def fix_place_names(clean_df):
    """Standardizes place names in DataFrame's 'place' column.

    Args:
        clean_df (pd.DataFrame): DataFrame with 'place' column.

    Returns:
        pd.DataFrame: DataFrame with standardized place names.
    """
    try:
        logging.info(f"Fixing place name. ")
        clean_df['observationAbout'] = clean_df['State'].apply(get_place_dcid)
        clean_df = clean_df[~(clean_df['observationAbout']
                              == '')]  # remove MultiState
        clean_df.drop(columns=['State'], inplace=True)
        return clean_df
    except Exception as e:
        logging.error(f"Error while fixing place name : {e}")


def process_non_infectious_data() -> None:
    try:
        logging.info(f"Processing starts.")
        f = open(schema_map_path, 'r')
        PV_MAP = json.load(f)
        f.close()
        df = pd.read_excel(input_path, sheet_name=sheet_name)
        # The dataset is sparse and hence, all null or empty values are replaced with empty string for easier processing and data manipulation
        df = df[~df.isna()]
        # fix the date format and resolve the place to dcids
        df = fix_date_format(df)
        df = fix_place_names(df)

        # make high-level statistics
        trans_mode_df = generate_aggregates(df,
                                            groupby_cols=[
                                                'observationDate',
                                                'observationAbout',
                                                'Primary Mode'
                                            ])
        trans_mode_df = trans_mode_df.drop_duplicates(subset=[
            'observationDate', 'observationAbout', 'Primary Mode', 'variable'
        ],
                                                      keep='last')
        trans_mode_df['agg_by'] = 'Transmission Mode'

        etiology_df = generate_aggregates(df,
                                          groupby_cols=[
                                              'observationDate',
                                              'observationAbout',
                                              'Primary Mode', 'Etiology'
                                          ])
        etiology_df['agg_by'] = 'Etiology'
        etiology_status_df = generate_aggregates(df,
                                                 groupby_cols=[
                                                     'observationDate',
                                                     'observationAbout',
                                                     'Primary Mode', 'Etiology',
                                                     'Etiology Status'
                                                 ])
        etiology_status_df['agg_by'] = 'Etiology Status'

        clean_df = pd.concat([trans_mode_df, etiology_df, etiology_status_df],
                             join='outer',
                             ignore_index=True)
        clean_df = clean_df[[
            'observationDate', 'observationPeriod', 'measurementMethod',
            'observationAbout', 'value', 'variable', 'Primary Mode', 'Etiology',
            'Etiology Status', 'agg_by'
        ]]
        sv_df = clean_df[[
            'variable', 'Primary Mode', 'Etiology', 'Etiology Status'
        ]]
        sv_df = sv_df.drop_duplicates()
        sv_df = sv_df.apply(make_stat_vars, args=(PV_MAP,), axis=1)

        # write statvar_dct to mcf file
        sv_dict_list = sv_df['sv_dict'].values.tolist()
        mcf_file_path = os.path.join(output_directory, f'{_FILE_PREFIX}.mcf')
        write_svdicts_to_file(sv_dict_list, mcf_file_path)

        sv_df = sv_df[[
            "variable", "Primary Mode", "Etiology", "Etiology Status",
            "variableMeasured"
        ]]

        # prepare the final clean csv
        clean_df = pd.merge(
            clean_df,
            sv_df,
            left_on=['variable', 'Primary Mode', 'Etiology', 'Etiology Status'],
            right_on=[
                'variable', 'Primary Mode', 'Etiology', 'Etiology Status'
            ],
            how='left')

        # empty strings for  null etiology and etiology status values
        clean_df = clean_df.fillna('')
        clean_df = clean_df[(clean_df['value'] != '') |
                            (clean_df['observationAbout'] != '')]
        # another check to ensure there is only 1 Etiology in the clean_csv
        clean_df = clean_df[~(clean_df['Etiology'].str.contains(';'))]
        # removing unused columns
        clean_df.drop(
            columns=['variable', 'Primary Mode', 'Etiology', 'Etiology Status'],
            inplace=True)
        clean_df.to_csv(f'{output_directory}/{_FILE_PREFIX}.csv', index=False)

        f = open(f"{output_directory}/{_FILE_PREFIX}.tmcf", "w")
        f.write(_TEMPLATE_MCF)
        f.close()
    except Exception as e:
        logging.fatal(f"Error while processing : {e}")


def main(_) -> None:
    mode = FLAGS.mode
    column_mapping = {
        "year": "Year",
        "month": "Month",
        "state": "State",
        "primary_mode": "Primary Mode",
        "etiology": "Etiology",
        "serotype_or_genotype": "Serotype or Genotype",
        "etiology_status": "Etiology Status",
        "setting": "Setting",
        "illnesses": "Illnesses",
        "hospitalizations": "Hospitalizations",
        "info_on_hospitalizations": "Info On Hospitalizations",
        "deaths": "Deaths",
        "info_on_deaths": "Info On Deaths",
        "food_vehicle": "Food Vehicle",
        "food_contaminated_ingredient": "Food Contaminated Ingredient",
        "ifsac_category": "IFSAC Category",
        "water_exposure": "Water Exposure",
        "water_type": "Water Type",
        "animal_type": "Animal Type"
    }
    if mode == "" or mode == "download":
        download_data_from_api(column_mapping=column_mapping)
    if mode == "" or mode == "process":
        process_non_infectious_data()


if __name__ == '__main__':
    app.run(main)
