# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        https://www.apache.org/licenses/LICENSE-2.0
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
import difflib
import json
import pandas as pd
import re

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


FLAGS = flags.FLAGS

flags.DEFINE_string("input_download_path", "tmp_data", "Input directory")
flags.DEFINE_string("existing_facilities_file", "existing_facilities",
                     "Filename for existing facilities ids")
flags.DEFINE_string("output_base_path", "output",
                     "Output directory for processed data.")
flags.DEFINE_string("parent_co_output_path", "table",
                     "Output directory for company info.")
flags.DEFINE_string("ownership_output_path", "ownership",
                     "Output directory for ownership.")
flags.DEFINE_string("svobs_output_path", "svobs",
                     "Output directory for StatVarObs.")

_DC_API_URL = "https://api.datacommons.org/place/stat-vars"

# V_PARENT_COMPANY_INFO table
_TABLE_PREFIX = "D_GHG_B"
_TABLE = "V_PARENT_COMPANY_INFO"

_OUT_FILE_PREFIX = "EpaParentCompany"
_OUT_SVOBS_FILE_PREFIX = "SVObs"
_COUNTY_CANDIDATES_CACHE = {} # Used by fh.get_county_candidates


# Cleaned CSV Columns (these are the *target* column names in the output CSVs)
_DCID = "dcid"
_EPA_FACILITY_GHG_ID = "epaGhgrpFacilityId"
_NAME = "name"
_YEAR = "year"
_PERCENT_OWNERSHIP = "ownership"
_ADDRESS = "address"
_CIP = "locatedIn"

# The following are for the StatVarOvbservations.
_PARENT_COMPANY_DCID = 'dcid'
_SV_MEASURED = "sv_measured"
_OBSERVATION_PERIOD = "obs_period"
_SVO_VAL = "value"
_OBSERVATION_DATE = "year"

_TABLE_CLEAN_CSV_HDR = (_DCID, _NAME, _ADDRESS, _CIP)
_OWNERSHIP_CLEAN_CSV_HDR = (_DCID, _EPA_FACILITY_GHG_ID, _YEAR,
                             _PERCENT_OWNERSHIP)
_SVOBS_CLEAN_CSV_HDR = (_PARENT_COMPANY_DCID, _SV_MEASURED, _OBSERVATION_PERIOD,
                         _SVO_VAL, _OBSERVATION_DATE)

# Global dictionaries for deduplication and counters
_DUPLICATE_MAPPING = {}
_COUNTERS_COMPANIES = {
    "missing_zip": set(),
    "percent_ownership_not_found": set(),
    "facility_does_not_exist": set(),
    "company_name_not_found": set(),
    "year_does_not_exist": set(),
    "company_ids_replaced": set(),
    "facility_id_extraction_failed": set(),
    "company_id_name_to_id_failed": set(),
}

# --- ALL HELPER FUNCTIONS MUST BE DEFINED HERE IN THE GLOBAL SCOPE ---

def _gen_table_mcf():
    lines = [
        "Node: dcid:EpaParentCompany",
        "subClassOf: dcs:Organization",
        "name: EpaParentCompany",
        "typeOf: schema:Class",
        "\n",
        "Node: dcid:locatedIn",
        "typeOf: schema:Property",
        "domainIncludes: schema:Place",
        "rangeIncludes: schema:Place",
        "name: locatedIn",
    ]
    return "\n".join(lines)


def _gen_ownership_mcf():
    lines = [
        "Node: dcid:EpaOrganizationOwnership",
        "description: The ownership of an EPA Facility by an Organization in a given year.",
        "typeOf: dcs:StatisticalVariable",
        "populationType: dcs:EpaParentCompany",
        "measuredProperty: owns",
        "statType: measurementResult",
        "\n",
        "Node: dcid:ownershipPercentage",
        "typeOf: schema:Property",
        "domainIncludes: dcs:EpaParentCompany",
        "rangeIncludes: schema:Number",
        "name: ownershipPercentage",
    ]
    return "\n".join(lines)


def _gen_ownership_tmcf():
    lines = [
        "Node: E:EpaParentCompanyOwnership->E0",
        "typeOf: dcs:StatVarObservation",
        "variableMeasured: dcid:EpaOrganizationOwnership",
        f"observationDate: C:EpaParentCompanyOwnership->{_YEAR}",
        f"observationAbout: C:EpaParentCompanyOwnership->{_DCID}",
        f"value: C:EpaParentCompanyOwnership->{_EPA_FACILITY_GHG_ID}",
        f"ownershipPercentage: C:EpaParentCompanyOwnership->{_PERCENT_OWNERSHIP}",
    ]
    return "\n".join(lines) + "\n"


