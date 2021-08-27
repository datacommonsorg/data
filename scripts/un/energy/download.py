# Copyright 2021 Google LLC
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
"""
Utility to download Energy Statstics Database from UNData
http://data.un.org/Data.aspx

Run this script in this folder:
python3 download.py
"""

import datetime
import io
import requests
import zipfile

from absl import flags
from absl import app

from un_energy_codes import get_all_energy_source_codes

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Data dir to download into')
flags.DEFINE_list('datasets', [], 'Datasets to download. Everything, if empty.')
flags.DEFINE_integer('start_year', 1990,
                     'Data set downloaded from the start year.')
flags.DEFINE_integer('end_year',
                     datetime.datetime.now().year,
                     'Data set downloaded until the end_year.')
flags.DEFINE_integer('years_per_batch', 10,
                     'Data set downloaded in batches of years.')

_DOWNLOAD_URL = 'https://data.un.org/Handlers/DownloadHandler.ashx?DataFilter=cmID:{energy_code};yr={years}&DataMartId=EDATA&Format=csv&c=0,1,2,3,4,5,6,7,8&s=_crEngNameOrderBy:asc,_enID:asc,yr:desc'


def download_zip_file(url: str, save_path: str):
    print(f'Downloading {url} to {save_path}')
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f'Failed to download {url}, response code: ', r.status_code)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(save_path)


def download_energy_dataset(energy_dataset: str):
    supported_datasets = get_all_energy_source_codes()
    if energy_dataset not in supported_datasets:
        print(f'Dataset "{energy_dataset}" not in list of supported codes:' +
              str(supported_datasets))
        return
    # Download data in batches of years as the download has a limit of 100k rows.
    years_list = list(range(FLAGS.start_year, FLAGS.years_per_batch + 1))
    years_list = [str(y) for y in range(FLAGS.start_year, FLAGS.end_year + 1)]
    batch_years = [
        years_list[i:i + FLAGS.years_per_batch]
        for i in range(0, len(years_list), FLAGS.years_per_batch)
    ]
    for year_batch in batch_years:
        start_year = year_batch[0]
        end_year = year_batch[-1]
        years_str = ','.join(year_batch)
        output = f'{FLAGS.data_dir}/undata-{energy_dataset}-{start_year}-{end_year}'
        print('Downloading UNData energy dataset: ',
              f'{energy_dataset} from {start_year} to {end_year}')
        download_url = _DOWNLOAD_URL.format(energy_code=energy_dataset,
                                            years=years_str)
        download_zip_file(download_url, output)


def main(_):
    assert FLAGS.data_dir
    supported_datasets = get_all_energy_source_codes()
    energy_datasets = FLAGS.datasets if FLAGS.datasets else supported_datasets
    for energy_code in energy_datasets:
        download_energy_dataset(energy_code)


if __name__ == '__main__':
    print('running main')
    app.run(main)
