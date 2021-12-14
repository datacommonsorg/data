# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script to process FBI Hate Crime table 1 publications."""
import os
import sys
import tempfile
import csv
import json
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

YEAR_INDEX = 0

# Columns in final cleaned CSV
OUTPUT_COLUMNS = ['Year', 'StatVar', 'Quantity']

# A config that maps the year to corresponding xls file with args to be used
# with pandas.read_excel()
YEARWISE_CONFIG = {
    '2020': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2020.xlsx',
        'args': {
            'header': 4,
            'skipfooter': 3
        }
    },
    '2019': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2019.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2018': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2018.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2017': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2017.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2016': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2016.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2015': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2015.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2014': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2014.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2013': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2013.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2012': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2012.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2011': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2011.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2010': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2010.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2009': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2009.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2008': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2008.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2007': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2007.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2006': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2006.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2005': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2005.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    },
    '2004': {
        'type': 'xls',
        'path': '../source_data/table1_xls/2004.xls',
        'args': {
            'header': 2,
            'skipfooter': 3
        }
    }
}


def _create_csv_mcf(csv_files: list, cleaned_csv_path: str,
                    config: dict) -> list:
    """Creates StatVars according to values in csv_files and write the final
    output to a csv.

    Args:
        csv_files: A list of CSV file paths to process.
        cleaned_csv_path: Path of the final cleaned CSV file.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/table1/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    with open(cleaned_csv_path, 'w') as output_f:
        writer = csv.DictWriter(output_f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, 'r') as input_f:
                reader = csv.DictReader(input_f)
                statvars_list = _write_output_csv(reader, writer, config)
                statvars.extend(statvars_list)
    return statvars


def _update_statvars(statvar_list: list, key_value: dict):
    """Given a list of statvars and a key:value pair, this functions adds the
    key value pair to each statvar.
    """
    for d in statvar_list:
        d.update(key_value)


def _update_statvar_dcids(statvar_list: list, config: dict):
    """Given a list of statvars, generates the dcid for each statvar after
    accounting for dependent PVs.
    """
    for d in statvar_list:
        ignore_props = _get_dpv(d, config)
        dcid = get_statvar_dcid(d, ignore_props=ignore_props)
        d['Node'] = dcid


def _write_row(year: int, statvar_dcid: str, quantity: str,
               writer: csv.DictWriter):
    """A wrapper to write data to the cleaned CSV."""
    processed_dict = {
        'Year': year,
        'StatVar': statvar_dcid,
        'Quantity': quantity
    }
    writer.writerow(processed_dict)


def _get_dpv(statvar: dict, config: dict) -> list:
    """A function that goes through the statvar dict and the config and returns
    a list of properties to ignore when generating the dcid.

    Args:
        statvar: A dictionary of prop:values of the statvar
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/config.json for
          an example. The 'dpv' key is used to identify dependent properties.

    Returns:
        A list of properties to ignore when generating the dcid
    """
    ignore_props = []
    for spec in config['dpv']:
        if spec['cprop'] in statvar:
            dpv_prop = spec['dpv']['prop']
            dpv_val = spec['dpv']['val']
            if dpv_val == statvar.get(dpv_prop, None):
                ignore_props.append(dpv_prop)
    return ignore_props


def _write_output_csv(reader: csv.DictReader, writer: csv.DictWriter,
                      config: dict) -> list:
    """Reads each row of a CSV and creates statvars for counts of
    Incidents, Offenses, Victims and Known Offenders with different bias
    motivations.

    Args:
        reader: CSV dict reader.
        writer: CSV dict writer of final cleaned CSV.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    for crime in reader:
        incident_statvar = {**config['populationType']['Incidents']}
        offense_statvar = {**config['populationType']['Offenses']}
        victim_statvar = {**config['populationType']['Victims']}
        offender_statvar = {**config['populationType']['KnownOffender']}

        statvar_list = [
            incident_statvar, offense_statvar, victim_statvar, offender_statvar
        ]
        bias_motivation = crime['bias motivation']
        bias_key_value = config['pvs'][bias_motivation]
        _update_statvars(statvar_list, bias_key_value)
        _update_statvar_dcids(statvar_list, config)

        _write_row(crime['Year'], incident_statvar['Node'], crime['incidents'],
                   writer)
        _write_row(crime['Year'], offense_statvar['Node'], crime['offenses'],
                   writer)
        _write_row(crime['Year'], victim_statvar['Node'], crime['victims'],
                   writer)
        _write_row(crime['Year'], offender_statvar['Node'],
                   crime['known offenders'], writer)

        statvars.extend(statvar_list)

    return statvars


def _create_mcf(stat_vars: list, mcf_file_path):
    """Writes all statvars to a .mcf file."""
    dcid_set = set()
    final_mcf = ''
    for sv in stat_vars:
        statvar_mcf_list = []
        dcid = sv['Node']
        if dcid in dcid_set:
            continue
        dcid_set.add(dcid)
        for p, v in sv.items():
            if p != 'Node':
                statvar_mcf_list.append(f'{p}: dcs:{v}')
        statvar_mcf = 'Node: dcid:' + dcid + '\n' + '\n'.join(statvar_mcf_list)
        final_mcf += statvar_mcf + '\n\n'

    with open(mcf_file_path, 'w') as f:
        f.write(final_mcf)


def _clean_dataframe(df: pd.DataFrame):
    """Clean the column names and bias motivation values in a dataframe."""
    df.columns = df.columns.str.replace(r'\n', ' ')
    df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
    df.columns = df.columns.str.replace(r'\d+', '', regex=True)
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.strip()

    df['bias motivation'] = df['bias motivation'].replace(r'[\d:]+',
                                                          '',
                                                          regex=True)
    df['bias motivation'] = df['bias motivation'].replace(r'\s+',
                                                          ' ',
                                                          regex=True)
    df['bias motivation'] = df['bias motivation'].str.strip()
    return df


if __name__ == '__main__':
    csv_files = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for year, config in YEARWISE_CONFIG.items():
            xls_file_path = os.path.join(_SCRIPT_PATH, config['path'])
            csv_file_path = os.path.join(tmp_dir, year + '.csv')

            read_file = pd.read_excel(xls_file_path, **config['args'])
            read_file = _clean_dataframe(read_file)
            read_file.insert(YEAR_INDEX, 'Year', year)
            read_file.to_csv(csv_file_path, index=None, header=True)
            csv_files.append(csv_file_path)

        config_path = os.path.join(_SCRIPT_PATH, 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        cleaned_csv_path = os.path.join(_SCRIPT_PATH, 'cleaned.csv')
        statvars = _create_csv_mcf(csv_files, cleaned_csv_path, config)

        mcf_path = os.path.join(_SCRIPT_PATH, 'output.mcf')
        _create_mcf(statvars, mcf_path)
