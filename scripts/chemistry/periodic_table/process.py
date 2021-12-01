# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Generate nodes for all elements in the periodic table.
"""

import numpy as np
import pandas as pd

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_list('input_csv', 'periodic_table.csv,compounds.csv',
                  'CSV file with properties of all elements.')
flags.DEFINE_string('output_prefix', 'substance',
                    'Output path for csv and tmcf files.')

_OUTPUT_COLUMNS = [
    'Name',
    'TypeOf',
    'ChemicalName',
    'Symbol',
    'Type',
    'AtomicNumber',
]

_NODE_TEMPLATE = """
Node: E:Substance->E0
typeOf: C:Substance->TypeOf
name: C:Substance->Name
chemicalName: C:Substance->ChemicalName
chemicalSymbol: C:Substance->Symbol
atomicNumber: C:Substance->AtomicNumber
chemicalSubstanceType: C:Substance->Type
"""


def _process_file(input_csv: str) -> pd.DataFrame:
    """Read the data from the input csv, clean it up and return a DataFrame

  Args:
    input_csv: CSV downloaded from the data source

  Returns:
    DataFrame with the output columns from the input
  """

    df = pd.read_csv(input_csv)

    # Remove extra whitespaces from string columns
    for col in ['Element', 'Symbol', 'Name', 'ChemicalName', 'Type', 'TypeOf']:
        if col in df:
            df[col] = df[col].str.strip()

    # Add Type for periodic table without TypeOf column
    if 'TypeOf' not in df:
        df['TypeOf'] = 'dcs:ChemicalElement'
    # Prepare the 'Type' column removing whitespaces and adding 'dcs:' prefix.
    if 'Type' in df:
        df['Type'] = df['Type'].apply(lambda t: 'dcs:' + t.replace(" ", "") if
                                      pd.notnull(t) and t.find(':') < 0 else '')

    # Add output columns
    if 'Name' not in df and 'Element' in df:
        df['Name'] = df['Element']

    if 'ChemicalName' not in df and 'Name' in df:
        df['ChemicalName'] = df['Name']

    return df


def process(input_csvs: list, output: str) -> None:
    """Read the data from the input csv, clean it up and generate the
  output csv and mcf with the required columns.

  Args:
    input_csv: CSV downloaded from the data source
    output: Output file prefix for generated csv and tmcf.
  """
    df_list = []
    for input_file in input_csvs:
        df_list.append(_process_file(input_file))

    # Merge DataFrames from all input files.
    df = pd.concat(df_list)

    # Get list of output columns available.
    output_columns = []
    for col in _OUTPUT_COLUMNS:
        if col in df:
            output_columns.append(col)

    # Write into the output csv
    df.to_csv(output + '.csv',
              columns=output_columns,
              index=False,
              header=True,
              mode='w')

    # Generate the tMCF file
    tmcf_file_path = output + '.tmcf'
    with open(tmcf_file_path, 'w', newline='') as f_out_tmcf:
        f_out_tmcf.write(_NODE_TEMPLATE)


def main(_) -> None:
    process(FLAGS.input_csv, FLAGS.output_prefix)


if __name__ == '__main__':
    app.run(main)