def _gen_company_tmcf():
    lines = [
        "Node: E:EpaParentCompanyTable->E1",
        "typeOf: dcs:EpaParentCompany",
        f"{_DCID}: C:EpaParentCompanyTable->{_DCID}",
        f"{_NAME}: C:EpaParentCompanyTable->{_NAME}",
        f"{_ADDRESS}: C:EpaParentCompanyTable->{_ADDRESS}",
        f"{_CIP}: C:EpaParentCompanyTable->{_CIP}",
    ]
    return "\n".join(lines) + "\n"


def _gen_svobs_tmcf():
    lines = [
        "Node: E:EpaParentCompanyStatVarObs->E0",
        'typeOf: dcs:StatVarObservation',
        f'observationAbout: C:EpaParentCompanyStatVarObs->{_PARENT_COMPANY_DCID}',
        f'variableMeasured: C:EpaParentCompanyStatVarObs->{_SV_MEASURED}',
        f'observationPeriod: C:EpaParentCompanyStatVarObs->{_OBSERVATION_PERIOD}',
        'unit: dcs:MetricTonCO2e',
        'measurementMethod: dcs:dcAggregate/EPA_GHGRP',
        f'value: C:EpaParentCompanyStatVarObs->{_SVO_VAL}',
        f'observationDate: C:EpaParentCompanyStatVarObs->{_OBSERVATION_DATE}',
    ]
    return "\n".join(lines) + "\n"

def _str_matching_replace(s):
    s = s.replace('LLC', '')
    s = s.replace('Corp', '')
    s = s.replace('Inc', '')
    s = s.replace('LP', '')
    s = re.sub('Co$', '', s)
    return s


def _add_to_duplicate_mapping(company_id_1, company_id_2, company_id_count):
    if ((company_id_1 in _DUPLICATE_MAPPING and
             company_id_2 == _DUPLICATE_MAPPING[company_id_1]) or
            (company_id_2 in _DUPLICATE_MAPPING and
             company_id_1 == _DUPLICATE_MAPPING[company_id_2])):
        logging.debug(f"Skipping duplicate mapping already present: {company_id_1} <-> {company_id_2}")
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
        logging.debug(f"Added/Updated duplicate mapping: {key} -> {val}")


def _add_static_duplicates(static_mappings, company_id_count):
    logging.info("Adding static duplicate mappings...")
    for k, v in static_mappings.items():
        if k not in company_id_count:
            company_id_count[k] = 0
        if v not in company_id_count:
            company_id_count[v] = 1
        
        _add_to_duplicate_mapping(k, v, company_id_count)
    logging.info(f"Static mappings added. Current duplicate map size: {len(_DUPLICATE_MAPPING)}")


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
                    
                    logging.debug(f"Comparing: '{m1}' vs '{m2}'")

                    seq1 = difflib.SequenceMatcher(a=_str_matching_replace(m1),
                                                     b=_str_matching_replace(m2))
                    seq2 = difflib.SequenceMatcher(a=m1, b=m2)

                    diff_score = max(seq1.ratio(), seq2.ratio())
                    logging.debug(f"Similarity score: {diff_score}")
                    
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
                logging.error(f"❌ Cycle detected in duplicate mapping starting from {k}. Path: {path + [v_loc]}")
                break
            path.append(v_loc)
            v_loc = _DUPLICATE_MAPPING[v_loc]
        _DUPLICATE_MAPPING[k] = v_loc
    logging.info("Multiple indirections resolved.")


def _get_county(company_id, zip, year):
    """Resolve the geo relations for the given Facility"""
    if zip == "zip/00000" or zip == "":
        _COUNTERS_COMPANIES["missing_zip"].add((company_id, year))
        return ""

    # Assumes fh.get_county_candidates does not use problematic table/table_prefix for its internal lookups.
    county_candidates = fh.get_county_candidates(zip)
    if not county_candidates:
        _COUNTERS_COMPANIES["missing_zip"].add((company_id, year))
        return ""

    county = ""
    if county_candidates[0]:
        county = county_candidates[0][0]
    elif county_candidates[1]:
        county = county_candidates[1][0]

    return county


