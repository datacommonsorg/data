import numpy as np
import os
import sys
import re
import string
import datetime
import pandas as pd
from absl import app, flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(
    _SCRIPT_PATH, '../../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

FLAGS = flags.FLAGS

#TODO: Some of the functions defined here can be used while processing the annual tables and hence making the common functions as a module is preferred.

_TEMPLATE_MCF = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod 
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""

#NOTE: At the moment, we are ignoring the non-integer value of reported disease incidents.
_FORMAT_UNREPORTED_CASES = {
	'-': '',
	'U': '',
	'N': '',
	'NN': '',
	'NP': '',
	'NC': ''
}

#NOTE: A map for different 
_PV_MAP = {
	'confirmed': {
		'medicalStatus': 'dcs:ConfirmedCase'
	},
	'probable': {
		'medicalStatus': 'dcs:ProbableCase'
	},
	'pediatric mortality': {
		'medicalStatus': 'dcs:PediatricMortality'
	},
	'age <5': {
		'age': '[- 5 Years]'
	},
	'age < 5': {
		'age': '[- 5 Years]'
	},
	'all serotypes': {
		'seroTypes': 'dcs:AllSerotypes'
	},
	'serotype b': {
		'seroTypes': 'dcs:BSerotype'
	},
	'unknown serotype': {
		'seroTypes': 'dcs:UnknownSerotype'
	},
	'non-b serotype': {
		'seroTypes': 'dcs:NonBSerotype'
	},
	'other serogroups': {
		'seroGroups': 'dcs:OtherSerogroups'
	},
	'unknown serogroup': {
		'seroGroups': 'dcs:UnknownSerogroups'
	},
	'all serogroups': {
		'seroGroups': 'dcs:AllSerogroups'
	},
	'serogroups ACWY': {
		'seroGroups': 'dcs:ACWYSerogroups'
	},
	'serogroup B': {
		'seroGroups': 'dcs:BSerogroup'
	},
	'perinatal infection': {
		'medicalCondition': 'dcs:PerinatalInfection'
	},
	'acute': {
		'medicalCondition': 'dcs:Acute'
	},
	'chronic': {
		'medicalCondition': 'dcs:Chronic'
	},
	'imported': {
		'medicalCondition': 'dcs:Imported'
	},
	'indigenous': {
		'medicalCondition': 'dcs:Indigenous'
	},
	'clinical': {
		'medicalCondition': 'dcs:Clincial'
	}
}

#TODO: Resolve path based on the script path for tests
_PLACE_DCID_DF = pd.read_csv("./data/place_name_to_dcid.csv", usecols=["Place Name", "Resolved place dcid"])
_DISEASE_DCID_DF = pd.read_csv("./data/diseases_map_to_pvs.csv")

def set_observationPeriod(column_name):
	if 'quarter' in column_name:
		return 'P1Q'
	return 'P1W'

# adapted from https://github.com/reichlab/pymmwr
def _start_date_of_year(year: int) -> datetime.date:
    """
    Return start date of the year using MMWR week rules
    """

    jan_one = datetime.date(year, 1, 1)
    diff = 7 * (jan_one.isoweekday() > 3) - jan_one.isoweekday()

    return jan_one + datetime.timedelta(days=diff)

def get_mmwr_week_end_date(year, week)-> datetime.date:
    """
    Return date from epiweek (starts at Sunday)
    """

    day_one = _start_date_of_year(year)
    diff = 7 * (week - 1)

    return day_one + datetime.timedelta(days=diff)

def resolve_reporting_places_to_dcids(place):
	try:
		# remove non printable special characters from column name
		place = ''.join(filter(lambda x:x in string.printable, place))
		place = place.strip()
		return  _PLACE_DCID_DF.loc[(_PLACE_DCID_DF['Place Name']==place), 'Resolved place dcid'].values[0]
	except:
		# return empty string when no matches are found.
		return ''

def format_column_header(column_list):
	for index, col_name in enumerate(column_list):
		# remove non printable special characters from column name
		col_name = ''.join(filter(lambda x:x in string.printable, col_name))
		# remove the double spaces amd tab spaces to single space
		col_name = col_name.replace(' ;', ';')
		col_name = col_name.replace('  ', ' ')
		col_name = col_name.replace('  ;', ';')
		col_name = col_name.replace('\t', ' ')
		col_name = col_name.replace('\t. ', '. ')
		col_name = col_name.replace('cont"d', 'contd.')
		col_name = col_name.replace('(', '')
		col_name = col_name.replace(')', '')
		# update the column name
		column_list[index] = col_name.strip()
	# for some datasets the first column is poorly formatted
	column_list[0] = 'Reporting Area'
	return column_list

def concat_rows_with_column_headers(rows_with_col_names, df_column_list):
	# some tows have NaN as the first element, we replace it with ''
	rows_with_col_names = rows_with_col_names.fillna('')
	# works with table structure where column=0 is always the 'Reporting Area' and the the other columns are the case counts with different aggregations
	rows_with_col_names = rows_with_col_names.groupby(df_column_list[0])[df_column_list[1:]].agg(lambda d: ";".join(set(d))).reset_index()

	## some csvs do not have data and need will throw an exception when column names are flattened.
	try:
		## flatten column names to list
		column_list = rows_with_col_names.loc[0, :].values.flatten().tolist()
		## remove non-printable
		return column_list
	except:
		# Dataframe does not have any data points and is pobably a note. 
		return []




def process_nndss_weekly(input_filepath:str):
	## from the csv files get the year, and week count
	filename = input_filepath.split('/')[-1]
	year = int(filename[10:14])
	week = int(filename[25:27])

	## get the ending date for the week -- date is subject to the week definition in https://ndc.services.cdc.gov/wp-content/uploads/MMWR_Week_overview.pdf
	observation_date = get_mmwr_week_end_date(year, week)

	df = pd.read_csv(input_filepath, header=None)

	## fix the column names of the file - the head of the dataframe has all the rows that have the column name
	rows_with_col_names = df[(df[0] == 'Reporting Area') | (df[0] == 'Reporting  Area') | (df[0] == 'Reporting area') | (df[0] == 'Reporting  area')]
	column_list = concat_rows_with_column_headers(rows_with_col_names, df.columns.tolist())

	# remove rows starting with 'Notes' or 'Total' or 'Notice'
	df = df[(df[0] != 'Notice') | (df[0] != 'Notes') | (df[0] != 'Total') | (df[0] != '"Notice"') | (df[0] != '"Notes"') | (df[0] != '"Total"') | (df[0] != '"Erratum"')]
	
	# remove rows that had column names
	df = df[~df.isin(rows_with_col_names)].dropna()

	# if dataframe 
	if len(column_list) > 2:
		# some csvs have a header row which has values starting from 0 to num_columns - 1 as the first row. We see if there such rows and drop them
		df = df.drop([0], errors='ignore')
		del rows_with_col_names

		# format column names
		column_list = format_column_header(column_list)
		# update columns of the dataframe
		df.columns = column_list

		# select columns of interest i.e. current week statistics
		current_week_stat_cols = [col for col in column_list if 'current' in col.lower() ]
		selected_cols = [column_list[0]] + current_week_stat_cols

		# filter the dataframe to current week stat columns
		df = df[selected_cols]

		# un-pivot the dataframe to place, column, value
		df = df.melt(id_vars=['Reporting Area'], value_vars=current_week_stat_cols,
        var_name='column_name', value_name='value')

		# add the observation date to the dataframe
		df['observationDate'] = observation_date

		# add the observation period based on the column names
		df['observationPeriod'] = df['column_name'].apply(set_observationPeriod)
		
		# convert the place names to geoIds
		df['observationAbout'] = df['Reporting Area'].apply(resolve_reporting_places_to_dcids)

		# fix the value column based on the data notes mentioned in NNDSS
		df['value'] = df['value'].replace(to_replace=_FORMAT_UNREPORTED_CASES, regex=True)

		return df


def generate_statvar_map_for_columns(column_list, place_list):

	sv_map = {}
	dcid_df = pd.DataFrame(columns=['Reporting Area', 'column_name', 'variableMeasured'])
	for column in column_list:
		# initialize the statvar dict for the current column
		svdict = {}
		svdict['populationType'] = 'dcs:MedicalConditionIncident'
		svdict['typeOf'] = 'dcs:StatisticalVariable'
		svdict['statType'] = 'dcs:measuredValue'
		svdict['measuredProperty'] = 'dcs:count'

		# column names have multiple pvs which are joined with ';'
		column_components = column.split(';')

		# remove duplicates substring from column name
		column_components = list(set(column_components))

		# flatten comma-separated components
		column_components = [i.strip() for i in column_components for i in i.split(',')]

		for component in column_components:
			component = component.strip()
			if not(component.lower() in _PV_MAP.keys()):
				# map to disease
				mapped_disease = _DISEASE_DCID_DF[_DISEASE_DCID_DF['name'].str.contains(component)][['name', 'dcid']]

				# when we have the best match i.e, only one row
				if mapped_disease.shape[0] == 1:
					svdict['incidentType'] = 'dcs:' + str(mapped_disease['dcid'].values[0])
					disease = str(mapped_disease['name'].values[0])
					disease = ''.join([e.title() for e in disease.split()])
					disease = disease.replace(',', '')
					svdict['disease'] = 'dcs:' + disease
					
			else:
				# check if the component is a key in _PV_MAP
				# add additional pvs from the column_name
				for key in _PV_MAP:
					if key in component.lower():
						#TODO: Handle the case when two values for same prop occurs
						svdict.update(_PV_MAP[key])

		# add pvs that are dependent on the place
		patterns_for_resident_pvs = ['Non-US', 'U.S. Residents','US Residents']

		places_with_resident_pvs = [place for place in place_list if any(substring in place for substring in patterns_for_resident_pvs)]

		# TODO: Move the repeated code to a function
		# generate dcid
		dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])
				
		# add to column_map
		key = 'Node: dcid:' + dcid
		if key not in sv_map.keys():
			sv_map[key] = svdict
		
		for place in place_list:
			if place not in places_with_resident_pvs:
				dcid_df = dcid_df.append({
					'Reporting Area': place,
					'column_name': column,
					'variableMeasured': dcid
				}, ignore_index=True)

		## if there are places with additional pvs, update the map and dataframe
		for place in places_with_resident_pvs:

			if 'Non-' not in place.strip():
				svdict_tmp = svdict.copy()
				svdict_tmp['residentStatus'] = 'dcs:USResident'
				# generate dcid
				dcid = get_statvar_dcid(svdict_tmp, ignore_props=['incidentType'])
			
				# add to column_map
				key = 'Node: dcid:' + dcid
				if key not in sv_map.keys():
					sv_map[key] = svdict_tmp
				dcid_df = dcid_df.append({
					'Reporting Area': place,
					'column_name': column,
					'variableMeasured': dcid
				}, ignore_index=True)
			

			elif 'Non-' in place.strip():
				svdict_tmp = svdict.copy()
				svdict_tmp['residentStatus'] = 'dcs:NonUSResident'
				# generate dcid
				dcid = get_statvar_dcid(svdict_tmp, ignore_props=['incidentType'])

				# add to column_map
				key = 'Node: dcid:' + dcid
				if key not in sv_map.keys():
					sv_map[key] = svdict_tmp
				dcid_df = dcid_df.append({
					'Reporting Area': place,
					'column_name': column,
					'variableMeasured': dcid
				}, ignore_index=True)

			else:
				# generate dcid
				dcid = get_statvar_dcid(svdict, ignore_props=['incidentType'])

				# add to column_map
				key = 'Node: dcid:' + dcid
				if key not in sv_map.keys():
					sv_map[key] = svdict
				dcid_df = dcid_df.append({
					'Reporting Area': place,
					'column_name': column,
					'variableMeasured': dcid
				}, ignore_index=True)

	return sv_map, dcid_df

