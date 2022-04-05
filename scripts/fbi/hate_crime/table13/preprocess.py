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
"""A script to process FBI Hate Crime table 13 publications."""
import os
import sys
import tempfile
import csv
import json
import numpy as np
import pandas as pd

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))  # for utils, geo_id_resolver
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../../util/'))  # state map

import geo_id_resolver
import utils
from name_to_alpha2 import USSTATE_MAP_SPACE

flags.DEFINE_string(
    'output_dir', _SCRIPT_PATH, 'Directory path to write the cleaned CSV and'
    'MCF. Default behaviour is to write the artifacts in the current working'
    'directory.')
flags.DEFINE_bool(
    'gen_statvar_mcf', False, 'Generate MCF of StatVars. Default behaviour is'
    'to not generate the MCF file.')
_FLAGS = flags.FLAGS

USSTATE_MAP_SPACE['U.S. Virgin Islands'] = 'VI'
USSTATE_MAP_SPACE['Virgin Islands'] = 'VI'

_YEAR_INDEX = 0

# Columns in final cleaned CSV
_OUTPUT_COLUMNS = ('Year', 'Geo', 'StatVar', 'ObsDate', 'ObsPeriod', 'Quantity')
_UNRESOLVED_GEOS = set()

# A config that maps the year to corresponding xls file with args to be used
# with pandas.read_excel().
_YEARWISE_CONFIG = {
    '2020': {
        'type': 'xls',
        'path': '../source_data/2020/table_13.xlsx',
        'args': {
            'header': 6,
            'skipfooter': 3
        }
    },
    '2019': {
        'type': 'xls',
        'path': '../source_data/2019/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 3
        }
    },
    '2018': {
        'type': 'xls',
        'path': '../source_data/2018/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 4
        }
    },
    '2017': {
        'type': 'xls',
        'path': '../source_data/2017/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 3
        }
    },
    '2016': {
        'type': 'xls',
        'path': '../source_data/2016/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 3
        }
    },
    '2015': {
        'type': 'xls',
        'path': '../source_data/2015/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 3
        }
    },
    '2014': {
        'type': 'xls',
        'path': '../source_data/2014/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 3,
            'usecols': list(range(0, 15))
        }
    },
    '2013': {
        'type': 'xls',
        'path': '../source_data/2013/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 4,
            'usecols': list(range(0, 15))
        }
    },
    '2012': {
        'type': 'xls',
        'path': '../source_data/2012/table_13.xls',
        'args': {
            'header': 5,
            'skipfooter': 4,
            'usecols': list(range(0, 13))
        }
    },
    '2011': {
        'type': 'xls',
        'path': '../source_data/2011/table_13.xls',
        'args': {
            'header': 4,
            'skipfooter': 4
        }
    },
    '2010': {
        'type': 'xls',
        'path': '../source_data/2010/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2009': {
        'type': 'xls',
        'path': '../source_data/2009/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2008': {
        'type': 'xls',
        'path': '../source_data/2008/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 3
        }
    },
    '2007': {
        'type': 'xls',
        'path': '../source_data/2007/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 4
        }
    },
    '2006': {
        'type': 'xls',
        'path': '../source_data/2006/table_13.xls',
        'args': {
            'header': 2,
            'skipfooter': 2
        }
    },
    '2005': {
        'type': 'xls',
        'path': '../source_data/2005/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 1
        }
    },
    '2004': {
        'type': 'xls',
        'path': '../source_data/2004/table_13.xls',
        'args': {
            'header': 3,
            'skipfooter': 1,
            'usecols': list(range(0, 7))
        }
    }
}


def _write_row(year: int, geo: str, statvar_dcid: str, obs_date: str,
               obs_period: str, quantity: str, writer: csv.DictWriter):
    """A wrapper to write data to the cleaned CSV."""
    processed_dict = {
        'Year': year,
        'Geo': geo,
        'StatVar': statvar_dcid,
        'ObsDate': obs_date,
        'ObsPeriod': obs_period,
        'Quantity': quantity
    }
    writer.writerow(processed_dict)


def _remove_from_list(l: list, e: str):
    try:
        l.remove(e)
    except ValueError as err:
        print(f"{e} not in list")


def _geo_resolution(row):
    # In earlier years, states are all caps
    if row['agency'].isupper():
        row['geo_dcid'] = geo_id_resolver.convert_to_place_dcid(
            row['state_abbr'], geo_type='State')
    elif row['agency type'] == 'Total':
        row['geo_dcid'] = geo_id_resolver.convert_to_place_dcid(
            row['state_abbr'], geo_type='State')
    else:
        row['geo_dcid'] = geo_id_resolver.convert_to_place_dcid(
            row['state_abbr'], geo=row['agency'], geo_type='City')
    return row


