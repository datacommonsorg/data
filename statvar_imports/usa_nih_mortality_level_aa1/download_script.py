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

import requests
import json
import csv
from absl import app
from absl import flags
from absl import logging
import os
import re

# --- Configuration & Setup ---

# Set logging level (INFO shows state progress, DEBUG shows file-level saves)
logging.set_verbosity(logging.INFO)

# Define command-line flags
FLAGS = flags.FLAGS
flags.DEFINE_string(
    "output_file_base",
    "nih_mortality_data",
    "The base name for the output CSV file (only used if combining all data).",
)

# User-Agent header to mimic a standard browser request
_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

# --- FIPS Code and Location Mappings ---

# Map of State FIPS codes to their two-letter abbreviations
_FIPS_TO_ABBR = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO',
    '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI',
    '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY',
    '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN',
    '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
    '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH',
    '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD',
    '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA',
    '54': 'WV', '55': 'WI', '56': 'WY', '72': 'PR'
}

# Map of State FIPS codes to their URL-friendly county-level description (for API path)
_FIPS_TO_NAME_SLUG = {
    '01': 'Alabama Counties', '02': 'Alaska Boroughs And Census Areas', '04': 'Arizona Counties', '05': 'Arkansas Counties',
    '06': 'California Counties', '08': 'Colorado Counties', '09': 'Connecticut Counties', '10': 'Delaware Counties',
    '11': 'District of Columbia', '12': 'Florida Counties', '13': 'Georgia Counties', '15': 'Hawaii Counties',
    '16': 'Idaho Counties', '17': 'Illinois Counties', '18': 'Indiana Counties', '19': 'Iowa Counties', '20': 'Kansas Counties',
    '21': 'Kentucky Counties', '22': 'Louisiana Parishes', '23': 'Maine Counties', '24': 'Maryland Counties',
    '25': 'Massachusetts Counties', '26': 'Michigan Counties', '27': 'Minnesota Counties', '28': 'Mississippi Counties',
    '29': 'Missouri Counties', '30': 'Montana Counties', '31': 'Nebraska Counties', '32': 'Nevada Counties',
    '33': 'New Hampshire Counties', '34': 'New Jersey Counties', '35': 'New Mexico Counties', '36': 'New York Counties',
    '37': 'North Carolina Counties', '38': 'North Dakota Counties', '39': 'Ohio Counties', '40': 'Oklahoma Counties',
    '41': 'Oregon Counties', '42': 'Pennsylvania Counties', '72': 'Puerto Rico', '44': 'Rhode Island Counties',
    '45': 'South Carolina Counties', '46': 'South Dakota Counties', '47': 'Tennessee Counties', '48': 'Texas Counties',
    '49': 'Utah Counties', '50': 'Vermont Counties', '51': 'Virginia Counties', '53': 'Washington Counties',
    '54': 'West Virginia Counties', '55': 'Wisconsin Counties', '56': 'Wyoming Counties'
}

# Map of State FIPS to a representative County FIPS code (e.g., the first one '001')
_FIPS_TO_COUNTY_FIPS = {
    '01': '01001', '02': '02900', '04': '04001', '05': '05001', '06': '06001', '08': '08001',
    '09': '09001', '10': '10001', '11': '11001', '12': '12001', '13': '13001', '15': '15001',
    '16': '16001', '17': '17001', '18': '18001', '19': '19001', '20': '20001', '21': '21001',
    '22': '22001', '23': '23001', '24': '24001', '25': '25001', '26': '26001', '27': '27001',
    '28': '28001', '29': '29001', '30': '30001', '31': '31001', '32': '32001', '33': '33001',
    '34': '34001', '35': '35001', '36': '36001', '37': '37001', '38': '38001', '39': '39001',
    '40': '40001', '41': '41001', '42': '42001', '44': '44001', '45': '45001', '46': '46001',
    '47': '47001', '48': '48001', '49': '49001', '50': '50001', '51': '51001', '53': '53001',
    '54': '54001', '55': '55001', '56': '56001', '72': '72001', '00': '00000'
}