def _get_key_val_for_svobs(facility_id, stat_var, facility_comp_ownership,
                             svobs_series):
    key_val = {}
    for svo_dict in svobs_series:
        for dt, v in svo_dict['val'].items():
            if (facility_id, dt) in facility_comp_ownership:
                for company_id, percentage in facility_comp_ownership[(
                        facility_id, dt)].items():
                    key = (company_id, stat_var, svo_dict['observationPeriod'],
                            dt)
                    if key not in key_val:
                        key_val[key] = {}
                    key_val.update({
                        key: {
                            _PARENT_COMPANY_DCID: company_id,
                            _SV_MEASURED: stat_var,
                            _OBSERVATION_PERIOD: svo_dict['observationPeriod'],
                            _OBSERVATION_DATE: dt,
                            _SVO_VAL: v * float(percentage) / 100
                        }
                    })

    return key_val


def _facility_year_company_percentages(ownership_filepath):
    facility_company_ownership = {}
    with open(ownership_filepath, "r", newline='') as owfp:
        cr = csv.DictReader(owfp)
        for in_row in cr:
            key = (in_row[_EPA_FACILITY_GHG_ID], in_row[_YEAR])
            if key not in facility_company_ownership:
                facility_company_ownership[key] = {}
            facility_company_ownership[key].update(
                {in_row[_DCID]: in_row[_PERCENT_OWNERSHIP]})

    return facility_company_ownership


def counters_string(counter_dict):
    result = []
    for k, v in counter_dict.items():
        if isinstance(v, set):
            result.append(f"{k} -> {len(v)} entries. Sample: {list(v)[:5]}")
        else:
            result.append(f"{k} -> {v}")
    return "\n".join(result)


