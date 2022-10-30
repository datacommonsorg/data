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
"""A script to process FBI Hate Crime table 2 publications."""
import os
import sys
import tempfile
import csv
import json
import pandas as pd

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))  # for utils

import utils

flags.DEFINE_string(
    'output_dir', _SCRIPT_PATH, 'Directory path to write the cleaned CSV and'
    'MCF. Default behaviour is to write the artifacts in the current working'
    'directory.')
flags.DEFINE_bool(
    'gen_statvar_mcf', False, 'Generate MCF of StatVars. Default behaviour is'
    'to not generate the MCF file.')
_FLAGS = flags.FLAGS

_YEAR_INDEX = 0

# Columns in final cleaned CSV
_OUTPUT_COLUMNS = ('Year', 'StatVar', 'Quantity')

# Years with two definitions of rape
_YEARS_WITH_TWO_RAPE_COLUMNS = ('2013', '2014', '2015', '2016')

# A config that maps the year to corresponding xls file with args to be used
# with pandas.read_excel()
_YEARWISE_CONFIG = {
    '2020': {
        'type': 'xls',
        'path': '../source_data/2020/table_2.xlsx',
        'args': {
            'header': 4,
            'skipfooter': 5
        }
    },
    '2019': {
        'type': 'xls',
        'path': '../source_data/2019/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 5
        }
    },
    '2018': {
        'type': 'xls',
        'path': '../source_data/2018/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 5
        }
    },
    '2017': {
        'type': 'xls',
        'path': '../source_data/2017/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 5
        }
    },
    '2016': {
        'type': 'xls',
        'path': '../source_data/2016/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 6
        }
    },
    '2015': {
        'type': 'xls',
        'path': '../source_data/2015/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 6
        }
    },
    '2014': {
        'type': 'xls',
        'path': '../source_data/2014/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 6
        }
    },
    '2013': {
        'type': 'xls',
        'path': '../source_data/2013/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 6
        }
    },
    '2012': {
        'type': 'xls',
        'path': '../source_data/2012/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2011': {
        'type': 'xls',
        'path': '../source_data/2011/table_2.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2010': {
        'type': 'xls',
        'path': '../source_data/2010/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2009': {
        'type': 'xls',
        'path': '../source_data/2009/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2008': {
        'type': 'xls',
        'path': '../source_data/2008/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2007': {
        'type': 'xls',
        'path': '../source_data/2007/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2006': {
        'type': 'xls',
        'path': '../source_data/2006/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2005': {
        'type': 'xls',
        'path': '../source_data/2005/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    },
    '2004': {
        'type': 'xls',
        'path': '../source_data/2004/table_2.xls',
        'args': {
            'header': 2,
            'skipfooter': 4
        }
    }
}


def _write_row(year: int, statvar_dcid: str, quantity: str,
               writer: csv.DictWriter):
    """A wrapper to write data to the cleaned CSV."""
    processed_dict = {
        'Year': year,
        'StatVar': statvar_dcid,
        'Quantity': quantity
    }
    writer.writerow(processed_dict)


def _write_output_csv(reader: csv.DictReader, writer: csv.DictWriter,
                      config: dict) -> list:
    """Reads each row of a CSV and creates statvars for counts of
    Incidents, Offenses, Victims and Known Offenders with different bias
    motivations.

    Args:
        reader: CSV dict reader.
        writer: CSV dict writer of final cleaned CSV.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/table2/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    for crime in reader:
        offense_type = crime['offense type']
        offense_type_key_value = config['pvs'][offense_type]

        if offense_type_key_value == "skip":
            continue

        incident_statvar = {**config['populationType']['Incidents']}
        offense_statvar = {**config['populationType']['Offenses']}
        victim_statvar = {**config['populationType']['Victims']}
        offender_statvar = {**config['populationType']['KnownOffender']}

        statvar_list = [
            incident_statvar, offense_statvar, victim_statvar, offender_statvar
        ]

        utils.update_statvars(statvar_list, offense_type_key_value)
        utils.update_statvar_dcids(statvar_list, config)

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


def _clean_dataframe(df: pd.DataFrame, year: str) -> pd.DataFrame:
    """Clean the column names and offense type values in a dataframe."""
    df.columns = df.columns.str.replace(r'\n', ' ', regex=True)
    df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)
    df.columns = df.columns.str.replace(r'\d+', '', regex=True)
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.strip()

    df['offense type'] = df['offense type'].replace(r'[\d:]+', '', regex=True)
    df['offense type'] = df['offense type'].replace(r'\s+', ' ', regex=True)
    df['offense type'] = df['offense type'].str.strip()
    df['offense type'] = df['offense type'].str.lower()

    # Replace first occurrence of 'other' with 'other crimes against person' and
    # second occurrence of 'other' with 'other crimes against property'.
    first_occurrence = True
    for idx, row in df.iterrows():
        if row['offense type'] == 'other':
            if first_occurrence:
                df.at[idx, 'offense type'] = 'other crimes against person'
                first_occurrence = False
            else:
                df.at[idx, 'offense type'] = 'other crimes against property'

    df.set_index('offense type', inplace=True)

    if year in _YEARS_WITH_TWO_RAPE_COLUMNS:
        df.loc['rape (revised definition)'] += df.loc[
            'rape (legacy definition)']
        df.drop(['rape (legacy definition)'], inplace=True)

    return df


def main(argv):
    csv_files = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for year, config in _YEARWISE_CONFIG.items():
            xls_file_path = os.path.join(_SCRIPT_PATH, config['path'])
            csv_file_path = os.path.join(tmp_dir, year + '.csv')

            read_file = pd.read_excel(xls_file_path, **config['args'])
            read_file = _clean_dataframe(read_file, year)
            read_file.insert(_YEAR_INDEX, 'Year', year)
            read_file.to_csv(csv_file_path, header=True)
            csv_files.append(csv_file_path)

        config_path = os.path.join(_SCRIPT_PATH, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        cleaned_csv_path = os.path.join(_FLAGS.output_dir, 'cleaned.csv')
        statvars = utils.create_csv_mcf(csv_files, cleaned_csv_path, config,
                                        _OUTPUT_COLUMNS, _write_output_csv)

        if _FLAGS.gen_statvar_mcf:
            mcf_path = os.path.join(_FLAGS.output_dir, 'output.mcf')
            utils.create_mcf(statvars, mcf_path)


if __name__ == '__main__':
    app.run(main)
