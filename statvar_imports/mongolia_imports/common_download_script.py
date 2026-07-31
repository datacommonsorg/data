# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import json
import os
import requests
import sys
from absl import app
from absl import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.set_verbosity(logging.INFO)

# Constant Table configurations
DEMOGRAPHICS_TABLES = [
    {
        "id": "DT_NSO_0300_002V1",
        "filename": "mid_year_total_population_by_region.csv",
        "header_mapping": {
            "keys": ["SCR_ENG", "CODE"],
            "cols": ["Aimag", "Код"]
        }
    },
    {
        "id": "DT_NSO_0300_033V1",
        "filename": "number_of_households_by_region.csv",
        "header_mapping": {
            "keys": ["SCR_ENG", "CODE"],
            "cols": ["Aimag", "Код"]
        }
    },
    {
        "id": "DT_NSO_0300_003V1",
        "filename": "total_population_by_age_group_and_sex.csv",
        "header_mapping": {
            "keys": ["SCR_ENG1", "SCR_ENG", "CODE"],
            "cols": ["Sex", "Age group"]
        }
    },
    {
        "id": "DT_NSO_0300_027V1",
        "filename": "total_population_by_sex_and_urban_rural.csv",
        "header_mapping": {
            "keys": ["SCR_ENG"],
            "cols": ["Location"]
        }
    },
    {
        "id":
            "DT_NSO_0300_077V1",
        "filename":
            "resident_population_by_agegroup_15_and_over_and_maritalstatus.csv",
        "header_mapping": {
            "keys": ["SCR_ENG", "SCR_ENG1", "SCR_ENG2", "CODE"],
            "cols": ["Marital Status", "Age Group", "Gender"]
        }
    },
    {
        "id": "DT_NSO_0300_004V1",
        "filename": "total_population_by_region_and_urban_rural.csv",
        "header_mapping": {
            "keys": ["SCR_ENG", "SCR_ENG1", "CODE1", "CODE"],
            "cols": ["Total", "Aimag", "Код"]
        }
    },
    {
        "id": "DT_NSO_0300_006V1",
        "filename": "number_of_households_by_region_and_urban_rural.csv",
        "header_mapping": {
            "keys": ["SCR_ENG", "SCR_ENG1", "CODE"],
            "cols": ["NUMBER OF HOUSEHOLDS", "Aimag", "Код"]
        }
    },
]

EDUCATION_TABLES = [{
    "id": "DT_NSO_2001_013V1",
    "filename": "number_of_students_in_universities_and_colleges_by_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG1", "SCR_ENG", "CODE"],
        "cols": ["Sex", "Aimag", "Код"]
    }
}, {
    "id":
        "DT_NSO_2001_013V2",
    "filename":
        "students_of_universities_and_colleges_by_professional_field.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Professional field"]
    }
}, {
    "id": "DT_NSO_2001_011V1",
    "filename": "number_of_kindergartens_by_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id":
        "DT_NSO_2001_016V1",
    "filename":
        "number_of_full_time_teachers_in_universities_and_colleges_by_sex.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Number of teacher"]
    }
}, {
    "id":
        "DT_NSO_2001_014V1",
    "filename":
        "graduates_of_universities_and_colleges_by_professional_field.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "SCR_MN", "CODE"],
        "cols": ["Professional fields", "Утга"]
    }
}, {
    "id":
        "DT_NSO_2001_015V2",
    "filename":
        "students_in_teritary_educational_institutions_by_sex_and_educational_degree.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Professional fields"]
    }
}]

HEALTH_TABLES = [{
    "id": "DT_NSO_2100_001V1",
    "filename": "number_of_abortions_by_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id": "DT_NSO_2100_015V1",
    "filename": "infant_mortality_per_1000_live_births_by_month_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id": "DT_NSO_2100_017V3",
    "filename": "number_of_mothers_delivered_child_by_month_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id": "DT_NSO_2100_018V5",
    "filename": "live_births_by_month_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id": "DT_NSO_2100_005V1",
    "filename": "number_of_hospital_beds_by_type.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}, {
    "id": "DT_NSO_2100_027V2",
    "filename": "deaths_by_month_and_region.csv",
    "header_mapping": {
        "keys": ["SCR_ENG", "CODE"],
        "cols": ["Aimag", "Код"]
    }
}]






