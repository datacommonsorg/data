# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script to parse and pre-process the Parent Company Info for Facilities tracked by EPA."""

import os.path
import pathlib
import sys

import csv
import difflib
import json
import pandas as pd
import re

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))
from us_epa.util import facilities_helper as fh
from us_epa.parent_company import static_corrections as sc

flags.DEFINE_string("input_download_path", "tmp_data", "Input directory")
flags.DEFINE_string("existing_facilities_file", "existing_facilities",
                    "Filename for existing facilities ids")
flags.DEFINE_string("output_base_path", "output",
                    "Output directory for processed data.")

FLAGS = flags.FLAGS

# V_PARENT_COMPANY_INFO table
_TABLE_PREFIX = "D_GHG_B"
_TABLE = "V_PARENT_COMPANY_INFO"

_EPA_FACILITY_GHG_ID = "epaGhgrpFacilityId"

# Mapping which contains the company id duplicates.
_DUPLICATE_MAPPING = {}


def _str(v):
    if not v:
        return ''
    return '"' + v + '"'


def _str_matching_replace(s):
    s = s.replace('LLC', '')
    s = s.replace('Corp', '')
    s = s.replace('Inc', '')
    s = s.replace('LP', '')

    # Ends with "Co"
    s = re.sub('Co$', '', s)
    return s


def _add_to_duplicate_mapping(company_id_1, company_id_2, company_id_count):

    # If (company_id_1, company_id_2) exist already (in either direction),
    # then no point continuing.
    if ((company_id_1 in _DUPLICATE_MAPPING and
         company_id_2 == _DUPLICATE_MAPPING[company_id_1]) or
        (company_id_2 in _DUPLICATE_MAPPING and
         company_id_1 == _DUPLICATE_MAPPING[company_id_2])):

        return

    # Determine whether company_id_1 should point to company_id_2 or the other
    # way round.
    # The primary criteria is:
    #   1. The id with appears fewer times should be replaced.
    #   2. If they are tied on the occurences, then replace the shorter id.
    key = company_id_1
    val = company_id_2
    comp_count = company_id_count[company_id_2]

    if ((company_id_count[company_id_1] > comp_count) or
        ((company_id_count[company_id_1] == comp_count) and
         (len(company_id_1) >= len(company_id_2)))):
        key = company_id_2
        val = company_id_1
        comp_count = company_id_count[company_id_1]

    # A previous mapping might already exist for 'key'. If so, only update the
    # mapping if the company_id being pointed to occurs less frequently than the
    # the 'value'.
    existing_company = val
    existing_count = comp_count
    if key in _DUPLICATE_MAPPING:
        existing_company = _DUPLICATE_MAPPING[key]
        existing_count = company_id_count[existing_company]

    # Only update if the company_id being mapped to has a greater count than
    # the existing_count (for a different company id).
    if ((comp_count >= existing_count) or
        ((comp_count == existing_count) and
         (len(val) >= len(existing_company)))):
        _DUPLICATE_MAPPING[key] = val


def _add_static_duplicates(static_mappings, company_id_count):
    for k, v in static_mappings.items():
        if k not in company_id_count:
            company_id_count[k] = 0
        if v not in company_id_count:
            company_id_count[v] = 1

        _add_to_duplicate_mapping(k, v, company_id_count)


def _insert_overlaps(loc_map, company_id_count):
    count_dupe_loc = 0
    loc_id_contained_count = 0
    for a, v in loc_map.items():
        v = list(v)
        if len(v) > 1:
            count_dupe_loc += 1
            id_match_found = False

            id_pairs = {}
            for i in range(len(v)):
                for j in range(i + 1, len(v)):
                    # Determine the SequenceMatcher ratio between the two ids.
                    v_i = v[i]
                    v_j = v[j]
                    m1 = v_i.lower()
                    m2 = v_j.lower()
                    seq1 = difflib.SequenceMatcher(a=_str_matching_replace(m1),
                                                   b=_str_matching_replace(m2))
                    seq2 = difflib.SequenceMatcher(a=m1, b=m2)

                    diff_score = max(seq1.ratio(), seq2.ratio())
                    id_pairs.update({(v_i, v_j): diff_score})

                    # If the score is > 80%, then add the duplicate relationship
                    if (diff_score > 0.8):
                        id_match_found = True
                        _add_to_duplicate_mapping(v_i, v_j, company_id_count)

            if id_match_found:
                loc_id_contained_count += 1

    return (count_dupe_loc, loc_id_contained_count)


def _resolve_multiple_indirections():
    # For multiple re-directions, map the final replacement ID for each of the
    # IDs being replaced.
    for k, v in _DUPLICATE_MAPPING.items():
        v_loc = v
        while (1):
            if v_loc in _DUPLICATE_MAPPING.keys():
                v_loc = _DUPLICATE_MAPPING[v_loc]
            else:
                _DUPLICATE_MAPPING[k] = v_loc
                break


