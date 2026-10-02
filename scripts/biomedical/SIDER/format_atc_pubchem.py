# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Author: Suhana Bedi
Date: 08/07/2023
Name: format_atc_pubchem.py
Description: converts one input drug_atc.tsv into a formatted 
formatted_pubchem_atc.csv file, converting PubChem Compound IDs
and ATC codes into dcids
@file_input: input .tsv with PubChem and ATC codes
@file_output: output .csv with PubChem and ATC dcids
'''

import pandas as pd
import numpy as np
import sys

def check_for_illegal_charc(s):
    """Checks for illegal characters in a string and prints an error statement if any are present
    Args:
        s: target string that needs to be checked
    
    """
    list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)

def check_for_dcid(row):
    check_for_illegal_charc(str(row['PubChem']))
    check_for_illegal_charc(str(row['ATC']))
    return row

def wrapper_fun(df):
	df.columns = ['PubChem', 'ATC']
	df['CompoundID'] = df['PubChem']
	df['PubChem'] = 'chem/' + df['PubChem'].astype(str)
	df['ATCCode'] = df['ATC']
	df['ATC'] = 'chem/' + df['ATC'].astype(str)
	df['ATCParent'] = 'dcid:chem/' + df['ATCCode'].str[:-2]
	df.loc[df["ATCParent"] == "dcid:chem/L01XE", "ATCParent"] = "dcid:chem/L01X"
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df 

def main():
	df_atc_drug = pd.read_csv('drug_atc.tsv', sep = '\t', header=None)
	df_atc_drug = wrapper_fun(df_atc_drug)
	df_atc_drug.to_csv('formatted_pubchem_atc.csv')

if __name__ == "__main__":
	main()