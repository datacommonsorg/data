# Copyright 2021 Google LLC
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
"""Script to generate schema mcfs and get the mapping of dimensions/indicators
to their corresponding schema dcid."""

import requests
import json
import re
import os

# Map of dimension code to title to use to build a dcid for that dimension
PROP_TITLE_MAP = {
    "GOVERNMENTBENEFIT":
        "Substance Use Disorder Government Benefit",
    "GROUP":
        "Substance Use Disorder Resource Group",
    "RSUDPREVENTIONPROGRAMME":
        "Substance Use Disorder Prevention Programmes",
    "RSUDMAINSUBSTANCEATTREATMENT":
        "Main Substance At Treatment",
    "POLICYADOPTIONLEVEL":
        "Policy Adopted At",
    "SUBSTANCETYPE":
        "Substance Type",
    "EMFFREQUENCY":
        "Emf Frequency",
    "EMFEXPOSED":
        "Emf Exposure Group ",
    "DRUG":
        "Drug Used",
    "RSUDHWF":
        "Occupation",
    "PROGRAMME":
        "Substance Use Disorder Program",
    "RSUDREP":
        "Representative Type",
    "RSUDSPECIFICPOPULATION":
        "Grouping Of People",
    "DRUGSUPERVISION":
        "Drug Supervision Requirement",
    "DRUGPRESCRIPTION":
        "Drug Prescription Requirement",
    "RSUDMONITORING":
        "Substance Use Disorder Monitoring System",
    "PUBLICPLACE":
        "Public Location Type",
    "MEASUREIMPORTANCETYPE":
        "Substance Abuse Reduction Measure Type",
    "NATIONALSYSTEMTYPE":
        "Substance Use Disorder Monitoring System",
    "EMFBODYPART":
        "Emf Exposure Body Part",
    "SEATTYPE":
        "Vehicle Occupant Type",
    "MOTOCYCLEOCCUPANTTYPE":
        "Vehicle Occupant Type",
    "RSUDMAINTENANCEACCESSRESTRICTIONS":
        "Substance Use Disorder Treatment Access Restrictions",
    "RSUD_HIVHEP_CT":
        "Hiv Hepatitis Services Available",
    "STANDARDOFCARE":
        "Standard Of Care",
    "BACGROUP":
        "Grouping Of People",
    "SUNBED_CONTROL":
        "Sunbed Compliance Measure",
    "RSUDTREATMENT":
        "Substance Use Disorder Treatment Type",
    "RSUDSUBSTANCEDEPENDENCE":
        "Substance Type",
    "PRICEMEASURETYPE":
        "Pricing Constraint Type",
    "SPONSORSHIPORIGINATOR":
        "Sponsorship Industry",
    "PUBLICPRIVATESETTING":
        "Location Type Of Service",
    "GOEQUESTION":
        "Global Observatory For EHealth Question",
    "RSUDREP":
        "Substance Use Disorder Resource Representative Type",
    "EMFRADIOBAND":
        "Emf Radio Band",
    "DRIVERTYPE":
        "Vehicle Driver Type",
    "OPENACCESSSERVICE":
        "Substance Use Disorder Open Access Service",
    "GOVERNMENTBENEFIT":
        "Substance Use Disorder Government Benefit",
    "RSUDPHARMACOTHERAPYOPTION":
        "Pharmacotherapy Option",
    "COORDINATINGENTITIES":
        "Substance Abuse Coordinating Entity",
    "PENALTYTYPE":
        "Legal Penalty Type",
    "CONSUMPTIONTYPE":
        "Alcohol Consumption Record Type",
    "COMMUNITYACTIONTYPE":
        "Government Supportable Community Action",
    "VEHICLESTANDARD":
        "Vehicle Feature Type",
    "HARMANDCONSEQUENCE":
        "Substance Abuse Consequence",
    "RSUDREPORTING":
        "Reporting Data Source"
}

