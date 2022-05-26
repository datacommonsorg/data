# these are generated because part of what the dataset considers to be different
# measures, we consider it as different units measuring the same
# StatisticalVariable
import json
import pandas as pd
import numpy as np
import logging

from util.constants import IGNORED_FIELDS

# i/o filenames
NRI_DATADICTIONARY_INFILE_FILENAME = "source_data/NRIDataDictionary.csv"
SCHEMA_OUTFILE_FILENAME = "output/fema_nri_stat_vars.mcf"
TMCF_OUTFILE_FILENAME = "output/fema_nri_counties.tmcf"

# feature flags
# skip {Annualized Frequency, Historic Loss Ratio, Exposure}
FLAG_SKIP_EAL_COMPONENTS = True
# skip {Building, Population, Population Equivalence, Agriculture}
FLAG_SKIP_IMPACTED_THING_COMPONENTS = True
# skip {Rating, National Percentile, State Percentile}
FLAG_SKIP_NON_SCORE_RELATIVE_MEASURES = True

# hard coded lists of interest
COMPOSITE_ROW_LAYERS = [
    "National Risk Index", "Expected Annual Loss", "Social Vulnerability",
    "Community Resilience"
]
EAL_COMPONENTS = [
    "Number of Events", "Annualized Frequency", "Historic Loss Ratio",
    "Exposure"
]
IMPACTED_THING_COMPONENTS = ["Building", "Population", "Agriculture"]
NON_SCORE_RELATIVE_MEASURES = ["Rating", "Percentile"]

# template strings
COMPOSITE_MCF_FORMAT = """Node: dcid:{node_dcid}
typeOf: dcs:StatisticalVariable
statType: measuredValue
populationType: dcs:NaturalHazardImpact
measuredProperty: dcs:{m_prop}
"""
HAZARD_MCF_FORMAT_BASE = """Node: dcid:{node_dcid}
typeOf: dcs:StatisticalVariable
populationType: dcs:NaturalHazardImpact
statType: measuredValue
naturalHazardType: dcs:{haz_type}
measuredProperty: {m_prop}
"""
TMCF_FORMAT = """
Node: E:FEMA_NRI->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{statvar_dcid}
observationAbout: C:FEMA_NRI_Counties->DCID_GeoID
observationDate: "{obs_date}"
value: C:FEMA_NRI_Counties->{field_name} 
"""

# mappings
DATACOMMONS_ALIASES = {
    "Score": "FemaNationalRiskScore",
    "SocialVulnerability": "femaSocialVulnerability",
    "CommunityResilience": "femaCommunityResilience",
    "HazardTypeRiskIndex": "femaNaturalHazardRiskIndex",
    "Hazard Type Risk Index": "femaNaturalHazardRiskIndex",
    "NationalRiskIndex": "femaNaturalHazardRiskIndex",
    "Expected Annual Loss": "expectedLoss",
    "ExpectedAnnualLoss": "expectedLoss"
}


def prune_list_dupes(l):
    """
    Given a list L, computes a new list K where the duplicate 
    items in L are omitted, but all other items keep their
    initial ordering.

    Returns the new list K
    """
    k = []
    for el in l:
        if el not in k:
            k.append(el)
    return k


def capitalize_first(string):
    """
    Given a string, capitalizes the first character.

    Returns the new string
    """
    return string[0].upper() + string[1:]


def apply_datacommon_alias(string):
    """
	Given a string, returns the defined alias for the Data Commons import.
	If no alias is found, returns the string as is.
	"""
    string = string.strip()
    if string in DATACOMMONS_ALIASES:
        return DATACOMMONS_ALIASES[string]
    else:
        logging.info(f"could not find alias for {string.replace(' ', '!')}")
        return string


def get_nth_dash_from_field_alias(row, i):
    """
	Given a row containing a list of words separated with dashes surrounded by
        spaces  in the "Field Alias" column and an index i, finds the i-th
        string between those dashes.
	Returns the string without the spaces associated with the neighboring dashes.
	"""
    return row["Field Alias"].split(" - ")[i]


def drop_spaces(string):
    """
	Given a string, removes the space characters contained in that string.
	Returns a new string without the spaces.
	"""
    return string.replace(" ", "")


def tmcf_from_row(row, index, statvar_dcid, unit):
    """
	Given a row of NRIDataDictionary describing a measure, generates the TMCF
    for that StatVar.
	Returns the TMCF as a string.
	"""

    # as of 2022-05-23, the "Version" field for all data is "November 2021"
    # "Field Name" in the data dictionary holds the name of the column in the data CSV
    tmcf = TMCF_FORMAT.format(
        index=index,
        statvar_dcid=statvar_dcid,
        obs_date=row["Version"],
        field_name=row["Field Name"])

    if unit is not None and unit:
        tmcf += f"unit: {unit}\n"

    return tmcf