def _add_state_alpha(row):
    row['state_abbr'] = USSTATE_MAP_SPACE.get(row['state'], '')
    return row


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
    global _UNRESOLVED_GEOS
    columns = list(reader.fieldnames)

    _remove_from_list(columns, 'state')
    _remove_from_list(columns, 'state_abbr')
    _remove_from_list(columns, 'Year')
    _remove_from_list(columns, 'agency')
    _remove_from_list(columns, 'agency type')
    _remove_from_list(columns, 'geo_dcid')

    for crime in reader:
        geo_id = crime['geo_dcid']
        statvar_list = []
        for c in columns:
            statvar = {**config['populationType'][c]}
            statvar.pop('observationPeriod', None)
            statvar.pop('isQuarter', None)
            statvar.pop('endingMonth', None)
            statvar_list.append(statvar)

        for idx, c in enumerate(columns):
            if crime[c] not in [np.nan, '', ' ']:  # Empty values
                geo = f'{crime["agency"].lower()} {crime["state_abbr"].lower()}'
                if config['populationType'][c]['isQuarter'] == "True":
                    ending_month = config['populationType'][c]['endingMonth']
                    obs_period = config['populationType'][c][
                        'observationPeriod']
                    obs_date = f"{crime['Year']}-{ending_month}"
                    if geo_id:
                        _write_row(crime['Year'], geo_id,
                                   statvar_list[idx]['Node'], obs_date,
                                   obs_period, crime[c], writer)
                    else:
                        _UNRESOLVED_GEOS.add(geo)
                else:
                    obs_period = config['populationType'][c][
                        'observationPeriod']
                    obs_date = crime['Year']
                    if geo_id:
                        _write_row(crime['Year'], geo_id,
                                   statvar_list[idx]['Node'], obs_date,
                                   obs_period, crime[c], writer)
                    else:
                        _UNRESOLVED_GEOS.add(geo)

        statvars.extend(statvar_list)

    return statvars


def _clean_dataframe(df: pd.DataFrame, year: str):
    """Clean the column names and offense type values in a dataframe."""
    if year in ['2020']:
        df.columns = [
            'state', 'agency type', 'agency', 'agency unit', 'r/e/a',
            'religion', 'sexual orientation', 'disability', 'gender',
            'gender identity', '1st quarter', '2nd quarter', '3rd quarter',
            '4th quarter', 'population'
        ]

        df.drop(['agency unit', 'population'], axis=1, inplace=True)

    elif year in ['2019', '2018', '2017', '2016', '2015']:
        df.columns = [
            'state', 'agency type', 'agency', 'r/e/a', 'religion',
            'sexual orientation', 'disability', 'gender', 'gender identity',
            '1st quarter', '2nd quarter', '3rd quarter', '4th quarter',
            'population'
        ]

        df.drop(['population'], axis=1, inplace=True)

    elif year in ['2014', '2013']:
        df.columns = [
            'state', 'agency type', 'agency', 'race', 'religion',
            'sexual orientation', 'ethnicity', 'disability', 'gender',
            'gender identity', '1st quarter', '2nd quarter', '3rd quarter',
            '4th quarter', 'population'
        ]

        df.drop(['population'], axis=1, inplace=True)

    elif year in ['2012', '2011', '2010', '2009', '2008', '2007']:
        df.columns = [
            'state', 'agency type', 'agency', 'race', 'religion',
            'sexual orientation', 'ethnicity', 'disability', '1st quarter',
            '2nd quarter', '3rd quarter', '4th quarter', 'population'
        ]

        df.drop(['population'], axis=1, inplace=True)

    elif year in ['2006']:
        df.columns = [
            'state', 'agency type', 'agency', 'quarters reported', 'race',
            'religion', 'sexual orientation', 'ethnicity', 'disability',
            'population'
        ]

        df.drop(['quarters reported', 'population'], axis=1, inplace=True)

    else:  # 2005, 2004
        df.columns = [
            'agency', 'quarters reported', 'race', 'religion',
            'sexual orientation', 'ethnicity', 'disability'
        ]
        df['agency'] = df['agency'].str.strip()

        # Assigning states
        agencies = list(df['agency'])
        states = list()
        agency_type_list = list()
        possible_agency_types = ('Cities', 'Metropolitan Counties',
                                 'Universities and Colleges',
                                 'Nonmetropolitan Counties',
                                 'State Police Agencies')

        # The agency column has state names in uppercase
        for agency in agencies:
            if agency.isupper():  # state
                curr_state = agency
                curr_agency_type = 'Cities'
            if agency in possible_agency_types:
                curr_agency_type = agency
            agency_type_list.append(curr_agency_type)
            states.append(curr_state)

        df['state'] = states
        df['agency type'] = agency_type_list

        # Removing aggregated total counts of cities
        df = df[df['agency'] != 'Cities']

        # Retaining only cities and states
        df = df[df['agency type'] == 'Cities']
        df.drop(['quarters reported'], axis=1, inplace=True)

    df['state'] = df['state'].fillna(method='ffill')
    df['agency type'] = df['agency type'].fillna(method='ffill')

    # Assigning agency to state
    df.loc[df['agency type'] == 'Total',
           'agency'] = df.loc[df['agency type'] == 'Total', 'state']

    # Cleaning cities
    df['agency'] = df['agency'].replace(r'[\d:]+', '', regex=True)
    df['agency'] = df['agency'].replace(r'\s+', ' ', regex=True)
    df['agency'] = df['agency'].str.strip()

    # Keep only cities and states
    df = df[((df['agency type'] == 'Cities') & (df['agency'].notna()) &
             (df['agency'] != '')) | (df['agency type'] == 'Total')]

    df['state'] = df['state'].str.title()
    df['state'] = df['state'].str.strip()

    df = df.apply(_add_state_alpha, axis=1)
    df = df.apply(_geo_resolution, axis=1)

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
            read_file.to_csv(csv_file_path, header=True, index=False)
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

        unresolved_geos_path = os.path.join(_SCRIPT_PATH, 'unresolved_geos.csv')
        with open(unresolved_geos_path, 'w') as f:
            ug_writer = csv.DictWriter(f, fieldnames=('name',))
            ug_writer.writeheader()
            for geo in _UNRESOLVED_GEOS:
                ug_writer.writerow({'name': geo})


if __name__ == '__main__':
    app.run(main)
