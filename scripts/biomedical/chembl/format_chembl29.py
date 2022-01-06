# Copyright 2022 Google LLC
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
'''
Author: Suhana Bedi
Date: 01/01/2021
Name: format_chembl29.py
Description: Add dcids for all the proteins and format the corresponding canonical_smiles and InchiKey IDs.
@file_input: input .txt from chembl database
@file_output: csv output file with dcid column and other properly formatted columns
'''

import sys
import csv
import pandas as pd


def format_col(df):
    """
    Format the columns of the input dataframe
    Args:
        df = chembl data
    Returns:
        chembl dataframe with formatted columns and added dcids
    """
    df['dcid'] = "bio/" + df['chembl_id'].astype(str)
    return df


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input, sep='\t')
    df = format_col(df)
    df.update('""' +
              df[['canonical_smiles', 'standard_inchi', 'standard_inchi_key'
                 ]].astype(str) + '""')

    df.to_csv(file_output,
              index=None,
              quoting=csv.QUOTE_NONE,
              quotechar="",
              escapechar="\\")


if __name__ == '__main__':
    main()