def extract_properties_from_row(row):
    """
	Given a row of NRIDataDictionary, extracts the relevant properties from it.

    Returns the properties as a dictionary
    """
    if is_composite_row(row):
        properties = extract_properties_from_composite_row(row)
        properties["is_composite"] = True
    else:
        properties = extract_properties_from_ind_hazard_row(row)
        properties["is_composite"] = False
    properties["row"] = row
    return properties


def schema_and_tmcf_from_properties(properties, index):
    """
	Given a row of NRIDataDictionary, computes the corresponding StatVar schema
    and StatVarObs schema template.

	Returns the StatVar MCF and StatVarObs TMCF as strings in a tuple.
	"""

    if properties["is_composite"]:
        schema, statvar_dcid = format_composite_field_properties_to_schema(
            properties)

    else:
        schema, statvar_dcid = format_ind_hazard_field_properties_to_schema(
            properties)

    statobs_tmcf = tmcf_from_row(properties["row"], index, statvar_dcid,
                                 properties["unit"])
    return schema, statobs_tmcf


def is_composite_row(row):
    """
	Given a row of NRIDataDictionary, computes whether that row is a measure of 
        all hazards in aggregate (composite).
	Returns boolean True if so, False otherwise.
	"""
    return row["Relevant Layer"] in COMPOSITE_ROW_LAYERS


def normalize_unit_for_measured_property(measured_property, unit):
    """
    Given a measured_property and unit, normalize it to KG terms.
    If m_prop is Expected Loss, makes the unit be USD if it is not Score.
    Otherwise, makes the unit empty if it is not Score.
    
    Returns the normalized measured_property and unit as a tuple.
    """

    if measured_property == "expectedLoss":
        if unit != "FemaNationalRiskScore":
            unit = "USDollar"
    else:
        if unit != "FemaNationalRiskScore":
            unit = ""

    return measured_property, unit


def extract_properties_from_composite_row(row):
    """
    Given a row of the data dictionary representing a composite field,
    extracts properties relevant to the schema and TMCF.

    Returns a dictionary with the following keys:
      - measured_property
      - unit
    """
    measured_property = apply_datacommon_alias(
        drop_spaces(get_nth_dash_from_field_alias(row, 0)))
    unit = apply_datacommon_alias(
        drop_spaces(get_nth_dash_from_field_alias(row, 1)))

    measured_property, unit = normalize_unit_for_measured_property(
        measured_property, unit)

    return {"measured_property": measured_property, "unit": unit}


def format_composite_field_properties_to_schema(properties):
    """
    Given properties of a composite field, formats a valid Schema for the
    StatisticalVariable representing that field.
    
    Returns the tuple:
        (Schema MCF in string format, the dcid of the StatVar)
    """
    measured_property = properties["measured_property"]

    if measured_property == "expectedLoss":
        dcid = f"Annual_{capitalize_first(measured_property)}_NaturalHazardImpact"
    else:
        dcid = f"{capitalize_first(measured_property)}_NaturalHazardImpact"

    formatted = COMPOSITE_MCF_FORMAT.format(
        node_dcid=dcid, m_prop=measured_property)

    if measured_property == "expectedLoss":
        formatted += "measurementQualifier: Annual\n"

    return formatted, dcid


def extract_properties_from_ind_hazard_row(row):
    """
    Given a row of the data dictionary representing a individual hazard field,
    extracts properties relevant to the schema and TMCF.

    Returns a dictionary with the following keys:
      - hazard_type
      - measured_property
      - measurement_qualifier
      - impacted_thing
      - unit
    """
    hazard_type = drop_spaces(get_nth_dash_from_field_alias(row, 0)) + "Event"
    # edge case; one hazard type exists but spelled slightly different between
    # NRI and DC.
    # solve by renaming to match existing DC class
    if hazard_type == "CoastalFloodingEvent":
        hazard_type = "CoastalFloodEvent"
    measured_property = apply_datacommon_alias(
        get_nth_dash_from_field_alias(row, 1))

    unit = ""
    # we want to cut off score/rating from measured_property and make it a unit
    if "Score" in measured_property or "Rating" in measured_property:
        unit = measured_property.split(' ')[-1]
        measured_property = apply_datacommon_alias(
            measured_property[:-len(unit)])
        unit = apply_datacommon_alias(unit)
    measured_property, unit = normalize_unit_for_measured_property(
        measured_property, unit)

    measurement_qualifier = ""
    if measured_property == "expectedLoss":
        measurement_qualifier = "Annual"

    measured_property = drop_spaces(measured_property)

    impacted_thing = ""
    if row["Field Alias"].count("-") > 1:
        impacted_thing = drop_spaces(get_nth_dash_from_field_alias(row, 2))
        if impacted_thing == "Total":
            impacted_thing = ""

    # impacted_thing might be "population" or "population equivalence"
    if "Population" in impacted_thing:
        impacted_thing = "People"

    return {
        "hazard_type": hazard_type,
        "measured_property": measured_property,
        "measurement_qualifier": measurement_qualifier,
        "impacted_thing": impacted_thing,
        "unit": unit
    }


