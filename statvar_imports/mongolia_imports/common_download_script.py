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

    url = "https://opendata.1212.mn/api/Data"
    data = {"tbl_id": table_id}
    headers = {"Content-Type": "application/json"}
    retry_logic = Retry(total=5, backoff_factor=1, allowed_methods=["POST"])
    adapter = HTTPAdapter(max_retries=retry_logic)
    session = requests.Session()
    session.mount("https://", adapter)

    try:
        response = session.post(url, headers=headers, data=json.dumps(data))

        # Check status code first
        if response.status_code == 200:
            response_data = response.json()

            if not response_data:
                # Checks if the dictionary is empty[from the source we are getting data in dictionary fomate]
                error_msg = f"FATAL ERROR for {table_id}: No data found in the source. Aborting script."
                logging.fatal(error_msg)
                raise RuntimeError(error_msg)

            logging.info("Success! Response data received.")

            if "DataList" in response_data and isinstance(
                    response_data["DataList"], list):
                data_list = response_data["DataList"]

                # Check for empty DataList and log the finding before aborting
                if not data_list:
                    logging.info(
                        f"Found 'DataList' structure in source, but it is empty: {table_id}."
                    )
                    error_msg = f"FATAL ERROR for {table_id}: 'DataList' is present but contains zero records. No data found from the Source"
                    logging.fatal(error_msg)
                    raise RuntimeError(error_msg)
                if len(data_list) < 40:  # Updated threshold to 40 records
                    logging.info(
                        f"Found 'DataList' structure in source, but it is empty or too small: {table_id}. DataList length: {len(data_list)}"
                    )
                    error_msg = f"FATAL ERROR for {table_id}: 'DataList' contains less than 40 records. Data is not sufficient."
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
                    f"Error for {table_id}: 'DataList' not found in the API response.\n"
                )
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
