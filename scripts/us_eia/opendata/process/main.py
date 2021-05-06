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
"""Process EIA datasets to produce TMCF and CSV."""

import os
from absl import flags
from absl import app

import coal
import common
import elec
import intl
import ng
import pet
import seds
import total

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Raw data dir')
flags.DEFINE_string('dataset', 'ELEC', 'Name of the dataset')


def get_extract_fn(dataset):
    if dataset == 'COAL':
        return coal.extract_place_statvar
    if dataset == 'ELEC':
        return elec.extract_place_statvar
    if dataset == 'INTL':
        return intl.extract_place_statvar
    if dataset == 'PET':
        return pet.extract_place_statvar
    if dataset == 'NG':
        return ng.extract_place_statvar
    elif dataset == 'SEDS':
        return seds.extract_place_statvar
    elif dataset == 'TOTAL':
        return total.extract_place_statvar
    assert False, 'Unsupported dataset: ' + dataset
    return None


def get_schema_fn(dataset):
    if dataset == 'COAL':
        return coal.generate_statvar_schema
    if dataset == 'ELEC':
        return elec.generate_statvar_schema
    return None


def main(_):
    assert FLAGS.data_dir
    assert FLAGS.dataset
    file_prefix = os.path.join(FLAGS.data_dir, FLAGS.dataset)
    common.process(in_json=file_prefix + '.txt',
                   out_csv=file_prefix + '.csv',
                   out_sv_mcf=file_prefix + '.mcf',
                   out_tmcf=file_prefix + '.tmcf',
                   extract_place_statvar_fn=get_extract_fn(FLAGS.dataset),
                   generate_statvar_schema_fn=get_schema_fn(FLAGS.dataset))


if __name__ == '__main__':
    app.run(main)
