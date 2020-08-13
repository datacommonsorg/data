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
"""Runs all of the scripts in order as if in a fresh directory.
"""
import requests, zipfile, io

import create_enums
import clean_data
import write_mcf


def download_files():
    url = 'https://www.fda.gov/media/89850/download'
    download = requests.get(url)
    files = zipfile.ZipFile(io.BytesIO(download.content))
    files.extractall('./raw_data')
    

def main():
    print('downloading raw data')
    download_files()
    print('Starting to create enums....')
    create_enums.main()
    print('Enums created- see FDADrugsEnumSchema.mcf')
    print('Starting to clean data....')
    clean_data.main()
    print('Finished cleaning data - see CleanData.csv')
    print('Starting to write data mcf....')
    write_mcf.main()
    print('Finished writing mcf - see FDADrugsFinal.mcf')


if __name__ == '__main__':
    main()
