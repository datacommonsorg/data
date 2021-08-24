import os
from absl import app, flags
from ..common.base import SubjectTableDataLoaderBase

FLAGS = flags.FLAGS

flags.DEFINE_string('output', None, 'Path to the folder for output files')
flags.DEFINE_string('tableID', None, 'Code of the subject Table (Eg. S2702)')
flags.DEFINE_string('download_id', None, 'download id from data.census.gov')
flags.DEFINE_string('input', None, 'Path to an already downloaded zip file with data')
flags.DEFINE_string('config', None, 'Path to a JSON file with import configurations')

flags.mark_flags_as_required(['output', 'config'])

def main(argv):
  loader = SubjectTableDataLoaderBase(tableID=FLAGS.tableID,
                                      acsEstimatePeriod='5',
                                      config_json=FLAGS.config,
                                      outputPath=FLAGS.output)

  if FLAGS.download_id is not None:
    loader.download_and_process(FLAGS.download_id)

  if FLAGS.input is not None:
    loader.process_zip(FLAGS.input)

  if (FLAGS.download_id is None) and (FLAGS.input is None):
    print("Invalid input! Ensure either a download_id for a download request from data.census.gov or the path to an already downloaded zip file of subject tables is provided and run the script again.")
    exit(1)


if __name__ == '__main__':
  app.run(main)
