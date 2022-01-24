from calendar import c
import json
import pandas as pd
import os
import json
import glob
from absl import app
from absl import flags

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
        matching_files = glob.glob(cur_exp, recursive=True)
        for cur_file in matching_files:
            # set of files
            if cur_file not in conf['input_files_expanded']:
                conf['input_files_expanded'][cur_file] = conf['input_files'][cur_exp]
    
    for cur_file in conf['input_files_expanded']:
        cur_df = get_df_from_file(cur_file, conf['input_files_expanded'][cur_file], conf['output_columns'])
        # concat df
        df = pd.concat([df, cur_df])
    
    # write to output
    df.to_csv(conf['output_file'], index=False)

def main(argv):
    write_combined_df(FLAGS.config_path)

if __name__ == '__main__':
  flags.mark_flags_as_required(['config_path'])
  app.run(main)