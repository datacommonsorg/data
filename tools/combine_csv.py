# Copyright 2020 Google LLC
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
"""Combine multiple csv files to form single file.
    Following config parameters can be used:
    - output_columns: Column name as key and dict with required boolean and
                        default value if not required as value.
    - output_file: Path to store the combined csv file.
    - input_files: Dict with path expression for single or set of files as key
                        and dict with old_column_name: new_column_name as value.
"""

import glob
import json
import os
import pandas as pd

from absl import app
from absl import flags
from calendar import c

# commandline flags
FLAGS = flags.FLAGS
flags.DEFINE_string('config_path', None,
                    'Path to json file containing config for combining files')


# get updated df from file path
def get_df_from_file(file_path: str, col_map: dict, output_columns: dict):
    df = pd.read_csv(file_path)
    df.rename(columns=col_map, inplace=True)
    for cur_col in output_columns:
        if cur_col not in df.columns:
            if 'required' not in output_columns[cur_col]:
                output_columns[cur_col]['required'] = False
            if output_columns[cur_col]['required']:
                raise ValueError(f'{cur_col} required but not found')
            else:
                if 'default_value' not in output_columns[cur_col]:
                    output_columns[cur_col]['default_value'] = ''
                df[cur_col] = output_columns[cur_col]['default_value']
    return df[list(output_columns)]


def write_combined_df(config_path: str):
    config_path = os.path.expanduser(config_path)
    with open(config_path) as fp:
        conf = json.load(fp)

    conf['input_files_expanded'] = {}
    df = pd.DataFrame()

    # get a list of files
    for cur_exp in conf['input_files']:
        # TODO cd to config path to get abs path
        _exp = os.path.expanduser(cur_exp)
        matching_files = glob.glob(_exp, recursive=True)
        for cur_file in matching_files:
            # set of files
            if cur_file not in conf['input_files_expanded']:
                conf['input_files_expanded'][cur_file] = conf['input_files'][
                    cur_exp]

    for cur_file in conf['input_files_expanded']:
        cur_df = get_df_from_file(cur_file,
                                  conf['input_files_expanded'][cur_file],
                                  conf['output_columns'])
        # concat df
        df = pd.concat([df, cur_df])

    # write to output
    output_path = conf['output_file']
    output_path = os.path.expanduser(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(conf['output_file'], index=False)


def main(argv):
    write_combined_df(FLAGS.config_path)


if __name__ == '__main__':
    flags.mark_flags_as_required(['config_path'])
    app.run(main)
