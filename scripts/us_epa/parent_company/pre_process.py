# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script to download, parse and process the Parent Company Info for Facilities tracked by EPA."""

import os.path
import pathlib
import sys
import csv
import difflib  # Still needed for SequenceMatcher
import json  # Still needed for some internal logic, though not directly in the fix area
import pandas as pd  # Used for pd.read_csv
import re  # Still needed for regex in _str_matching_replace

from absl import app
from absl import flags
from absl import logging

# Configure absl.logging for console output
logging.set_verbosity(logging.INFO)

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

# Mapping which contains the company id duplicates. This is global and is populated by preprocess.
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
    s = re.sub('Co$', '', s)
    return s


def _add_to_duplicate_mapping(company_id_1, company_id_2, company_id_count):
    # This function operates on the global _DUPLICATE_MAPPING
    if ((company_id_1 in _DUPLICATE_MAPPING and
         company_id_2 == _DUPLICATE_MAPPING[company_id_1]) or
        (company_id_2 in _DUPLICATE_MAPPING and
         company_id_1 == _DUPLICATE_MAPPING[company_id_2])):

        return

    key = company_id_1
    val = company_id_2
    comp_count = company_id_count.get(company_id_2, 0)

    if ((company_id_count.get(company_id_1, 0) > comp_count) or
        ((company_id_count.get(company_id_1, 0) == comp_count) and
         (len(company_id_1) >= len(company_id_2)))):
        key = company_id_2
        val = company_id_1
        comp_count = company_id_count.get(company_id_1, 0)

    existing_company = val
    existing_count = comp_count
    if key in _DUPLICATE_MAPPING:
        existing_company = _DUPLICATE_MAPPING[key]
        existing_count = company_id_count.get(existing_company, 0)

    if ((comp_count >= existing_count) or
        ((comp_count == existing_count) and
         (len(val) >= len(existing_company)))):
        _DUPLICATE_MAPPING[key] = val


def _add_static_duplicates(static_mappings, company_id_count):
    logging.info("Adding static duplicate mappings...")
    for k, v in static_mappings.items():
        if k not in company_id_count:
            company_id_count[k] = 0
        if v not in company_id_count:
            company_id_count[v] = 1

        _add_to_duplicate_mapping(k, v, company_id_count)
    logging.info(
        f"Static mappings added. Current duplicate map size: {len(_DUPLICATE_MAPPING)}"
    )


def _insert_overlaps(loc_map, company_id_count):
    count_dupe_loc = 0
    loc_id_contained_count = 0
    logging.info("Inserting overlaps based on location maps...")
    for a, v in loc_map.items():
        v = list(v)
        if len(v) > 1:
            count_dupe_loc += 1
            id_match_found = False

            for i in range(len(v)):
                for j in range(i + 1, len(v)):
                    v_i = v[i]
                    v_j = v[j]
                    m1 = v_i.lower()
                    m2 = v_j.lower()

                    seq1 = difflib.SequenceMatcher(a=_str_matching_replace(m1),
                                                   b=_str_matching_replace(m2))
                    seq2 = difflib.SequenceMatcher(a=m1, b=m2)

                    diff_score = max(seq1.ratio(), seq2.ratio())

                    if (diff_score > 0.8):
                        id_match_found = True
                        _add_to_duplicate_mapping(v_i, v_j, company_id_count)

            if id_match_found:
                loc_id_contained_count += 1

    return (count_dupe_loc, loc_id_contained_count)


def _resolve_multiple_indirections():
    logging.info("Resolving multiple indirections in duplicate mappings...")
    for k, v in _DUPLICATE_MAPPING.items():
        v_loc = v
        path = [k]
        while v_loc in _DUPLICATE_MAPPING:
            if v_loc in path:
                logging.error(
                    f" Cycle detected in duplicate mapping starting from {k}. Path: {path + [v_loc]}"
                )
                break
            path.append(v_loc)
            v_loc = _DUPLICATE_MAPPING[v_loc]
        _DUPLICATE_MAPPING[k] = v_loc
    logging.info("Multiple indirections resolved.")