def main(_) -> None:
	#TODO: add path to places_to_dcid and diseases_to_pvs csv files as args to the script
	flags.DEFINE_string('input_path', './data/nndss_weekly_data_updated',
						'Path to the directory with weekly data scrapped from NNDSS')
	flags.DEFINE_string(
		'output_path', './data/output',
		'Path to the directory where generated files are to be stored.')

	input_path = FLAGS.input_path
	output_path = FLAGS.output_path
	processed_dataframe_list = []

	#TODO: Parallelize this step
	# for all files in the data directory process the files and append to a common dataframe
	for filename in os.listdir(input_path):
		table_id = filename.split('table_')[1].split('.')[0]
		lowercase_in_tablename = re.findall(r'[a-z]', table_id)
		if filename.endswith('.csv') and len(lowercase_in_tablename) < 2:
			file_inputpath = os.path.join(input_path, filename)
			df = process_nndss_weekly(file_inputpath)
			processed_dataframe_list.append(df)

	# concat list of all processed data frames
	cleaned_dataframe = pd.concat(processed_dataframe_list, ignore_index=False)
	del processed_dataframe_list

	# for each unique column generate the statvar with constraints
	unique_columns = cleaned_dataframe['column_name'].unique().tolist()
	unique_places = cleaned_dataframe['Reporting Area'].unique().tolist()

	# column - statvar dictionary map
	sv_map, dcid_df = generate_statvar_map_for_columns(unique_columns, unique_places)
	
	# map the statvars to column names
	cleaned_dataframe = pd.merge(cleaned_dataframe, dcid_df, on=['Reporting Area', 'column_name'], how='left')

	# set measurement method
	cleaned_dataframe['measurementMethod'] ='dcs:CDC_NNDSS_Diseases_WeeklyTables'


	#TODO: 2. If reporting area is US Territories, drop observation and make a sum of case counts across US States with mMethod = dc/Aggregate




	## Create output directory if not present
	if not os.path.exists(output_path):
		os.makedirs(output_path)
	# write outputs to file
	f = open(os.path.join(output_path, 'cdc_wonder_weekly.tmcf'), 'w')
	f.write(_TEMPLATE_MCF)
	f.close()

	# write statvar mcf file from col_map
	f = open(os.path.join(output_path, 'cdc_wonder_weekly.mcf'), 'w')

	for dcid, pvdict in sv_map.items():
		f.write(dcid + '\n')
		for p, v in pvdict.items():
			if p != 'disease':
				f.write(p + ":" + v + "\n")
		f.write("\n")
	f.close()

	# remove disease prop before writing

	# write csv
	cleaned_dataframe['observationAbout'].replace('', np.nan, inplace=True)
	cleaned_dataframe['value'].replace('', np.nan, inplace=True)
	cleaned_dataframe.dropna(subset=['value', 'observationAbout'], inplace=True)
	cleaned_dataframe.to_csv(os.path.join(output_path, 'cdc_wonder_weekly.csv'), index=False)



if __name__ == '__main__':
    app.run(main)