def _run_deduplication_preprocessing_steps(input_table_path, existing_facilities_file):
    """
    This function consolidates the duplicate mapping generation logic.
    It populates the global _DUPLICATE_MAPPING and _COUNTERS_COMPANIES.
    """
    logging.info(f"Starting deduplication preprocessing steps. Input path: {input_table_path}")
    
    existing_facilities_path = os.path.join(input_table_path,
                                             existing_facilities_file + ".csv")
    logging.info(f"Loading existing facilities from: {existing_facilities_path}")
    relevant_facility_ids = set(
        pd.read_csv(existing_facilities_path)[_EPA_FACILITY_GHG_ID].values)
    logging.info(f"Loaded {len(relevant_facility_ids)} relevant facility IDs.")

    input_table_csv_path = os.path.join(input_table_path, _TABLE + ".csv")
    logging.info(f"Loading main input table from: {input_table_csv_path}")

    unique_company_names = set()
    address_map = {}
    facility_map = {}

    unique_company_ids = set()
    company_id_count = {}

    logging.info("First inserting static mappings...")
    _add_static_duplicates(sc.company_id_mappings, company_id_count)

    logging.info("Reading Table Info data to build maps...")
    with open(input_table_csv_path, "r", newline='') as rfp:
        cr = csv.DictReader(rfp)
        
        logging.info(f"CSV Headers found in '{input_table_csv_path}': {cr.fieldnames}")
        
        # --- Resolve actual CSV header names (case-insensitive) ---
        actual_csv_headers = {field.lower(): field for field in cr.fieldnames}
        
        CSV_FACILITY_ID_COL = actual_csv_headers.get('facility_id')
        CSV_PARENT_COMPANY_NAME_COL = actual_csv_headers.get('parent_company_name')
        CSV_YEAR_COL = actual_csv_headers.get('year')
        CSV_PARENT_CO_PERCENT_OWN_COL = actual_csv_headers.get('parent_co_percent_own')
        CSV_PARENT_CO_STREET_ADDRESS_COL = actual_csv_headers.get('parent_co_street_address')
        CSV_PARENT_CO_CITY_COL = actual_csv_headers.get('parent_co_city')
        CSV_PARENT_CO_STATE_COL = actual_csv_headers.get('parent_co_state')
        CSV_PARENT_CO_ZIP_COL = actual_csv_headers.get('parent_co_zip')
        
        # Validate critical columns are found.
        if not all([CSV_FACILITY_ID_COL, CSV_PARENT_COMPANY_NAME_COL, CSV_YEAR_COL, 
                     CSV_PARENT_CO_PERCENT_OWN_COL, CSV_PARENT_CO_STREET_ADDRESS_COL, 
                     CSV_PARENT_CO_CITY_COL, CSV_PARENT_CO_STATE_COL, CSV_PARENT_CO_ZIP_COL]):
             logging.fatal(f"❌ FATAL: One or more critical CSV columns not found or could not be resolved. "
                           f"Expected but missing: "
                           f"{'facility_id' if not CSV_FACILITY_ID_COL else ''}, "
                           f"{'parent_company_name' if not CSV_PARENT_COMPANY_NAME_COL else ''}, "
                           f"{'year' if not CSV_YEAR_COL else ''}, "
                           f"{'parent_co_percent_own' if not CSV_PARENT_CO_PERCENT_OWN_COL else ''}, "
                           f"{'parent_co_street_address' if not CSV_PARENT_CO_STREET_ADDRESS_COL else ''}, "
                           f"{'parent_co_city' if not CSV_PARENT_CO_CITY_COL else ''}, "
                           f"{'parent_co_state' if not CSV_PARENT_CO_STATE_COL else ''}, "
                           f"{'parent_co_zip' if not CSV_PARENT_CO_ZIP_COL else ''}. "
                           f"Actual CSV headers found: {cr.fieldnames}. Script cannot proceed.")
             sys.exit(1)
        
        logging.info(f"Resolved CSV column mappings: Facility ID: '{CSV_FACILITY_ID_COL}', Company Name: '{CSV_PARENT_COMPANY_NAME_COL}', etc. from headers: {cr.fieldnames}")


        for i, in_row in enumerate(cr):
            if i % 500 == 0:
                logging.info(f"Preprocessing row {i} to build deduplication maps...")
            
            facility_id = in_row.get(CSV_FACILITY_ID_COL, '').strip()
            if not facility_id:
                logging.warning(f"⚠️ Skipping preprocessing of row {i+1}: Mandatory FACILITY_ID is empty or blank. Row: {in_row}")
                _COUNTERS_COMPANIES["facility_id_extraction_failed"].add(str(in_row))
                continue
            
            ghg_id = _EPA_FACILITY_GHG_ID + "/" + facility_id

            if ghg_id not in relevant_facility_ids:
                logging.debug(f"Skipping preprocessing of row {i+1}: '{ghg_id}' not found in relevant_facility_ids.")
                _COUNTERS_COMPANIES["facility_does_not_exist"].add(ghg_id)
                continue

            company_name_raw = in_row.get(CSV_PARENT_COMPANY_NAME_COL, '').strip()
            company_name = company_name_raw.replace("\"", "").replace("'", "")
            if not company_name:
                logging.warning(f"⚠️ Skipping preprocessing of row {i+1}: 'PARENT_COMPANY_NAME' not found or empty for {ghg_id}. Row: {in_row}")
                _COUNTERS_COMPANIES["company_name_not_found"].add(ghg_id)
                continue

            company_id = fh.name_to_id(company_name)
            if not company_id:
                logging.warning(f"⚠️ Skipping preprocessing of row {i+1}: Mandatory company_id is empty (from name_to_id) for {company_name}. Row: {in_row}")
                _COUNTERS_COMPANIES["company_id_name_to_id_failed"].add(str(in_row))
                continue

            year = in_row.get(CSV_YEAR_COL, '').strip()
            
            percent_own = in_row.get(CSV_PARENT_CO_PERCENT_OWN_COL, '').strip()

            address = ", ".join(filter(None, [
                in_row.get(CSV_PARENT_CO_STREET_ADDRESS_COL, '').strip(),
                in_row.get(CSV_PARENT_CO_CITY_COL, '').strip(),
                in_row.get(CSV_PARENT_CO_STATE_COL, '').strip(),
                in_row.get(CSV_PARENT_CO_ZIP_COL, '').strip()[:5]
            ]))
            address = address.strip()

            if address not in address_map:
                address_map[address] = set()
            address_map[address].add(company_id)

            if facility_id not in facility_map:
                facility_map[facility_id] = set()
            facility_map[facility_id].add(company_id)

            unique_company_ids.add(company_id)

            if company_id not in company_id_count:
                company_id_count[company_id] = 0
            company_id_count[company_id] += 1

    logging.info("Completed reading Table Info data and building maps for duplicate detection.")
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

    rows_written_to_duplicates_csv = 0
    logging.info("Writing DuplicateIdMappings.csv...")
    output_path = os.path.join(input_table_path, "DuplicateIdMappings.csv")
    with open(output_path, "w", newline='') as opth:
        writer = csv.DictWriter(opth, ["Id", "MappedTo", "Occurences"])
        writer.writeheader()

        for k, v in dict(sorted(_DUPLICATE_MAPPING.items())).items():
            d = {"Id": k, "MappedTo": v, "Occurences": company_id_count.get(v, 0)}
            writer.writerow(d)
            rows_written_to_duplicates_csv += 1

    logging.info("****************")
    logging.info(f"Num Rows Written (Duplicate Mappings) = {rows_written_to_duplicates_csv}")
    logging.info(f"Number records (from existing_facilities_path): {len(relevant_facility_ids)}")
    logging.info(f"Unique Facilities: {len(relevant_facility_ids)}")
    logging.info(f"Unique Company Names: {len(unique_company_names)}")

    logging.info(f"Duplicate Keys: {len(_DUPLICATE_MAPPING)}")
    logging.info(f"Unique (before) Company Ids: {len(unique_company_ids)}")
    logging.info(f"Unique (after) Company Ids: {len(unique_company_ids) - len(_DUPLICATE_MAPPING)}")
    logging.info("****************")
    logging.info(f"duplicate address = {count_dupe_addr}")
    logging.info(f"duplicate address, id match found = {address_id_contained_count}")
    logging.info(f"duplicate facility = {count_dupe_facility}")
    logging.info(f"duplicate facility, id match found = {facility_id_contained_count}")
    
    logging.info("\n--- Detailed Preprocessing Counters (from _run_deduplication_preprocessing_steps) ---")
    for k, v in _COUNTERS_COMPANIES.items():
        if isinstance(v, set) and v:
            logging.info(f"{k}: {len(v)} entries. Sample: {list(v)[:5]}")
        else:
            logging.info(f"{k}: 0 entries or non-set type (or handled elsewhere).")
    logging.info("Deduplication preprocessing steps completed.")


