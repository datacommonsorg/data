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
from six.moves import urllib
import re
from absl import logging
from absl import app
from absl import logging
from absl import flags
import os

_FLAGS = flags.FLAGS
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
flags.DEFINE_string('mode', '', 'Options: download or process')

PATH = 'demo_r_mlifexp.tsv'


def nuts_to_iso(data):
    """Convert 2-letter NUTS codes for countries to ISO 3166-1 alpha-3 codes."""
    # TODO(jefferyoldham): Consider using util/geo/geo_to_dcid_mappings.go's
    # CountryCodeToDCID subject to NUTS's two additions. If so, remove
    # countries_codes_and_coordinate.csv
    ISO_2_TO_3_PATH = ('./countries_codes_and_coordinates.csv')
    codes = pd.read_csv(ISO_2_TO_3_PATH)
    codes["Alpha-2 code"] = codes["Alpha-2 code"].str.extract(r'"([a-zA-Z]+)"')
    codes["Alpha-3 code"] = codes["Alpha-3 code"].str.extract(r'"([a-zA-Z]+)"')
    # NUTS code matches ISO 3166-1 alpha-2 with two exceptions
    codes["NUTS"] = codes["Alpha-2 code"]
    codes.loc[codes["NUTS"] == "GR", "NUTS"] = "EL"
    codes.loc[codes["NUTS"] == "GB", "NUTS"] = "UK"
    code_dict = codes.set_index('NUTS').to_dict()['Alpha-3 code']
    data.loc[data.index, 'geo'] = data['geo'].map(code_dict)
    assert (~data['geo'].isnull()).all()
    return data


def obtain_value(entry):
    """Extract value from entry. 
    The entries could be like: '81.6', ': ', '79.9 e', ': e'.
    """
    entry = entry.split(' ', maxsplit=-1)[0]  # Discard notes.
    if not entry or entry == ':':
        return None
    return float(entry)


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


def preprocess(file_path):
    """Preprocess the tsv file for importing into DataCommons.
      Args:
         input_file: Path to the input TSV file.
     Returns:
         None"""
    try:
        logging.info('File processing start')
        data = pd.read_csv(file_path, delimiter='\t')
        data = data.rename(columns=({
            'freq,unit,sex,age,geo\TIME_PERIOD': 'unit,sex,age,geo\\time'
        }))
        data['unit,sex,age,geo\\time'] = data[
            'unit,sex,age,geo\\time'].str.slice(2)
        identifier = 'unit,sex,age,geo\\time'
        assert data.columns.values[0].endswith(
            '\\time'), "Expected the first column header to end with '\\time'."
        years = list(data.columns.values)
        years.remove(identifier)
        data = pd.melt(data,
                       id_vars=identifier,
                       value_vars=years,
                       var_name='year',
                       value_name='life_expectancy')

        # Format string into desired format.
        data['year'] = data['year'].astype(int)  # remove spaces, e.g. "2018 "
        data['life_expectancy'] = data['life_expectancy'].apply(obtain_value)

        # Generate the statvars that each row belongs to.
        data[['unit', 'sex', 'age',
              'geo']] = data[identifier].str.split(',', expand=True)
        assert (data['unit'] == 'YR').all()
        data['sex'] = data['sex'].map({'F': '_Female', 'M': '_Male', 'T': ''})
        assert (~data['sex'].isnull()).all()
        age_except = data['age'].isin(['Y_GE85', 'Y_LT1'])
        data.loc[age_except, 'age'] = data.loc[age_except, 'age'].map({
            'Y_GE85': '85OrMoreYears',
            'Y_LT1': 'Upto1Years'
        })
        data.loc[~age_except, 'age'] = data.loc[~age_except, 'age'].str.replace(
            'Y', '') + "Years"
        data = data.drop(columns=[identifier])
        data['StatVar'] = "LifeExpectancy_Person_" + data['age'] + data['sex']
        data = data.drop(columns=['unit', 'sex', 'age'])
        statvars = data['StatVar'].unique()

        # Convert the nuts codes to dcids
        data_country = data[data['geo'].str.len() <= 2]
        data_nuts = data[~(data['geo'].str.len() <= 2)]
        data_country = nuts_to_iso(
            data_country)  # convert nuts code to ISO 3166-1 alpha-3
        data.loc[data_country.index, 'geo'] = 'country/' + data_country['geo']
        data.loc[data_nuts.index, 'geo'] = 'nuts/' + data_nuts['geo']

        # Separate data of different StatVars from one column into multiple columns
        # For example:
        # geo       year  StatVar           sv1_geo   sv1_year   sv2_geo   sv2_year
        # nuts/AT1  2018  sv1         =>    nuts/AT1  2018      nuts/AT2   2018
        # nuts/AT2  2018  sv2
        data_grouped = data.groupby('StatVar')
        subsets = []
        for _, subset in data_grouped:
            pivot = subset['StatVar'].iloc[0]  # get the statvar name
            subset = subset.rename(
                columns={
                    'geo': pivot + '_geo',
                    'year': pivot + '_year',
                    'life_expectancy': pivot
                })
            subset = subset.drop(columns=['StatVar']).reset_index(drop=True)
            subsets.append(subset)
        data = pd.concat(subsets, axis=1, join='outer')

        # Save the processed data into CSV file.
        data.to_csv(PATH[:-4] + '_cleaned.csv', index=False)
        logging.info('File processing completed')
        return
    except Exception as e:
        logging.fatal(f'Processing error {e}')


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
        preprocess(input_file)


if __name__ == "__main__":
    app.run(main)