# Map of dimension code to description to use for the property node.
PROP_NODE_DESCRIPTION_MAP = {
    "IHRSPARCAPACITYLEVEL":
        "International Health Regulations (IHR) State Party Self-Assessment Annual Report (SPAR) Capacity Level",
    "AMRGLASSCATEGORY":
        "Antimicrobial resistance (amr) Global Antimicrobial Resistance and Use Surveillance System (GLASS) Category",
    "EMFEXPOSED":
        "Electromagnetic Fields Exposure Group",
    "EMFFREQUENCY":
        "Electromagnetic Fields Frequency",
    "EMFRADIOBAND":
        "Electromagnetic Fields Radio Band",
    "EMFBODYPART":
        "Electromagnetic Fields Exposure Body Part"
}


def categorize_dimensions(data_files):
    """ Categorize dimensions as cprops, spatial dimensions or time dimensions
    Args:
        data_files: list of the raw data json files
    Returns:
        an object: {
            spatial: map of spatial dimensions to the number of occurences,
            time: list of time dimensions,
            cprop: sorted list of {id: dimension code as string,
                                   num: number of occurences}
        }
    """
    spatial_dim = {}
    time_dim = set()
    cprop_dim = {}
    for f in data_files:
        with open(f, "r+") as indicator_data:
            indicator_data = json.load(indicator_data).get("value", [])
        if len(indicator_data) == 0:
            continue
        for data in indicator_data:
            spatial_dim_type = data.get("SpatialDimType", "")
            spatial_dim_count = spatial_dim.get(spatial_dim_type, 0)
            spatial_dim[spatial_dim_type] = spatial_dim_count + 1
            time_dim.add(data.get("TimeDimType", ""))
            dim1Type = data.get("Dim1Type", "")
            if not dim1Type:
                continue
            dim1Count = cprop_dim.get(dim1Type, 0)
            cprop_dim[dim1Type] = dim1Count + 1
            dim2Type = data.get("Dim2Type", "")
            if not dim2Type:
                continue
            dim2Count = cprop_dim.get(dim2Type, 0)
            cprop_dim[dim2Type] = dim2Count + 1
            dim3Type = data.get("Dim3Type", "")
            if not dim3Type:
                continue
            dim3Count = cprop_dim.get(dim3Type, 0)
            cprop_dim[dim3Type] = dim3Count + 1
    cprop_list = []
    for prop in cprop_dim:
        cprop_list.append({"id": prop, "num": cprop_dim.get(prop)})
    sorted_cprop_list = sorted(cprop_list,
                               key=lambda x: x.get("num"),
                               reverse=True)
    result = {
        "spatial": spatial_dim,
        "time": list(time_dim),
        "cprop": sorted_cprop_list
    }
    return result


def get_enum_node(dcid):
    node = []
    node.append("Node: dcid:" + dcid)
    node.append("typeOf: schema:Class")
    node.append("subClassOf: schema:Enumeration")
    node.append(f'name: "{dcid}"')
    node.append("")
    return node


def get_prop_node(dcid, description, range_dcid, domainType):
    node = []
    node.append("Node: dcid:" + dcid)
    node.append(f'name: "{dcid}"')
    if description:
        node.append(f'description: "{description}"')
    node.append("typeOf: schema:Property")
    node.append(f"domainIncludes: dcs:{domainType}")
    node.append("rangeIncludes: dcs:" + range_dcid)
    node.append("")
    return node


def get_val_node(dcid, type_of):
    node = []
    node.append("Node: dcid:" + dcid)
    node.append(f'name: "{dcid}"')
    node.append("typeOf: dcs:" + type_of)
    node.append("")
    return node


