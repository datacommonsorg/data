# Copyright 2023 Google LLC
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
"""
Author: Suhana Bedi
Date: 02/20/2023
Name: format_variants 
Description: converts a .tsv from PharmGKB into a clean csv format, 
where each columns contains linkages or references to only 
database only for the purpose of clarity and understanding
@file_input: input .tsv from PharmGKB
@file_output: formatted .csv with PharmGKB and other database annotations
"""
import pandas as pd 
import numpy as np
import sys

def format_cols(df):
	"""
	Formats the variants dataframe and generates dcid
	Args:
		df = unformatted dataframe
	Returns:
		df = formatted dataframe
	"""
	df = df[['Variant ID', 'Variant Name']]
	df['dcid'] = 'bio/' + df['Variant Name']
	return df 

def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep = '\t')
	df = format_cols(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')


if __name__ == '__main__':
	main()