# Cause of Death (COD)
_COD_PARAMS = {
    '251': 'Accidents & Adverse Effects', '264': "Alzheimer's Disease", '001': 'Cancer',
    '249': 'Cerebrovascular Diseases', '253': 'Chronic Lower Respiratory Disease', '257': 'Chronic Liver Disease & Cirrohosis', '254': 'Diabetes Mellitus',
    '250': 'Heart Disease', '260': 'Homicide & Legal Intervention', '277': 'Influenza', '258': "Kidney Disease (Neph. & Nephrosis)",
    '278': 'Pneumonia','259':"Septicemia",'256':"Suicide & Self-Inflicted Injury"
}

# Race
_RACE_PARAMS = {
    '07': "White (Non-Hispanic/Latino)", '28': "Black or African American (Non-Hispanic/Latino)", '38': "American Indian or Alaska Native (Non-Hispanic/Latino)", '48': "Asian, Native Hawaiian or Pacific Islander (Non-Hispanic/Latino)",
    '05': "Hispanic or Latino (any race)",
}

# Sex
_SEX_PARAMS = {
    '1': 'Male', '2': 'Female',
}

# Age Group
_AGE_PARAMS = {
    '600': "Age <1", '719': 'Ages 1-9', '177': 'Ages 1-19', '050': 'Ages 10-19', '077': 'Ages 20-39',
    '122': 'Ages 40-64', '157': 'Ages 65+', '160': 'Ages 65-74', '167': 'Ages 75-84', '171': 'Ages 85+',
}

# Rural/Urban Status
_RURAL_URBAN_PARAMS = {
    '1': 'Rural',
    '2': 'Urban',
}


# Template for the complex URL parameters required by the NIH API
_URL_PARAMS_TEMPLATE = (
    "cod={cod}&cod_options=cod_15&ratetype=aa&ratetype_options=ratetype_2&race={race}&race_options=race_6&sex={sex}&sex_options=sex_3&age={age}&age_options=age_11&ruralurban={ruralurban}&ruralurban_options=ruralurban_3&yeargroup=5&yeargroup_options=year5yearmort_1&statefips={fips}&statefips_options=area_states"
    "&county={county_fips}&county_options=counties_{state_name_slug}&comparison=counties_to_us&comparison_options=comparison_counties&radio_comparison=areas&radio_comparison_options=cods_or_areas"
)


_URL_FRONT_END_TEMPLATE = "https://hdpulse.nimhd.nih.gov/data-portal/mortality/table?{params}"

# Actual API endpoint that returns the data
_URL_DATA_SOURCE_TEMPLATE = "https://hdpulse.nimhd.nih.gov/data-portal/api/data_setup.php?{params}&function=getExport&displayType=table&path=mortality"

# --- Helper Functions ---

def create_slug(name):
    """
    Converts a descriptive string (like a parameter name) into a file-safe snake_case slug.
    """
    # Remove special characters except spaces/underscores
    slug = re.sub(r'[^a-zA-Z0-9\s_]', '', name.strip())
    # Replace spaces/hyphens with a single underscore
    slug = re.sub(r'[\s\-+]+', '_', slug)
    return slug.strip('_')


