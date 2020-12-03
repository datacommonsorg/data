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
"""Downloads raw data files, cleans the raw data, and generates the mcf file."""

import zipfile
import io
import requests
import clean
import clean
import generate_mcf


def download_files():
    '''Download Drugs@FDA files and write them to raw_data/ '''

    url = 'https://www.fda.gov/media/89850/download'
    download = requests.get(url)
    files = zipfile.ZipFile(io.BytesIO(download.content))
    files.extractall('./raw_data')


def main():
    '''Download data, create enums, clean data, write mcf.'''

    print('downloading raw data...')
    download_files()

    file_names = {
        'products_file_name': './raw_data/Products.txt',
        'applications_file_name': './raw_data/Applications.txt',
        'te_file_name': './raw_data/TE.txt',
        'market_stat_file_name': './raw_data/MarketingStatus.txt',
        'clean_products_out': './clean_products.txt',
        'clean_data_out': './clean_data.csv',
    }

    print('Cleaning data....')
    drugs_df = clean.get_df(file_names)

    print('Writing mcf....')
    generate_mcf.create_mcf('./FDADrugs.mcf', drugs_df)

    print('Finished!')


if __name__ == '__main__':
    main()
