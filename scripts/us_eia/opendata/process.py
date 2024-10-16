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
import os 
import sys
import zipfile

import requests

from absl import flags
from absl import app

from process import coal, common, elec, intl, ng, nuclear, pet, seds, total

MANIFEST_URL = "https://api.eia.gov/bulk/manifest.txt"

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Data dir to download into')
flags.DEFINE_string('dataset', '', 'Datasets to download. Everything, if empty.')

# Value: (name, extract_fn, schema_fn)
_DATASETS = {
    'COAL': ('Coal', coal.extract_place_statvar, coal.generate_statvar_schema),
    'ELEC': ('Electricity', elec.extract_place_statvar,
             elec.generate_statvar_schema),
    'INTL': ('Energy Overview (INTL)', intl.extract_place_statvar, None),
    'PET': ('Petroleum', pet.extract_place_statvar, None),
    'NG': ('Natural Gas', ng.extract_place_statvar, None),
    'NUC_STATUS': ('Nuclear Outages', nuclear.extract_place_statvar,
                   nuclear.generate_statvar_schema),
    'SEDS': ('Consumption, Production, Prices and Expenditure (SEDS)',
             seds.extract_place_statvar, None),
    'TOTAL': ('Energy Overview (TOTAL)', total.extract_place_statvar, None)
}


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
        if FLAGS.dataset and dataset_name not in FLAGS.dataset:
            continue
        print(dataset_name)
        dataset = datasets[dataset_name]
        print("dataset", dataset)
        download_file(dataset['accessURL'], f'{FLAGS.data_dir}/{dataset_name}')
        print(f'{FLAGS.data_dir}/{dataset_name}')
        print(FLAGS.data_dir, FLAGS.dataset)
        file_prefix = os.path.join(f'{FLAGS.data_dir}/{dataset_name}', FLAGS.dataset)
        print("file_prefix", file_prefix)
        common.process(dataset=FLAGS.dataset,
                   dataset_name=_DATASETS[FLAGS.dataset],
                   in_json=file_prefix + '.txt',
                   out_csv=file_prefix + '.csv',
                   out_sv_mcf=file_prefix + '.mcf',
                   out_svg_mcf=file_prefix + '.svg.mcf',
                   out_tmcf=file_prefix + '.tmcf',
                   extract_place_statvar_fn=_DATASETS[FLAGS.dataset][1],
                   generate_statvar_schema_fn=_DATASETS[FLAGS.dataset][2])



if __name__ == '__main__':
    app.run(main)
