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
"""Script to generate csv and the mcf for the StatisticalVariables. """

import requests
import json
import csv
import re
import os

# Drop these values because they just indicate that there's no data for the
# particular observation
VALUES_TO_DROP = {
    "No data", "Data not available", "Not available", "Not applicable",
    "*Filler*"
}


def get_time_period(entry):
    """For a data entry, get the time period.
    Args:
        entry: an entry from the WHO indicator api eg. {
          "Id": 13233998,
          "IndicatorCode": "EMFLIMITELECTRIC",
          "SpatialDimType": "COUNTRY",
          "SpatialDim": "AUS",
          "TimeDimType": "YEAR",
          "TimeDim": 2014,
          "Dim1Type": "EMFEXPOSED",
          "Dim1": "EMFPUBLIC",
          "Dim2Type": "EMFFREQUENCY",
          "Dim2": "EMFLOW",
          "Dim3Type": null,
          "Dim3": null,
          "DataSourceDimType": null,
          "DataSourceDim": null,
          "Value": "[5]/[10]",
          "NumericValue": null,
          "Low": null,
          "High": null,
          "Comments": "5 kV/m : continuous exposure 5 - 10 kV/m :
                    exposure limited to a few hours a day > 10 kV/m : exposure
                    limited to a few minutes a day, provided the induced current
                    density does not exceed 2 mA/m2 and precautions are taken to
                    prevent hazardous indirect coupling",
          "Date": "2016-05-27T13:50:19.3+02:00",
          "TimeDimensionValue": "2014",
          "TimeDimensionBegin": "2014-01-01T00:00:00+01:00",
          "TimeDimensionEnd": "2014-12-31T00:00:00+01:00"
        }
    Returns:
        time_period as a string
    """
    # TODO: Look into using standard Date/Time parsers to do this
    time_begin = entry.get("TimeDimensionBegin", "").split("-")
    time_begin_year = time_begin[0]
    time_end = entry.get("TimeDimensionEnd", "").split("-")
    time_end_year = time_end[0]
    time_period = "P1Y"
    if time_begin_year != time_end_year:
        diff = int(time_end_year) - int(time_begin_year)
        time_period = f"P{diff + 1}Y"
    return time_period


def get_value(entry):
    """For a data entry, get the value.
    Args: 
        entry: an entry from the WHO indicator api
    Returns:
        value as a string and the statType as a string
    """
    value = entry.get("NumericValue")
    statType = "measuredValue"
    if value is None:
        statType = "measurementResult"
        value = entry.get("Value", "")
        if value:
            value = value.replace(',', '').replace('\n', '')
            if not re.findall('\w', value):
                value = ''
            if "[" in value:
                value = f"'{value}'"
    return value, statType


def get_dimension_pv(cprop_mapping, value_mapping, type_key, value_key, entry):
    """ Get the mapped cprop and value for a dimension in a data entry.
    Args:
        cprop_mapping: map of dimension type code to corresponding schema dcid
        value_mapping: map of dimension type code to map of dimension value to
                       corresponding schema dcid
        type_key: key to get the dimension type from the data entry
        value_key: key to get the dimension value from the data entry
        entry: an entry from the WHO indicator api
    Returns:
        the mapped property and value strings
    """
    d_type = entry.get(type_key, "")
    d_value = entry.get(value_key, "")
    prop = cprop_mapping.get(d_type, "")
    val = value_mapping.get(d_type, {}).get(d_value, "")
    return prop, val


def update_dcid(dcid, prop, val):
    """Given a dcid and pv, update the dcid to include the pv.
    Args:
        dcid: current dcid
        prop: the property of the value to add to the dcid
        val: the value to add to the dcid
    Returns:
        updated dcid as a string
    """
    val_dcid = val.split(":")[-1]
    if val_dcid[0:4] == "WHO/":
        val_dcid = val_dcid[4:]
    if prop == "age":
        val_dcid = val_dcid.replace("+", "PLUS").replace("-", "TO").replace(
            "TOPLUS", "PLUS")
    return dcid + "_" + val_dcid