def preprocess(input_table_path, existing_facilities_file):
    """
    Performs core preprocessing steps, primarily focusing on identifying duplicate
    company IDs and building the _DUPLICATE_MAPPING.

    This function is designed to be called by `process_companies`
    """
    logging.info(
        f"Starting `preprocess` function. Input path: {input_table_path}")

    existing_facilities_path = os.path.join(input_table_path,
                                            existing_facilities_file + ".csv")
    logging.info(
        f"Loading existing facilities from: {existing_facilities_path}")
    relevant_facility_ids = set(
        pd.read_csv(existing_facilities_path)[_EPA_FACILITY_GHG_ID].values)
    logging.info(f"Loaded {len(relevant_facility_ids)} relevant facility IDs.")

    input_table = os.path.join(input_table_path, _TABLE + ".csv")
    logging.info(f"Loading main input table from: {input_table}")

    unique_company_names = set()
    address_map = {}
    facility_map = {}

    unique_company_ids = set()
    company_id_count = {}
    # num_rows_written is no longer tracked here. It's tracked in process_companies.

    logging.info("First inserting static mappings...")
    _add_static_duplicates(sc.company_id_mappings, company_id_count)

    logging.info("Reading Table Info data to build maps...")
    with open(input_table, "r") as rfp:
        cr = csv.DictReader(rfp)

        logging.info(f"CSV Headers found in '{input_table}': {cr.fieldnames}")

        # Determine the actual key used in the CSV for facility ID
        actual_facility_id_csv_key = None
        if "FACILITY_ID" in cr.fieldnames:
            actual_facility_id_csv_key = "FACILITY_ID"
        elif "facility_id" in cr.fieldnames:
            actual_facility_id_csv_key = "facility_id"

        if not actual_facility_id_csv_key:
            logging.fatal(
                f" FATAL: Neither 'FACILITY_ID' nor 'facility_id' found in CSV headers. Cannot proceed. Found headers: {cr.fieldnames}"
            )
            sys.exit(1)

        logging.info(
            f"Using CSV header '{actual_facility_id_csv_key}' for Facility ID extraction."
        )

        for i, in_row in enumerate(cr):
            if i % 500 == 0:
                logging.info(f"Processing row {i} from input table...")

            # --- CRITICAL SIMPLIFICATION: Get facility_id directly using correct CSV key ---
            # And pass EMPTY table_prefix to fh.v so it uses row.get(col, '')
            # The 'col' argument to fh.v should be the actual key from the DictReader.

            # Option A: Directly use the value from the in_row dict
            # This is the simplest if fh.v just needs the value and not
            # to resolve it using table_prefix internally.
            facility_id = in_row.get(actual_facility_id_csv_key, '')

            if not facility_id:  # Check if the extracted ID is empty/falsy
                logging.fatal(
                    f" FATAL: Mandatory FACILITY_ID is empty in row {i+1}. Skipping. Row content: {in_row}"
                )
                # _COUNTERS_COMPANIES["facility_id_extraction_failed"].add(str(in_row)) # Counters are in process_companies
                continue

            ghg_id = _EPA_FACILITY_GHG_ID + "/" + facility_id

            if ghg_id not in relevant_facility_ids:

                continue

            company_name = fh.get_name(
                _TABLE,
                in_row,
                "PARENT_COMPANY_NAME",
                table_prefix=_TABLE_PREFIX
            )  # This should use table_prefix for company_name
            company_name = company_name.replace("\"", "").replace("'", "")
            if not company_name:

                continue
            unique_company_names.add(company_name)
            company_id = fh.name_to_id(company_name)

            if not company_id:
                logging.fatal(
                    f" FATAL: Mandatory company_id is empty (from name_to_id) for row {i+1}. Skipping. Row content: {in_row}"
                )
                # _COUNTERS_COMPANIES["company_id_name_to_id_failed"].add(str(in_row))
                continue

            address = _str(
                fh.get_address(_TABLE, in_row, table_prefix=_TABLE_PREFIX)
            )  # This should use table_prefix for address

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

            if company_id not in company_id_count:
                company_id_count[company_id] = 0
            company_id_count[company_id] += 1

    logging.info("Completed reading Table Info data and building maps.")
    logging.info("Determining Address duplicates...")
    (count_dupe_addr,
     address_id_contained_count) = _insert_overlaps(address_map,
                                                    company_id_count)
    logging.info("Determining Facility duplicates...")
    (count_dupe_facility,
     facility_id_contained_count) = _insert_overlaps(facility_map,
                                                     company_id_count)

    logging.info("Resolving duplicate indirections..")
    _resolve_multiple_indirections()

    # --- Start writing DuplicateIdMappings.csv ---
    rows_written_to_duplicates_csv = 0
    logging.info("Writing to DuplicateIdMappings.csv...")
    output_path = os.path.join(input_table_path, "DuplicateIdMappings.csv")
    with open(output_path, "w") as opth:
        writer = csv.DictWriter(opth, ["Id", "MappedTo", "Occurences"],
                                doublequote=False,
                                escapechar="\\")
        writer.writeheader()

        for k, v in dict(sorted(_DUPLICATE_MAPPING.items())).items():
            d = {
                "Id": k,
                "MappedTo": v,
                "Occurences": company_id_count.get(v, 0)
            }
            writer.writerow(d)
            rows_written_to_duplicates_csv += 1
    # --- End writing DuplicateIdMappings.csv ---
    logging.info(
        f"Num Rows Written (Duplicate Mappings) = {rows_written_to_duplicates_csv}"
    )
    logging.info(
        f"Number records (from existing_facilities_path): {len(pd.read_csv(existing_facilities_path))}"
    )
    logging.info(f"Unique Facilities: {len(relevant_facility_ids)}")
    logging.info(f"Unique Company Names: {len(unique_company_names)}")

    logging.info(f"Duplicate Keys: {len(_DUPLICATE_MAPPING)}")
    logging.info(f"Unique (before) Company Ids: {len(unique_company_ids)}")
    logging.info(
        f"Unique (after) Company Ids: {len(unique_company_ids) - len(_DUPLICATE_MAPPING)}"
    )

    logging.info(f"duplicate address = {count_dupe_addr}")
    logging.info(
        f"duplicate address, id match found = {address_id_contained_count}")
    logging.info(f"duplicate facility = {count_dupe_facility}")
    logging.info(
        f"duplicate facility, id match found = {facility_id_contained_count}")

    # We remove the detailed _COUNTERS_COMPANIES printing from here
    # as _COUNTERS_COMPANIES is part of the `process_companies` function's scope,
    # not `preprocess`.


def main(_):
    # Validate inputs.
    assert FLAGS.input_download_path, "Input download path not specified."
    assert FLAGS.existing_facilities_file, "Existing facilities file not specified."

    existing_facilities_full_path = os.path.join(
        FLAGS.input_download_path, FLAGS.existing_facilities_file + ".csv")
    main_input_table_full_path = os.path.join(FLAGS.input_download_path,
                                              _TABLE + ".csv")

    assert os.path.exists(existing_facilities_full_path), \
        f"Existing facilities file not found: {existing_facilities_full_path}"
    assert os.path.exists(main_input_table_full_path), \
        f"Main input table file not found: {main_input_table_full_path}"

    preprocess(FLAGS.input_download_path, FLAGS.existing_facilities_file)


if __name__ == "__main__":
    app.run(main)
