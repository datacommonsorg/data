# Copyright 2024 Google LLC
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

"""
This script downloads datasets from the National Statistics Office (NSO) of Mongolia
PxWeb API via util.download_util.
"""

import os
import sys

from absl import app
from absl import flags
from absl import logging

# Add the repository root to sys.path so we can import util.download_util
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.join(_SCRIPT_DIR, '..', '..')
sys.path.append(_REPO_ROOT)

from util import download_util

FLAGS = flags.FLAGS

DEMOGRAPHICS_TABLES = [
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_002V1.px", "filename": "mid_year_total_population_by_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_033V1.px", "filename": "number_of_households_by_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_003V1.px", "filename": "total_population_by_age_group_and_sex.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_027V1.px", "filename": "total_population_by_sex_and_urban_rural.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_077V2.px", "filename": "resident_population_by_agegroup_15_and_over_and_maritalstatus.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Population%20and%20household/DT_NSO_0300_004V1.px", "filename": "total_population_by_region_and_urban_rural.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Population%2C%20household/1_Population%2C%20household/DT_NSO_0300_006V1.px", "filename": "number_of_households_by_region_and_urban_rural.csv"}
]

EDUCATION_TABLES = [
    {"url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Education%2C%20Science%2C%20and%20Intellectual%20Property/DT_NSO_2001_013V1.px", "filename": "number_of_students_in_universities_and_colleges_by_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Universities%2C%20institutes%20and%20colleges/DT_NSO_2001_013V2.px", "filename": "students_of_universities_and_colleges_by_professional_field.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Education%2C%20Science%2C%20and%20Intellectual%20Property/DT_NSO_2001_011V1.px", "filename": "number_of_kindergartens_by_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Universities%2C%20institutes%20and%20colleges/DT_NSO_2001_016V1.px", "filename": "number_of_full_time_teachers_in_universities_and_colleges_by_sex.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Universities%2C%20institutes%20and%20colleges/DT_NSO_2001_014V1.px", "filename": "graduates_of_universities_and_colleges_by_professional_field.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Universities%2C%20institutes%20and%20colleges/DT_NSO_2001_015V2.px", "filename": "students_in_teritary_educational_institutions_by_sex_and_educational_degree.csv"}
]

HEALTH_TABLES = [
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Main%20indicators%20for%20Health%20sector/DT_NSO_2100_001V1.px", "filename": "number_of_abortions_by_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Health/DT_NSO_2100_015V1.px", "filename": "infant_mortality_per_1000_live_births_by_month_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Health/DT_NSO_2100_017V3.px", "filename": "number_of_mothers_delivered_child_by_month_region.csv"},
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Births%2C%20deaths/DT_NSO_2100_018V5.px", "filename": "live_births_by_month_region.csv"},
    {
        "url": "https://data.1212.mn/api/v1/en/NSO/Regional%20development/Health/DT_NSO_2100_005V3.px",
        "filename": "number_of_hospital_beds_by_type.csv",
        "query": [{
            "code": "Бүс",
            "selection": {
                "filter": "item",
                "values": ["0"]
            }
        }]
    },
    {"url": "https://data.1212.mn/api/v1/en/NSO/Education%2C%20health/Births%2C%20deaths/DT_NSO_2100_027V2.px", "filename": "deaths_by_month_and_region.csv"}
]

def fetch_and_save_data(url, csv_filepath, query=None):
    """
    Fetches exactly formatted CSV data from the PxWeb API.
    """
    logging.info(f"Downloading {url} -> {csv_filepath}...")
    
    # Request PxWeb to output as CSV pre-pivoted by period
    pxweb_json_payload = {
        "query": query or [],
        "response": {
            "format": "csv"
        }
    }

    try:
        downloaded = download_util.download_file_from_url(
            url=url,
            params=pxweb_json_payload,
            method='POST',
            timeout=60,
            retries=5,
            retry_secs=5,
            output_file=csv_filepath,
            overwrite=True
        )
        if (
            not downloaded
            or not os.path.exists(csv_filepath)
            or os.path.getsize(csv_filepath) <= 10
        ):
            error_msg = (
                f"FATAL ERROR: Failed to download valid file {csv_filepath} from {url}"
            )
            logging.fatal(error_msg)
            raise RuntimeError(error_msg)
            
        logging.info(f"Successfully downloaded CSV file: {csv_filepath}")

    except Exception as e:
        error_msg = f"FATAL ERROR: Failed to download from {url}: {e}"
        logging.fatal(error_msg)
        raise RuntimeError(error_msg)

def main(_):
    logging.set_verbosity(logging.INFO)

    # Demographics Data
    demographics_dir = os.path.join(_SCRIPT_DIR, "mongolia_demographics", "input_files")
    os.makedirs(demographics_dir, exist_ok=True)
    for table in DEMOGRAPHICS_TABLES:
        filepath = os.path.join(demographics_dir, table['filename'])
        fetch_and_save_data(table['url'], filepath)

    # Education Data
    education_dir = os.path.join(_SCRIPT_DIR, "mongolia_education", "input_files")
    os.makedirs(education_dir, exist_ok=True)
    for table in EDUCATION_TABLES:
        filepath = os.path.join(education_dir, table['filename'])
        fetch_and_save_data(table['url'], filepath)

    # Health Data
    health_dir = os.path.join(_SCRIPT_DIR, "mongolia_health", "input_files")
    os.makedirs(health_dir, exist_ok=True)
    for table in HEALTH_TABLES:
        filepath = os.path.join(health_dir, table['filename'])
        fetch_and_save_data(table['url'], filepath, table.get('query'))

    logging.info("All tasks completed")

if __name__ == "__main__":
    app.run(main)
