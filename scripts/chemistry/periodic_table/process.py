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

flags.DEFINE_string('input_csv', 'periodic_table.csv',
                    'CSV file with properties of all elements.')
flags.DEFINE_string('output_prefix', 'elements',
                    'Output path for csv and tmcf files.')

_OUTPUT_COLUMNS = [
    'AtomicNumber',
    'Element',
    'Symbol',
    'Type',
]

_NODE_TEMPLATE = """
Node: E:Elements->E0
typeOf: dcs:ChemicalElement
name: C:Elements->Element
chemicalName: C:Elements->Element
chemicalSymbol: C:Elements->Symbol
atomicNumber: C:Elements->AtomicNumber
chemicalSubstanceType: C:Elements->Type
"""

def process(input_csv: str, output: str) -> None:
  """Read the data from the input csv, clean it up and generate the
  output csv and mcf with the required columns.

  Args:
    input_csv: CSV downloaded from the data source
    output: Output file prefix for generated csv and tmcf.
  """

  df = pd.read_csv(input_csv)

  # Remove extra whitespaces
  for col in ['Element', 'Symbol']:
    df[col] = df[col].str.strip()

  # Clean the 'Type' column to remove whitespace and add 'dcs:' prefix.
  df['Type'] = df['Type'].apply(lambda t:
                                 'dcs:'+t.replace(" ", "") if pd.notnull(t) else '')

  # Write into the output csv
  df.to_csv(output + '.csv', columns = _OUTPUT_COLUMNS, index = False, header = True, mode = 'w')
  # Generate the tMCF file
  tmcf_file_path = output + '.tmcf'
  with open(tmcf_file_path, 'w', newline='') as f_out_tmcf:
      f_out_tmcf.write(_NODE_TEMPLATE)

def main(_) -> None:
  process(FLAGS.input_csv, FLAGS.output_prefix)

if __name__ == '__main__':
  app.run(main)
