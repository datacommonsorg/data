from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import io
import os
import zipfile

from absl import logging
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_retry_session(retries=3, backoff_factor=1):
    """Creates a requests.Session with connection pooling and retry backoff."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry,
                          pool_connections=10,
                          pool_maxsize=10)
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
                if ("country" in f.filename.lower() and
                    f.filename.endswith('.csv') and not f.is_dir())
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
            logging.warning(
                f"    -> Not found (404) for {country_iso} ({gas}) at {url}")
            return None
        status_code = (e.response.status_code
                       if getattr(e, 'response', None) is not None else "N/A")
        logging.error(
            f"    -> HTTP Error for {country_iso} ({gas}) at {url} (Status: {status_code}): {e}"
        )
        raise
    except requests.exceptions.RequestException as e:
        status_code = (e.response.status_code
                       if getattr(e, 'response', None) is not None else "N/A")
        logging.error(
            f"    -> Request failed for {country_iso} ({gas}) at {url} (Status: {status_code}): {e}"
        )
        raise
    except zipfile.BadZipFile as e:
        logging.error(
            f"    -> Bad zip file for {country_iso} ({gas}) at {url}: {e}")
        raise
    except Exception as e:
        logging.error(
            f"    -> Unexpected error for {country_iso} ({gas}) at {url}: {e}")
        raise


def _format_emission(x):
    """Formats numeric emission values without scientific notation or precision artifacts."""
    try:
        if pd.notna(x) and str(x).strip():
            f = float(x)
            if np.isnan(f) or np.isinf(f):
                return ''
            return '0' if f == 0.0 else np.format_float_positional(f, trim='-')
        return ''
    except (ValueError, TypeError):
        logging.warning(f"Dropping non-numeric emission value: {x!r}")
        return ''


# Legacy per-gas subsectors that combine multiple v7 subsectors.
LEGACY_SUBSECTOR_ROLLUPS = {
    "shipping": [
        "domestic-shipping",
        "international-shipping",
        "non-broadcasting-vessels",
    ],
    "wastewater-treatment-and-discharge": [
        "domestic-wastewater-treatment-and-discharge",
        "industrial-wastewater-treatment-and-discharge",
    ],
}

# Legacy OldAPI categories that combine multiple v7 subsectors.
LEGACY_COMPOSITE_GROUPS = {
    "sector_maritime": [
        "domestic-shipping",
        "international-shipping",
        "non-broadcasting-vessels",
    ],
    "subsector_shipping": [
        "domestic-shipping",
        "international-shipping",
        "non-broadcasting-vessels",
    ],
    "subsector_aviation": ["domestic-aviation", "international-aviation"],
    "subsector_wastewater-treatment-and-discharge": [
        "domestic-wastewater-treatment-and-discharge",
        "industrial-wastewater-treatment-and-discharge",
    ],
    "subsector_residential-commercial-onsite-heating": [
        "residential-onsite-fuel-usage",
        "non-residential-onsite-fuel-usage",
    ],
    "subsector_manure-management": [
        "manure-left-on-pasture-cattle",
        "manure-management-cattle-operation",
        "manure-management-other",
    ],
    "subsector_managed-soils": [
        "crop-residues",
        "manure-applied-to-soils",
        "other-agricultural-soil-emissions",
        "synthetic-fertilizer-application",
    ],
    "subsector_enteric-fermentation": [
        "enteric-fermentation-cattle-operation",
        "enteric-fermentation-cattle-pasture",
        "enteric-fermentation-other",
    ],
}

# Keys mapped in climate_pvmap_greenhousegas.csv.
GREENHOUSEGAS_PVMAP_KEYS = frozenset({
    "co2e_100yr",
    "sector_agriculture",
    "sector_buildings",
    "sector_mineral-extraction",
    "sector_forestry-and-land-use",
    "sector_manufacturing",
    "sector_maritime",
    "sector_fossil-fuel-operations",
    "sector_power",
    "sector_transportation",
    "sector_waste",
    "subsector_wastewater-treatment-and-discharge",
    "subsector_solid-waste-disposal",
    "subsector_incineration-and-open-burning-of-waste",
    "subsector_biological-treatment-of-solid-waste-and-biogenic",
    "subsector_copper-mining",
    "subsector_sand-quarrying",
    "subsector_rock-quarrying",
    "subsector_iron-mining",
    "subsector_coal-mining",
    "subsector_aluminum",
    "subsector_fluorinated-gases",
    "subsector_cement",
    "subsector_food-beverage-tobacco",
    "subsector_glass",
    "subsector_iron-and-steel",
    "subsector_pulp-and-paper",
    "subsector_petrochemical-steam-cracking",
    "subsector_lime",
    "subsector_other-manufacturing",
    "subsector_shrubgrass-fires",
    "subsector_forest-land-fires",
    "subsector_forest-land-clearing",
    "subsector_residential-commercial-onsite-heating",
    "subsector_rice-cultivation",
    "subsector_manure-management",
    "subsector_managed-soils",
    "subsector_enteric-fermentation",
    "subsector_cropland-fires",
    "subsector_other-solid-fuels",
    "subsector_oil-and-gas-refining",
    "subsector_oil-and-gas-production",
    "subsector_road-transportation",
    "subsector_railways",
    "subsector_aviation",
    "subsector_other-transport",
    "subsector_electricity-generation",
    "subsector_other-energy-use",
    "subsector_shipping",
    "subsector_bauxite-mining",
})


def append_legacy_subsector_rollups(df):
    """Appends composite rows for legacy subsectors (shipping, wastewater-treatment-and-discharge)."""
    required_cols = {
        'iso3_country', 'subsector', 'start_time', 'gas', 'emissions_quantity'
    }
    if not required_cols.issubset(df.columns):
        return df

    base_df = df[~df['subsector'].isin(LEGACY_SUBSECTOR_ROLLUPS)].copy()
    base_df['_val'] = pd.to_numeric(base_df['emissions_quantity'],
                                    errors='coerce')
    valid_df = base_df.dropna(subset=['iso3_country', 'start_time', '_val'])

    extra_cols = [
        c for c in df.columns if c not in {
            'iso3_country', 'sector', 'subsector', 'start_time', 'gas',
            'emissions_quantity'
        }
    ]
    rollup_frames = []
    for legacy_sub, sub_list in LEGACY_SUBSECTOR_ROLLUPS.items():
        comp_df = valid_df[valid_df['subsector'].isin(sub_list)]
        if comp_df.empty:
            continue
        agg_spec = {'_val': 'sum'}
        for col in extra_cols:
            agg_spec[col] = 'first'
        grp = comp_df.groupby(['iso3_country', 'start_time', 'gas'],
                              as_index=False).agg(agg_spec)
        grp['sector'] = ''
        grp['subsector'] = legacy_sub
        grp['emissions_quantity'] = grp['_val'].apply(_format_emission)
        grp = grp.drop(columns=['_val'])
        for col in df.columns:
            if col not in grp.columns:
                grp[col] = ''
        rollup_frames.append(grp[list(df.columns)])

    if not rollup_frames:
        return base_df.drop(columns=['_val'])
    return pd.concat([base_df.drop(columns=['_val'])] + rollup_frames,
                     ignore_index=True)


def generate_greenhousegas_input(co2e_100yr_df, output_dir):
    """Generates pre-aggregated greenhousegas_co2e_100yr.csv for GreenhouseGas StatVars."""
    required_cols = {
        'iso3_country', 'sector', 'subsector', 'start_time',
        'emissions_quantity'
    }
    if not required_cols.issubset(co2e_100yr_df.columns):
        logging.warning(
            "Skipping greenhousegas_co2e_100yr.csv generation; missing required columns."
        )
        return

    df = co2e_100yr_df[~co2e_100yr_df['subsector'].isin(
        LEGACY_SUBSECTOR_ROLLUPS)][list(required_cols)].copy()
    df['val'] = pd.to_numeric(df['emissions_quantity'], errors='coerce')
    df = df.dropna(subset=['iso3_country', 'start_time', 'val'])

    # 1. Country total, 2. Sector totals, 3. Subsector totals
    total_grp = df.groupby(['iso3_country', 'start_time'],
                           as_index=False)['val'].sum()
    total_grp['gas'] = 'co2e_100yr'

    sec_grp = df.groupby(['iso3_country', 'start_time', 'sector'],
                         as_index=False)['val'].sum()
    sec_grp['gas'] = 'sector_' + sec_grp['sector'].astype(str)
    sec_grp = sec_grp[sec_grp['gas'].isin(GREENHOUSEGAS_PVMAP_KEYS)]

    sub_grp = df.groupby(['iso3_country', 'start_time', 'subsector'],
                         as_index=False)['val'].sum()
    sub_grp['gas'] = 'subsector_' + sub_grp['subsector'].astype(str)
    sub_grp = sub_grp[sub_grp['gas'].isin(GREENHOUSEGAS_PVMAP_KEYS)]

    records = [
        total_grp[['iso3_country', 'start_time', 'gas', 'val']],
        sec_grp[['iso3_country', 'start_time', 'gas', 'val']],
        sub_grp[['iso3_country', 'start_time', 'gas', 'val']],
    ]

    # 4. Multi-subsector legacy rollups
    for gas_key, sub_list in LEGACY_COMPOSITE_GROUPS.items():
        comp_df = df[df['subsector'].isin(sub_list)]
        if not comp_df.empty:
            comp_grp = comp_df.groupby(['iso3_country', 'start_time'],
                                       as_index=False)['val'].sum()
            comp_grp['gas'] = gas_key
            records.append(
                comp_grp[['iso3_country', 'start_time', 'gas', 'val']])

    out_df = pd.concat(records, ignore_index=True)
    out_df['sector'] = ''
    out_df['subsector'] = ''
    out_df['end_time'] = ''
    out_df['emissions_quantity'] = out_df['val'].apply(_format_emission)
    out_df = out_df[[
        'iso3_country', 'sector', 'subsector', 'start_time', 'end_time', 'gas',
        'emissions_quantity'
    ]]

    ghg_output_filename = os.path.join(output_dir,
                                       "greenhousegas_co2e_100yr.csv")
    ghg_temp_filename = f"{ghg_output_filename}.tmp"
    try:
        out_df.to_csv(ghg_temp_filename, index=False)
        os.replace(ghg_temp_filename, ghg_output_filename)
        logging.info(
            f"  -> Successfully created {ghg_output_filename} with {len(out_df)} rows.\n"
        )
    except Exception:
        if os.path.exists(ghg_temp_filename):
            try:
                os.remove(ghg_temp_filename)
            except OSError:
                pass
        raise


def download_and_segregate_by_gas():
    """
    Generates a fresh list of country download URLs and then downloads all
    data, saving a separate concatenated CSV for each gas.
    """
    failed_downloads = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with get_retry_session() as session:
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
                f"Status: {response.status_code}.")
        except requests.exceptions.RequestException as e:
            status_code = (e.response.status_code if getattr(
                e, 'response', None) is not None else "N/A")
            response_text = (e.response.text if getattr(e, 'response', None)
                             is not None else "No response body")
            logging.error(
                f"Error: Could not fetch country list from API ({countries_url}). "
                f"Status: {status_code}, Response: {response_text}, Error: {e}")
            raise

        local_country_codes = set()
        try:
            with open(os.path.join(script_dir, 'check_country.csv'), 'r') as f:
                local_country_codes = {
                    line.strip() for line in f if line.strip()
                }
            logging.info(
                f"Read {len(local_country_codes)} countries from 'check_country.csv'."
            )
        except FileNotFoundError:
            logging.warning(
                "Warning: 'check_country.csv' not found. Will only use countries from API."
            )

        combined_codes = sorted(
            list(api_country_codes.union(local_country_codes)))
        if not combined_codes:
            logging.error("No countries to process. Exiting.")
            raise RuntimeError(
                "No country codes found from API or check_country.csv.")

        logging.info(
            f"Total unique countries to process: {len(combined_codes)}")

        gases = ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]
        base_url = "https://downloads.climatetrace.org/latest/country_packages"

        logging.info("--- Step 2: Downloading and Processing Data ---")

        output_dir = os.path.join(script_dir, "input_files")
        os.makedirs(output_dir, exist_ok=True)

        logging.info(
            f"Found data for the following gas types: {', '.join(gases)}\n")

        for gas in gases:
            logging.info(f"--- Starting processing for gas: {gas} ---")

            gas_dataframes = []
            critical_errors = []
            skipped_count = 0
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_iso = {
                    executor.submit(
                        download_and_process_zip,
                        f"{base_url}/{gas}/{iso}.zip",
                        iso,
                        gas,
                        session,
                    ):
                        iso for iso in combined_codes
                }
                for future in as_completed(future_to_iso):
                    iso = future_to_iso[future]
                    try:
                        result_df = future.result()
                        if result_df is not None and not result_df.empty:
                            gas_dataframes.append(result_df)
                        else:
                            skipped_count += 1
                            failed_downloads.append(f"{iso} ({gas})")
                    except Exception as e:
                        logging.error(f"Critical error for {iso} ({gas}): {e}")
                        critical_errors.append(f"{iso} ({gas}) - Error: {e}")

            logging.info(
                f"Download summary for {gas}: {len(gas_dataframes)} succeeded, "
                f"{skipped_count} skipped (404/empty), {len(critical_errors)} failed."
            )

            if critical_errors:
                raise RuntimeError(f"Critical download failures for {gas}:\n" +
                                   "\n".join(critical_errors))

            if not gas_dataframes:
                logging.error(
                    f"No data was downloaded for {gas}. The output file will not be created."
                )
                raise RuntimeError(f"No data was downloaded for gas: {gas}")

            output_filename = os.path.join(output_dir,
                                           f"all_countries_{gas}.csv")
            temp_filename = f"{output_filename}.tmp"
            logging.info(
                f"\n  -> All downloads for {gas} complete. Concatenating...")

            try:
                final_df = pd.concat(gas_dataframes, ignore_index=True)

                # Format emissions_quantity to avoid scientific notation
                if 'emissions_quantity' in final_df.columns:
                    logging.info(
                        "  -> Formatting 'emissions_quantity' column...")
                    final_df['emissions_quantity'] = final_df[
                        'emissions_quantity'].apply(_format_emission)

                final_df = append_legacy_subsector_rollups(final_df)

                logging.info(
                    f"  -> Saving combined data to {output_filename}...")
                final_df.to_csv(temp_filename, index=False)
                os.replace(temp_filename, output_filename)
                logging.info(
                    f"  -> Successfully created {output_filename} with {len(final_df)} rows.\n"
                )
                if gas == "co2e_100yr":
                    generate_greenhousegas_input(final_df, output_dir)
            except Exception as e:
                if os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except OSError:
                        pass
                logging.error(
                    f"  -> An error occurred during the final processing for {gas}: {e}\n"
                )
                raise

    logging.info("--- All processing complete. ---")
    if failed_downloads:
        logging.warning(
            f"The following {len(failed_downloads)} downloads were not found (404) "
            "or contained no relevant CSV files:")
        for failure in sorted(failed_downloads):
            logging.warning(f"  - {failure}")
    else:
        logging.info("All downloads succeeded!")


if __name__ == '__main__':
    download_and_segregate_by_gas()
