# TODO: casing of property values
# TODO: write to a file

from os import stat
import pandas as pd
import numpy as np

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
Node: dcid:{mProp}_{mQual}_NaturalHazardImpact
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

def tmcf_from_row(row):
	if is_composite_row(row):
		return tmcf_from_composite_row(row)
	else:
		return tmcf_from_individual_hazard_row(row)

def is_composite_row(row):
	return row["Relevant Layer"] in COMPOSITE_ROW_LAYERS

def tmcf_from_composite_row(row):
	measuredProperty = drop_spaces(get_nth_dash_from_field(row, 0))
	measurementQualifier = drop_spaces(get_nth_dash_from_field(row, 1))

	formatted = COMPOSITE_MCF_FORMAT.format(mProp=measuredProperty, mQual = measurementQualifier)

	return formatted

def tmcf_from_individual_hazard_row(row):
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

	return formatted


dd = pd.read_csv("source_data/NRIDataDictionary.csv")

print(f"[info] ignoring {len(IGNORED_FIELDS)} fields")
dd = dd[~dd["Field Name"].isin(IGNORED_FIELDS)]

for _, row in dd.iterrows():
	print(tmcf_from_row(row))