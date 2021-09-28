"""Generic proces module to generate the csv/tmcf and csv"""
import os
import sys
import json

from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, './common'))  # for col_map_generator, data_loader

from generate_col_map import generate_stat_var_map, process_zip_file
from data_loader import process_subject_tables

FLAGS = flags.FLAGS
flags.DEFINE_string('option', 'all', 'Specify how to run the process, colmap -- generates column map, process -- runs processing, all -- runs colmap first and then proessing')
flags.DEFINE_string('table_prefix', 'S2702', '[for processing]Subject Table ID as a prefix for output files, eg: S2702')
flags.DEFINE_string('spec_path', './common/testdata/spec.json', 'Path to the JSON spec [mandatory]')
flags.DEFINE_string('input_path', None, 'Path to input directory with (current support only for zip files)')
flags.DEFINE_string('output_dir', './', 'Path to the output directory')
flags.DEFINE_boolean('has_percent', False, '[for processing]Specify the datasets has percentage values that needs to be convered to counts')
flags.DEFINE_boolean('debug', False, '[for processing]set the flag to add additional columns to debug')

def set_column_map(input_path, spec_path, output_dir):
  generated_col_map = process_zip_file(input_path, spec_path, write_output=False)
  f = open(os.path.join(output_dir, 'column_map.json'), 'w')
  json.dump(generated_col_map, f, indent=4)
  f.close()

def main(argv):
  ## get inputs from flags
  option = FLAGS.option.lower()
  table_prefix = FLAGS.table_prefix
  spec_path = FLAGS.spec_path
  input_path = FLAGS.input_path
  output_dir = FLAGS.output_dir
  has_percent = FLAGS.has_percent
  debug = FLAGS.debug

  ## TODO: replace the constraint of zip in next PR
  ## check file extension, since only zip files is supported 
  _, file_extension = os.path.splitext(input_path)

  if file_extension == '.zip':
    if option == 'colmap':
        set_column_map(input_path, spec_path, output_dir)
    if option == 'process':
      process_subject_tables(table_prefix=table_prefix, input_path=input_path, 
        output_dir=output_dir, column_map_path=os.path.join(output_dir, 'column_map.json'), spec_path=spec_path, debug=debug, delimiter='!!', has_percent=has_percent)

    if option == 'all':
      set_column_map(input_path, spec_path, output_dir)
      process_subject_tables(table_prefix=table_prefix, input_path=input_path, 
        output_dir=output_dir, column_map_path=os.path.join(output_dir, 'column_map.json'), spec_path=spec_path, debug=debug, delimiter='!!', has_percent=has_percent)
  else:
    print("At the moment, we support only zip files.")

if __name__ == '__main__':
  flags.mark_flags_as_required(['table_prefix', 'spec_path', 'input_path', 'output_dir'])
  app.run(main)
