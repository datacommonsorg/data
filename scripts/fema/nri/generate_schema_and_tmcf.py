# todo: remove duplicate schemas
	# these are generated because part of what the dataset considers to be different measures,
	# we consider it as different units measuring the same StatisticalVariable

import pandas as pd
import numpy as np
import logging

# i/o filenames
NRI_DATADICTIONARY_INFILE_FILENAME = "source_data/NRIDataDictionary.csv"
SCHEMA_OUTFILE_FILENAME = "output/fema_nri_schema.mcf"
TMCF_OUTFILE_FILENAME = "output/fema_nri_counties.tmcf"

# flags
FLAG_SKIP_EAL_COMPONENTS = True # skip {Annualized Frequency, Historic Loss Ratio, Exposure}
FLAG_SKIP_IMPACTED_THING_COMPONENTS = True # skip {Building, Population, Population Equivalence, Agriculture}
FLAG_SKIP_NON_SCORE_RELATIVE_MEASURES = True # skip {Rating, National Percentile, State Percentile}

# hard coded lists of interest
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
EAL_COMPONENTS = ["Number of Events", "Annualized Frequency", "Historic Loss Ratio", "Exposure"]
IMPACTED_THING_COMPONENTS = ["Building", "Population", "Agriculture"]
NON_SCORE_RELATIVE_MEASURES = ["Rating", "Percentile"]

# template strings
COMPOSITE_MCF_FORMAT = """Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:NaturalHazardImpact
measuredProperty: dcs:{mProp}
"""
HAZARD_MCF_FORMAT_BASE = """Node: dcid:{nodeDCID}
typeOf: dcs:StatisticalVariable
populationType: dcs:NaturalHazardImpact
naturalHazardType: dcs:{hazType}
measuredProperty: {mProp}
"""
TMCF_FORMAT = """
Node: E:FEMA_NRI->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statVarDCID}
observationAbout: C:FEMA_NRI_Counties->DCID_GeoID
observationDate: "{obsDate}"
value: C:FEMA_NRI_Counties->{fieldName} 
"""

# mappings
DATACOMMONS_ALIASES = {
	"Score": "FemaNationalRiskScore",
	"SocialVulnerability": "femaSocialVulnerability",
	"CommunityResilience": "femaCommunityResilience",
	"HazardTypeRiskIndex": "femaNaturalHazardRiskIndex",
	"Hazard Type Risk Index": "femaNaturalHazardRiskIndex",
	"NationalRiskIndex":  "femaNaturalHazardRiskIndex",
	"Expected Annual Loss": "ExpectedLoss",
	"ExpectedAnnualLoss": "ExpectedLoss"
}

def apply_datacommon_alias(string):
	"""
	Given a string, returns the defined alias for the Data Commons import.
	If no alias is found, returns the string as is.
	"""
	string = string.strip()
	if string in DATACOMMONS_ALIASES:
		return DATACOMMONS_ALIASES[string]
	else:
		print(f"could not find alias for {string.replace(' ', '!')}")
		return string


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

def tmcf_from_row(row, index, statvar_dcid):
	"""
	Given a row of NRIDataDictionary describing a measure, generates the TMCF for that StatVar.
	Returns the TMCF as a string.
	"""

	# as of 2022-05-23, the "Version" field for all data is "November 2021"
	# "Field Name" in the data dictionary holds the name of the column in the data CSV
	return TMCF_FORMAT.format(
		index = index,
		statvar_dcid = statvar_dcid,
		obsDate=row["Version"],
		field_name=row["Field Name"]
	)


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
	measuredProperty = apply_datacommon_alias(drop_spaces(get_nth_dash_from_field_alias(row, 0)))
	unit = apply_datacommon_alias(drop_spaces(get_nth_dash_from_field_alias(row, 1)))

	if measuredProperty == "ExpectedLoss":
		dcid = f"Annual_{measuredProperty}_NaturalHazardImpact"
	else:
		dcid = f"{measuredProperty}_NaturalHazardImpact"
	
	formatted = COMPOSITE_MCF_FORMAT.format(nodeDCID = dcid, mProp=measuredProperty)

	if measuredProperty == "ExpectedLoss":
		formatted += "measurementQualifier: Annual\n"

	return formatted, dcid

