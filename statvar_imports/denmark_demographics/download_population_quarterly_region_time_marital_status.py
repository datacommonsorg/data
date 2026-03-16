import requests
import pandas as pd
import itertools
import os
from datetime import datetime

# --- CONFIGURATION ---
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "FOLK1A"

#FLAG: Set to True to download all available time periods
DOWNLOAD_ALL = False

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# --- STEP 1: Determine Current and Previous Year ---
current_year = datetime.now().year
previous_year = current_year - 1
target_years = [str(previous_year), str(current_year)]

print(f"Targeting data for years: {target_years}")

# --- STEP 2: Get Metadata (Regions and Quarters) ---
print("Fetching table metadata...")
meta_url = f"https://api.statbank.dk/v1/tableinfo/{table_id}"
meta_res = requests.get(meta_url)
meta_data = meta_res.json()

regions = []
all_quarters = []

for var in meta_data.get('variables', []):
    if var['id'] == 'OMRÅDE':
        regions = [val['id'] for val in var['values']]
    if var['id'] == 'Tid':
        # Statbank 'Tid' IDs are usually like '2020K1', '2020K2'
        all_quarters = [val['id'] for val in var['values']]

# --- STEP 3: Download Logic ---
if DOWNLOAD_ALL:
    target_quarters = all_quarters
    print(f"Flag 'DOWNLOAD_ALL' is True. Targeting all {len(target_quarters)} quarters.")
else:
    # Filter quarters to only include those in our target years
    target_quarters = [q for q in all_quarters if any(year in q for year in target_years)]
    print(f"Flag 'DOWNLOAD_ALL' is False. Targeting {len(target_quarters)} quarters for {target_years}.")

if not target_quarters:
    print("No matching quarters found for the specified years.")
    exit()

print(f"Targeting {len(target_quarters)} quarters: {target_quarters}")

# --- STEP 4: Loop through each Region ---
def find_key_recursive(source_dict, target_key):
    if target_key in source_dict: return source_dict[target_key]
    for key, value in source_dict.items():
        if isinstance(value, dict):
            found = find_key_recursive(value, target_key)
            if found is not None: return found
    return None

for region_code in regions:
    print(f"Processing Region Code: {region_code}...")
    
    payload = {
       "table": table_id,
       "format": "JSONSTAT",
       "lang": "en",
       "variables": [
          {"code": "OMRÅDE", "values": [region_code]}, 
          {"code": "KØN", "values": ["*"]},
          {"code": "ALDER", "values": ["*"]},
          {"code": "CIVILSTAND", "values": ["*"]},
          {"code": "Tid", "values": target_quarters} # <--- Filtered Quarters
       ]
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        full_data = response.json()
        dims = find_key_recursive(full_data, 'dimension')
        vals = find_key_recursive(full_data, 'value')
        
        if dims and vals:
            # ... (Rest of your processing logic remains the same)
            ids = find_key_recursive(full_data, 'id') or list(dims.keys())
            role = find_key_recursive(full_data, 'role') or {}
            metric_ids = role.get('metric', [])
            dim_list = []
            col_names = []
            
            for d_id in ids:
                if d_id in metric_ids or d_id.lower() in ['indhold', 'contents']: continue
                labels = dims[d_id]['category']['label']
                dim_list.append(list(labels.values()))
                col_names.append(d_id)

            df = pd.DataFrame(list(itertools.product(*dim_list)), columns=col_names)
            df['Value'] = vals
            df = df.rename(columns={'OMRÅDE': 'Region', 'ALDER': 'Age', 'CIVILSTAND': 'Marital_Status', 'Tid': 'Quarter', 'KØN': 'Sex'})

            df.loc[df['Sex'] == 'Total', 'Sex'] = 'Gender_Total'
            df.loc[df['Marital_Status'] == 'Total', 'Marital_Status'] = 'Marital_Total'

            filename = f'population_quarterly_region_time_marital_status_{region_code}.csv'
            df.to_csv(os.path.join(output_dir, filename), index=False)
            print(f"    Saved: {filename}")
    else:
        print(f"    Failed {region_code}: {response.status_code}")

print("\nDownload complete.")