def get_value_to_write(values_list):
    """Given a list of values, choose the one ranked highest.
    Args: 
        values_list: list of value objects: {
          "spatial_dim": the place this value is for,
          "time_dim_value": the time of this measured value,
          "time_period": the observation period,
          "value": the value,
          "date": the exact date of this value,
          "commentsLength": length of the comments,
          "hasEmptyDimVal": whether this value has any dimension values that
                            mapped to an empty string
        }
    Returns:
        a single value object
    """
    values_list = sorted(values_list,
                         key=lambda x: x.get("commentsLength"),
                         reverse=True)
    values_list = sorted(values_list,
                         key=lambda x: x.get("date", ""),
                         reverse=True)
    values_list = sorted(values_list, key=lambda x: x.get("hasEmptyDimVal"))
    return values_list[0]


def process_dimensions(cprop_mapping, value_mapping, person_dimensions, entry,
                       mcf, sv_dcid):
    """ Process each of the dimensions in the data entry (up to 3)
    Args:
        cprop_mapping: map of dimension type code to corresponding schema dcid
        values_mapping: map of dimension type code to map of dimension value to
                        corresponding schema dcid
        person_dimensions: list of cprops that indicate populationType of person
        entry: an entry from the WHO indicator api
        mcf: list of strings that correspond to the statvar mcf file
        sv_dcid: dcid of the current stat var
    Returns:
        sv_dcid: the updated sv_dcid
        has_empty_mapped_val: whether any dimension values mapped to an empty
                              string
    """
    has_empty_mapped_val = False
    has_person_dimension = False
    d1_prop, d1_val = get_dimension_pv(cprop_mapping, value_mapping, "Dim1Type",
                                       "Dim1", entry)
    if d1_prop and not d1_val:
        has_empty_mapped_val = True
    if entry.get("Dim1Type", "") in person_dimensions:
        has_person_dimension = True
    if d1_prop and d1_val:
        mcf.append(f"{d1_prop}: {d1_val}")
        sv_dcid = update_dcid(sv_dcid, d1_prop, d1_val)
    d2_prop, d2_val = get_dimension_pv(cprop_mapping, value_mapping, "Dim2Type",
                                       "Dim2", entry)
    if d2_prop and not d2_val:
        has_empty_mapped_val = True
    if entry.get("Dim2Type", "") in person_dimensions:
        has_person_dimension = True
    if d2_prop and d2_val:
        mcf.append(f"{d2_prop}: {d2_val}")
        sv_dcid = update_dcid(sv_dcid, d2_prop, d2_val)
    d3_prop, d3_val = get_dimension_pv(cprop_mapping, value_mapping, "Dim3Type",
                                       "Dim3", entry)
    if d3_prop and not d3_val:
        has_empty_mapped_val = True
    if entry.get("Dim3Type", "") in person_dimensions:
        has_person_dimension = True
    if d3_prop and d3_val:
        mcf.append(f"{d3_prop}: {d3_val}")
        sv_dcid = update_dcid(sv_dcid, d3_prop, d3_val)
    if has_person_dimension:
        mcf.append("populationType: dcs:Person")
    else:
        mcf.append("populationType: dcs:Thing")
    return sv_dcid, has_empty_mapped_val


