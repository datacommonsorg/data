# Copyright 2020 Google LLC
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

import pandas as pd
import numpy as np
import re
import os
import urllib.request
from absl import logging
from absl import app
from absl import flags

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
flags.DEFINE_string('input_file', 'input_files/input_file.tsv',
                    'Path to input TSV file')
flags.DEFINE_string('output_file', 'demo_r_mlifexp_cleaned.csv',
                    'Path to output CSV file')
flags.DEFINE_string('mode', '',
                    'Mode of operation: download, process, or empty (both)')


def nuts_to_iso(data):
    """Convert 2-letter NUTS codes for countries to ISO 3166-1 alpha-3 codes."""
    ISO_2_TO_3_PATH = os.path.join(_MODULE_DIR,
                                   'countries_codes_and_coordinates.csv')
    if not os.path.exists(ISO_2_TO_3_PATH):
        raise FileNotFoundError(
            f"{ISO_2_TO_3_PATH} not found. This file is required for ISO conversion."
        )
        return data

    codes = pd.read_csv(ISO_2_TO_3_PATH)
    # The file seems to have quoted values like '"AD"'
    codes["Alpha-2 code"] = codes["Alpha-2 code"].str.extract(r'"([a-zA-Z]+)"')
    codes["Alpha-3 code"] = codes["Alpha-3 code"].str.extract(r'"([a-zA-Z]+)"')

    # NUTS code matches ISO 3166-1 alpha-2 with two exceptions
    codes["NUTS"] = codes["Alpha-2 code"]
    codes.loc[codes["NUTS"] == "GR", "NUTS"] = "EL"
    codes.loc[codes["NUTS"] == "GB", "NUTS"] = "UK"

    code_dict = codes.set_index('NUTS')['Alpha-3 code'].to_dict()

    def map_geo(geo):
        if len(geo) == 2:
            iso3 = code_dict.get(geo)
            if iso3:
                return f'country/{iso3}'
        return f'nuts/{geo}'

    data['place'] = data['geo'].apply(map_geo)
    return data


def obtain_value(entry):
    """Extract value from entry. 
    The entries could be like: '81.6', ': ', '79.9 e', ': e'.
    """
    if isinstance(entry, (int, float)):
        return float(entry)
    entry = str(entry).split(' ', maxsplit=-1)[0]  # Discard notes.
    if not entry or entry == ':':
        return None
    try:
        return float(entry)
    except ValueError:
        return None


def download_data(download_link, download_path):
    """Downloads raw data from Eurostat website and stores it in instance
       data frame.
    
        Args:
        download_link(str): A string representing the URL of the data source.
        download_path(str): A string specifying the local file path where the downloaded data will be saved.
        
        Returns:None
        
    """
    try:
        logging.info(f'Processing file: {download_path}')
        urllib.request.urlretrieve(download_link, "demo_r_mlifexp.tsv.gz")
        raw_df = pd.read_table("demo_r_mlifexp.tsv.gz")
        raw_df.to_csv(download_path, index=False, sep='\t')
        logging.info(f'Downloaded {download_path} from {download_link}')
    except Exception as e:
        logging.fatal(f'Download error for: {download_link}: {e}')


def preprocess(input_file, output_file):
    logging.info(f'Processing file: {input_file}')

    # Read TSV
    data = pd.read_csv(input_file, delimiter='\t')

    # Identify the first column which contains multiple dimensions
    identifier = data.columns[0]
    years = [col for col in data.columns if col != identifier]

    # Melt to long format
    data = pd.melt(data,
                   id_vars=identifier,
                   value_vars=years,
                   var_name='year',
                   value_name='value')

    # Clean year and value
    data['year'] = data['year'].str.strip().astype(int)
    data['value'] = data['value'].apply(obtain_value)

    # Drop rows with NaN values
    data = data.dropna(subset=['value'])
    dims = identifier.split('\\')[0].split(',')
    data[dims] = data[identifier].str.split(',', expand=True)

    # Map sex
    data['sex_mapped'] = data['sex'].map({
        'F': '_Female',
        'M': '_Male',
        'T': ''
    })

    # Map age
    age_map = {
        'Y_GE85': '85OrMoreYears',
        'Y_LT1': 'Upto1Years',
        'Y_GE95': '95OrMoreYears'
    }

    def map_age(age):
        if age in age_map:
            return age_map[age]
        if age.startswith('Y'):
            return age[1:] + "Years"
        return age + "Years"

    data['age_mapped'] = data['age'].apply(map_age)

    # Create SV (StatVar)
    data['SV'] = "dcid:LifeExpectancy_Person_" + data['age_mapped'] + data[
        'sex_mapped']

    # Map geo to place
    data = nuts_to_iso(data)

    # Select final columns
    final_df = data[['year', 'place', 'SV', 'value']]

    # Sort for consistency
    final_df = final_df.sort_values(['year', 'place', 'SV'])

    # Save to CSV
    final_df.to_csv(output_file, index=False)
    logging.info(f'Processed data saved to {output_file}')


def main(_):
    mode = _FLAGS.mode
    _DATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/demo_r_mlifexp/?format=TSV&compressed=true"

    input_path = os.path.join(_MODULE_DIR, 'input_files')
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    input_file = os.path.join(input_path, 'input_file.tsv')

    if mode == "" or mode == "download":
        download_data(_DATA_URL, input_file)
    if mode == "" or mode == "process":
        preprocess(input_file, _FLAGS.output_file)


if __name__ == "__main__":
    app.run(main)
