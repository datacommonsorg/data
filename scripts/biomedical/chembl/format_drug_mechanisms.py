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

import pandas as pd
import numpy as np
import sys
import json

DRUG_TYPE_DICT = {
	"-1:Unknown": "dcs:DrugTypeUnknown",
	"10:Polymer": "dcs:DrugTypePolymer",
	"1:Synthetic Small Molecule": "dcs:DrugTypeSmallMolecule",
	"2:Enzyme": "dcs:DrugTypeEnzyme",
	"3:Oligosaccharide": "dcs:DrugTypeOligosaccharide",
	"4:Oligonucleotide": "dcs:DrugTypeOligonucleotide",
	"5:Oligopeptide": "dcs:DrugTypeOligopeptide",
	"6:Antibody": "dcs:DrugTypeAntibody",
	"7:Natural Product-derived": "dcs:DrugTypeNaturalProductDerived",
	"8:Cell-based": "dcs:DrugTypeCellBased",
	"9:Inorganic":"dcs:DrugTypeInorganic"
}

DICT_AVAILABILITY = {'Unknown':'dcs:DrugAvailabilityTypeUnknown',
 'Prescription Only':'dcs:DrugAvailabilityTypePrescriptionOnly',
 'Withdrawn':'dcs:DrugAvailabilityTypeWithdrawn',
 'Discontinued':'dcs:DrugAvailabilityTypeDiscontinued',
 'Over the Counter':'dcs:DrugAvailabilityTypeOverTheCounter'}

DICT_DRUG_PHASE = {
	0:'DrugDevelopmentPhase0',
	1:'DrugDevelopmentPhase1',
	2:'DrugDevelopmentPhase2',
	3:'DrugDevelopmentPhase3',
	4:'DrugDevelopmentPhase4'
}

def check_for_illegal_charc(s):
	"""Checks for illegal characters in a string and prints an error statement if any are present
	Args:
		s: target string that needs to be checked
	
	"""
	list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)

def convert_json_to_dict(file_input):
	file = open(file_input, 'r')
	json_data = json.load(file)
	return json_data

def format_compound_synonyms(df):
	# drop the columns used in other imports and not required in this one
	df = df.drop(columns = ['USAN Definition', 'USAN Stem - Substem', 'Level 4 ATC Codes', 'Level 3 ATC Codes', 'Level 2 ATC Codes', 'Level 1 ATC Codes'])
	# explode the synonyms into different rows for a specific compound
	df = df.assign(Synonyms=df.Synonyms.str.split("|")).explode('Synonyms')
	df.reset_index(drop=True, inplace=True)
	df.rename(columns={'Research Codes': 'Codes'}, inplace=True)
	# explode the research codes into different rows for a specific compound
	df = df.assign(Codes=df.Codes.str.split("|")).explode('Codes')
	df.reset_index(drop=True, inplace=True)
	# remove the synonyms already present in codes (research codes) column
	df = df.query("Synonyms != Codes")
	list_codes = list(df['Codes'].unique())
	list_codes.remove(np.nan)
	df = df[~df.Synonyms.isin(list_codes)]
	return df

def split_rows(df):
	# rename the columns and explode the rows on the semi-colons
	df = df.rename(columns={'Indication Class':'IndicationClass', 'Withdrawn Class':'WithdrawnClass', 'Withdrawn Reason':'WithdrawnReason', 'Withdrawn Country':'WithdrawnCountry', 'USAN Stem':'USANStem', 'ATC Codes':'ATC', 'Drug Applicants':'DrugApplicants'})
	df = df.assign(IndicationClass=df.IndicationClass.str.split(";")).explode('IndicationClass')
	df = df.assign(WithdrawnClass=df.WithdrawnClass.str.split(";")).explode('WithdrawnClass')
	df = df.assign(WithdrawnReason=df.WithdrawnReason.str.split(";")).explode('WithdrawnReason')
	df = df.assign(WithdrawnCountry=df.WithdrawnCountry.str.split(";")).explode('WithdrawnCountry')
	df = df.assign(DrugApplicants=df.DrugApplicants.str.split("|")).explode('DrugApplicants')
	## different delimiter for ATC codes
	df = df.assign(ATC=df.ATC.str.split("|")).explode('ATC')
	df = df.replace(',','', regex=True)
	return df

