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
import sys

from absl import flags
from absl import app

# Allows the following module imports to work when running as a script
# relative to scripts/
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from us_eia.opendata.process import coal, common, elec, intl, ng, nuclear, pet, seds, total

FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Raw data dir')
flags.DEFINE_string('dataset', 'ELEC', 'Name of the dataset')

# Value: (name, extract_fn, schema_fn)
_DATASETS = {
    'COAL': ('Coal', coal.extract_place_statvar, coal.generate_statvar_schema),
    'ELEC':
    ('Electricity', elec.extract_place_statvar, elec.generate_statvar_schema),
    'INTL': ('Energy Overview (INTL)', intl.extract_place_statvar, None),
    'PET': ('Petroleum', pet.extract_place_statvar, None),
    'NG': ('Natural Gas', ng.extract_place_statvar, None),
    'NUC_STATUS': ('Nuclear Outages', nuclear.extract_place_statvar,
                   nuclear.generate_statvar_schema),
    'SEDS': ('Consumption, Production, Prices and Expenditure (SEDS)',
             seds.extract_place_statvar, None),
    'TOTAL': ('Energy Overview (TOTAL)', total.extract_place_statvar, None)
}


def main(_):
    assert FLAGS.data_dir
    assert FLAGS.dataset
    file_prefix = os.path.join(FLAGS.data_dir, FLAGS.dataset)
    common.process(dataset=FLAGS.dataset,
                   dataset_name=_DATASETS[FLAGS.dataset][0],
                   in_json=file_prefix + '.txt',
                   out_csv=file_prefix + '.csv',
                   out_sv_mcf=file_prefix + '.mcf',
                   out_svg_mcf=file_prefix + '.svg.mcf',
                   out_tmcf=file_prefix + '.tmcf',
                   extract_place_statvar_fn=_DATASETS[FLAGS.dataset][1],
                   generate_statvar_schema_fn=_DATASETS[FLAGS.dataset][2])


if __name__ == '__main__':
    app.run(main)