def fetch_api_data(api_url, referer_url):
    """Fetches JSON data from the NIH API endpoint with required headers."""
    if not api_url:
        
        error_message = "FATAL ERROR: API Data Source URL is empty. Terminating script."
        logging.fatal(error_message)
        raise RuntimeError(error_message)

    headers = {
        'User-Agent': _USER_AGENT,
        'Referer': referer_url,  # Required by the API
        'Accept': 'application/json, text/plain, */*',
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"FATAL ERROR: Error fetching API URL: {e}. Terminating script."
        logging.warning(error_message)
        raise RuntimeError(error_message) from e
  

def process_nih_json(raw_data, cod_name, race_name, sex_name, age_name, ruralurban_name):
    """
    Extracts tabular data from the API's 'csvData' string, parses it, and
    prepends the parameter context to each row.
    """
    if not isinstance(raw_data, dict) or 'csvData' not in raw_data:
        
        error_message = "FATAL ERROR: JSON data does not contain the expected 'csvData' key. Terminating script."
        logging.fatal(error_message)
        raise RuntimeError(error_message)

    csv_data_string = raw_data['csvData']

    # CRITICAL: Regex pre-processing to quote fields containing commas,
    # specifically those with a number, an asterisk, and a trend description
    regex_pattern = r'(\d+\.?\d*\*?),\s*(\d+\s(rising|falling|stable))'
    quoted_csv_data = re.sub(regex_pattern, r'"\1, \2"', csv_data_string, flags=re.IGNORECASE)
    lines = quoted_csv_data.split('\n')

    # --- 1. Extract Period (e.g., 2019-2023) from the metadata ---
    if len(lines) < 4:
        logging.warning("CSV data string is too short to extract metadata.")
        # We don't fatal here, as data might still be usable.
        period = "Unknown Period"
    else:
        try:
            # The period is expected to be the last element of the second line
            metadata_line = lines[1].strip().strip('"')
            period = metadata_line.split(',')[-1].strip()
        except IndexError:
            period = "Unknown Period"
            logging.warning("Could not parse the data period from metadata line.")

    # --- 2. Define New Header/Value Rows (Contextual Columns) ---
    new_headers = ["Period", "Cause of Death", "Race", "Sex", "Age Group", "Rural/Urban Status"]
    new_values = [period, cod_name, race_name, sex_name, age_name, ruralurban_name]

    # --- 3. Locate Data Block (Find the actual CSV header dynamically) ---
    start_index = -1
    for i, line in enumerate(lines[:15]): # Search first few lines
        line_stripped = line.strip()
        # Look for the header line which contains FIPS, Rate, and an area description
        is_area_header = any(area_type in line_stripped for area_type in ['County', 'Parish', 'Borough Or Census Area'])
        if line_stripped and all(keyword in line_stripped for keyword in ['FIPS', 'Rate']) and is_area_header:
            start_index = i
            break

    if start_index == -1:
        # Changed to logging.fatal and added RuntimeError
        error_message = "FATAL ERROR: Could not find the start of the data (header line). API format may have changed. Terminating script."
        logging.fatal(error_message)
        raise RuntimeError(error_message)

    # Determine end of data (before the footer/notes section)
    end_index = len(lines)
    for i in range(start_index + 1, len(lines)):
        if lines[i].startswith('Suggested Citation:'):
            end_index = i
            break

    data_lines = lines[start_index:end_index]
    if not data_lines:
        logging.warning("Extracted data block is empty.")
        return None

    # --- 4. Parse and Prepend Contextual Data ---
    data_output = []
    csv_reader = csv.reader(data_lines, delimiter=',', quoting=csv.QUOTE_MINIMAL)

    is_header = True
    for row in csv_reader:
        # Clean data: remove tilde (~) which often denotes suppressed or unstable data
        cleaned_row = [cell.strip().replace('~', '') for cell in row]

        # Skip rows that are empty or are state-level aggregates
        if not any(cleaned_row) or cleaned_row[0] == 'United States' or len(cleaned_row[0]) < 5:
            continue

        if is_header:
            # Prepend the custom headers
            final_row = new_headers + cleaned_row
            is_header = False
        else:
            # Prepend the custom values
            final_row = new_values + cleaned_row

        data_output.append(final_row)

    if len(data_output) <= 1 and not is_header:
        logging.warning("CSV parsing resulted in no data rows (only header).")
        return data_output if data_output else None

    return data_output


def main(_):
    """
    Main execution function. Fetches and saves county-level mortality data
    for all parameter permutations for all targeted states.
    """

    
    # Retrieve all state FIPS codes defined in the map, excluding the national aggregate '00'
    fips_codes_to_process = [fips for fips in _FIPS_TO_ABBR.keys() if fips != '00']
    # -------------------------------------------------------------

    # Calculate total runs for logging
    total_states = len(fips_codes_to_process)
    total_cod = len(_COD_PARAMS)
    total_race = len(_RACE_PARAMS)
    total_sex = len(_SEX_PARAMS)
    total_age = len(_AGE_PARAMS)
    total_rural_urban = len(_RURAL_URBAN_PARAMS)

    total_runs = total_states * total_cod * total_race * total_sex * total_age * total_rural_urban
    logging.info(f"TOTAL API CALLS EXPECTED: **{total_runs:,}**")
    
    # --- Start Processing States ---
    for fips in fips_codes_to_process:
        state_abbr = _FIPS_TO_ABBR[fips]
        state_name_slug = _FIPS_TO_NAME_SLUG.get(fips, 'default_state')
        county_fips = _FIPS_TO_COUNTY_FIPS.get(fips, '00000')
        state_full_name = state_name_slug.replace('_', ' ').title()

        # --- Folder Management (With Fatal/RuntimeError Check) ---
        base_dir = 'raw_folders'
        state_dir = os.path.join(base_dir, state_full_name)
        try:
            os.makedirs(state_dir, exist_ok=True)
            logging.info(f"Processing State: {state_full_name} ({state_abbr}). Saving to {state_dir}")
        except OSError as e:
            # FATAL CONDITION: If directory creation fails, log and raise RuntimeError.
            error_message = f"FATAL ERROR: Could not create directory {state_dir} for FIPS {fips}: {e}. Terminating script."
            logging.fatal(error_message)
            raise RuntimeError(error_message) from e
        # ---------------------------------------------------------

        # Iterate through every possible combination of parameters
        for cod_code, cod_name in _COD_PARAMS.items():
            for race_code, race_name in _RACE_PARAMS.items():
                for sex_code, sex_name in _SEX_PARAMS.items():
                    for age_code, age_name in _AGE_PARAMS.items():
                        for ruralurban_code, ruralurban_name in _RURAL_URBAN_PARAMS.items():

                            # 1. Construct the API call URLs
                            params = _URL_PARAMS_TEMPLATE.format(
                                fips=fips, county_fips=county_fips, state_name_slug=state_name_slug,
                                cod=cod_code, race=race_code, sex=sex_code, age=age_code, ruralurban=ruralurban_code
                            )
                            referer_url = _URL_FRONT_END_TEMPLATE.format(params=params)
                            api_url = _URL_DATA_SOURCE_TEMPLATE.format(params=params)

                            # 2. Fetch the raw JSON data
                            # Execution will halt inside fetch_api_data if connection/response is critical error
                            raw_api_data = fetch_api_data(api_url, referer_url)

                            data = None
                            if raw_api_data:
                                # 3. Process the data
                                # Execution will halt inside process_nih_json if JSON structure is critically flawed
                                data = process_nih_json(
                                        raw_api_data,
                                        cod_name, race_name, sex_name, age_name, ruralurban_name
                                    )

                            if data and len(data) > 1:
                                # 4. Save the processed data to a unique CSV file
                                filename_parts = [
                                    state_abbr, create_slug(cod_name), create_slug(race_name),
                                    create_slug(sex_name), create_slug(age_name), create_slug(ruralurban_name)
                                ]
                                final_output_file_name = f"{'_'.join(filename_parts)}.csv"
                                final_output_path = os.path.join(state_dir, final_output_file_name)

                                try:
                                    with open(final_output_path, 'w', newline='', encoding='utf-8') as csvfile:
                                        writer = csv.writer(csvfile)
                                        writer.writerows(data)

                                    data_row_count = len(data) - 1
                                    logging.info(f"Saved {data_row_count} rows for {final_output_file_name}")

                                except IOError as e:
                                    # Changed to logging.fatal and added RuntimeError
                                    error_message = f"FATAL ERROR: Failed to write to file {final_output_path}: {e}. Terminating script."
                                    logging.fatal(error_message)
                                    raise RuntimeError(error_message) from e
                            else:
                                logging.warning(f"Skipping set: No data found for {state_abbr} / {cod_name} / {race_name}")

    logging.info("Completed all requested state data processing runs. Data saved to 'raw_folders/' directory.")

if __name__ == '__main__':
    app.run(main)