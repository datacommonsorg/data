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
import os
import pandas as pd
from absl import flags, app

from place_to_dcid import PLACE_MAP

_TEMPLATE_MCF = """
Node: E:SubjectTable->E0
typeOf: dcs:StatVarObservation
measurementMethod: dcs:Aggregate_NCHS013_BRFSS2016To2018
observationAbout: C:SubjectTable->observationAbout
observationDate: C:SubjectTable->observationDate
variableMeasured: C:SubjectTable->variableMeasured
value: C:SubjectTable->value
scalingFactor: C:SubjectTable->scalingFactor
"""

_SV_MCF = """Node: dcid:StandardError_Person_Children_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
statType: dcs:stdError
age: [- 18 Years]
healthOutcome: dcs:Asthma

Node: dcid:Percent_Person_Children_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
statType: dcs:measuredValue
measuredProperty: dcs:count
age: [- 18 Years]
healthOutcome: dcs:Asthma
measurementDenominator: dcs:Count_Person_Upto18Years

Node: dcid:StandardError_Person_Adults_WithAsthma
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
statType: dcs:stdError
age: [18 - Years]
healthOutcome: dcs:Asthma
"""

def get_statvar_dcid(row):
	if row['Age Group'] == 'Adult' and row['column_name'] == 'Prevalence':
		return 'Percent_Person_WithAsthma'
	if row['Age Group'] == 'Adult' and row['column_name'] == 'Error':
		return 'StandardError_Person_Adults_WithAsthma'
	if row['Age Group'] == 'Child' and row['column_name'] == 'Prevalence':
		return 'Percent_Person_Children_WithAsthma'
	if row['Age Group'] == 'Child' and row['column_name'] == 'Error':
		return 'StandardError_Person_Children_WithAsthma'

def associate_place_dcids(row):
	county_suffixes = ['Municipality', 'Census Area', 'County', 'Parish', 'Borough', 'District', 'city']
	counties_in_states = PLACE_MAP[row['Alpha2']]

	county_name = row['Counties']
	county_name = county_name.replace('City and Borough', 'Borough')
	county_name = county_name.replace(',', '')

	if not any([suffix for suffix in county_suffixes if suffix in county_name]):
		county_name = county_name + ' County'

	if county_name in counties_in_states.keys():
		return counties_in_states[county_name]
	else:
		print(f"No matches were found for {county_name}, {row['State']} ({row['Alpha2']})")
		return ''
	
	
def make_extract_df_readable(clean_df):
	# forward fill
	clean_df = clean_df.assign(Counties=clean_df.Counties.str.split(', ')).explode('Counties', ignore_index=False)
	
	# make prevelance and error as separate columns
	clean_df['Prevalence'] = clean_df['Prevalence, % (SE)'].str.extract(r'(\d+.\d+)').astype('float')
	clean_df['Error'] = clean_df['Prevalence, % (SE)'].str.extract(r'\((\d+.\d+)').astype('float')
	clean_df.drop(columns=['Prevalence, % (SE)'], inplace=True)
	
	# unpivot the column
	clean_df = clean_df.melt(id_vars=['Counties', 'Age Group', 'State', 'Alpha2'], value_vars=['Prevalence', 'Error'], var_name='column_name', value_name='value')
	
	# assign statvars based on age_group and column_name
	clean_df['variableMeasured'] = clean_df.apply(get_statvar_dcid, axis=1)
	clean_df['scalingFactor'] = clean_df['variableMeasured'].apply(lambda e: 100 if 'Children_WithAsthma' in e else '')
	
	# drop empty county
	clean_df = clean_df[clean_df['Counties']!='']

	# assign place ids to the county names
	clean_df['observationAbout'] = clean_df.apply(associate_place_dcids, axis=1)
	clean_df = clean_df[clean_df['observationAbout']!='']
	clean_df['observationDate'] = '2018'

	return clean_df
	
def main(_):
	filename_prefix = "brfss_asthma"
	## process the extracted tabular data
	df = pd.read_csv("./data/Extracted_State-maps-for-asthma-prevalence-by-six-level-urban-rural-classification-2016-2018.tsv", sep="\t")
	df = make_extract_df_readable(df)
	df.to_csv(f"{filename_prefix}.csv", index=False)

	## write template mcf and statvar mcf file
	f = open(f"{filename_prefix}.tmcf", "w")
	f.write(_TEMPLATE_MCF)
	f.close()

	f = open(f"{filename_prefix}.mcf", "w")
	f.write(_SV_MCF)
	f.close()
	
	

if __name__ == '__main__':
	app.run(main)