def generate_csv_and_sv(data_files, schema_mapping, sv_dcid_mapping,
                        output_dir):
    """ Generate the csv and stat var mcf files.
  Args:
      data_files: list of the raw data json files
      schema_mapping: an object: {
            cprops: map of dimension type code to its corresponding schema dcid,
            values: map of dimension type code to map of dimension value to its
                    corresponding schema dcid,
            indicators: map of indicator codes to its corresponding schema dcid
      }
      sv_dcid_mapping: a map of autogenerated sv dcid to curated sv dcid
      output_dir: directory to output the csv, stat var mcf, and skipped dcids info to
  """
    seen_sv = set()
    # map of sv dcids that are used but don't have a mcf node generated to a
    # set of autogenerated sv dcids that are mapped to this dcid.
    skipped_mcf_sv = {}
    mcf_result = []
    cprop_mapping = schema_mapping.get("cprops", {})
    value_mapping = schema_mapping.get("values", {})
    person_dimensions = schema_mapping.get("personDimensions", {})
    with open(os.path.join(output_dir, "who.csv"), "w+") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["year", "period", "country", "statVar", "value"])
        for f in data_files:
            with open(f, "r+") as indicator_values:
                indicator_values = json.load(indicator_values).get("value", [])
            value_map = {}
            for entry in indicator_values:
                time_dim_value = entry.get("TimeDim")
                if not time_dim_value:
                    continue
                time_period = get_time_period(entry)
                spatial_dim_type = entry.get("SpatialDimType")
                if not spatial_dim_type == "COUNTRY":
                    continue
                spatial_dim = entry.get("SpatialDim")
                i_code = entry.get("IndicatorCode", "")
                sv_dcid = "WHO/" + i_code
                mcf = [
                    "typeOf: dcs:StatisticalVariable",
                    f"measuredProperty: dcs:who/{i_code}"
                ]
                value, statType = get_value(entry)
                mcf.append(f"statType: dcs:{statType}")
                if not value or value in VALUES_TO_DROP:
                    continue
                sv_dcid, has_empty_mapped_val = process_dimensions(
                    cprop_mapping, value_mapping, person_dimensions, entry, mcf,
                    sv_dcid)
                if sv_dcid in sv_dcid_mapping:
                    # if there is a curated dcid for this sv dcid, use the
                    # curated dcid and add it to the skipped_mcf_sv so that we
                    # skip adding an mcf node for this dcid
                    curated_dcid = sv_dcid_mapping[sv_dcid]
                    if not curated_dcid in skipped_mcf_sv:
                        skipped_mcf_sv[curated_dcid] = set()
                    skipped_mcf_sv[curated_dcid].add(sv_dcid)
                    sv_dcid = curated_dcid
                if not sv_dcid in seen_sv:
                    value_map[sv_dcid] = {}
                    if not sv_dcid in skipped_mcf_sv:
                        mcf.insert(0, f"Node: dcid:{sv_dcid}")
                        mcf_result.extend(mcf + [""])
                seen_sv.add(sv_dcid)
                map_key = f"{spatial_dim}^{time_dim_value}^{time_period}"
                if not map_key in value_map[sv_dcid]:
                    value_map[sv_dcid][map_key] = []
                comments_length = 0
                if entry.get("Comments", ""):
                    comments_length = len(entry.get("Comments"))
                new_value_entry = {
                    "spatial_dim": spatial_dim,
                    "time_dim_value": time_dim_value,
                    "time_period": time_period,
                    "value": value,
                    # date, commentsLength, and hasEmptyDimVal used to choose
                    # the value entry to use when there are duplicate obs values
                    "date": entry.get("Date", ""),
                    "commentsLength": comments_length,
                    "hasEmptyDimVal": has_empty_mapped_val
                }
                value_map[sv_dcid][map_key].append(new_value_entry)
            for sv_dcid in value_map:
                for key in value_map[sv_dcid]:
                    val_to_write = get_value_to_write(value_map[sv_dcid][key])
                    spatial_dim = val_to_write.get("spatial_dim")
                    writer.writerow([
                        val_to_write.get("time_dim_value"),
                        val_to_write.get("time_period"),
                        f"dcid:country/{spatial_dim}", f"dcs:{sv_dcid}",
                        val_to_write.get("value")
                    ])
        with open(os.path.join(output_dir, "who_sv.mcf"), "w+") as mcf_file:
            mcf_file.write("\n".join(mcf_result))
        with open(os.path.join(output_dir, "skipped_mcf_sv.json"),
                  "w+") as skipped_file:
            skipped_mcf_sv_result = {}
            for sv in skipped_mcf_sv:
                skipped_mcf_sv_result[sv] = list(skipped_mcf_sv[sv])
            skipped_file.write(json.dumps(skipped_mcf_sv_result))