def generate_dimensions_schema(curated_dim_types, person_dim_types,
                               dim_categories):
    """ Autogenerate schema and the mapping from dimension to schema
    Args:
        curated_dim_types: dictionary of dimension code to corresponding schema
                        dcid for curated schema mappings
        person_dim_types: list of dimension codes where domainIncludes should be
                        person
        dim_categories: an object: {
            spatial: map of spatial dimensions to the number of occurences,
            time: list of time dimensions,
            cprop: sorted list of {id: dimension code as string,
                                   num: number of occurences}
        }
    Returns:
        mcf_result: list of strings that correspond to the schema mcf file
                    generated
        dim_map: an object: {
            dimTypes: map of dimension code to its corresponding schema dcid
            dimValues: map of dimension code to map of dimension value to its
                       corresponding schema dcid
        }
    """
    cprops = set()
    for prop in dim_categories.get("cprop", []):
        cprops.add(prop.get("id"))
    seen_dcids = {}
    mcf_result = []
    dim_type_map = {}
    dim_value_map = {}
    dimensions = requests.get(
        "https://ghoapi.azureedge.net/api/Dimension").json().get("value", [])
    for d in dimensions:
        d_code = d.get('Code', "")
        if not d_code in cprops or d_code in curated_dim_types:
            continue
        # Make the dimension title usable as a dcid by replacing _ with space,
        # capitalizing the first letter of every word and removing an end "s"
        # eg. "SUBSTANCE_ABUSE_AWARENESS_ACTIVITY_TYPES" ->
        # "Substance Abuse Awareness Activity Type"
        d_title = d.get('Title').replace("_", " ").title()
        if d_title[-1:] == "s":
            d_title = d_title[:-1]
        if d_code in PROP_TITLE_MAP:
            d_title = PROP_TITLE_MAP[d_code]
        # Get the dcid for the property node by making the first letter in the
        # title lowercase and removing white spaces
        # eg. "Substance Abuse Awareness Activity Type" ->
        # "substanceAbuseAwarenessActivityType"
        prop_dcid = (d_title[0].lower() + d_title[1:]).replace(" ", "")
        # Get the dcid for the enum node by taking the dcid for the property
        # node, making the first letter uppercase and add "Enum" to the end
        # eg. "substanceAbuseAwarenessActivityType" ->
        # "SubstanceAbuseAwarenessActivityTypeEnum"
        enum_dcid = prop_dcid[0].upper() + prop_dcid[1:] + "Enum"
        if not prop_dcid in seen_dcids:
            description = ""
            if d_code in PROP_NODE_DESCRIPTION_MAP:
                name = PROP_NODE_DESCRIPTION_MAP[d_code]
            domainType = "Thing"
            if d_code in person_dim_types:
                domainType = "Person"
            mcf_result.extend(get_enum_node(enum_dcid))
            mcf_result.extend(
                get_prop_node(prop_dcid, description, enum_dcid, domainType))
        seen_dcids[prop_dcid] = set()
        dim_type_map[d_code] = prop_dcid
        dim_value_map[d_code] = {}
        d_values = requests.get(
            f"https://ghoapi.azureedge.net/api/Dimension/{d_code}/DimensionValues"
        ).json().get("value", [])
        for value in d_values:
            v_code = value.get('Code')
            v_title = value.get('Title').title()
            # Get node dcid from v_title by removing white space, comma, -, and
            # period, adding "WHO/" prefix, and replacing "/" with "Or"
            # eg. "Finance/taxation" -> "WHO/FinanceOrTaxation" or
            # "Government-sponsored mHealth programmes are being evaluated" ->
            # "WHO/GovernmentSponsoredMhealthProgrammesAreBeingEvaluated"
            v_title = re.sub("\s|\,|\-|\.", "", v_title)
            node_dcid = "WHO/" + v_title.replace("/", "Or")
            if not node_dcid in seen_dcids[prop_dcid]:
                mcf_result.extend(get_val_node(node_dcid, enum_dcid))
            seen_dcids[prop_dcid].add(node_dcid)
            dim_value_map[d_code][v_code] = "dcs:" + node_dcid
    dim_map = {"dimTypes": dim_type_map, "dimValues": dim_value_map}
    return mcf_result, dim_map