def process_companies(input_table_path, existing_facilities_file,
                      output_path_info, output_path_ownership):
    """
    This function processes the main parent company data, writes output CSVs.
    """
    
    logging.info("Starting main processing loop to generate output files...")

    # Load dupes from the file generated by _run_deduplication_preprocessing_steps
    dupes = {}
    dupes_filepath = os.path.join(input_table_path, "DuplicateIdMappings.csv")
    if os.path.exists(dupes_filepath):
        # FIX: Use DictReader to read the CSV file
        with open(dupes_filepath, "r", newline='') as dfp:
            cr = csv.DictReader(dfp)
            for row in cr:
                dupes[row['Id']] = row['MappedTo']
        logging.info(f"Loaded {len(dupes)} duplicate ID mappings from {dupes_filepath} for main processing.")
    else:
        logging.fatal(f"❌ FATAL: DuplicateIdMappings.csv not found at {dupes_filepath}. "
                      f"This file must be generated by the deduplication preprocessing step first. Script cannot proceed.")
        sys.exit(1)

    processed_companies = set()
    table_path = os.path.join(output_path_info, _OUT_FILE_PREFIX)
    ownership_path = os.path.join(output_path_ownership, _OUT_FILE_PREFIX)

    with \
        open(table_path + "Table.csv", "w", newline='') as twfp, \
        open(ownership_path + "Ownership.csv", "w", newline='') as owfp:
        tableWriter = csv.DictWriter(twfp, _TABLE_CLEAN_CSV_HDR, doublequote=False, escapechar="\\")
        tableWriter.writeheader()

        ownershipWriter = csv.DictWriter(owfp, _OWNERSHIP_CLEAN_CSV_HDR)
        ownershipWriter.writeheader()

        existing_facilities_path = os.path.join(
            input_table_path, existing_facilities_file + ".csv")

        facility_ids_from_existing = set(
            pd.read_csv(existing_facilities_path)[_EPA_FACILITY_GHG_ID].values)
        
        input_table_csv_path = os.path.join(input_table_path, _TABLE + ".csv")
        rows_written_to_output = 0

        logging.info(f"Starting main processing loop for {input_table_csv_path} (generating output CSVs)...")
        with open(input_table_csv_path, "r", newline='') as rfp:
            cr = csv.DictReader(rfp)
            
            # --- Resolve actual CSV header names (case-insensitive) for main processing loop ---
            actual_csv_headers = {field.lower(): field for field in cr.fieldnames}
            
            CSV_FACILITY_ID_COL = actual_csv_headers.get('facility_id')
            CSV_PARENT_COMPANY_NAME_COL = actual_csv_headers.get('parent_company_name')
            CSV_YEAR_COL = actual_csv_headers.get('year')
            CSV_PARENT_CO_PERCENT_OWN_COL = actual_csv_headers.get('parent_co_percent_own')
            CSV_PARENT_CO_STREET_ADDRESS_COL = actual_csv_headers.get('parent_co_street_address')
            CSV_PARENT_CO_CITY_COL = actual_csv_headers.get('parent_co_city')
            CSV_PARENT_CO_STATE_COL = actual_csv_headers.get('parent_co_state')
            CSV_PARENT_CO_ZIP_COL = actual_csv_headers.get('parent_co_zip')

            if not all([CSV_FACILITY_ID_COL, CSV_PARENT_COMPANY_NAME_COL, CSV_YEAR_COL, 
                         CSV_PARENT_CO_PERCENT_OWN_COL, CSV_PARENT_CO_STREET_ADDRESS_COL, 
                         CSV_PARENT_CO_CITY_COL, CSV_PARENT_CO_STATE_COL, CSV_PARENT_CO_ZIP_COL]):
                 logging.fatal(f"❌ FATAL: One or more critical CSV columns not found in main processing loop. "
                               f"Headers: {cr.fieldnames}. Script cannot proceed.")
                 sys.exit(1)
            
            logging.info(f"Using resolved CSV column mappings for processing rows in {input_table_csv_path}.")

            for i, in_row in enumerate(cr):
                if i % 1000 == 0:
                    logging.info(f"Processing row {i} from main input table (generating output).")

                facility_id = in_row.get(CSV_FACILITY_ID_COL, '').strip()
                if not facility_id:
                    logging.warning(f"⚠️ Skipping row {i+1} (output generation): Mandatory FACILITY_ID is empty. Row: {in_row}")
                    _COUNTERS_COMPANIES["facility_id_extraction_failed"].add(str(in_row))
                    continue
                
                ghg_id = _EPA_FACILITY_GHG_ID + "/" + facility_id
                
                if ghg_id not in facility_ids_from_existing:
                    logging.debug(f"Skipping row {i+1} (output generation): '{ghg_id}' not found in relevant_facility_ids. Row: {in_row}")
                    _COUNTERS_COMPANIES["facility_does_not_exist"].add(ghg_id)
                    continue

                company_name_raw = in_row.get(CSV_PARENT_COMPANY_NAME_COL, '').strip()
                company_name = company_name_raw.replace("\"", "").replace("'", "")
                if not company_name:
                    logging.warning(f"⚠️ Skipping row {i+1} (output generation): 'PARENT_COMPANY_NAME' not found or empty for {ghg_id}. Row: {in_row}")
                    _COUNTERS_COMPANIES["company_name_not_found"].add(ghg_id)
                    continue

                company_id = fh.name_to_id(company_name)
                if not company_id:
                    logging.warning(f"⚠️ Skipping row {i+1} (output generation): Mandatory company_id is empty (from name_to_id) for {company_name}. Row: {in_row}")
                    _COUNTERS_COMPANIES["company_id_name_to_id_failed"].add(str(in_row))
                    continue

                if company_id in dupes:
                    _COUNTERS_COMPANIES["company_ids_replaced"].add(company_id)
                    company_id = dupes[company_id]
                company_id = "EpaParentCompany/" + company_id

                year = in_row.get(CSV_YEAR_COL, '').strip()
                if not year:
                    logging.warning(f"⚠️ Skipping row {i+1} (output generation): 'YEAR' is empty for {ghg_id}. Row: {in_row}")
                    _COUNTERS_COMPANIES["year_does_not_exist"].add((company_id, ghg_id))
                    
                percent_own = in_row.get(CSV_PARENT_CO_PERCENT_OWN_COL, '').strip()
                if not percent_own:
                    logging.warning(f"⚠️ Skipping row {i+1} (output generation): 'PARENT_CO_PERCENT_OWN' is empty for {ghg_id}. Row: {in_row}")
                    _COUNTERS_COMPANIES["percent_ownership_not_found"].add((company_id, year))
                    percent_own = 100

                ownership_out_row = {
                    _DCID: company_id,
                    _EPA_FACILITY_GHG_ID: ghg_id,
                    _PERCENT_OWNERSHIP: percent_own,
                    _YEAR: year
                }
                rows_written_to_output += 1
                ownershipWriter.writerow(ownership_out_row)

                if company_id.lower() not in processed_companies:
                    zip_code_raw = in_row.get(CSV_PARENT_CO_ZIP_COL, '').strip()
                    zip_code = zip_code_raw[:5]
                    
                    zip_for_county = ""
                    if zip_code:
                        zip_for_county = "zip/" + zip_code
                    else:
                        logging.warning(f"⚠️ Missing zip code for company: {company_id}, year: {year}. Row: {in_row}")
                        _COUNTERS_COMPANIES["missing_zip"].add((company_id, year))

                    county = _get_county(company_id, zip_for_county, year)

                    street_address = in_row.get(CSV_PARENT_CO_STREET_ADDRESS_COL, '').strip()
                    city = in_row.get(CSV_PARENT_CO_CITY_COL, '').strip()
                    state = in_row.get(CSV_PARENT_CO_STATE_COL, '').strip()
                    zip_part_for_address = in_row.get(CSV_PARENT_CO_ZIP_COL, '').strip()[:5]

                    full_address = ", ".join(filter(None, [street_address, city, state, zip_part_for_address]))
                    
                    table_out_row = {
                        _DCID: company_id,
                        _NAME: company_name_raw,
                        _ADDRESS: full_address,
                        _CIP: ", ".join(fh.get_cip(zip_for_county, county)),
                    }
                    tableWriter.writerow(table_out_row)
                    processed_companies.add(company_id.lower())

        logging.info(f"Main processing loop completed. Produced {rows_written_to_output} rows for output CSVs.")
        logging.info("Geo Resolution Stats: \n" +
                     counters_string(_COUNTERS_COMPANIES))

        logging.info(f"Company ID duplicated replaced (from COUNTERS_COMPANIES) = {len(_COUNTERS_COMPANIES['company_ids_replaced'])}")


    logging.info("Generating MCF and TMCF files...")
    table_mcf_path = os.path.join(output_path_info, _OUT_FILE_PREFIX + "Table.mcf")
    ownership_mcf_path = os.path.join(output_path_ownership, _OUT_FILE_PREFIX + "Ownership.mcf")
    table_tmcf_path = os.path.join(output_path_info, _OUT_FILE_PREFIX + "Table.tmcf")
    ownership_tmcf_path = os.path.join(output_path_ownership, _OUT_FILE_PREFIX + "Ownership.tmcf")

    with open(table_mcf_path, "w") as fp:
        fp.write(_gen_table_mcf())
    logging.info(f"Generated {table_mcf_path}")

    with open(ownership_mcf_path, "w") as fp:
        fp.write(_gen_ownership_mcf())
    logging.info(f"Generated {ownership_mcf_path}")

    with open(table_tmcf_path, "w") as fp:
        fp.write(_gen_company_tmcf())
    logging.info(f"Generated {table_tmcf_path}")

    with open(ownership_tmcf_path, "w") as fp:
        fp.write(_gen_ownership_tmcf())
    logging.info(f"Generated {ownership_tmcf_path}")
    logging.info("MCF and TMCF file generation completed.")


