import requests
import zipfile
import pandas as pd
import io
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_process_zip(url, country_iso, gas):
    """
    Downloads a single zip file and processes it in memory, returning a DataFrame.
    """
    try:
        logging.info(f"  Downloading: {country_iso} for {gas}...")
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
                logging.warning(f"    -> No relevant CSV files found in zip for {country_iso} ({gas})")
                return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"    -> Not found (404) for {country_iso} ({gas}) at {url}")
        else:
            logging.error(f"    -> HTTP Error for {country_iso} ({gas}) at {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"    -> Unexpected error for {country_iso} ({gas}) at {url}: {e}")
        return None

def download_and_segregate_by_gas():
    """
    Generates a fresh list of country download URLs and then downloads all
    data, saving a separate concatenated CSV for each gas.
    """
    failed_downloads = []
    
    logging.info("--- Step 1: Generating Country URL List ---")
    api_country_codes = set()
    try:
        countries_url = "https://api.climatetrace.org/v7/admins?level=0"
        response = requests.get(countries_url)
        response.raise_for_status()
        countries = response.json()
        api_country_codes = {country['id'] for country in countries}
        logging.info(f"Successfully fetched {len(api_country_codes)} countries from API.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error: Could not fetch country list from API: {e}")
        # Not raising here, we might still have check_country.csv

    local_country_codes = set()
    try:
        with open('check_country.csv', 'r') as f:
            local_country_codes = {line.strip() for line in f if line.strip()}
        logging.info(f"Read {len(local_country_codes)} countries from 'check_country.csv'.")
    except FileNotFoundError:
        logging.warning("Warning: 'check_country.csv' not found. Will only use countries from API.")

    combined_codes = sorted(list(api_country_codes.union(local_country_codes)))
    if not combined_codes:
        logging.error("No countries to process. Exiting.")
        return

    logging.info(f"Total unique countries to process: {len(combined_codes)}")

    gases = ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]
    base_url = "https://downloads.climatetrace.org/latest/country_packages"
    country_urls = {}
    for iso in combined_codes:
        country_urls[iso] = {}
        for gas in gases:
            url = f"{base_url}/{gas}/{iso}.zip"
            country_urls[iso][gas] = url
    
    logging.info("--- Step 1 Complete: URL List Generated ---\n")
    logging.info("--- Step 2: Downloading and Processing Data ---")
    
    output_dir = "input_files"
    os.makedirs(output_dir, exist_ok=True)

    all_gases = sorted(list(set(gas for gases in country_urls.values() for gas in gases)))
    logging.info(f"Found data for the following gas types: {', '.join(all_gases)}\n")

    for gas in all_gases:
        logging.info(f"--- Starting processing for gas: {gas} ---")

        gas_specific_urls = []
        for iso, gas_data in country_urls.items():
            if gas in gas_data:
                gas_specific_urls.append({"iso": iso, "url": gas_data[gas]})

        gas_dataframes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {
                executor.submit(download_and_process_zip, item['url'], item['iso'], gas): item
                for item in gas_specific_urls
            }
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result_df = future.result()
                    if result_df is not None and not result_df.empty:
                        gas_dataframes.append(result_df)
                    else:
                        failed_downloads.append(f"{item['iso']} ({gas})")
                except Exception as e:
                    logging.error(f"Unhandled error for {item['iso']} ({gas}): {e}")
                    failed_downloads.append(f"{item['iso']} ({gas}) - Error: {e}")

        if not gas_dataframes:
            logging.info(f"No data was downloaded for {gas}. The output file will not be created.")
            continue

        output_filename = os.path.join(output_dir, f"all_countries_{gas}.csv")
        logging.info(f"\n  -> All downloads for {gas} complete. Concatenating...")
        
        try:
            final_df = pd.concat(gas_dataframes, ignore_index=True)

            # Format emissions_quantity to avoid scientific notation
            if 'emissions_quantity' in final_df.columns:
                logging.info(f"  -> Formatting 'emissions_quantity' column...")
                final_df['emissions_quantity'] = final_df['emissions_quantity'].apply(
                    lambda x: format(x, '.16f').rstrip('0').rstrip('.') if pd.notna(x) else x
                )

            logging.info(f"  -> Saving combined data to {output_filename}...")
            final_df.to_csv(output_filename, index=False)
            logging.info(f"  -> Successfully created {output_filename} with {len(final_df)} rows.\n")
        except Exception as e:
            logging.error(f"  -> An error occurred during the final processing for {gas}: {e}\n")

    logging.info("--- All processing complete. ---")
    if failed_downloads:
        logging.warning(f"The following {len(failed_downloads)} downloads failed:")
        for failure in sorted(failed_downloads):
            logging.warning(f"  - {failure}")
    else:
        logging.info("All downloads succeeded!")


if __name__ == '__main__':
    download_and_segregate_by_gas()
