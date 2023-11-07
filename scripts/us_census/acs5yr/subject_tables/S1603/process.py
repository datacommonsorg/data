"""Process data from Census ACS5Year Subject Table S1603."""
import os
import sys
import pandas as pd
import numpy as np
from absl import app, flags
import json

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

#pylint: disable=wrong-import-position
#pylint: disable=import-error
_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../', 'common'))

from data_loader import SubjectTableDataLoaderBase  # commit hash - aee443ee
from resolve_geo_id import convert_to_place_dcid
from generate_col_map import process_zip_file
#pylint: enable=wrong-import-position
#pylint: enable=import-error
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
# flags.DEFINE_string(
#     'output_dir',
#     '/Users/sanikap/Desktop/ACS/data/scripts/us_census/acs5yr/output_files/',
#     'Path to the output directory')
flags.DEFINE_boolean(
    'has_percent', False,
    '[for processing]Specify the datasets has percentage values that needs to be convered to counts'
)
flags.DEFINE_boolean(
    'debug', False,
    '[for processing]set the flag to add additional columns to debug')


class S1603SubjectTableDataLoader(SubjectTableDataLoaderBase):
    """
    A child class for the S1603 import.
    """

    def _process_dataframe(self, df, filename):
        """processes a dataframe read from a csv file"""
        df = self._replace_ignore_values_with_nan(
            df)  #handle the values to be ignored
        year = filename.split(f'ACSST{self.estimate_period}Y')[1][:4]
        print(f"Processing: {filename}", end=" |  ", flush=True)
        # if has_percent is set, convert percentages to counts. Requires the
        # 'denominators' key to be specified in the spec
        percent_years = ['2014', '2013', '2012', '2011', '2010']
        if self.has_percent and year in percent_years:
            print(" Converting percent to number", end=" |  ", flush=True)
            df = self._convert_percent_to_numbers(df)

        # if column map is not available generate, will rarely be False
        column_map = self.column_map[year]

        # add stats to dict_counter for current year
        self.counter_dict[year] = {
            "filename":
                filename,
            "number of columns in dataset":
                df.shape[1],
            "number of rows in dataset":
                df.shape[0],
            "number of statVars generated for columns":
                len(list(column_map.keys())),
            "number of observations":
                0,
            "number of unique StatVars with observations":
                0,
        }

        csv_file = open(self.clean_csv_path, 'a')
        column_headers = list(df.columns.values)
        if 'Geography' in column_headers:
            place_geoIds = df['Geography'].apply(convert_to_place_dcid)
        else:
            place_geoIds = df['id'].apply(convert_to_place_dcid)

        # update the clean csv
        for column in df.columns.tolist():
            if column in column_map:
                obs_df = pd.DataFrame(columns=self.csv_columns)
                obs_df['Place'] = place_geoIds
                obs_df['StatVar'] = column_map[column]['Node']
                obs_df['Quantity'] = df[column].values.tolist()
                # add unit to the csv
                try:
                    unit = column_map[column]['unit']
                    del column_map[column]['unit']
                except KeyError:
                    unit = np.nan
                obs_df['Unit'] = unit

                # add scaling factor to the csv
                try:
                    scalingFactor = column_map[column]['scalingFactor']
                    del column_map[column]['scalingFactor']
                except KeyError:
                    unit = np.nan
                    scalingFactor = np.nan

                # if StatVar not in mcf_dict, add dcid
                dcid = column_map[column]['Node']

                if dcid not in self.mcf_dict:
                    ## key --> node dcid
                    self.mcf_dict[dcid] = {}
                    ## add pvs to dict
                    for key, value in column_map[column].items():
                        if key != 'Node':
                            self.mcf_dict[dcid][key] = value

                obs_df['ScalingFactor'] = scalingFactor
                obs_df['Year'] = year
                obs_df['Column'] = column

                # Replace empty places (unresolved geoIds) as null values
                obs_df['Place'].replace('', np.nan, inplace=True)

                # Drop rows with observations for empty (null) values
                obs_df.dropna(subset=['Place', 'Quantity'],
                              axis=0,
                              inplace=True)

                # Write the processed observations to the clean_csv
                if self.year_count == 0:
                    obs_df.to_csv(csv_file, header=True, index=False, mode='w')
                else:
                    obs_df.to_csv(csv_file, header=False, index=False, mode='a')
                self.year_count += 1

                # update stats for the year:
                self.counter_dict[year]["number of unique geos"] = len(
                    obs_df['Place'].unique())
                self.counter_dict[year][
                    "number of observations"] += obs_df.shape[0]
                self.counter_dict[year][
                    "number of unique StatVars with observations"] += len(
                        obs_df['StatVar'].unique())
                self.counter_dict[year]["number of StatVars in mcf_dict"] = len(
                    list(self.mcf_dict.keys()))
        csv_file.close()
        print(
            f" Completed with { self.counter_dict[year]['number of observations'] } observation for { self.counter_dict[year]['number of unique StatVars with observations'] } StatVars at { self.counter_dict[year]['number of unique geos'] } places. ",
            flush=True)


def set_column_map(input_path, spec_path, output_dir):
    generated_col_map = process_zip_file(input_path,
                                         spec_path,
                                         write_output=False)
    f = open(os.path.join(output_dir, 'column_map.json'), 'w')
    json.dump(generated_col_map, f, indent=4)
    f.close()


def main(argv):
    option = FLAGS.option.lower()
    table_prefix = FLAGS.table_prefix
    spec_path = FLAGS.spec_path
    input_path = FLAGS.input_path
    output_dir = FLAGS.output_dir
    has_percent = FLAGS.has_percent
    debug = FLAGS.debug

    set_column_map(input_path, spec_path, output_dir)
    data_loader = S1603SubjectTableDataLoader(table_id='S1603',
                                              col_delimiter='!!',
                                              has_percent=True,
                                              debug=True,
                                              output_path_dir=output_dir,
                                              json_spec=spec_path,
                                              column_map_path=os.path.join(
                                                  output_dir,
                                                  'column_map.json'),
                                              decimal_places=3,
                                              estimate_period=5,
                                              header_row=1)
    data_loader._process_zip_file(input_path)


if __name__ == '__main__':
    flags.mark_flags_as_required(
        ['table_prefix', 'spec_path', 'input_path', 'output_dir'])
    app.run(main)