def find_table_path(session, table_id):
    import functools
    import re
    tid = table_id.upper()
    if tid.endswith(".PX"):
        tid = tid[:-3]
    
    # Base ID for fuzzy version match (e.g., DT_NSO_0300_077V1 -> DT_NSO_0300_077)
    base_match = re.match(r"(DT_NSO_\d+_\d+)V\d+", tid)
    base_id = base_match.group(1) if base_match else tid
    
    sectors_url = "https://data.1212.mn/api/v1/en/NSO"
    try:
        r = session.get(sectors_url)
        if r.status_code != 200:
            return None
        sectors = r.json()
    except Exception as e:
        logging.error(f"Failed to fetch sectors: {e}")
        return None
        
    candidates = []
    for sector in sectors:
        sector_id = sector.get("id")
        if not sector_id:
            continue
        subsectors_url = f"https://data.1212.mn/api/v1/en/NSO/{sector_id}"
        try:
            r = session.get(subsectors_url)
            if r.status_code != 200:
                continue
            subsectors = r.json()
        except Exception:
            continue
            
        for subsector in subsectors:
            subsector_id = subsector.get("id")
            if not subsector_id:
                continue
            tables_url = f"https://data.1212.mn/api/v1/en/NSO/{sector_id}/{subsector_id}"
            try:
                r = session.get(tables_url)
                if r.status_code != 200:
                    continue
                tables = r.json()
            except Exception:
                continue
                
            for table in tables:
                table_item_id = table.get("id", "").upper()
                if table_item_id.endswith(".PX"):
                    table_item_id = table_item_id[:-3]
                
                # Exact match
                if table_item_id == tid:
                    return sector_id, subsector_id, table.get("id")
                
                # Fuzzy version match candidate
                if table_item_id.startswith(base_id):
                    candidates.append((sector_id, subsector_id, table.get("id"), table_item_id))
                    
    if candidates:
        # Sort candidates so that we get the highest version first or exact version if possible
        candidates.sort(key=lambda x: x[3], reverse=True)
        logging.info(f"Fuzzy version match found for {table_id}: selected {candidates[0][2]}")
        return candidates[0][0], candidates[0][1], candidates[0][2]
        
    return None


