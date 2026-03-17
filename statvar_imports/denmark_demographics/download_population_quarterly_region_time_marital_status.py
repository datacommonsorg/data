import requests
import pandas as pd
import itertools
import os

# --- CONFIGURATION ---
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "FOLK1A"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

payload = {
   "table": table_id,
   "format": "JSONSTAT",
   "lang": "en",
   "variables": [
      {"code": "OMRÅDE", "values": ["000"]},  # All of Denmark
      {"code": "KØN", "values": ["*"]},
      {"code": "ALDER", "values": ["*"]},
      {"code": "CIVILSTAND", "values": ["*"]},
      {"code": "Tid", "values": ["*"]} 
   ]
}

def find_key_recursive(source_dict, target_key):
    if target_key in source_dict: return source_dict[target_key]
    for key, value in source_dict.items():
        if isinstance(value, dict):
            found = find_key_recursive(value, target_key)
            if found is not None: return found
    return None

response = requests.post(url, json=payload)

if response.status_code == 200:
    full_data = response.json()
    dims = find_key_recursive(full_data, 'dimension')
    vals = find_key_recursive(full_data, 'value')
    
    if dims and vals:
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

        # Build the DataFrame
        df = pd.DataFrame(list(itertools.product(*dim_list)), columns=col_names)
        df['Value'] = vals
        
        # Renaming and Cleanup
        df = df.rename(columns={'OMRÅDE': 'Region', 'ALDER': 'Age', 'CIVILSTAND': 'Marital_Status', 'Tid': 'Quarter', 'KØN': 'Sex'})
        df.loc[df['Sex'] == 'Total', 'Sex'] = 'Gender_Total'
        df.loc[df['Marital_Status'] == 'Total', 'Marital_Status'] = 'Marital_Total'

        filename = f'population_quarterly_region_time_marital_status_input.csv'
        df.to_csv(os.path.join(output_dir, filename), index=False)
        print(f"Done! Saved {len(df)} rows to {filename}")
else:
    print(f"Error: {response.status_code} - {response.text}")
