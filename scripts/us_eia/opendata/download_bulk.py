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
Utility to download all EIA data from https://api.eia.gov/bulk/manifest.txt
Files are stored in raw_data.

Run this script in this folder:
python3 download_bulk.py
"""

import io
import zipfile

import requests

from absl import flags
from absl import app

MANIFEST_URL = "https://api.eia.gov/bulk/manifest.txt"

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Data dir to download into')
flags.DEFINE_list('datasets', [], 'Datasets to download. Everything, if empty.')


def download_file(url: str, save_path: str):
    print(f'Downloading {url} to {save_path}')
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(save_path)


def download_manifest():
    return requests.get(MANIFEST_URL).json()


def main(_):
    assert FLAGS.data_dir
    manifest_json = download_manifest()
    datasets = manifest_json.get('dataset', {})
    for dataset_name in datasets:
        if FLAGS.datasets and dataset_name not in FLAGS.datasets:
            continue
        print(dataset_name)
        dataset = datasets[dataset_name]
        download_file(dataset['accessURL'], f'{FLAGS.data_dir}/{dataset_name}')


if __name__ == '__main__':
    app.run(main)
