# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import json
import pandas as pd

from absl import app
from absl import flags

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
default_output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "output")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")
flags.DEFINE_string("output_path", default_output_path, "Import Data File's List")

class SubnationalPopulation:
    def __init__(self,
                 input_files: list,
                 output_path: str) -> None:
        self._input_files = input_files
        self._output_path = output_path
        self._final_df = pd.DataFrame()

    def _convert_area_code(self, df: pd.DataFrame):
        """
        Reads the file data and cleans it for concatenation
        in Final CSV.

        Args:
            df (pd.DataFrame): input df for changing column.

        Returns:
            df (pd.DataFrame): provides the df with changed column.
        """
        json_address = os.path.join(os.path.dirname(os.path.abspath(__file__)),'countrystatecode.json')
        with open(json_address) as json_file:
            data = json.load(json_file)
        df = df.replace({"Country Name":data})
        return df

    def _process_file(self,file_path: str):
        """
        Reads the file data and cleans it for concatenation
        in Final CSV.

        Args:
            file_path (str): path to csv file as the input

        Returns:
            df (pd.DataFrame): provides the cleaned df as output
        """
        df = pd.read_excel(file_path,skipfooter=5)
        df = df.drop(columns=['Series Name','Series Code','Level_attr','Country Code'])
        df = df.melt(id_vars=['Country Name'],
                         var_name='year',
                         value_name='Count_Person')
        df['year']=df['year'].str[:4]
        df = self._convert_area_code(df)
        return df

    
    def parse_source_files(self):
        """
        Reads the files present in the input folder. Calls the appropriate
        function based on the type of file and procceses it.

        Args:
            None

        Returns:
            None
        """
        for file_path in self._input_files:
            df = self._process_file(file_path)
            self._final_df = pd.concat([self._final_df, df])


def main(_):
    input_path = _FLAGS.input_path
    output_path = _FLAGS.output_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    loader = SubnationalPopulation(ip_files, output_path)
    loader.parse_source_files()


if __name__ == '__main__':
    app.run(main)