import pandas as pd
import os
import logging
import requests
import time
from datetime import datetime
from google.cloud import storage
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# GCS Template Path
GCS_TEMPLATE_PATH = "gs://datcom-prod-imports/statvar_imports/statistics_poland/poland_data_sample/StatisticsPoland_input.csv"

# Local Output Directory
OUTPUT_DIR = os.path.join(BASE_PATH, "source_files")

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
        
        # Method 1: Direct Pandas Read (requires gcsfs)
        # return pd.read_csv(gcs_path, header=[0,1,2,3], index_col=[0,1])
        
        # Method 2: Google Cloud Storage Client (More robust if gcsfs isn't configured)
        storage_client = storage.Client()
        
        # Parse bucket and blob
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

def fetch_variables():
    """Fetches all variables for Subject P3447."""
    logging.info(f"Downloading variable list for Subject {SUBJECT_ID}...")
    v_map = {}
    
    # Check pages 0-10 to ensure we get ALL variables
    for page in range(10): 
        url = f"{API_BASE_URL}/variables?subject-id={SUBJECT_ID}&page-size=100&lang=pl&page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code != 200: break
            data = resp.json()
            results = data.get('results', [])
            if not results: break
            
            for item in results:
                full_name_parts = [str(v) for k, v in item.items() if k.startswith('n') and v]
                full_name = " ".join(full_name_parts).lower()
                v_map[str(item['id'])] = full_name
            
            if len(results) < 100: break
        except Exception as e:
            logging.error(f"Metadata error page {page}: {e}")
            break
            
    logging.info(f"Indexed {len(v_map)} variables.")
    return v_map

def download_and_process():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    # 1. LOAD TEMPLATE FROM GCS
    template_df = load_template_from_gcs(GCS_TEMPLATE_PATH)
    if template_df is None: return

    # Force index to strings
    template_df.index = template_df.index.set_levels([
        template_df.index.levels[0].astype(str), 
        template_df.index.levels[1].astype(str)
    ])
    
    region_map = get_template_map(template_df)
    v_metadata = fetch_variables()
    if not v_metadata: return

    master_data = []
    unique_cols = template_df.columns.droplevel('Year').unique()
    current_year = datetime.now().year
    
    # 2. MATCH & DOWNLOAD (Specific Ages Only)
    for age, sex, loc in unique_cols:
        # SKIP TOTALS HERE -> We will calculate them later!
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
        
        # Download Loop
        for lv in ["0", "2"]:
            api_url = f"{API_BASE_URL}/data/by-variable/{var_id}"
            params = [('unit-level', lv), ('page-size', '100')]
            
            for y in range(2003, current_year + 2): 
                params.append(('year', str(y)))
            
            try:
                resp = requests.get(api_url, headers=HEADERS, params=params, timeout=20)
                if resp.status_code != 200: continue
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
        time.sleep(0.05)

    if not master_data:
        logging.error("No data collected.")
        return

    # 3. PROCESS & CALCULATE TOTALS
    full_df = pd.DataFrame(master_data)
    
    for year in sorted(full_df['Year'].unique()):
        year_df = full_df[full_df['Year'] == year]
        
        # Pivot specific ages
        pivot_df = year_df.pivot_table(
            index=['Code', 'Name'],
            columns=['Age', 'Sex', 'Location', 'Year'],
            values='Value'
        )
        
        # Sum Age columns to create "Total" Age column
        totals = pivot_df.groupby(level=['Sex', 'Location', 'Year'], axis=1).sum()
        
        # Map calculated totals to the 'Age' level (using 'total' label for now)
        new_columns = pd.MultiIndex.from_tuples(
            [('total', s, l, y) for s, l, y in totals.columns],
            names=['Age', 'Sex', 'Location', 'Year']
        )
        totals.columns = new_columns
        
        combined_df = pd.concat([pivot_df, totals], axis=1)

        # 4. REINDEX AGAINST TEMPLATE
        # Construct expected columns based on template structure for THIS year
        target_columns = []
        for col in template_df.columns:
            t_age, t_sex, t_loc, _ = col
            
            # Map Template Age to Our Age
            if pd.isna(t_age) or str(t_age).strip() == '':
                lookup_age = 'total'
            else:
                lookup_age = t_age
                
            target_columns.append((lookup_age, t_sex, t_loc, str(year)))

        # Reindex rows (Code/Name)
        final_df = combined_df.reindex(template_df.index)
        
        # Reindex columns to match template order
        try:
            final_df = final_df[target_columns]
            
            # Restore original headers (e.g. putting back empty strings for Total Age)
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
    download_and_process()