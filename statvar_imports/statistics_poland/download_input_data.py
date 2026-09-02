import pandas as pd
import os
import logging
import requests
import time
import sys
import traceback
from datetime import datetime
from google.cloud import storage
import io
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Outputs exactly to source_files to match your manifest.json
OUTPUT_DIR = os.path.join(BASE_PATH, "source_files")

GCS_TEMPLATE_PATH = "gs://datcom-prod-imports/statvar_imports/statistics_poland/poland_data_sample/StatisticsPoland_input.csv"

API_BASE_URL = "https://bdl.stat.gov.pl/api/v1"
API_KEY = "c9a9da02-47ab-4391-dff1-08de66e5ba7b"
HEADERS = {'X-ClientId': API_KEY}

SUBJECT_ID = "P3447"

SEX_STEMS = {
    'total': [], 
    'males': ['męż'], 
    'females': ['kob'] 
}
LOC_STEMS = {
    'total': [], 
    'in urban areas': ['miast'], 
    'in rural areas': ['wsi', 'wieś'] 
}

# AGE STEMS
AGE_STEMS = {
    '0-2': '0-2', '3-6': '3-6', '7-12': '7-12', '13-15': '13-15', 
    '16-19': '16-19', '20-24': '20-24', '25-34': '25-34', '35-44': '35-44', 
    '45-54': '45-54', '55-64': '55-64', '65 and more': '65' 
}

def load_template_from_gcs(gcs_path):
    """Loads the template CSV directly from GCS."""
    try:
        logging.info(f"Reading template from {gcs_path}...")
        storage_client = storage.Client()
        path_parts = gcs_path.replace("gs://", "").split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1]
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_text()
        
        return pd.read_csv(io.StringIO(content), header=[0,1,2,3], index_col=[0,1])
    except Exception as e:
        logging.error(f"Failed to load template from GCS: {e}")
        return None

def get_template_map(template_df):
    """Maps Region Name -> Code (as String)."""
    name_to_code = {}
    for code, name in template_df.index:
        clean_name = str(name).strip().upper()
        name_to_code[clean_name] = str(code).strip()
    return name_to_code

def get_http_session(retries=10, backoff_factor=1.5):
    """Creates a requests session with automatic HTTP retries and backoff."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def make_request(session, url, headers=None, params=None, timeout=60):
    """Makes an HTTP GET request using the session's configured retry strategy and timeout."""
    try:
        return session.get(url, headers=headers, params=params, timeout=timeout)
    except Exception as e:
        logging.error(f"HTTP GET failed for {url}: {e}")
        return None

def fetch_variables(session):
    """Fetches all variables for Subject P3447 with retries."""
    logging.info(f"Downloading variable list for Subject {SUBJECT_ID}...")
    v_map = {}
    
    for page in range(10): 
        url = f"{API_BASE_URL}/variables?subject-id={SUBJECT_ID}&page-size=100&lang=pl&page={page}"
        try:
            resp = make_request(session, url, headers=HEADERS, timeout=60)
            if resp is None or resp.status_code != 200:
                logging.warning(f"Metadata page {page} returned status {resp.status_code if resp else 'None'}")
                break
            data = resp.json()
            results = data.get('results', [])
            if not results:
                break
            
            for item in results:
                full_name_parts = [str(v) for k, v in item.items() if k.startswith('n') and v]
                full_name = " ".join(full_name_parts).lower()
                v_map[str(item['id'])] = full_name
            
            if len(results) < 100:
                break
        except Exception as e:
            logging.error(f"Metadata error page {page} after retries: {e}")
            break
            
    logging.info(f"Indexed {len(v_map)} variables.")
    return v_map

