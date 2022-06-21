"""One-off script to get columns across all years in a zip file and summarize
it in a csv"""

import os
import json
import pandas as pd

from absl import flags, app
from zipfile import ZipFile

FLAGS = flags.FLAGS

flags.DEFINE_string('zip_file_path', './s0505/s0505_state_county_places.zip', 'Path to the input zip file')
flags.DEFINE_string('table_id', 's0505', 'Table ID')
flags.DEFINE_integer('header', 1, 'Row index of the csv with table header')
flags.DEFINE_string('output_dir_path', './', 'Path to store output csv')


def _get_column_names_across_years(zip_file_path,
                                   table_id,
                                   header=1,
                                   output_dir_path='./'):
    """utility function that goes over all files in the zipfile to populate
  column names per year in a pandas dataframe.

  Arguments:
    zip_file_path: path to the zip file
    table_id: ID of the table
    header: row index that needs to be considered as column header. (default:2)
    output_dir_path: path where the output csv is to be saved. (default: ./)
  """
    df = pd.DataFrame(columns=[
        '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018',
        '2019'
    ])
    dict_col = {
    	"all": []
    }
    zf = ZipFile(zip_file_path)
    for filename in zf.namelist():
        if 'data_with_overlays' in filename:
            data_df = pd.read_csv(zf.open(filename, 'r'),
                                  header=header,
                                  low_memory=False)
            year = filename.split(f'ACSST5Y')[1][:4]
            data_df = data_df.dropna(axis=0)
            print(year, len(data_df['id'].unique()))
            dict_col[year] = data_df.columns.tolist()
            dict_col['all'].append(data_df.columns.tolist())

    f = open("s0505/s0505_yearwise_columns.json", "w")
    json.dump(dict_col, f, indent=4)
    f.close()


def main(argv):
    """main method"""
    _get_column_names_across_years(FLAGS.zip_file_path,
                                   FLAGS.table_id,
                                   header=FLAGS.header,
                                   output_dir_path=FLAGS.output_dir_path)


if __name__ == "__main__":
    flags.mark_flags_as_required(['zip_file_path', 'table_id'])
    app.run(main)
