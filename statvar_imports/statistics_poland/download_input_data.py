from datetime import datetime
import io
import logging
import os
import sys
import time

from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- CONFIGURATION ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Outputs to source_files to match manifest.json
OUTPUT_DIR = os.path.join(BASE_PATH, "source_files")

GCS_TEMPLATE_PATH = (
    "gs://datcom-prod-imports/statvar_imports/statistics_poland/"
    "poland_data_sample/StatisticsPoland_input.csv")

API_BASE_URL = "https://bdl.stat.gov.pl/api/v1"
SUBJECT_ID = "P3447"
VAR_BATCH_SIZE = 50
DEFAULT_BDL_SECRET_RESOURCE = ("projects/datcom-import-automation-prod/secrets/"
                               "statistics-poland-bdl-api-key/versions/latest")

SEX_STEMS = {'total': [], 'males': ['męż'], 'females': ['kob']}
LOC_STEMS = {
    'total': [],
    'in urban areas': ['miast'],
    'in rural areas': ['wsi', 'wieś']
}

# AGE STEMS
AGE_STEMS = {
    '0-2': '0-2',
    '3-6': '3-6',
    '7-12': '7-12',
    '13-15': '13-15',
    '16-19': '16-19',
    '20-24': '20-24',
    '25-34': '25-34',
    '35-44': '35-44',
    '45-54': '45-54',
    '55-64': '55-64',
    '65 and more': '65'
}


def _fetch_secret_api_key(secret_resource=None):
    """Reads optional BDL API key from GCP Secret Manager without logging it.

    SECURITY: Never pass BDL_API_KEY via ExecutorConfig.user_script_env, because
    import-automation/executor/main.py logs Import config in cleartext.
    """
    resource = (secret_resource if secret_resource is not None else
                os.environ.get("BDL_API_SECRET_RESOURCE",
                               DEFAULT_BDL_SECRET_RESOURCE)).strip()
    if not resource:
        return ""
    try:
        from google.cloud import secretmanager  # pylint: disable=import-outside-toplevel
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": resource})
        return response.payload.data.decode("utf-8").strip()
    except Exception:
        return ""


def get_request_headers(api_key=None, use_secret_manager=True):
    """Builds outbound HTTP headers at call time, stripping whitespace."""
    raw_key = os.environ.get("BDL_API_KEY") if api_key is None else api_key
    cleaned_key = str(raw_key).strip() if raw_key is not None else ""
    if not cleaned_key and api_key is None and use_secret_manager:
        cleaned_key = str(_fetch_secret_api_key() or "").strip()
    if cleaned_key:
        return {'X-ClientId': cleaned_key}
    return {}


