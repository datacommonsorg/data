import pandas as pd
import os
from datetime import datetime

def build_climate_data():
    """
    Downloads, parses, and combines live climate data from data.cdc.gov,
    then saves it to a Parquet file.
    """
    print("--- Starting Live Data Build Process ---")
    
    urls = {
        "SPEI": "https://data.cdc.gov/resource/6nbv-ifib.csv",
        "SPI": "https://data.cdc.gov/resource/xbk2-5i4e.csv",
        "PDSI": "https://data.cdc.gov/resource/en5r-5ds4.csv"
    }
    
    all_data = []
    
    for index_type, url in urls.items():
        try:
            print(f"Downloading data for {index_type}...")
            full_url = f"{url}?$limit=10000000"
            df = pd.read_csv(full_url)
            print(f"Successfully downloaded {len(df)} rows for {index_type}.")

            # --- Standardize the dataframe ---
            df["month"] = df["month"].map("{:02}".format)
            df["date"] = df["year"].astype(str) + "-" + df["month"].astype(str)
            
            if "fips" in df.columns:
                df.rename(columns={'fips': 'countyfips'}, inplace=True)
            
            df['countyfips'] = df['countyfips'].astype(str).str.zfill(5)
            
            if index_type == 'SPEI':
                df.rename(columns={'spei': 'Value'}, inplace=True)
            elif index_type == 'SPI':
                df.rename(columns={'spi': 'Value'}, inplace=True)
            elif index_type == 'PDSI':
                df.rename(columns={'pdsi': 'Value'}, inplace=True)

            df['index_type'] = index_type
            
            cols_to_keep = ['date', 'countyfips', 'Value', 'index_type']
            if all(col in df.columns for col in cols_to_keep):
                all_data.append(df[cols_to_keep])
            else:
                print(f"!!! WARNING: Could not process {index_type} due to missing columns.")

        except Exception as e:
            print(f"!!! ERROR: Failed to load or process data for {index_type}. Error: {e}")
            continue

    if not all_data:
        print("!!! FATAL: Could not load any climate data. Aborting build.")
        return

    # --- Combine and Save ---
    print("Combining datasets...")
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df['date'] = pd.to_datetime(combined_df['date'])

    output_path = os.path.join(os.path.dirname(__file__), 'climate_indices.parquet')
    combined_df.to_parquet(output_path, index=False)

    print(f"--- Build Successful ---")
    print(f"Successfully saved combined data to {output_path}")
    print(f"Total rows processed: {len(combined_df)}")

if __name__ == "__main__":
    build_climate_data()
