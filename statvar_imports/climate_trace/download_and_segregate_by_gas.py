
import requests
import zipfile
import pandas as pd
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_and_process_zip(url, country_iso, gas):
    """
    Downloads a single zip file and processes it in memory, returning a DataFrame.
    """
    try:
        print(f"  Downloading: {country_iso} for {gas}...")
        response = requests.get(url)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            csv_files_info = [
                f for f in zip_ref.infolist()
                if "country" in f.filename.lower() and f.filename.endswith('.csv') and not f.is_dir()
            ]

            df_list = []
            for file_info in csv_files_info:
                with zip_ref.open(file_info.filename) as file_in_zip:
                    df = pd.read_csv(file_in_zip)
                    df_list.append(df)
            
            if df_list:
                return pd.concat(df_list, ignore_index=True)
            else:
                return None
    except requests.exceptions.RequestException as e:
        print(f"    -> Failed to download {url}: {e}")
        return None
    except zipfile.BadZipFile:
        print(f"    -> Bad zip file for {url}")
        return None
    except Exception as e:
        print(f"    -> An unexpected error occurred for {url}: {e}")
        return None

def download_and_segregate_by_gas():
    """
    Generates a fresh list of country download URLs and then downloads all
    data, saving a separate concatenated CSV for each gas.
    """
    print("--- Step 1: Generating Country URL List ---")
    api_country_codes = set()
    try:
        countries_url = "https://api.climatetrace.org/v7/admins?level=0"
        response = requests.get(countries_url)
        response.raise_for_status()
        countries = response.json()
        api_country_codes = {country['id'] for country in countries}
        print(f"Successfully fetched {len(api_country_codes)} countries from API.")
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch country list from API: {e}. Proceeding with local list only.")

    local_country_codes = set()
    try:
        with open('check_country.csv', 'r') as f:
            local_country_codes = {line.strip() for line in f if line.strip()}
        print(f"Read {len(local_country_codes)} countries from 'check_country.csv'.")
    except FileNotFoundError:
        print("Warning: 'check_country.csv' not found. Will only use countries from API.")

    combined_codes = sorted(list(api_country_codes.union(local_country_codes)))
    print(f"Total unique countries to process: {len(combined_codes)}")

    gases = ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]
    base_url = "https://downloads.climatetrace.org/latest/country_packages"
    country_urls = {}
    for iso in combined_codes:
        country_urls[iso] = {}
        for gas in gases:
            url = f"{base_url}/{gas}/{iso}.zip"
            country_urls[iso][gas] = url
    
    print("--- Step 1 Complete: URL List Generated ---\\n")
    print("--- Step 2: Downloading and Processing Data ---")
    
    output_dir = "input_files"
    os.makedirs(output_dir, exist_ok=True)

    all_gases = sorted(list(set(gas for gases in country_urls.values() for gas in gases)))
    print(f"Found data for the following gas types: {', '.join(all_gases)}\\n")

    for gas in all_gases:
        print(f"--- Starting processing for gas: {gas} ---")

        gas_specific_urls = []
        for iso, gas_data in country_urls.items():
            if gas in gas_data:
                gas_specific_urls.append({"iso": iso, "url": gas_data[gas]})

        gas_dataframes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {
                executor.submit(download_and_process_zip, item['url'], item['iso'], gas): item
                for item in gas_specific_urls
            }
            for future in as_completed(future_to_url):
                result_df = future.result()
                if result_df is not None and not result_df.empty:
                    gas_dataframes.append(result_df)

        if not gas_dataframes:
            print(f"No data was downloaded for {gas}. The output file will not be created.")
            continue

        output_filename = os.path.join(output_dir, f"all_countries_{gas}.csv")
        print(f"\\n  -> All downloads for {gas} complete. Concatenating...")
        
        try:
            final_df = pd.concat(gas_dataframes, ignore_index=True)
            print(f"  -> Saving combined data to {output_filename}...")
            final_df.to_csv(output_filename, index=False)
            print(f"  -> Successfully created {output_filename} with {len(final_df)} rows.\\n")
        except Exception as e:
            print(f"  -> An error occurred during the final processing for {gas}: {e}\\n")

    print("--- All processing complete. ---")

if __name__ == '__main__':
    download_and_segregate_by_gas()