def format_numeric_cols(df):
	df['First Approval'] = df['First Approval'].astype(str).apply(lambda x: x.replace('.0',''))
	df['USAN Year'] = df['USAN Year'].astype(str).apply(lambda x: x.replace('.0',''))
	return df

def format_boolean_cols(df):
	list_bool_cols = ['Passes Rule of Five', 'Oral', 'Parenteral', 'Topical', 'Black Box']
	for i  in list_bool_cols:
		df[i] = df[i].map({0: 'False', 1: 'True'})
	list_uncertain_bool_cols = ['First In Class', 'Prodrug']
	for x  in list_uncertain_bool_cols:
		df[x] = df[x].map({0: 'False', 1: 'True', -1: np.nan})
	return df

def format_enum_cols(df):
	df['Chirality'] = df['Chirality'].str.replace(" ", "", regex=True)
	df['Chirality'] = 'dcs:ChemicalCompoundChiralityType' + df['Chirality'].astype(str)
	df["Drug Type"] = df["Drug Type"].map(DRUG_TYPE_DICT)
	df['Availability Type'] = df['Availability Type'].map(DICT_AVAILABILITY)
	df['Phase'] = df['Phase'].map(DICT_DRUG_PHASE)
	return df

def format_usan_atc(df):
	df = df.replace({'\'': '', ';':''}, regex=True)
	df['USANStem'] = df['USANStem'].str.split(' ', n=1).str[0]
	df['USANStem'] = df['USANStem'].str.replace('-','')
	df['USANStem'] = 'chem/' + df['USANStem'].astype(str)
	df['USANStem'] = df['USANStem'].str.replace('chem/vir fos','chem/vir')
	df['USANStem'] = df['USANStem'].replace('chem/nan',np.nan)
	df['USANStemName'] = df['USANStem'].str[5:]
	df['ATCCode'] = df['ATC']
	df['ATC'] = 'chem/' + df['ATC']
	df['ATC'] = df['ATC'].replace('chem/nan',np.nan)
	return df

def format_cols(df):
	df = format_numeric_cols(df)
	df = format_boolean_cols(df)
	df = format_enum_cols(df)
	df = format_usan_atc(df)
	df = df.drop_duplicates()
	list_cols = ['ATC', 'WithdrawnReason', 'WithdrawnCountry', 'WithdrawnClass']
	for i in list_cols:
		df[i] = df[i].str.strip()
		df[i] = df[i].str.replace(' ', '')
	df['WithdrawnClass'] = df['WithdrawnClass'].str.title()
	df['WithdrawnClass'] = df['WithdrawnClass'].str.replace('None', 'Unknown')
	df['WithdrawnClass'] = 'dcs:DrugWithdrawnClassType' + df['WithdrawnClass']
	dict_pubchem_chembl = convert_json_to_dict('chembl-pubchem-mapping.json')
	dict_pubchem_chembl = dict([(value, key) for key, value in dict_pubchem_chembl.items()])
	df['dcid'] = df['Parent Molecule'].map(dict_pubchem_chembl).fillna('chem/' + df['Parent Molecule'].astype(str))
	df = df.replace(to_replace = ['nan', 'None'], value =np.nan)
	return df

def format_string_cols(df):
	df.update('"' +
			  df[['Synonyms', 'Codes', 'DrugApplicants', 'IndicationClass', 'Patent', 'Drug Type', 'Chirality', 'Availability Type', 'Withdrawn Year', 'WithdrawnReason', 'WithdrawnCountry', 'WithdrawnClass', 'Smiles']].astype(str) + '"')
	df.replace("\"nan\"", np.nan, inplace=True)
	return df 

def check_for_dcid(row):
	check_for_illegal_charc(str(row['dcid']))
	check_for_illegal_charc(str(row['USANStem']))
	check_for_illegal_charc(str(row['ATC']))
	return row

def driver_function(df):
	df = format_compound_synonyms(df)
	df = split_rows(df)
	df = format_cols(df)
	df = format_string_cols(df)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df

def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input, sep='\t')
	df = driver_function(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')
	


if __name__ == '__main__':
	main()