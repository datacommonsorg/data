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

from absl import flags
from absl import app

import property_maps

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Data dir to download into')
flags.DEFINE_list('datasets', [], 'Datasets to download. Everything, if empty.')

def download_zip_file(url: str, output_file: str):
    print(f'Downloading {url} to {save_path}')
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(save_path)

def download_energy_dataset(energy_dataset: str):
    energy_datasets = property_maps.get_all_energy_source_codes()
    if energy_dataset not in energy_datasets:
        print('Dataset {energy_dataset} not in supported codes {energy_datasets}')
        return
    # Download data in batches of 5 years as the download has a limit of 100k rows.
    years_list = list(range(_DATA_START_YEAR, datetime.datetime.now().year + 1))
    years_list = [str(y) for y in range(_DATA_START_YEAR, datetime.datetime.now().year + 1)]
    batch_years = [years_list[i: i + _DATA_BATCH_YEARS] for i in range(0, len(years_list), _DATA_BATCH_YEARS)]
    for year_batch in batch_years:
      start_year = year_batch[0]
      end_year = year_batch[-1]f'{FLAGS.data_dir}/undata-{energy_dataset}')
      years_str = ','.join(year_batch)
      output = f'{FLAGS.data_dir}/undata-{energy_dataset}-{start_year}-{end_year}'
      print(f'Downloading UNData energy dataset: {energy_dataset} from {start_year} to {end_year}')
      download_url = _DOWNLOAD_URL.format(energy_code = energy_dataset, years = years_str)
      download_zip_file(download_url, output)

def main(_):
    assert FLAGS.data_dir
    energy_datasets = property_maps.get_all_energy_source_codes()
    for energy_code in energy_datasets:
        if FLAGS.datasets and FLAGS.dataset == 'all' or energy_code not in FLAGS.datasets:
            continue
        download_energy_dataset(energy_code)

if __name__ == '__main__':
    print('running main')
    app.run(main)
