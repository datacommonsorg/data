"""Process EIA datasets to produce TMCF and CSV."""

import os
from absl import flags
from absl import app

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

# Value: (name, extract_fn, schema_fn)
_DATASETS = {
    'ELEC': ('Electricity', elec.extract_place_statvar,
             elec.generate_statvar_schema),
    'INTL': ('Energy Overview (INTL)', intl.extract_place_statvar, None),
    'PET': ('Petroleum', pet.extract_place_statvar, None),
    'NG': ('Natural Gas', ng.extract_place_statvar, None),
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
                   out_tmcf=file_prefix + '.tmcf',
                   extract_place_statvar_fn=_DATASETS[FLAGS.dataset][1],
                   generate_statvar_schema_fn=_DATASETS[FLAGS.dataset][2])


if __name__ == '__main__':
    app.run(main)