def statvar_from_individual_hazard_row(row):
	"""
	Helper function for statvar_from_row()
	"""

	hazardType = drop_spaces(get_nth_dash_from_field_alias(row, 0)) + "Event"
	measuredProperty = apply_datacommon_alias(get_nth_dash_from_field_alias(row, 1))
	
	unit = ""
	# we want to cut off score/rating from measuredProperty and make it a unit instead
	if "Score" in measuredProperty or "Rating" in measuredProperty:
		unit = measuredProperty.split(' ')[-1]
		measuredProperty = apply_datacommon_alias(measuredProperty[:-len(unit)])
		unit = apply_datacommon_alias(unit)

	measurementQualifier = ""
	if measuredProperty == "ExpectedLoss":
		measurementQualifier = "Annual"

	measuredProperty = drop_spaces(measuredProperty)
	
	impactedThing = ""
	if row["Field Alias"].count("-") > 1:
		impactedThing = drop_spaces(get_nth_dash_from_field_alias(row, 2))
		if impactedThing == "Total":
			impactedThing = ""
	
	statType = ""
	if "Population" in impactedThing:
		statType = "ValueOfStatisticalLifeEquivalent" if impactedThing == "PopulationEquivalence" else "Count"
		impactedThing = "People"

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

	return formatted, dcid


if __name__ == "__main__":
	# computed variables
	# if field alias includes any of these strings, we skip that row from the schema and TMCF generation
	field_alias_strings_to_skip = []

	if FLAG_SKIP_EAL_COMPONENTS:
		field_alias_strings_to_skip.extend(EAL_COMPONENTS)
	if FLAG_SKIP_IMPACTED_THING_COMPONENTS:
		field_alias_strings_to_skip.extend(IMPACTED_THING_COMPONENTS)
	if FLAG_SKIP_NON_SCORE_RELATIVE_MEASURES:
		field_alias_strings_to_skip.extend(NON_SCORE_RELATIVE_MEASURES)

	# load the dataset and drop the ignored fields
	dd = pd.read_csv(NRI_DATADICTIONARY_INFILE_FILENAME)

	logging.info(f"[info] ignoring {len(IGNORED_FIELDS)} fields in NRIDataDictionary")
	dd = dd[~dd["Field Name"].isin(IGNORED_FIELDS)]
	dd = dd.reset_index()

	schema_out = ""
	tmcf_out = ""

	for index, row in dd.iterrows():
		skipped = False

		should_skip_component = any([eal_comp in row["Field Alias"] for eal_comp in field_alias_strings_to_skip])
		if should_skip_component :
			logging.info(f"Skipping individual hazard row {row['Field Alias']}" + 
			" because it is an EAL component and FLAG_SKIP_EAL_COMPONENTS is {FLAG_SKIP_EAL_COMPONENTS}")
			skipped = True
		
		if not skipped:
			statvar_mcf, statvar_dcid = statvar_from_row(row)
			statobs_tmcf = tmcf_from_row(row, index, statvar_dcid)
			
			schema_out += statvar_mcf + "\n"
			tmcf_out += statobs_tmcf


	# write out the results
	with open(SCHEMA_OUTFILE_FILENAME, "w") as outfile:
		logging.info(f"Writing StatVar MCF to {SCHEMA_OUTFILE_FILENAME}")
		outfile.write(schema_out)

	with open(TMCF_OUTFILE_FILENAME, "w") as outfile:
		logging.info(f"Writing County TMCF to {TMCF_OUTFILE_FILENAME}")
		outfile.write(tmcf_out)