def format_ind_hazard_field_properties_to_schema(properties):
    """
    Given properties of a individual hazard field, formats a valid Schema for
    the StatisticalVariable representing that field.

    Returns the tuple:
        (Schema MCF in string format, the dcid of the StatVar)
    """
    hazard_type = properties["hazard_type"]
    measured_property = properties["measured_property"]
    measurement_qualifier = properties["measurement_qualifier"]
    impacted_thing = properties["impacted_thing"]
    unit = properties["unit"]

    # create a list of names that might go on the dcid
    dcid_list = [
        measurement_qualifier, measured_property, "NaturalHazardImpact",
        hazard_type, impacted_thing
    ]

    # drop empty dcid_list elements
    dcid_list = [element for element in dcid_list if element]

    # capitalize dcid_list elements
    dcid_list = [capitalize_first(element) for element in dcid_list]

    # join the rest with underscores to obtain the final dcid
    dcid = "_".join(dcid_list)

    formatted = HAZARD_MCF_FORMAT_BASE.format(
        node_dcid=dcid,
        haz_type=hazard_type,
        m_prop=drop_spaces(measured_property))

    if impacted_thing:
        formatted += f"impactedThing: {impacted_thing}\n"

    if measurement_qualifier:
        formatted += f"measurementQualifier: {measurement_qualifier}\n"

    return formatted, dcid


if __name__ == "__main__":
    # if field alias includes any of these strings, we skip that row from the
    # schema and TMCF generation
    field_alias_strings_to_skip = []

    if FLAG_SKIP_EAL_COMPONENTS:
        field_alias_strings_to_skip.extend(EAL_COMPONENTS)
    if FLAG_SKIP_IMPACTED_THING_COMPONENTS:
        field_alias_strings_to_skip.extend(IMPACTED_THING_COMPONENTS)
    if FLAG_SKIP_NON_SCORE_RELATIVE_MEASURES:
        field_alias_strings_to_skip.extend(NON_SCORE_RELATIVE_MEASURES)

    # load the dataset and drop the ignored fields
    dd = pd.read_csv(NRI_DATADICTIONARY_INFILE_FILENAME)

    logging.info(
        f"[info] ignoring {len(IGNORED_FIELDS)} fields in NRIDataDictionary")
    dd = dd[~dd["Field Name"].isin(IGNORED_FIELDS)]
    dd = dd.reset_index()

    extracted_properties = []
    for index, row in dd.iterrows():
        skipped = False

        should_skip_component = any([
            eal_comp in row["Field Alias"]
            for eal_comp in field_alias_strings_to_skip
        ])
        if should_skip_component:
            logging.info((
                f"Skipping individual hazard row {row['Field Alias']}"
                " because it is an EAL component and FLAG_SKIP_EAL_COMPONENTS is "
                f"{FLAG_SKIP_EAL_COMPONENTS}"))
            skipped = True

        if not skipped:
            extracted_properties.append(extract_properties_from_row(row))

    schemas = []
    tmcfs = []

    for properties in extracted_properties:
        statvar_mcf, statobs_tmcf = schema_and_tmcf_from_properties(
            properties, index)

        schemas.append(statvar_mcf)
        tmcfs.append(statobs_tmcf)

    # prune out duplicate nodes
    # - we might get duplicate nodes because the rows might be repeated
    #   on the dimensions that we do not extract
    # - this hits an edge case in the import tool, which we want to avoid
    schemas = prune_list_dupes(schemas)
    tmcfs = prune_list_dupes(tmcfs)

    schema_out = "\n".join(schemas)
    tmcf_out = "".join(tmcfs)

    # write out the results
    with open(SCHEMA_OUTFILE_FILENAME, "w") as outfile:
        logging.info(f"Writing StatVar MCF to {SCHEMA_OUTFILE_FILENAME}")
        outfile.write(schema_out)

    with open(TMCF_OUTFILE_FILENAME, "w") as outfile:
        logging.info(f"Writing County TMCF to {TMCF_OUTFILE_FILENAME}")
        outfile.write(tmcf_out)