def process_svobs(svobs_path, facility_company_ownership, facility_svo_dict):
    """Processes StatVar Observations and writes to CSV/TMCF."""
    logging.info("Starting process_svobs...")
    company_svo_dict = {}
    for facility_id, sv_dict in facility_svo_dict.items():
        for sv, svobs in sv_dict.items():
            if not svobs:
                continue

            key_val = _get_key_val_for_svobs(facility_id, sv,
                                             facility_company_ownership,
                                             svobs['sourceSeries'])
            for (k, v) in key_val.items():
                if k not in company_svo_dict:
                    company_svo_dict[k] = {
                        _PARENT_COMPANY_DCID: v[_PARENT_COMPANY_DCID],
                        _SV_MEASURED: v[_SV_MEASURED],
                        _OBSERVATION_PERIOD: v[_OBSERVATION_PERIOD],
                        _OBSERVATION_DATE: v[_OBSERVATION_DATE],
                        _SVO_VAL: 0
                    }
                company_svo_dict[k][_SVO_VAL] += v[_SVO_VAL]

    out_path = os.path.join(svobs_path, _OUT_SVOBS_FILE_PREFIX)
    with open(out_path + ".csv", "w", newline='') as svofp:
        writer = csv.DictWriter(svofp,
                                 _SVOBS_CLEAN_CSV_HDR)
        writer.writeheader()

        num_rows = 0
        for k, v in company_svo_dict.items():
            if num_rows % 1000 == 0:
                logging.info(f"processed {num_rows} rows (SVObs)")
            out_row = {
                _PARENT_COMPANY_DCID: v[_PARENT_COMPANY_DCID],
                _SV_MEASURED: v[_SV_MEASURED],
                _OBSERVATION_PERIOD: v[_OBSERVATION_PERIOD],
                _SVO_VAL: v[_SVO_VAL],
                _OBSERVATION_DATE: v[_OBSERVATION_DATE]
            }
            writer.writerow(out_row)
            num_rows += 1

    with open(out_path + ".tmcf", "w") as fp:
        fp.write(_gen_svobs_tmcf())
    logging.info("process_svobs completed.")


