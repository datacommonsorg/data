import requests
import zipfile
import pandas as pd
import io
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_retry_session(retries=3, backoff_factor=1):
    """Creates a requests.Session with connection pooling and retry backoff."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def download_and_process_zip(url, country_iso, gas, session=None):
    """
    Downloads a single zip file and processes it in memory, returning a DataFrame.
    """
    try:
        logging.info(f"  Downloading: {country_iso} for {gas}...")
        client = session if session is not None else requests
        response = client.get(url, timeout=60)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            csv_files_info = [
                f for f in zip_ref.infolist()
                if ("country" in f.filename.lower() and f.filename.endswith('.csv') and
                    not f.is_dir())
            ]

            df_list = []
            for file_info in csv_files_info:
                with zip_ref.open(file_info.filename) as file_in_zip:
                    df = pd.read_csv(file_in_zip)
                    df_list.append(df)
            
            if df_list:
                return pd.concat(df_list, ignore_index=True)
            else:
                logging.warning(
                    f"    -> No relevant CSV files found in zip for {country_iso} ({gas})"
                )
                return None
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logging.warning(f"    -> Not found (404) for {country_iso} ({gas}) at {url}")
            return None
        status_code = (
            e.response.status_code if getattr(e, 'response', None) is not None else "N/A"
        )
        logging.error(
            f"    -> HTTP Error for {country_iso} ({gas}) at {url} (Status: {status_code}): {e}"
        )
        raise
    except requests.exceptions.RequestException as e:
        status_code = (
            e.response.status_code if getattr(e, 'response', None) is not None else "N/A"
        )
        logging.error(
            f"    -> Request failed for {country_iso} ({gas}) at {url} (Status: {status_code}): {e}"
        )
        raise
    except zipfile.BadZipFile as e:
        logging.error(f"    -> Bad zip file for {country_iso} ({gas}) at {url}: {e}")
        raise
    except Exception as e:
        logging.error(f"    -> Unexpected error for {country_iso} ({gas}) at {url}: {e}")
        raise

def download_and_segregate_by_gas():
    """
    Generates a fresh list of country download URLs and then downloads all
    data, saving a separate concatenated CSV for each gas.
    """
    failed_downloads = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    session = get_retry_session()
    
    logging.info("--- Step 1: Generating Country List ---")
    api_country_codes = set()
    countries_url = "https://api.climatetrace.org/v7/admins?level=0"
    logging.info(f"Fetching country list from API: {countries_url}")
    try:
        response = session.get(countries_url, timeout=60)
        response.raise_for_status()
        countries = response.json()
        api_country_codes = {country['id'] for country in countries}
        logging.info(
            f"Successfully fetched {len(api_country_codes)} countries from API ({countries_url}). "
            f"Status: {response.status_code}."
        )
    except requests.exceptions.RequestException as e:
        status_code = (
            e.response.status_code if getattr(e, 'response', None) is not None else "N/A"
        )
        response_text = (
            e.response.text if getattr(e, 'response', None) is not None else "No response body"
        )
        logging.error(
            f"Error: Could not fetch country list from API ({countries_url}). "
            f"Status: {status_code}, Response: {response_text}, Error: {e}"
        )
        # Not raising here, we might still have check_country.csv

    local_country_codes = set()
    try:
        with open(os.path.join(script_dir, 'check_country.csv'), 'r') as f:
            local_country_codes = {line.strip() for line in f if line.strip()}
        logging.info(f"Read {len(local_country_codes)} countries from 'check_country.csv'.")
    except FileNotFoundError:
        logging.warning("Warning: 'check_country.csv' not found. Will only use countries from API.")

    combined_codes = sorted(list(api_country_codes.union(local_country_codes)))
    if not combined_codes:
        logging.error("No countries to process. Exiting.")
        raise RuntimeError("No country codes found from API or check_country.csv.")

    logging.info(f"Total unique countries to process: {len(combined_codes)}")

    gases = ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]
    base_url = "https://downloads.climatetrace.org/latest/country_packages"

    logging.info("--- Step 2: Downloading and Processing Data ---")
    
    output_dir = os.path.join(script_dir, "input_files")
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Found data for the following gas types: {', '.join(gases)}\n")

    for gas in gases:
        logging.info(f"--- Starting processing for gas: {gas} ---")

        gas_dataframes = []
        critical_errors = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_iso = {
                executor.submit(
                    download_and_process_zip,
                    f"{base_url}/{gas}/{iso}.zip",
                    iso,
                    gas,
                    session
                ): iso
                for iso in combined_codes
            }
            for future in as_completed(future_to_iso):
                iso = future_to_iso[future]
                try:
                    result_df = future.result()
                    if result_df is not None and not result_df.empty:
                        gas_dataframes.append(result_df)
                    else:
                        failed_downloads.append(f"{iso} ({gas})")
                except Exception as e:
                    logging.error(f"Critical error for {iso} ({gas}): {e}")
                    critical_errors.append(f"{iso} ({gas}) - Error: {e}")

        if critical_errors:
            raise RuntimeError(
                f"Critical download failures for {gas}:\n" + "\n".join(critical_errors)
            )

        if not gas_dataframes:
            logging.info(f"No data was downloaded for {gas}. The output file will not be created.")
            continue

        output_filename = os.path.join(output_dir, f"all_countries_{gas}.csv")
        temp_filename = f"{output_filename}.tmp"
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
            final_df.to_csv(temp_filename, index=False)
            os.replace(temp_filename, output_filename)
            logging.info(
                f"  -> Successfully created {output_filename} with {len(final_df)} rows.\n"
            )
        except Exception as e:
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except OSError:
                    pass
            logging.error(f"  -> An error occurred during the final processing for {gas}: {e}\n")
            raise

    session.close()
    logging.info("--- All processing complete. ---")
    if failed_downloads:
        logging.warning(
            f"The following {len(failed_downloads)} downloads were not found (404) "
            "or contained no relevant CSV files:"
        )
        for failure in sorted(failed_downloads):
            logging.warning(f"  - {failure}")
    else:
        logging.info("All downloads succeeded!")


if __name__ == '__main__':
    download_and_segregate_by_gas()