def fetch_and_save_data(table_id, csv_filepath, header_mapping):
    """
    Fetches data from the API for a given table ID, pivots it,
    and saves it to a specified CSV file with dynamic headers.

    Args:
        table_id (str): The 'tbl_id' for the API request.
        csv_filepath (str): The path for the output CSV file.
        header_mapping (dict): A dictionary mapping the first columns'
                               names to the keys in the JSON data.
    """
    logging.info(f"Processing {table_id} -> {csv_filepath}...")

    retry_logic = Retry(total=5, backoff_factor=1, allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retry_logic)
    session = requests.Session()
    session.mount("https://", adapter)

    try:
        # 1. Resolve table path
        path_info = find_table_path(session, table_id)
        if not path_info:
            error_msg = f"FATAL ERROR for {table_id}: Table not found in API catalog. Aborting."
            logging.fatal(error_msg)
            raise RuntimeError(error_msg)
            
        sector_id, subsector_id, table_filename = path_info
        logging.info(f"Resolved path for {table_id}: NSO/{sector_id}/{subsector_id}/{table_filename}")

        # 2. Fetch metadata (English and Mongolian)
        en_meta_url = f"https://data.1212.mn/api/v1/en/NSO/{sector_id}/{subsector_id}/{table_filename}"
        mn_meta_url = f"https://data.1212.mn/api/v1/mn/NSO/{sector_id}/{subsector_id}/{table_filename}"
        
        en_meta_res = session.get(en_meta_url)
        mn_meta_res = session.get(mn_meta_url)
        
        if en_meta_res.status_code != 200 or mn_meta_res.status_code != 200:
            error_msg = f"FATAL ERROR for {table_id}: Failed to fetch metadata (EN: {en_meta_res.status_code}, MN: {mn_meta_res.status_code})"
            logging.fatal(error_msg)
            raise RuntimeError(error_msg)
            
        en_meta = en_meta_res.json()
        mn_meta = mn_meta_res.json()

        # 3. Fetch all data using POST
        data_url = f"https://data.1212.mn/api/v1/en/NSO/{sector_id}/{subsector_id}/{table_filename}"
        payload = {
            "query": [],
            "response": {
                "format": "json"
            }
        }
        headers = {"Content-Type": "application/json"}
        response = session.post(data_url, headers=headers, json=payload)

        # Check status code first
        if response.status_code == 200:
            response_data = response.json()

            if not response_data or "data" not in response_data:
                error_msg = f"FATAL ERROR for {table_id}: No data found in the source. Aborting script."
                logging.fatal(error_msg)
                raise RuntimeError(error_msg)

            logging.info("Success! Response data received.")

            # Map variables
            variables = en_meta["variables"]
            period_var_idx = -1
            for idx, var in enumerate(variables):
                code_lower = var.get("code", "").lower()
                text_lower = var.get("text", "").lower()
                if any(p in code_lower or p in text_lower for p in ["year", "period", "time", "month", "он", "сар"]):
                    period_var_idx = idx
                    break
                    
            class_vars = []
            for idx, (en_v, mn_v) in enumerate(zip(en_meta["variables"], mn_meta["variables"])):
                if idx != period_var_idx:
                    class_vars.append((idx, en_v, mn_v))
                    
            N = len(class_vars)
            
            # Map POST response data to data_list format
            data_list = []
            for item in response_data.get("data", []):
                keys = item.get("key", [])
                vals = item.get("values", [])
                if not vals:
                    continue
                    
                row_data = {}
                row_data["DTVAL_CO"] = vals[0]
                
                if period_var_idx != -1:
                    period_key = keys[period_var_idx]
                    en_var = en_meta["variables"][period_var_idx]
                    try:
                        val_idx = en_var["values"].index(period_key)
                        row_data["Period"] = en_var["valueTexts"][val_idx]
                    except ValueError:
                        row_data["Period"] = period_key
                else:
                    row_data["Period"] = ""
                    
                for i, (var_idx, en_v, mn_v) in enumerate(class_vars):
                    suffix = str(N - 1 - i) if i < N - 1 else ""
                    key_val = keys[var_idx]
                    try:
                        val_idx = en_v["values"].index(key_val)
                        en_text = en_v["valueTexts"][val_idx]
                        mn_text = mn_v["valueTexts"][val_idx]
                    except ValueError:
                        en_text = key_val
                        mn_text = key_val
                    row_data[f"CODE{suffix}"] = key_val
                    row_data[f"SCR_ENG{suffix}"] = en_text
                    row_data[f"SCR_MN{suffix}"] = mn_text
                data_list.append(row_data)

            # Check for empty DataList and log the finding before aborting
            if not data_list:
                logging.info(
                    f"Found empty DataList for: {table_id}."
                )
                error_msg = f"FATAL ERROR for {table_id}: DataList contains zero records. No data found from the Source"
                logging.fatal(error_msg)
                raise RuntimeError(error_msg)
            if len(data_list) < 40:  # Updated threshold to 40 records
                logging.info(
                    f"Found too small DataList: {table_id}. DataList length: {len(data_list)}"
                )
                error_msg = f"FATAL ERROR for {table_id}: DataList contains less than 40 records. Data is not sufficient."
                logging.fatal(error_msg)
                raise RuntimeError(error_msg)

            pivoted_data = {}
            all_periods = set()

            for item in data_list:
                period = item.get("Period", "")
                row_keys = [
                    item.get(key, "") for key in header_mapping['keys']
                ]
                dtval_co = item.get("DTVAL_CO", "")
                row_key = tuple(row_keys)

                if period:
                    all_periods.add(period)
                if row_key not in pivoted_data:
                    pivoted_data[row_key] = {}
                pivoted_data[row_key][period] = dtval_co

            sorted_periods = sorted(list(all_periods))

            try:
                with open(csv_filepath, 'w', newline='',
                          encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)

                    csv_headers = header_mapping['cols'] + sorted_periods
                    csv_writer.writerow(csv_headers)

                    for row_key, period_values in pivoted_data.items():

                        # It creates the row using only as many keys as there are column names.
                        row = list(row_key)[:len(header_mapping['cols'])]

                        for period in sorted_periods:
                            row.append(period_values.get(period, ""))
                        csv_writer.writerow(row)

                logging.info(
                    f"Successfully created CSV file: {csv_filepath}\n")
            except IOError as e:
                error_msg = f"Failed to write CSV file {csv_filepath}: {e}"
                logging.fatal(error_msg)
                raise RuntimeError(error_msg)
        else:
            logging.warning(
                f"Error for {table_id}: Request failed with status code {response.status_code}\n"
            )

    except requests.exceptions.RequestException as e:
        error_msg = f"FATAL ERROR for {table_id}: An unrecoverable error occurred during the API request: {e}"
        logging.fatal(error_msg)
        raise RuntimeError(error_msg)


def main(_):
    demographics_dir = "../mongolia_demographics/input_files"
    os.makedirs(demographics_dir, exist_ok=True)

    for table in DEMOGRAPHICS_TABLES:
        filepath = os.path.join(demographics_dir, table['filename'])
        fetch_and_save_data(table['id'], filepath, table['header_mapping'])

    # Education Data
    education_dir = "../mongolia_education/input_files"
    os.makedirs(education_dir, exist_ok=True)

    for table in EDUCATION_TABLES:
        filepath = os.path.join(education_dir, table['filename'])
        fetch_and_save_data(table['id'], filepath, table['header_mapping'])

    # Health Data
    health_dir = "../mongolia_health/input_files"
    os.makedirs(health_dir, exist_ok=True)

    for table in HEALTH_TABLES:
        filepath = os.path.join(health_dir, table['filename'])
        fetch_and_save_data(table['id'], filepath, table['header_mapping'])

    logging.info("All tasks completed")


if __name__ == "__main__":
    app.run(main)