def generate_svobs_helper(ownership_relationships_filepath, svobs_path_info):
    """Helper function to retrieve facility SVObs and call process_svobs."""
    logging.info("Starting generate_svobs_helper...")
    
    facility_company_ownership = _facility_year_company_percentages(
        ownership_relationships_filepath)

    facilities = set()
    for (facility_id, year) in facility_company_ownership:
        facilities.add(facility_id)

    facilities = list(facilities)
    logging.info(f"Found {len(facilities)} unique facilities for SVObs.")

    statVars = fh.get_all_statvars(_DC_API_URL, facilities)
    facility_svo_dict = fh.get_all_svobs(facilities, statVars)
    logging.info(f"# SVs : {len(statVars)}")
    logging.info(f"# Facilities (with SVObs data) : {len(facility_svo_dict)}")

    process_svobs(svobs_path_info, facility_company_ownership,
                  facility_svo_dict)
    logging.info("generate_svobs_helper completed.")


def main(argv):
    # Validate inputs.
    assert FLAGS.input_download_path, "Input download path must be specified."
    assert FLAGS.existing_facilities_file, "Existing facilities file must be specified."
    assert FLAGS.output_base_path, "Output base path must be specified."
    assert FLAGS.parent_co_output_path, "Parent company output path must be specified."
    assert FLAGS.ownership_output_path, "Ownership output path must be specified."
    assert FLAGS.svobs_output_path, "SVObs output path must be specified."

    existing_facilities_full_path = os.path.join(FLAGS.input_download_path,
                                                 FLAGS.existing_facilities_file + ".csv")
    main_input_table_full_path = os.path.join(FLAGS.input_download_path, _TABLE + ".csv")

    assert os.path.exists(existing_facilities_full_path), \
        f"Existing facilities file not found: {existing_facilities_full_path}"
    assert os.path.exists(main_input_table_full_path), \
        f"Main input table file not found: {main_input_table_full_path}"

    output_path_info = os.path.join(FLAGS.output_base_path,
                                     FLAGS.parent_co_output_path)
    output_path_ownership = os.path.join(FLAGS.output_base_path,
                                         FLAGS.ownership_output_path)
    svobs_path_info = os.path.join(FLAGS.output_base_path,
                                   FLAGS.svobs_output_path)

    pathlib.Path(FLAGS.output_base_path).mkdir(exist_ok=True)
    pathlib.Path(output_path_info).mkdir(exist_ok=True)
    pathlib.Path(output_path_ownership).mkdir(exist_ok=True)
    pathlib.Path(svobs_path_info).mkdir(exist_ok=True)

    logging.info("Running deduplication preprocessing steps (populating _DUPLICATE_MAPPING)...")
    _run_deduplication_preprocessing_steps(FLAGS.input_download_path, FLAGS.existing_facilities_file)
    logging.info("Deduplication preprocessing completed. Mappings generated.")

    logging.info("Beginning main company data processing (generating Table.csv and Ownership.csv)...")
    process_companies(FLAGS.input_download_path, FLAGS.existing_facilities_file,
                      output_path_info, output_path_ownership)
    logging.info("Main company data processing completed.")

    ownership_path_prefix = os.path.join(output_path_ownership, _OUT_FILE_PREFIX)
    ownership_relationships_filepath = ownership_path_prefix + "Ownership.csv"
    assert os.path.exists(ownership_relationships_filepath), \
        f"Ownership relationships file not found: {ownership_relationships_filepath}"
    
    logging.info("Generating StatVar Observations...")
    generate_svobs_helper(ownership_relationships_filepath, svobs_path_info)
    logging.info("StatVar Observations generation completed.")

if __name__ == "__main__":
    app.run(main)