def build_indicator_node(dcid, i_name):
    description = get_indicator_description(i_name)
    result = []
    result.append(f"Node: dcid:{dcid}")
    result.append(f'name: "{dcid}"')
    result.append(f'description: "{description}"')
    result.append("typeOf: schema:Property")
    result.append("domainIncludes: dcs:Thing")
    result.append("rangeIncludes: schema:Number, schema:Text")
    result.append("")
    return result


def get_indicator_description(indicator_name):
    """Replace non ascii characters in indicator name to create a string
    that can be used as a node description.
    Args:
        indicator_name: the indicator name as a string.
    Returns:
        description: a string that can be used as a node description.
    """
    description = re.sub("\–|\−", "-", indicator_name)
    description = re.sub('\“|\”', '"', description)
    description = description.replace(" ", "")
    description = description.replace("m²", "square metre")
    return description


def generate_indicators_schema():
    """ Autogenerate schema and the mapping from indicator to schema
    Returns:
        mcf_result: list of strings that correspond to the schema mcf file generated
        indicator_map: map of indicator code to its corresponding schema dcid
    """
    mcf_result = []
    indicator_map = {}
    indicator_list = requests.get(
        "https://ghoapi.azureedge.net/api/Indicator").json().get("value", [])
    for indicator in indicator_list:
        code = indicator.get("IndicatorCode", "")
        name = indicator.get("IndicatorName", "")
        dcid = "who/" + code
        indicator_mcf = build_indicator_node(dcid, name)
        mcf_result.extend(indicator_mcf)
        indicator_map[code] = dcid
    return mcf_result, indicator_map


def generate_schema(data_files, curated_dim_file, artifact_dir, mcf_dir):
    """ Autogenerate a schema and the mapping from dimensions/indicators to
    schema.
    Args:
        data_files: list of the raw data json files
        curated_dim_file: schema mapping for dimensions that have a manually
        curated schema. format: {
                dimTypes: map of dimension type code to its corresponding schema dcid
                dimValues: map of dimension type code to map of dimension value to its corresponding schema dcid
        }
        artifact_dir: directory to save schema mapping and dim categories files in. If empty, don't save artifacts
        mcf_dir: directory to save the schema mcf file in. If empty, save to current directory.
    Returns:
        schema_mapping: an object: {
            cprops: map of dimension type code to its corresponding schema dcid,
            values: map of dimension type code to map of dimension value to its corresponding schema dcid,
            indicators: map of indicator codes to its corresponding schema dcid
        }
    """
    dim_categories = categorize_dimensions(data_files)
    with open(curated_dim_file, "r+") as curated_dim_map:
        curated_dim_map = json.load(curated_dim_map)
    curated_dim_types = curated_dim_map.get("dimTypes", {})
    person_dim_types = curated_dim_map.get("personDimensions", {})
    dim_mcf, dim_map = generate_dimensions_schema(curated_dim_types,
                                                  person_dim_types,
                                                  dim_categories)
    indicator_mcf, indicator_map = generate_indicators_schema()
    cprop_mapping = {}
    values_mapping = {}
    cprop_mapping.update(dim_map.get("dimTypes", {}))
    cprop_mapping.update(curated_dim_types)
    values_mapping.update(dim_map.get("dimValues", {}))
    values_mapping.update(curated_dim_map.get("dimValues", {}))
    schema_mapping = {
        "cprops": cprop_mapping,
        "values": values_mapping,
        "indicators": indicator_map,
        "personDimensions": person_dim_types
    }
    # save mcf file
    with open(os.path.join(mcf_dir, "who_generated_schema.mcf"),
              "w+") as dim_mcf_file:
        dim_mcf_file.write("\n".join(dim_mcf + indicator_mcf))
    # save artifacts
    if artifact_dir:
        with open(os.path.join(artifact_dir, "schema_mapping.json"),
                  "w+") as schema_mapping_file:
            schema_mapping_file.write(json.dumps(schema_mapping))
        with open(os.path.join(artifact_dir, "dim_categories.json"),
                  "w+") as dim_categories_file:
            dim_categories_file.write(json.dumps(dim_categories))
    return schema_mapping