def download_and_process():
    # Safely create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    template_df = load_template_from_gcs(GCS_TEMPLATE_PATH)
    if template_df is None: 
        raise ValueError("Template DataFrame failed to load from GCS.")

    template_df.index = template_df.index.set_levels([
        template_df.index.levels[0].astype(str), 
        template_df.index.levels[1].astype(str)
    ])
    
    session = get_http_session()
    region_map = get_template_map(template_df)
    v_metadata = fetch_variables(session)
    if not v_metadata: 
        raise ValueError("Variable metadata failed to download.")

    master_data = []
    unique_cols = template_df.columns.droplevel('Year').unique()
    current_year = datetime.now().year
    
    for age, sex, loc in unique_cols:
        if pd.isna(age) or str(age).strip() == '' or str(age).lower() == 'total':
            continue

        target_age = AGE_STEMS.get(age, age)
        sex_stems = SEX_STEMS[sex]
        loc_stems = LOC_STEMS[loc]
        
        var_id = None
        for vid, vname in v_metadata.items():
            name_no_space = vname.replace(" ", "")
            target_age_no_space = target_age.replace(" ", "")
            if target_age_no_space not in name_no_space: continue
            
            if sex_stems:
                if not any(s in vname for s in sex_stems): continue
            else:
                if 'męż' in vname or 'kob' in vname: continue
                
            if loc_stems:
                if not any(s in vname for s in loc_stems): continue
            else:
                if 'miast' in vname or 'wsi' in vname or 'wieś' in vname: continue
            
            var_id = vid
            break
        
        if not var_id:
            logging.warning(f"SKIPPING: {age}|{sex}|{loc}")
            continue
            
        logging.info(f"MATCH: {age}|{sex}|{loc} -> ID {var_id}")
        
        for lv in ["0", "2"]:
            api_url = f"{API_BASE_URL}/data/by-variable/{var_id}"
            params = [('unit-level', lv), ('page-size', '100')]
            
            for y in range(2003, current_year + 2): 
                params.append(('year', str(y)))
            
            try:
                resp = make_request(session, api_url, headers=HEADERS, params=params, timeout=60)
                if resp is None or resp.status_code != 200:
                    logging.error(f"Download returned status {resp.status_code if resp else 'None'} for var {var_id} level {lv}")
                    continue
                results = resp.json().get('results', [])
                if not results: continue
                
                sample_res = results[0]
                api_name_key = next((k for k in ['name', 'n', 'unitName'] if k in sample_res), None)
                if not api_name_key: continue

                for res in results:
                    api_name = res[api_name_key].upper().strip()
                    if api_name == "POLSKA": api_name = "POLAND"
                    
                    matched_code = region_map.get(api_name)
                    matched_name = api_name 
                    if not matched_code:
                        for t_name, t_code in region_map.items():
                            if t_name in api_name:
                                matched_code = t_code
                                matched_name = t_name 
                                break
                    
                    if matched_code is not None:
                        for val in res['values']:
                            master_data.append({
                                'Code': str(matched_code),
                                'Name': matched_name,
                                'Year': str(val['year']),
                                'Value': val['val'],
                                'Age': age, 'Sex': sex, 'Location': loc
                            })
            except Exception as e:
                logging.error(f"Download Error on {var_id}: {e}")
            time.sleep(0.1)
        time.sleep(0.1)

    if not master_data:
        raise ValueError("No data collected during the download loop.")

    full_df = pd.DataFrame(master_data)
    
    for year in sorted(full_df['Year'].unique()):
        year_df = full_df[full_df['Year'] == year]
        
        pivot_df = year_df.pivot_table(
            index=['Code', 'Name'],
            columns=['Age', 'Sex', 'Location', 'Year'],
            values='Value'
        )
        
        # CLOUD FIX: Replaced 'axis=1' grouping which crashes in modern Pandas environments.
        # Transposing before and after groupby achieves the exact same result safely.
        totals = pivot_df.T.groupby(level=['Sex', 'Location', 'Year']).sum().T
        
        new_columns = pd.MultiIndex.from_tuples(
            [('total', s, l, y) for s, l, y in totals.columns],
            names=['Age', 'Sex', 'Location', 'Year']
        )
        totals.columns = new_columns
        
        combined_df = pd.concat([pivot_df, totals], axis=1)

        target_columns = []
        for col in template_df.columns:
            t_age, t_sex, t_loc, _ = col
            lookup_age = 'total' if pd.isna(t_age) or str(t_age).strip() == '' else t_age
            target_columns.append((lookup_age, t_sex, t_loc, str(year)))

        final_df = combined_df.reindex(template_df.index)
        
        try:
            final_df = final_df[target_columns]
            final_headers = []
            for col in template_df.columns:
                 t_age, t_sex, t_loc, _ = col
                 final_headers.append((t_age, t_sex, t_loc, str(year)))
            
            final_df.columns = pd.MultiIndex.from_tuples(final_headers, names=['Age', 'Sex', 'Location', 'Year'])
        except KeyError as e:
            logging.warning(f"Column alignment warning for {year}: {e}")
            pass
        
        out_path = os.path.join(OUTPUT_DIR, f"StatisticsPoland_input_{year}.csv")
        final_df.to_csv(out_path)
        logging.info(f"Generated: {out_path}")

if __name__ == "__main__":
    try:
        download_and_process()
    except Exception as e:
        # CLOUD FIX: Catch any unhandled exceptions to prevent silent exit 1 failures.
        # This pushes the exact stack trace directly into Cloud Logging.
        logging.critical(f"FATAL SCRIPT ERROR: {e}")
        logging.critical(traceback.format_exc())
        sys.exit(1)