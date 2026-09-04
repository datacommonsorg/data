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
Date: 01/18/2023
Name: format_atc
Description: converts a .csv file containing ATC (Anatomical Therapeutic Chemical code) codes, its daily dosage, unit of measurement.  
@file_input: input .csv from ATC codes scraped from WHO website
@file_output: formatted .csv with ATC codes with dcids, 5 atc levels
"""
ADM_R_ENUM_DICT = {'"Inhal. powder"': "dcs:AdministrationRouteRespiratory",
'Chewing gum': "dcs:AdministrationRouteOral",
'Inhal': "dcs:AdministrationRouteRespiratory",
'Inhal.aerosol': "dcs:AdministrationRouteRespiratory",
'Inhal.powder': "dcs:AdministrationRouteRespiratory",
'Inhal.solution': "dcs:AdministrationRouteRespiratory",
'Instill.solution': "dcs:AdministrationRouteNasal",
'N': "dcs:AdministrationRouteNasal",
'O': "dcs:AdministrationRouteOral",
'P': "dcs:AdministrationRouteParenteral",
'R': "dcs:AdministrationRouteRectal",
'SL': "dcs:AdministrationRouteSublingual,AdministrationRouteBuccal",
'TD': "dcs:AdministrationRouteTransdermal",
'V': "dcs:AdministrationRouteVaginal",
'implant': "dcs:AdministrationRouteImplantation",
'intravesical': "dcs:AdministrationRouteIntravesical",
'lamella': "dcs:AdministrationRouteTopical",
'ointment': "dcs:AdministrationRouteTopical",
'oral aerosol': "dcs:AdministrationRouteOral",
's.c. implant': "dcs:AdministrationRouteImplantation",
'urethral':"dcs:AdministrationRouteUrethral"}

DOSAGE_FORM_ENUM_DICT = {'"Inhal. powder"': "dcs:DosageFormAerosolPowder",
'Chewing gum': "dcs:DosageFormGumChewing",
'Inhal.aerosol': "dcs:DosageFormAerosol",
'Inhal.powder': "dcs:DosageFormAerosolPowder",
'Inhal.solution': "dcs:DosageFormSolution",
'Instill.solution': "dcs:DosageFormSolution",
'lamella': "dcs:DosageFormLamella",
'oral aerosol': "dcs:DosageFormAerosol",
's.c. implant': "dcs:DosageFormImplant"
}

UOM_ENUM_DICT = {'LSU': 'LipoproteinLipaseReleasingUnits',
'MU': 'Units',
'TU': 'Units',
'U': 'Units',
'g': 'Grams',
'mcg': 'Micrograms',
'mg': 'Milligrams',
'ml': 'Milliliters',
'mmol': 'Millimolar'
}

# import the required packages
import pandas as pd
import numpy as np
import sys 

#Disable false positive index chaining warnings
pd.options.mode.chained_assignment = None

def check_for_illegal_charc(s):
	list_illegal = ["'", "*" ">", "<", "@", "]", "[", "|", ":", ";" " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)

def isNaN(var):
    return var != var

def format_atc_name(df):
	"""Formats the ATC code names for each of the compounds
	Args:
		df: dataframe with atc names 
	Returns:
		df: dataframe with formatted atc names 
	
	"""
	df['atc_name'] = df['atc_name'].str.replace(r"[\"]", '', regex=True) ## replaces all quotes with empty value
	df['atc_name'] = df['atc_name'].str.lower() ## makes all names lowercase
	return df

def format_atc_levels(df):
	"""Splits the ATC codes into 5 different levels based on characters and string length
	Args:
		df: dataframe with atc codes
	Returns:
		df: dataframe with atc codes split in 5 different levels
	
	"""
	df['specialization'] = np.nan
	for index,row in df.iterrows():
		val = df.loc[index, 'atc_code']
		val = str(val)
		if(len(val) == 1):
			df.loc[index, 'specialization'] = np.nan
		elif(len(val) == 3):
			df.loc[index, 'specialization'] = val[0]
		elif(len(val) == 4):
			df.loc[index, 'specialization'] = val[0:3]
		elif(len(val) == 5):
			df.loc[index, 'specialization'] = val[0:4]
		else:
			df.loc[index, 'specialization'] = val[0:5]
	df['specialization'] = 'chem/' + df['specialization']
	df.replace("chem/nan", np.nan, inplace=True)
	return df

def format_cols(df):
	for index,row in df.iterrows():
		if (df.loc[index, 'atc_code'] == 'B01AF03'):
			df.loc[index, 'ddd'] = df.loc[index, 'uom']
			df.loc[index, 'uom'] = df.loc[index, 'adm_r']
			df.loc[index, 'adm_r'] = df.loc[index, 'note']
			df.loc[index, 'note'] = np.nan
		if(df.loc[index, 'uom'] == 'tablet'):
			df.loc[index, 'uom'] = np.nan
			df.loc[index,'ddd'] = np.nan
			df.loc[index,'dosageForm'] = 'DosageFormTablet'
		if(isNaN(df.loc[index, 'uom']) | isNaN(df.loc[index, 'ddd'])):
			df.loc[index, 'ddd'] = np.nan
			df.loc[index, 'uom'] = np.nan
		if(df.loc[index, 'uom'] == 'MU'):
			df.loc[index, 'ddd'] = 1000000 * df.loc[index, 'ddd']
		if(df.loc[index, 'uom'] == 'MU'):
			df.loc[index, 'ddd'] = 1000 * df.loc[index, 'ddd']    
	return df

def format_enums(df):
	df["adm_r_enum"]=df['adm_r'].map(ADM_R_ENUM_DICT)
	df['dosageForm']= df['adm_r'].map(DOSAGE_FORM_ENUM_DICT)
	df['uom']= df['uom'].map(UOM_ENUM_DICT)
	return df

def format_quantity_node(df):
    df['quantity_dcid'] = df['uom'].fillna('').astype(str) + df['ddd'].fillna('').astype(str)
    df['quantity_name'] = df['uom'].fillna('').astype(str) + ' ' +  df['ddd'].fillna('').astype(str)
    return df

def check_for_illegal_charc(s):
	list_illegal = ["'", "#", "–", "*" ">", "<", "@", "]", "[", "|", ":", ";", " "]
	if any([x in s for x in list_illegal]):
		print('Error! dcid contains illegal characters!', s)

def check_for_dcid(row):
	check_for_illegal_charc(str(row['uom']))
	check_for_illegal_charc(str(row['quantity_dcid']))
	check_for_illegal_charc(str(row['dcid']))
	return row

def driver_function(df):
	"""Runs all the required functions for data processing in the right order
	Args:
		df: dataframe with unprocessed data
	Returns:
		df: dataframe with fully processed data
	
	"""
	df = format_atc_name(df)
	df = format_atc_levels(df)
	df = format_cols(df)
	df = format_enums(df)
	df = format_quantity_node(df)
	df['dcid'] = 'chem/' + df['atc_code']
	df.update('"' +
			  df[['atc_name', 'uom', 'adm_r', 'note', 'quantity_dcid', 'quantity_name']].astype(str) + '"')
	df.replace("\"nan\"", np.nan, inplace=True)
	df = df.apply(lambda x: check_for_dcid(x),axis=1)
	return df


def main():
	file_input = sys.argv[1]
	file_output = sys.argv[2]
	df = pd.read_csv(file_input)
	df = driver_function(df)
	df.to_csv(file_output, doublequote=False, escapechar='\\')
	

if __name__ == '__main__':
	main()