import requests
import pandas as pd
import os
from io import StringIO
import re

# --- CONFIGURATION ---
url = "https://api.statbank.dk/v1/data"
output_dir = "./input_files/"
table_id = "BEFOLK2"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# --- FETCH DATA ---
payload = {
   "table": table_id,
   "format": "BULK",
   "lang": "en",
   "variables": [
      {"code": "KØN", "values": ["*"]},
      {"code": "ALDER", "values": ["*"]},
      {"code": "Tid", "values": ["*"]}
   ]
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    df = pd.read_csv(StringIO(response.text), sep=';')
    sex_col, age_col, time_col, val_col = df.columns

    # 1. DYNAMIC SEX SORTING (Total -> Men -> Women)
    # We look for "Total" dynamically, then assume the rest are Men/Women
    sex_order = sorted(df[sex_col].unique(), key=lambda x: 0 if 'total' in str(x).lower() else 1)
    # If the API returns Men/Women, this ensures 'Total' is index 0
    df[sex_col] = pd.Categorical(df[sex_col], categories=sex_order, ordered=True)

    # 2. DYNAMIC AGE SORTING (Age, total -> 0-4 -> 5-9...)
    def get_age_rank(age_str):
        age_str = str(age_str).lower()
        if 'total' in age_str:
            return -1
        nums = re.findall(r'\d+', age_str)
        return int(nums[0]) if nums else 999

    # Create a temporary sort key
    df['age_sort'] = df[age_col].apply(get_age_rank)

    # 3. DYNAMIC YEAR SORTING
    # Ensure years are integers so 1901 comes before 2026
    df[time_col] = df[time_col].apply(lambda x: int(re.search(r'\d+', str(x)).group()))

    # Sort the dataframe before pivoting
    df = df.sort_values([sex_col, 'age_sort', time_col])

    # 4. PIVOT
    # We drop the age_sort key during pivot to keep the output clean
    df_pivot = df.pivot_table(
        index=[sex_col, age_col],
        columns=time_col,
        values=val_col,
        aggfunc='first',
        sort=False # CRITICAL: Keeps our manual sort order
    ).reset_index()
    df_pivot = df_pivot.rename(columns={'ALDER': 'Age', 'KØN': 'Sex'})

    # --- SAVE ---
    filename = "population_sex_age_time_input.csv"
    save_path = os.path.join(output_dir, filename)
    df_pivot.to_csv(save_path, index=False, encoding='utf-8-sig')

    print(f"File saved successfully: {save_path}")

else:
    print(f"Request failed: {response.status_code}")