def load_template_from_gcs(gcs_path):
    """Loads the template CSV directly from GCS with local fallback."""
    try:
        logging.info(f"Reading template from {gcs_path}...")
        storage_client = storage.Client()
        path_parts = gcs_path.replace("gs://", "").split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1]

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_text()

        return pd.read_csv(io.StringIO(content),
                           header=[0, 1, 2, 3],
                           index_col=[0, 1])
    except Exception as e:
        logging.warning(
            f"Failed to load template from GCS ({e}); checking local fallback..."
        )
        local_path = os.path.join(BASE_PATH, "test",
                                  "StatisticsPoland_input.csv")
        if os.path.exists(local_path):
            logging.info(
                f"Loading template from local fallback {local_path}...")
            return pd.read_csv(local_path,
                               header=[0, 1, 2, 3],
                               index_col=[0, 1])
        logging.error(f"No local fallback available at {local_path}.")
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
    retry_strategy = Retry(total=retries,
                           connect=retries,
                           read=retries,
                           status=retries,
                           backoff_factor=backoff_factor,
                           status_forcelist=[429, 500, 502, 503, 504],
                           allowed_methods=["GET"],
                           respect_retry_after_header=True,
                           raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def make_request(session, url, headers=None, params=None, timeout=60):
    """Makes an HTTP GET request using configured retry strategy and outbound logging."""
    try:
        sanitized_headers = dict(headers) if headers else {}
        if 'X-ClientId' in sanitized_headers:
            sanitized_headers['X-ClientId'] = '***REDACTED***'
        logging.info(
            f"HTTP GET {url} params={params} headers={sanitized_headers}")
        return session.get(url, headers=headers, params=params, timeout=timeout)
    except Exception as e:
        logging.error(f"HTTP GET failed for {url}: {e}")
        return None


def fetch_variables(session, headers=None):
    """Fetches all variables for Subject P3447 with retries."""
    logging.info(f"Downloading variable list for Subject {SUBJECT_ID}...")
    req_headers = get_request_headers() if headers is None else headers
    v_map = {}
    page = 0

    while True:
        url = (
            f"{API_BASE_URL}/variables?subject-id={SUBJECT_ID}&page-size=100&lang=pl&page={page}"
        )
        resp = make_request(session, url, headers=req_headers, timeout=60)
        if resp is None or resp.status_code != 200:
            status = resp.status_code if resp is not None else "None"
            error_msg = f"Metadata page {page} failed with status {status}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        data = resp.json()
        results = data.get('results', [])
        if not results:
            break

        for item in results:
            full_name_parts = [
                str(v) for k, v in item.items() if k.startswith('n') and v
            ]
            full_name = " ".join(full_name_parts).lower()
            v_map[str(item['id'])] = full_name

        if len(results) < 100:
            break
        page += 1

    logging.info(f"Indexed {len(v_map)} variables.")
    return v_map


def fetch_units(session, headers=None):
    """Fetches country (level=0) and voivodeship (level=2) units from BDL API."""
    logging.info("Downloading level 0 and level 2 territorial units...")
    req_headers = get_request_headers() if headers is None else headers
    units = []
    page = 0

    while True:
        url = f"{API_BASE_URL}/units"
        params = [('level', '0'), ('level', '2'), ('page-size', '100'),
                  ('format', 'json'), ('page', str(page))]
        resp = make_request(session,
                            url,
                            headers=req_headers,
                            params=params,
                            timeout=60)
        if resp is None or resp.status_code != 200:
            status = resp.status_code if resp is not None else "None"
            error_msg = f"Units page {page} failed with status {status}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        results = resp.json().get('results', [])
        if not results:
            break

        for item in results:
            name_key = next((k for k in ['name', 'n', 'unitName'] if k in item),
                            None)
            if not name_key or 'id' not in item:
                error_msg = f"Malformed unit entry on page {page}: {item}"
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            units.append((str(item['id']), str(item[name_key])))

        if len(results) < 100:
            break
        page += 1

    logging.info(f"Indexed {len(units)} territorial units.")
    return units


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

    headers = get_request_headers()
    session = get_http_session()
    region_map = get_template_map(template_df)
    v_metadata = fetch_variables(session, headers=headers)
    if not v_metadata:
        raise ValueError("Variable metadata failed to download.")

    unique_cols = template_df.columns.droplevel('Year').unique()
    current_year = datetime.now().year

    var_id_to_slice = {}
    ordered_var_ids = []
    for age, sex, loc in unique_cols:
        if pd.isna(age) or str(age).strip() == '' or str(
                age).lower() == 'total':
            continue

        target_age = AGE_STEMS.get(age, age)
        sex_stems = SEX_STEMS.get(sex, [])
        loc_stems = LOC_STEMS.get(loc, [])

        var_id = None
        for vid, vname in v_metadata.items():
            name_no_space = vname.replace(" ", "")
            target_age_no_space = target_age.replace(" ", "")
            if target_age_no_space not in name_no_space:
                continue

            if sex_stems:
                if not any(s in vname for s in sex_stems):
                    continue
            else:
                if 'męż' in vname or 'kob' in vname:
                    continue

            if loc_stems:
                if not any(s in vname for s in loc_stems):
                    continue
            else:
                if 'miast' in vname or 'wsi' in vname or 'wieś' in vname:
                    continue

            var_id = vid
            break

        if not var_id:
            error_msg = (f"Failed to match variable for slice: age='{age}', "
                         f"sex='{sex}', loc='{loc}'")
            logging.error(error_msg)
            raise RuntimeError(error_msg)

        logging.info(f"MATCH: {age}|{sex}|{loc} -> ID {var_id}")
        var_id_to_slice[str(var_id)] = (age, sex, loc)
        ordered_var_ids.append(str(var_id))

    units = fetch_units(session, headers=headers)
    if not units:
        raise ValueError("Territorial units failed to download.")

    mapped_units = []
    for unit_id, raw_name in units:
        api_name = raw_name.upper().strip()
        if api_name == "POLSKA":
            api_name = "POLAND"

        matched_code = region_map.get(api_name)
        matched_name = api_name
        if not matched_code:
            for t_name, t_code in region_map.items():
                if t_name in api_name:
                    matched_code = t_code
                    matched_name = t_name
                    break

        if matched_code is not None:
            mapped_units.append((unit_id, str(matched_code), matched_name))
        else:
            logging.warning(
                f"Region '{api_name}' from API could not be mapped to any "
                f"template code; skipping.")

    var_batches = [
        ordered_var_ids[i:i + VAR_BATCH_SIZE]
        for i in range(0, len(ordered_var_ids), VAR_BATCH_SIZE)
    ]
    year_params = [('year', str(y)) for y in range(2003, current_year + 2)]

    # Querying by-unit in batches of 50 variables takes ~34 data requests total
    # (17 units x 2 batches), well within BDL's 100 req / 15m anonymous quota.
    master_data = []
    for unit_id, matched_code, matched_name in mapped_units:
        api_url = f"{API_BASE_URL}/data/by-unit/{unit_id}"
        for batch in var_batches:
            params = ([('page-size', '100'), ('format', 'json')] +
                      [('var-id', vid) for vid in batch] + year_params)
            resp = make_request(session,
                                api_url,
                                headers=headers,
                                params=params,
                                timeout=60)
            if resp is None or resp.status_code != 200:
                status = resp.status_code if resp is not None else "None"
                error_msg = (
                    f"Download failed with status {status} for unit {unit_id}")
                logging.error(error_msg)
                raise RuntimeError(error_msg)

            results = resp.json().get('results', [])
            for item in results:
                vid = str(item.get('id', ''))
                slice_info = var_id_to_slice.get(vid)
                if not slice_info:
                    continue
                age, sex, loc = slice_info
                for val in item.get('values', []):
                    master_data.append({
                        'Code': matched_code,
                        'Name': matched_name,
                        'Year': str(val['year']),
                        'Value': val['val'],
                        'Age': age,
                        'Sex': sex,
                        'Location': loc
                    })
            time.sleep(0.1)

    if not master_data:
        raise ValueError("No data collected during the download loop.")

    full_df = pd.DataFrame(master_data)

    for year in sorted(full_df['Year'].unique()):
        year_df = full_df[full_df['Year'] == year]

        pivot_df = year_df.pivot_table(
            index=['Code', 'Name'],
            columns=['Age', 'Sex', 'Location', 'Year'],
            values='Value')

        # Replaced axis=1 grouping which crashes in modern Pandas environments.
        # Transposing before and after groupby achieves the exact same result safely.
        totals = pivot_df.T.groupby(level=['Sex', 'Location', 'Year']).sum().T

        new_columns = pd.MultiIndex.from_tuples(
            [('total', s, loc, y) for s, loc, y in totals.columns],
            names=['Age', 'Sex', 'Location', 'Year'])
        totals.columns = new_columns

        combined_df = pd.concat([pivot_df, totals], axis=1)

        target_columns = []
        for col in template_df.columns:
            t_age, t_sex, t_loc, _ = col
            lookup_age = 'total' if pd.isna(t_age) or str(
                t_age).strip() == '' else t_age
            target_columns.append((lookup_age, t_sex, t_loc, str(year)))

        final_df = combined_df.reindex(template_df.index)

        final_headers = []
        for col in template_df.columns:
            t_age, t_sex, t_loc, _ = col
            final_headers.append((t_age, t_sex, t_loc, str(year)))

        final_df = final_df.reindex(columns=pd.MultiIndex.from_tuples(
            target_columns, names=['Age', 'Sex', 'Location', 'Year']))
        final_df.columns = pd.MultiIndex.from_tuples(
            final_headers, names=['Age', 'Sex', 'Location', 'Year'])

        out_path = os.path.join(OUTPUT_DIR,
                                f"StatisticsPoland_input_{year}.csv")
        temp_out_path = f"{out_path}.tmp"
        final_df.to_csv(temp_out_path)
        os.replace(temp_out_path, out_path)
        logging.info(f"Generated: {out_path}")


def main(argv=None):
    try:
        download_and_process()
    except Exception as e:
        # Pushes the exact stack trace directly into Cloud Logging.
        logging.critical(f"FATAL SCRIPT ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
