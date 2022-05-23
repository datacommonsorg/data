from os import stat
import pandas as pd
import numpy as np
import logging

# i/o filenames
NRI_DATADICTIONARY_INFILE_FILENAME = "source_data/NRIDataDictionary.csv"
SCHEMA_OUTFILE_FILENAME = "fema_nri_schema.mcf"
TMCF_OUTFILE_FILENAME = "fema_nri_counties.tmcf"

IGNORED_FIELDS = [
		"OBJECTID",
		"Shape",
		"Shape_Length",
		"Shape_Area",
		"STATE",
		"STATEABBRV",
		"STATEFIPS",
		"COUNTY",
		"COUNTYTYPE",
		"COUNTYFIPS",
		"STCOFIPS",
		"NRI_ID",
		"TRACT",
		"TRACTFIPS",
		"POPULATION",
		"BUILDVALUE",
		"AGRIVALUE",
		"AREA",
		"NRI_VER",
		"AIANNHCE",
		"FEDREG2020",
		"FEDERAL_ID",
		"JURS_NAME",
		"JURS_AREA",
		"JURS_TYPE",
		"HIFLD_NAME",
		"HIFLD_AREA",
		"HIFLD_TYPE"
]

COMPOSITE_ROW_LAYERS = ["National Risk Index", "Expected Annual Loss", "Social Vulnerability", "Community Resilience"]

COMPOSITE_MCF_FORMAT = """Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:NaturalHazardImpact
measuredProperty: dcs:{mProp}
measurementQualifier: dcs:{mQual}
"""

HAZARD_MCF_FORMAT_BASE_APPR1 = """Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:{hazType}
measuredProperty: {mProp}
"""

def get_nth_dash_from_field_alias(row, i):
	"""
	Given a row containing a list of words separated with dashes surrounded by spaces 
		in the "Field Alias" column and an index i, finds the i-th string between those dashes.
	Returns the string without the spaces associated with the neighboring dashes.
	"""
	return row["Field Alias"].split(" - ")[i]

def drop_spaces(string):
	"""
	Given a string, removes the space characters contained in that string.
	Returns a new string without the spaces.
	"""
	return string.replace(" ", "")

def tmcf_from_row(row, index, statVarDCID):
	"""
	Given a row of NRIDataDictionary describing a measure, generates the TMCF for that StatVar.
	Returns the TMCF as a string.
	"""

	# as of 2022-05-23, the "Version" field for all data is "November 2021"
	# "Field Name" in the data dictionary holds the name of the column in the data CSV
	TMCF = f"""
Node: E:FEMA_NRI->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statVarDCID}
observationAbout: C:FEMA_NRI_Counties->DCID_GeoID
observationDate: "{row["Version"]}"
value: C:FEMA_NRI_Counties->{row["Field Name"]} 
"""

	return TMCF

def statvar_from_row(row):
	"""
	Given a row of NRIDataDictionary, computes the corresponding StatVar Schema.
	Returns the StatVar MCF node as a string.
	"""
	if is_composite_row(row):
		return statvar_from_composite_row(row)
	else:
		return statvar_from_individual_hazard_row(row)

def is_composite_row(row):
	"""
	Given a row of NRIDataDictionary, computes whether that row is a measure of all hazards
		in aggregate (composite).
	Returns boolean True if so, False otherwise.
	"""
	return row["Relevant Layer"] in COMPOSITE_ROW_LAYERS

def statvar_from_composite_row(row):
	"""
	Helper function for statvar_from_row()
	"""
	measuredProperty = drop_spaces(get_nth_dash_from_field_alias(row, 0))
	measurementQualifier = drop_spaces(get_nth_dash_from_field_alias(row, 1))

	dcid = f"{measuredProperty}_{measurementQualifier}_NaturalHazardImpact"

	formatted = COMPOSITE_MCF_FORMAT.format(nodeDCID = dcid, mProp=measuredProperty, mQual = measurementQualifier)

	return formatted, dcid

def statvar_from_individual_hazard_row(row):
	"""
	Helper function for statvar_from_row()

	NOTE: until import document gets more comments, I am implementing this script for approach 1.
	"""

	hazardType = drop_spaces(get_nth_dash_from_field_alias(row, 0)) + "Event"
	measuredProperty = get_nth_dash_from_field_alias(row, 1)
	measurementQualifier = ""
	# we want to cut off score/rating from measuredProperty and make it a measurement qualifier instead
	if "Score" in measuredProperty or "Rating" in measuredProperty:
		measurementQualifier = measuredProperty.split(' ')[-1]
		measuredProperty = measuredProperty[:-len(measurementQualifier)]

	measuredProperty = drop_spaces(measuredProperty)
	
	impactedThing = ""
	if row["Field Alias"].count("-") > 1:
		impactedThing = drop_spaces(get_nth_dash_from_field_alias(row, 2))
		if impactedThing == "Total":
			impactedThing = ""
	
	statType = ""
	if "Population" in impactedThing:
		statType = "ValueOfStatisticalLifeEquivalent" if impactedThing == "PopulationEquivalence" else "Count"
		impactedThing = "Population"

	# create a list of names that might go on the dcid
	dcid_list = [
		measurementQualifier,
		statType,
		measuredProperty,
		hazardType,
		impactedThing
	]

	# drop empty dcid_list elements
	dcid_list = [element for element in dcid_list if element]

	# join the rest with underscores to obtain the final dcid
	dcid = "_".join(dcid_list)

	formatted = HAZARD_MCF_FORMAT_BASE_APPR1.format(nodeDCID = dcid, hazType = hazardType, mProp = drop_spaces(measuredProperty))

	if statType:
		formatted += f"statType: {statType}\n"

	if impactedThing:
		formatted += f"impactedThing: {impactedThing}\n"

	if measurementQualifier:
		formatted += f"measurementQualifier: {measurementQualifier}\n"

	if "Expected Annual Loss" in measuredProperty:
		formatted += f"unit: USDollar\n"

	return formatted, dcid

dd = pd.read_csv(NRI_DATADICTIONARY_INFILE_FILENAME)

logging.info(f"[info] ignoring {len(IGNORED_FIELDS)} fields in NRIDataDictionary")

dd = dd[~dd["Field Name"].isin(IGNORED_FIELDS)]
dd = dd.reset_index()
schema_out = ""
tmcf_out = ""
for index, row in dd.iterrows():
	statvar_mcf, statvar_dcid = statvar_from_row(row)
	statobs_tmcf = tmcf_from_row(row, index, statvar_dcid)
	
	schema_out += statvar_mcf + "\n"
	tmcf_out += statobs_tmcf

with open(SCHEMA_OUTFILE_FILENAME, "w") as outfile:
	logging.info(f"Writing StatVar MCF to {SCHEMA_OUTFILE_FILENAME}")
	outfile.write(schema_out)

with open(TMCF_OUTFILE_FILENAME, "w") as outfile:
	logging.info(f"Writing County TMCF to {TMCF_OUTFILE_FILENAME}")
	outfile.write(tmcf_out)