#
# Copyright 2020 Google LLC
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
import sys

sys.path.insert(1, '../../../../util')
from six.moves import urllib
from alpha2_to_dcid import COUNTRY_MAP
from nuts_codes_names import NUTS1_CODES_NAMES
import numpy as np
import pandas as pd
import io
import csv
import os
from absl import app
from absl import logging
from absl import flags

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
flags.DEFINE_string('mode', '', 'Options: download or process')

_OUTPUT_COLUMNS = [
    'Date',
    'GeoId',
    'Count_Person_PerArea',
]


def download_data(download_link, download_path):
    """Downloads raw data from Eurostat website and stores it in instance
       data frame.
    
        Args:
        download_link(str): A string representing the URL of the data source.
        download_path(str): A string specifying the local file path where the downloaded data will be saved.
        
        Returns:None
        
    """
    try:
        logging.info(f'Downloading: {download_link}')
        urllib.request.urlretrieve(download_link, "demo_r_d3dens.tsv.gz")
        raw_df = pd.read_table("demo_r_d3dens.tsv.gz")
        raw_df.to_csv(download_path, index=False, sep='\t')
        logging.info(f'Downloaded {download_path} from {download_link}')
    except Exception as e:
        logging.fatal(f'Download error for: {download_link}: {e}')


def translate_wide_to_long(file_path):
    """ Reshaping DataFrames from Wide to Long Format
    Args: 
        This argument specifies the path to the input file
    Returns:
        df: long-format version of the original raw_df.
    
    """
    try:
        logging.info('Transforming data: wide to long.. ')
        df = pd.read_csv(file_path, delimiter='\t')
        df = df.rename(columns=({
            'freq,unit,geo\TIME_PERIOD': 'unit,geo\\time'
        }))
        df['unit,geo\\time'] = df['unit,geo\\time'].str.slice(2)
        header = list(df.columns.values)
        years = header[1:]

        # Pandas.melt() unpivots a DataFrame from wide format to long format.
        df = pd.melt(df,
                     id_vars=header[0],
                     value_vars=years,
                     var_name='time',
                     value_name='value')

        # Separate geo and unit columns.
        new = df[header[0]].str.split(",", n=1, expand=True)
        df['geo'] = new[1]
        df['unit'] = new[0]
        df.drop(columns=[header[0]], inplace=True)
        df['geo'] = df['geo'].apply(lambda geo: f'nuts/{geo}' if any(
            g.isdigit() for g in geo) or ('nuts/' + geo in NUTS1_CODES_NAMES)
                                    else COUNTRY_MAP.get(geo, f'{geo}'))

        # Remove empty rows, clean values to have all digits.
        df = df[df['value'].notna() & df['value'].str.contains('[0-9]')].copy()
        possible_flags = [' ', ':', 'b', 'e', 'bep', 'be', 'ep', 'p']
        for flag in possible_flags:
            df['value'] = df['value'].str.replace(flag, '')

        df['value'] = pd.to_numeric(df['value'])
        logging.info('Transforming data: wide to long.. completed ')
        return df
    except Exception as e:
        logging.fatal(f'Transforming error {e}')


def preprocess(df, cleaned_csv):
    """ Preprocesses a DataFrame and saves the cleaned data to a CSV file.
    Args:
        df: The raw, unprocessed DataFrame.
        cleaned_csv: The path to the CSV file where the cleaned data will be saved.

    Returns:
        None
    """
    try:
        logging.info(f'Processing file: {cleaned_csv}')
        with open(cleaned_csv, 'w', newline='') as f_out:
            writer = csv.DictWriter(f_out,
                                    fieldnames=_OUTPUT_COLUMNS,
                                    lineterminator='\n')
            writer.writeheader()
            for _, row in df.iterrows():
                writer.writerow({
                    # 'Date': '%s-%s-%s' % (row_dict['TIME'][:4], '01', '01'),
                    'Date': '%s' % (row['time'][:4]),
                    'GeoId': '%s' % row['geo'],
                    'Count_Person_PerArea': float(row['value']),
                })
        logging.info('File processing completed')
        return df
    except Exception as e:
        logging.fatal(f'Processing error {e}')


def get_template_mcf(output_columns, _TMCF):
    """Automate Template MCF generation since there are many Statistical Variables.
      Args:
            output_columns: A list of strings representing all the output columns from the data.
            _TMCF: The path to a template MCF file used as the base structure.
        Returns:
            None
    """
    TEMPLATE_MCF_TEMPLATE = """
        Node: E:EurostatNUTS3_DensityTracking->E{index}
        typeOf: dcs:StatVarObservation
        variableMeasured: dcs:{stat_var}
        observationAbout: C:EurostatNUTS3_DensityTracking->GeoId
        observationDate: C:EurostatNUTS3_DensityTracking->Date
        value: C:EurostatNUTS3_DensityTracking->{stat_var}
        measurementMethod: "EurostatRegionalStatistics"
        unit: PersonPerSquareKilometer
        """
    try:
        logging.info('Template MCF processing ')
        stat_vars = output_columns[2:]
        with open(_TMCF, 'w', newline='') as f_out:
            for i in range(len(stat_vars)):
                f_out.write(
                    TEMPLATE_MCF_TEMPLATE.format_map({
                        'index': i,
                        'stat_var': _OUTPUT_COLUMNS[2:][i]
                    }))

        logging.info('Template MCF processing completed')
    except Exception as e:
        logging.fatal(f'Processing error {e}')


def main(_):
    mode = _FLAGS.mode
    _DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_d3dens/?format=TSV&compressed=true"
    _CLEANED_CSV = "./PopulationDensity_Eurostat_NUTS3.csv"
    _TMCF = "./PopulationDensity_Eurostat_NUTS3.tmcf"

    input_path = os.path.join(_MODULE_DIR, 'input_files')
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    input_file = os.path.join(input_path, 'input_file.tsv')
    if mode == "" or mode == "download":
        download_data(_DATA_URL, input_file)
    if mode == "" or mode == "process":
        translate_df = translate_wide_to_long(input_file)
        preprocess(translate_df, _CLEANED_CSV)
        get_template_mcf(_OUTPUT_COLUMNS, _TMCF)


if __name__ == "__main__":
    app.run(main)
