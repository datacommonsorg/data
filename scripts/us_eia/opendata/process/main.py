"""Process EIA datasets to produce TMCF and CSV."""

import common
import elec
import os
from absl import flags
from absl import app


FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Raw data dir')
flags.DEFINE_string('dataset', 'ELEC', 'Name of the dataset')


def get_extract_fn(dataset):
  if dataset == 'ELEC':
    return elec.extract_place_statvar
  else:
    assert False, 'Unsupported dataset: ' + dataset


def get_schema_fn(dataset):
  if dataset == 'ELEC':
    return elec.generate_statvar_schema
  else:
    return None


def main(args):
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
