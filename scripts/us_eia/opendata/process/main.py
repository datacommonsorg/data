"""Process EIA datasets to produce TMCF and CSV."""

import common
import os
from absl import flags
from absl import app


FLAGS = flags.FLAGS
flags.DEFINE_string('data_dir', 'tmp_raw_data', 'Raw data dir')
flags.DEFINE_string('dataset', 'ELEC', 'Name of the dataset')


def main(args):
  assert FLAGS.data_dir
  assert FLAGS.dataset
  file_prefix = os.path.join(FLAGS.data_dir, FLAGS.dataset)
  common.process(file_prefix + '.txt', file_prefix + '.csv',
                 file_prefix + '.mcf', file_prefix + '.tmcf')


if __name__ == '__main__':
  app.run(main)
