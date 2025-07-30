# Copyright 2025 Google LLC
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


import os
import sys
import hashlib
import pandas as pd
import requests
import re 
from urllib.parse import urlparse, parse_qs, urlencode
from absl import logging
from absl import app 



# Define the base directory for GCS output (or local output)
_GCS_OUTPUT_BASE_DIR = "gcs_output"

def fetch_api_data(api_url):
    """
    Fetches JSON data from the given API URL using the requests library.
    Handles network errors, HTTP status codes, and JSON decoding errors.
    Returns the parsed JSON dictionary on success, None on any failure.
    """
    logging.info(f"Attempting to fetch data from: {api_url}")
    try:
        # Make the HTTP GET request
        response = requests.get(api_url)

        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()

        # Attempt to parse the response as JSON
        data = response.json()
        logging.info("Data fetched and parsed successfully.")
        return data

    except requests.exceptions.HTTPError as http_err:
        logging.fatal(f"HTTP error occurred for {api_url}: {http_err} - Response: {response.text[:200]}...")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        logging.fatal(f"Connection error occurred for {api_url}: {conn_err}")
        return None
    except requests.exceptions.Timeout as timeout_err:
        logging.fatal(f"Timeout error occurred for {api_url}: {timeout_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        logging.fatal(f"A general request error occurred for {api_url}: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        logging.fatal(f"Error decoding JSON response from {api_url}: {json_err}. Response content: {response.text[:200]}...")
        return None
    except Exception as e:
        logging.fatal(f"An unexpected error occurred while fetching {api_url}: {e}")
        return None

def extract_metadata_mapping(headers):
    """
    Extracts display name mappings for both indicators and dimensions from the 'Headers' section.
    Returns a dictionary mapping original IDs to DisplayNames.
    """
    items = headers.get("Items", [])
    mapping = {}
    for h in items:
        if h.get("indicator_dimension") in ["Indicator", "Dimension"]:
            mapping[h["ID"]] = h.get("DisplayName", h["ID"])
    return mapping

def flatten_data_records(raw_records):
    """
    Flattens a list of raw data records into a consistent format suitable for a DataFrame.
    This function intelligently handles two common structures observed in NDAP API responses:
    1. A list containing a single dictionary where keys are indicator IDs and values are nested
       dictionaries containing statistical measures (like 'avg', 'max', 'min').
    2. A list of dictionaries where each dictionary directly represents a row of data,
       with dimensions and indicators as direct key-value pairs (possibly with 'avg' nested).
    """
    cleaned_records = []
    if not raw_records:
        return cleaned_records

    first_record = raw_records[0]

    if len(raw_records) == 1 and isinstance(first_record, dict) and \
       all(isinstance(val, dict) and 'avg' in val for val in first_record.values()):
        
        for indicator_id, details in first_record.items():
            flat_row = {'Indicator': indicator_id}
            for key, value in details.items():
                flat_row[key] = value
            cleaned_records.append(flat_row)
    else:
        # This is the crucial 'else' block for disaggregated/flat data
        logging.debug("Detected flat or disaggregated data structure in flatten_data_records.")
        for row in raw_records:
            flat_row = {}
            for key, value in row.items():
                # If an indicator value is still nested (e.g., if it has 'avg'), extract 'avg'.
                # Otherwise, keep the value as is (for dimensions or already flat indicators).
                flat_row[key] = value["avg"] if isinstance(value, dict) and "avg" in value else value
            cleaned_records.append(flat_row)
 
    return cleaned_records

def hash_page_records(records):
    """
    Generates an MD5 hash for a list of records. Used to detect identical pages
    during pagination to prevent infinite loops. Ensures consistent hashing by
    sorting dictionary items and converting values to string.
    """
    m = hashlib.md5()
    for rec in records:
        sorted_items = sorted([(k, str(v)) for k, v in rec.items()])
        record_string = str(sorted_items)
        m.update(record_string.encode('utf-8'))
    return m.hexdigest()

def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs preprocessing steps on the DataFrame, including:
    - Generating 'YearCode' from 'Year' column.
    - Generating 'DistrictName' from 'District' and 'State' columns.
    
    Args:
        df (pd.DataFrame): The DataFrame to preprocess.
        
    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    # Step 1: Add 'YearCode' column
    if 'Year' in df.columns:
        # Ensure 'Year' is treated as string to apply regex safely
        df['Year'] = df['Year'].astype(str)
        # Insert 'YearCode' right after 'Year'
        df.insert(df.columns.get_loc('Year') + 1, 'YearCode', '')
        # Extract 4-digit numbers as year codes
        df['YearCode'] = df['Year'].apply(lambda x: ', '.join(re.findall(r'\b\d{4}\b', x)) if pd.notna(x) else '')
        
        if not (df['YearCode'] == '').all(): # Check if any YearCode was actually extracted
            logging.info(" 'YearCode' column generated successfully.")
        else:
            logging.warning(" 'Year' column found, but no 4-digit years could be extracted for 'YearCode'.")
    

    # Step 2: Generate 'DistrictName' from 'District' and 'State'
    if 'District' in df.columns and 'State' in df.columns:
        # Find the correct insertion point (after 'District' if it exists)
        insert_loc = df.columns.get_loc('District') + 1 if 'District' in df.columns else (df.columns.get_loc('State') + 1 if 'State' in df.columns else len(df.columns))
        df.insert(insert_loc, 'DistrictName', '')
        df['DistrictName'] = df.apply(
            lambda row: f"{row['District']}_{row['State']}" if pd.notna(row['District']) and pd.notna(row['State']) else '',
            axis=1
        )
        if not (df['DistrictName'] == '').all(): # Check if any DistrictName was actually generated
            logging.info(" 'DistrictName' column generated successfully.")
        else:
            logging.warning(" 'District' and 'State' columns found, but no 'DistrictName' could be generated (perhaps missing values).")
    else:
        logging.info("'District' or 'State' columns not found, skipping 'DistrictName' generation.")
        
    return df

def process_ndap_api(api_url, output_dir, output_filename=None):
    """
    Downloads all paginated data from an NDAP API URL, processes it,
    and saves it to a CSV file.
    """
    logging.info(f"\n Starting full data fetch for: {api_url}")
    all_fetched_records = []
    current_page = 1
    seen_page_hashes = set() # Stores hashes of page content to detect duplicates

    metadata_headers = None # Will hold metadata/headers from the first successfully fetched page.

    # Parse the base URL to cleanly add/update the 'pageno' parameter
    base_url_parsed = urlparse(api_url)
    query_params = parse_qs(base_url_parsed.query)
    
    # Remove any existing pageno from the base URL to rebuild it accurately
    if 'pageno' in query_params:
        del query_params['pageno']
    
    # Reconstruct the base URL without pageno, ready for pagination
    base_url_for_pagination = base_url_parsed._replace(query=urlencode(query_params, doseq=True)).geturl()

    while True:
        paginated_url = f"{base_url_for_pagination}&pageno={current_page}"
        data = fetch_api_data(paginated_url)

        if data is None: 
            logging.fatal(f" Failed to retrieve valid data for page {current_page}, stopping pagination.")
            break

        page_raw_records = data.get("Data", [])
        
        if metadata_headers is None:
            metadata_headers = data.get("Headers", {})

        page_processed_records = flatten_data_records(page_raw_records)

        if not page_processed_records:
            logging.info(f" Page {current_page} returned no processed records after flattening, indicating end of data.")
            break

        current_page_hash = hash_page_records(page_processed_records)
        if current_page_hash in seen_page_hashes:
            logging.info(f" Page {current_page} has duplicate content. Stopping pagination to avoid infinite loop.")
            break
        seen_page_hashes.add(current_page_hash)

        all_fetched_records.extend(page_processed_records)
        logging.info(f" Page {current_page}: {len(page_processed_records)} records fetched. Total records collected: {len(all_fetched_records)}")

        current_page += 1

    # Final processing and saving to CSV
    if not all_fetched_records:
        logging.fatal(f" No data was fetched across all pages for URL: {api_url}. This API call might be problematic.")
        return

    column_name_mapping = extract_metadata_mapping(metadata_headers if metadata_headers else {})
    
    df = pd.DataFrame(all_fetched_records)
    
    valid_renames = {old_name: new_name for old_name, new_name in column_name_mapping.items() if old_name in df.columns}
    df.rename(columns=valid_renames, inplace=True)

    # Call the new preprocessing method here
    df = preprocess_dataframe(df)

    os.makedirs(output_dir, exist_ok=True)
    
    final_output_filename = output_filename if output_filename else generate_filename(api_url)
    output_filepath = os.path.join(output_dir, final_output_filename)
    
    df.to_csv(output_filepath, index=False, encoding='utf-8')
    logging.info(f" All data successfully saved to: {output_filepath} (Total records: {len(all_fetched_records)})")


def main(argv):
    output_directory = _GCS_OUTPUT_BASE_DIR

    api_configs = {
        "NFHS_Survey4.csv": "https://loadqa.ndapapi.com/v1/openapi?API_Key=gAAAAABoiHE-U-_pBt86RVzXej_3OZ4-W1DcOh0LT4nvwSKkZdTgWXMAtSp24J_Au9O-eL7gM6IcJqGRq42deVhdSS0pHotzbgKJU36gH_OtubzLQvy4gzi4YamMuQU0VIkUHrFeoAKmCl-PVnTfhjOS0t5mvQ5XoVH1ApTS7qzSml6H0NCKKcYO6WxIBucT5B36lQa5lY1_&ind=I7034_6,I7034_7,I7034_8,I7034_9,I7034_10,I7034_11,I7034_12,I7034_13,I7034_14,I7034_15,I7034_16,I7034_17,I7034_18,I7034_19,I7034_20,I7034_21,I7034_22,I7034_23,I7034_24,I7034_25,I7034_26,I7034_27,I7034_28,I7034_29,I7034_30,I7034_31,I7034_32,I7034_33,I7034_34,I7034_35,I7034_36,I7034_37,I7034_38,I7034_39,I7034_40,I7034_41,I7034_42,I7034_43,I7034_44,I7034_45,I7034_46,I7034_47,I7034_48,I7034_49,I7034_50,I7034_51,I7034_52,I7034_53,I7034_54,I7034_55,I7034_56,I7034_57,I7034_58,I7034_59,I7034_60,I7034_61,I7034_62,I7034_63,I7034_64,I7034_65,I7034_66,I7034_67,I7034_68,I7034_69,I7034_70,I7034_71,I7034_72,I7034_73,I7034_74,I7034_75,I7034_76,I7034_77,I7034_78,I7034_79,I7034_80,I7034_81,I7034_82,I7034_83,I7034_84,I7034_85,I7034_86,I7034_87,I7034_88,I7034_89,I7034_90,I7034_91,I7034_92,I7034_93,I7034_94,I7034_95,I7034_96,I7034_97,I7034_98&dim=Country,StateName,StateCode,DistrictName,DistrictCode,Year,TRU&pageno=1",
        "NFHS_state.csv": "https://loadqa.ndapapi.com/v1/openapi?API_Key=gAAAAABoiHEaAsQxmqRW9wF-6I5HPgPKhskfLnVTcaU8EfgvhZGpXD6OtzyAZnW6F-syR2rijWlYPJ9rs1WsEKOgi2-vfr2amYbJsFpmnQdz11R4Zf6UyBaj4Hy3ymejec3DU3vH5kMVJ8GfaGjyQhkSSQasRz_K1B1lmRPIq1DkQZVj1Blwqa0EVaEWJz4BtQAmT7mcCt5h&ind=I6821_6,I6821_7,I6821_8,I6821_9,I6821_10,I6821_11,I6821_12,I6821_13,I6821_14,I6821_15,I6821_16,I6821_17,I6821_18,I6821_19,I6821_20,I6821_21,I6821_22,I6821_23,I6821_24,I6821_25,I6821_26,I6821_27,I6821_28,I6821_29,I6821_30,I6821_31,I6821_32,I6821_33,I6821_34,I6821_35,I6821_36,I6821_37,I6821_38,I6821_39,I6821_40,I6821_41,I6821_42,I6821_43,I6821_44,I6821_45,I6821_46,I6821_47,I6821_48,I6821_49,I6821_50,I6821_51,I6821_52,I6821_53,I6821_54,I6821_55,I6821_56,I6821_57,I6821_58,I6821_59,I6821_60,I6821_61,I6821_62,I6821_63,I6821_64,I6821_65,I6821_66,I6821_67,I6821_68,I6821_69,I6821_70,I6821_71,I6821_72,I6821_73,I6821_74,I6821_75,I6821_76,I6821_77,I6821_78,I6821_79,I6821_80,I6821_81,I6821_82,I6821_83,I6821_84,I6821_85,I6821_86,I6821_87,I6821_88,I6821_89,I6821_90,I6821_91,I6821_92,I6821_93,I6821_94,I6821_95,I6821_96,I6821_97,I6821_98,I6821_99,I6821_100,I6821_101,I6821_102,I6821_103,I6821_104,I6821_105,I6821_106,I6821_107,I6821_108,I6821_109,I6821_110,I6821_111,I6821_112,I6821_113,I6821_114,I6821_115,I6821_116,I6821_117,I6821_118,I6821_119,I6821_120,I6821_121,I6821_122,I6821_123,I6821_124,I6821_125,I6821_126,I6821_127,I6821_128,I6821_129,I6821_130,I6821_131,I6821_132,I6821_133,I6821_134,I6821_135,I6821_136&dim=Country,StateName,StateCode,Year,TRU,D6821_5&pageno=1",
        "NFHS_Survey5.csv": "https://loadqa.ndapapi.com/v1/openapi?API_Key=gAAAAABoiHJ0lepNXH0_Q9Ejc39RDxzOBzk5QPdq9vhzFwLxLISZtksFD9pAeEUmj8gGdFFRXSwFcHXQs-QMZcu44fF-1zCboI0BXmNTfbe_0i79QtBN-HG3Le_XKuue88PS7g8C0MkAYJJV5NJbYqlR7rD6dzm-iXG0s7cZRfcr0Ku1lFaAO1DXQjMc3P7bhYfhvLeQHPT8&ind=I6822_7,I6822_8,I6822_9,I6822_10,I6822_11,I6822_12,I6822_13,I6822_14,I6822_15,I6822_16,I6822_17,I6822_18,I6822_19,I6822_20,I6822_21,I6822_22,I6822_23,I6822_24,I6822_25,I6822_26,I6822_27,I6822_28,I6822_29,I6822_30,I6822_31,I6822_32,I6822_33,I6822_34,I6822_35,I6822_36,I6822_37,I6822_38,I6822_39,I6822_40,I6822_41,I6822_42,I6822_43,I6822_44,I6822_45,I6822_46,I6822_47,I6822_48,I6822_49,I6822_50,I6822_51,I6822_52,I6822_53,I6822_54,I6822_55,I6822_56,I6822_57,I6822_58,I6822_59,I6822_60,I6822_61,I6822_62,I6822_63,I6822_64,I6822_65,I6822_66,I6822_67,I6822_68,I6822_69,I6822_70,I6822_71,I6822_72,I6822_73,I6822_74,I6822_75,I6822_76,I6822_77,I6822_78,I6822_79,I6822_80,I6822_81,I6822_82,I6822_83,I6822_84,I6822_85,I6822_86,I6822_87,I6822_88,I6822_89,I6822_90,I6822_91,I6822_92,I6822_93,I6822_94,I6822_95,I6822_96,I6822_97,I6822_98,I6822_99,I6822_100,I6822_101,I6822_102,I6822_103,I6822_104,I6822_105,I6822_106,I6822_107,I6822_108,I6822_109,I6822_110&dim=Country,StateName,StateCode,DistrictName,DistrictCode,Year&pageno=1"
    }

    for filename, url in api_configs.items():
        process_ndap_api(url, output_directory, output_filename=filename)

if __name__ == "__main__":
    app.run(main)
