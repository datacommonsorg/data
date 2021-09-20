"""Process data from Census ACS5Year Subject Table S1702."""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
import sys

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '..'))

from common import data_loader

_SPEC_PATH = 'config.json'
_OUTPUT_PATH = 'output/'
_ZIP_PATH = 'testdata/alabama.zip'


class S1702TableDataLoader(data_loader.SubjectTableDataLoaderBase):
    """
    A child class for the S1702 import.
    """
    def _convert_percent_to_numbers(self, df):
        df_columns = df.columns.tolist()
        for count_col, percent_col_list in self.features['denominators'].items():
            if count_col in df_columns:
                for col in percent_col_list:
                    if col in df_columns:
                        df[col] = df[col].astype(float)
                        df[count_col] = df[count_col].astype(float)
                        df[col] = (df[col] / 100) * df[count_col]
                        df[col] = df[col].round(3)
        return df


if __name__ == "__main__":
    data_loader_obj = S1702TableDataLoader(table_id='S1702',
                                           estimate_period=5,
                                           json_spec_path=_SPEC_PATH,
                                           output_dir_path=_OUTPUT_PATH,
                                           zip_file_path=_ZIP_PATH)
