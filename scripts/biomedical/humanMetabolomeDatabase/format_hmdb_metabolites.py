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
'''
Author: Suhana Bedi
Date: 07/23/2021
Name: format_hmdb_metabolites.py
Description: Add dcids for all the metabolites in the Human Metabolome database. 
Add the suitable enum keywords to columns which are represented as enums 
in the data commons schema. 
@file_input: input .csv from hmdb_metabolite_add_chembl.py
@file_output: csv output file with dcids and enum keywords added
'''
import sys
import pandas as pd


def main():

    file_input = sys.argv[1]
    file_output = sys.argv[2]
    df = pd.read_csv(file_input)

    # Add dcid
    df['Id'] = 'bio/' + df['accession'].astype(str)

    # Add enum keywords
    enum_dict = {
        'kingdom': 'dcs:ChemicalCompoundCategory',
        'direct_parent': 'dcs:ChemicalCompoundParent',
        'super_class': 'dcs:ChemicalCompoundSuperClass',
        'class': 'dcs:ChemicalCompoundClass',
        'sub_class': 'dcs:ChemicalCompoundSubClass',
        'molecular_framework': 'dcs:ChemicalCompoundMolecularFramework'
    }

    for i in enum_dict:
        df[i] = df[i].str.lower()
        df[i] = df[i].str.replace(' ', '_')
        df[i] = df[i].str.replace(',', '')
        df[i] = enum_dict.get(i) + df[i].astype(str)
        nan_remove = enum_dict.get(i) + 'nan'
        df[i] = df[i].str.replace(nan_remove, '')

    df.update(
        '"' +
        df[['iupac_name', 'name', 'chebi_id', 'drugbank', 'smiles', 'chembl'
           ]].astype(str) + '"')
    df.to_csv(file_output)


if __name__ == "__main__":
    main()
