# TODO: casing of property values

from os import stat
import pandas as pd
import numpy as np
import logging

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

COMPOSITE_MCF_FORMAT = """
Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:NaturalHazardImpact
measuredProperty: dcs:{mProp}
measurementQualifier: dcs:{mQual}
"""

HAZARD_MCF_FORMAT_BASE_APPR1 = """
Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:{hazType}
measuredProperty: {mProp}
"""

def get_nth_dash_from_field(row, i):
	return row["Field Alias"].split(" - ")[i]

def drop_spaces(string):
	return string.replace(" ", "")

def tmcf_from_row(row, statVarDCID):
	"""
	Given a row of NRIDataDictionary describing a measure, generates the TMCF for that StatVar.
	Returns the TMCF as a string.
	"""

	# the "Sort" field is an unique, monotonically increasing ID.
	# 	there will be gaps in this ID, which should be OK? 
	# as of 2022-05-23, the "Version" field for all data is "November 2021"
	# "Field Name" in the data dictionary holds the name of the column in the data CSV
	TMCF = f"""
Node: E:FEMA_NRI->E{row["Sort"]}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statVarDCID}
observationAbout: C:FEMA_NRI_Counties->DCID_GeoID
observationDate: "{row["Version"]}"
value: C:FEMA_NRI_Counties->{row["Field Name"]} 
"""

	return TMCF

def statvar_from_row(row):
	if is_composite_row(row):
		return statvar_from_composite_row(row)
	else:
		return statvar_from_individual_hazard_row(row)

def is_composite_row(row):
	return row["Relevant Layer"] in COMPOSITE_ROW_LAYERS

def statvar_from_composite_row(row):
	measuredProperty = drop_spaces(get_nth_dash_from_field(row, 0))
	measurementQualifier = drop_spaces(get_nth_dash_from_field(row, 1))

	dcid = f"{measuredProperty}_{measurementQualifier}_NaturalHazardImpact"

	formatted = COMPOSITE_MCF_FORMAT.format(nodeDCID = dcid, mProp=measuredProperty, mQual = measurementQualifier)

	return formatted, dcid

def statvar_from_individual_hazard_row(row):
	"""
	FYI: until import document gets more comments, I am implementing this script for approach 1.
	"""

	hazardType = drop_spaces(get_nth_dash_from_field(row, 0)) + "Event"
	measuredProperty = get_nth_dash_from_field(row, 1)
	measurementQualifier = ""
	# we want to cut off score/rating from measuredProperty and make it a measurement qualifier instead
	if "Score" in measuredProperty or "Rating" in measuredProperty:
		measurementQualifier = measuredProperty.split(' ')[-1]
		measuredProperty = measuredProperty[:-len(measurementQualifier)]

	measuredProperty = drop_spaces(measuredProperty)
	
	impactedThing = ""
	if row["Field Alias"].count("-") > 1:
		impactedThing = drop_spaces(get_nth_dash_from_field(row, 2))
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


dd = pd.read_csv("source_data/NRIDataDictionary.csv")

logging.info(f"[info] ignoring {len(IGNORED_FIELDS)} fields in NRIDataDictionary")

dd = dd[~dd["Field Name"].isin(IGNORED_FIELDS)]

schema_out = ""
tmcf_out = ""
for _, row in dd.iterrows():
	statvar_mcf, statvar_dcid = statvar_from_row(row)
	statobs_tmcf = tmcf_from_row(row, statvar_dcid)
	
	schema_out += statvar_mcf
	tmcf_out += statobs_tmcf

schema_outfile_filename = "fema_nri_schema.mcf"
tmcf_outfile_filename = "fema_nri_counties.tmcf"

with open(schema_outfile_filename, "w") as outfile:
	logging.info(f"Writing StatVar MCF to {schema_outfile_filename}")
	outfile.write(schema_out)

with open(tmcf_outfile_filename, "w") as outfile:
	logging.info(f"Writing County TMCF to {tmcf_outfile_filename}")
	outfile.write(tmcf_out)