def preprocess(input_table_path, existing_facilities_file):
    # Get the existing facility ids in a set.
    existing_facilities_path = os.path.join(input_table_path,
                                            existing_facilities_file + ".csv")

    relevant_facility_ids = set(
        pd.read_csv(existing_facilities_path)[_EPA_FACILITY_GHG_ID].values)
    input_table = os.path.join(input_table_path, _TABLE + ".csv")

    unique_company_names = set()
    address_map = {}
    facility_map = {}

    unique_company_ids = set()
    company_id_count = {}
    num_rows_written = 0

    # Enter all static mappings.
    print("First inserting static mappings...")
    _add_static_duplicates(sc.company_id_mappings, company_id_count)

    print("Reading Table Info data...")
    with open(input_table, "r") as rfp:
        cr = csv.DictReader(rfp)
        for in_row in cr:
            facility_id = fh.v(_TABLE,
                               in_row,
                               "FACILITY_ID",
                               table_prefix=_TABLE_PREFIX)
            ghg_id = _EPA_FACILITY_GHG_ID + "/" + facility_id

            # Only proceed if the facility_id exists in Data Commons.
            if ghg_id not in relevant_facility_ids:
                continue

            company_name = fh.get_name(_TABLE,
                                       in_row,
                                       "PARENT_COMPANY_NAME",
                                       table_prefix=_TABLE_PREFIX)
            company_name = company_name.replace("\"", "").replace("'", "")
            if not company_name:
                continue
            unique_company_names.add(company_name)
            company_id = fh.name_to_id(company_name)

            address = _str(
                fh.get_address(_TABLE, in_row, table_prefix=_TABLE_PREFIX))

            # Populate the address_map and facility_map.
            if address not in address_map:
                address_map[address] = set()

            existing_ids = address_map[address]
            existing_ids.add(company_id)
            address_map.update({address: existing_ids})

            if facility_id not in facility_map:
                facility_map[facility_id] = set()
            existing_ids = facility_map[facility_id]
            existing_ids.add(company_id)
            facility_map.update({facility_id: existing_ids})

            unique_company_ids.add(company_id)

            # Count the number of occurences of the company_id.
            if company_id not in company_id_count:
                company_id_count[company_id] = 0
            company_id_count[company_id] += 1

    print("Determining Address duplicates...")
    (count_dupe_addr,
     address_id_contained_count) = _insert_overlaps(address_map,
                                                    company_id_count)
    print("Determining Facility duplicates...")
    (count_dupe_facility,
     facility_id_contained_count) = _insert_overlaps(facility_map,
                                                     company_id_count)

    print("Resolving duplicate indirections..")
    _resolve_multiple_indirections()

    # Write.
    print("Writing to file...")
    output_path = os.path.join(input_table_path, "DuplicateIdMappings.csv")
    with open(output_path, "w") as opth:
        writer = csv.DictWriter(opth, ["Id", "MappedTo", "Occurences"],
                                doublequote=False,
                                escapechar="\\")
        writer.writeheader()

        for k, v in dict(sorted(_DUPLICATE_MAPPING.items())).items():
            d = {"Id": k, "MappedTo": v, "Occurences": company_id_count[v]}
            writer.writerow(d)
            num_rows_written += 1

    # Print some statistics.
    print("****************")
    print("Num Rows Written = ", num_rows_written)
    print("Number records: ", len(pd.read_csv(existing_facilities_path)))
    print("Unique Facilities: ", len(relevant_facility_ids))
    print("Unique Company Names: ", len(unique_company_names))

    print("Duplicate Keys: ", len(_DUPLICATE_MAPPING))
    print("Unique (before) Company Ids: ", len(unique_company_ids))
    print("Unique (after) Company Ids: ",
          len(unique_company_ids) - len(_DUPLICATE_MAPPING))
    print("****************")
    print("duplicate address = ", count_dupe_addr)
    print("duplicate address, id match found = ", address_id_contained_count)
    print("duplicate facility = ", count_dupe_facility)
    print("duplicate facility, id match found = ", facility_id_contained_count)


def main(_):
    # Validate inputs.
    assert FLAGS.input_download_path
    assert FLAGS.existing_facilities_file
    assert os.path.exists(
        os.path.join(FLAGS.input_download_path,
                     FLAGS.existing_facilities_file + ".csv"))
    assert os.path.exists(
        os.path.join(FLAGS.input_download_path, _TABLE + ".csv"))

    preprocess(FLAGS.input_download_path, FLAGS.existing_facilities_file)


if __name__ == "__main__":
    app.run(main)
