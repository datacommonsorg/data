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
"""Generic proces module to generate the csv/tmcf and csv"""
# TODO: Add unit tests
import os
import sys
import json

from absl import app, flags
# TODO: logs from the column map step is empty when invoked from here, needs to be checked

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             './common'))  # for col_map_generator, data_loader

from generate_col_map import generate_stat_var_map, process_zip_file, generate_mcf_from_column_map
from data_loader import process_subject_tables

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'option', 'all',
    'Specify how to run the process, colmap -- generates column map, process -- runs processing, all -- runs colmap first and then proessing'
)
flags.DEFINE_string(
    'table_prefix', None,
    '[for processing]Subject Table ID as a prefix for output files, eg: S2702')
flags.DEFINE_string('spec_path', None, 'Path to the JSON spec [mandatory]')
flags.DEFINE_string(
    'input_path', None,
    'Path to input directory with (current support only for zip files)')
flags.DEFINE_string('output_dir', './', 'Path to the output directory')
flags.DEFINE_boolean(
    'create_mcf', True,
    '[for colmap]Set False to prevent generation of StatVar mcf file with column map'
)
flags.DEFINE_boolean(
    'has_percent', False,
    '[for processing]Specify the datasets has percentage values that needs to be convered to counts'
)
flags.DEFINE_boolean(
    'debug', False,
    '[for processing]set the flag to add additional columns to debug')


def set_column_map(input_path, spec_path, output_dir, create_mcf):
    generated_col_map = process_zip_file(input_path,
                                         spec_path,
                                         write_output=False)
    output_dir = os.path.expanduser(output_dir)
    f = open(os.path.join(output_dir, 'column_map.json'), 'w')
    json.dump(generated_col_map, f, indent=4)
    f.close()

    if create_mcf:
        generate_mcf_from_column_map(generated_col_map, output_dir)


def main(argv):
    ## get inputs from flags
    option = FLAGS.option.lower()
    table_prefix = FLAGS.table_prefix
    spec_path = FLAGS.spec_path
    input_path = FLAGS.input_path
    output_dir = FLAGS.output_dir
    has_percent = FLAGS.has_percent
    create_mcf = FLAGS.create_mcf
    debug = FLAGS.debug

    # TODO: remove the constraint of inputs being only zip file
    # context: the current implementation of the column map generator accepts
    # only zip files as input and we will need to add new methods to handle inputs
    # as a directory of files or a single csv file.
    _, file_extension = os.path.splitext(input_path)

    if file_extension == '.zip':
        if option == 'colmap':
            set_column_map(input_path, spec_path, output_dir, create_mcf)
        if option == 'process':
            if not table_prefix:
                print('table_prefix required to run data loader')
            else:
                process_subject_tables(table_prefix=table_prefix,
                                       input_path=input_path,
                                       output_dir=output_dir,
                                       column_map_path=os.path.join(
                                           output_dir, 'column_map.json'),
                                       spec_path=spec_path,
                                       debug=debug,
                                       delimiter='!!',
                                       has_percent=has_percent)

        if option == 'all':
            set_column_map(input_path, spec_path, output_dir, create_mcf)
            if not table_prefix:
                print('table_prefix required to run data loader')
            else:
                process_subject_tables(table_prefix=table_prefix,
                                       input_path=input_path,
                                       output_dir=output_dir,
                                       column_map_path=os.path.join(
                                           output_dir, 'column_map.json'),
                                       spec_path=spec_path,
                                       debug=debug,
                                       delimiter='!!',
                                       has_percent=has_percent)
    else:
        print("At the moment, we support only zip files.")


if __name__ == '__main__':
    flags.mark_flags_as_required(
        ['spec_path', 'input_path'])
    app.run(main)
