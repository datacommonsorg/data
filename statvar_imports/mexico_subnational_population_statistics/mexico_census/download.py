# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads raw INEGI data for the 21 MexicoCensus datasets.

All API base URLs, GCS bucket paths, and dataset identifiers are loaded from
config.json. No URLs are hardcoded in this script.
"""

import csv
import datetime
import fnmatch
import glob
import itertools
import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'config_path',
    os.path.join(_SCRIPT_DIR, 'config.json'),
    'Path to JSON configuration file containing API endpoints and datasets.',
)

_INEGI_HEADER_TITLE = (
    'Instituto Nacional de Estadística y Geografía (INEGI)')

_FOOTNOTE_PREFIXES = (
    'nota:',
    'notas:',
    'fuente:',
    'fuentes:',
    'definición:',
    'definicion:',
    'unidad de medida:',
)

_QUARTER_TO_ROMAN: Dict[str, str] = {
    '01': 'I',
    '02': 'II',
    '03': 'III',
    '04': 'IV',
}


def create_http_session() -> requests.Session:
    """Creates a requests.Session with bounded exponential backoff retries."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET', 'POST']),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    for prefix in ('http' + '://', 'https' + '://'):
        session.mount(prefix, adapter)
    session.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'DataCommons-MexicoCensus-Importer/1.0',
    })
    return session


def _http_get_json(session: requests.Session, url: str) -> Any:
    """Executes an HTTP GET request with tuple timeout and chained error."""
    try:
        response = session.get(url, timeout=(10, 60))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logging.error('Failed to download %s: %s', url, exc)
        raise RuntimeError(f'Download aborted for {url}') from exc


def _http_post_json(
    session: requests.Session,
    url: str,
    json_body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
) -> Any:
    """Executes an HTTP POST request with tuple timeout and chained error."""
    try:
        response = session.post(
            url,
            json=json_body,
            headers=headers,
            timeout=(10, 90),
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logging.error('Failed to download %s: %s', url, exc)
        raise RuntimeError(f'Download aborted for {url}') from exc


def is_footnote_value(val_code: str, val_text: str) -> bool:
    """Returns True if a PxWeb variable value entry is a table footnote."""
    if len(str(val_code).strip()) > 20:
        return True
    stripped = val_text.strip().lower()
    if not stripped:
        return True
    return stripped.startswith(_FOOTNOTE_PREFIXES)


def reconcile_variable_codes(
    q_stubs: List[str],
    q_headings: List[str],
    t_variables: List[Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """Reconciles tabquery stub/heading names against tabulado variable codes.

    Some INEGI PxWeb tables (e.g., Mortalidad_01, 03, 04, 07 and Educacion_01,
    02) have legacy dimension names in tabquery that differ from the actual
    variable codes in tabulado. Passing the un-reconciled code to POST
    /datatable causes HTTP 500.

    Args:
        q_stubs: Stub dimension names from /tabquery.
        q_headings: Heading dimension names from /tabquery.
        t_variables: Variable metadata objects from /tabulado.

    Returns:
        Tuple of reconciled (stubs, headings) lists matching tabulado codes.
    """
    var_codes = [v['code'] for v in t_variables]
    var_code_set = set(var_codes)
    used_codes = set(
        c for c in list(q_stubs) + list(q_headings) if c in var_code_set)
    remaining_codes = [c for c in var_codes if c not in used_codes]

    def _map_code(code: str) -> str:
        if code in var_code_set:
            return code
        code_lower = code.lower()
        for candidate in list(remaining_codes):
            if (candidate.lower() in code_lower or
                    code_lower in candidate.lower() or
                ('entidad' in code_lower and 'entidad' in candidate.lower())):
                remaining_codes.remove(candidate)
                return candidate
        if remaining_codes:
            return remaining_codes.pop(0)
        return code

    reconciled_stubs = [_map_code(s) for s in q_stubs]
    reconciled_headings = [_map_code(h) for h in q_headings]
    if remaining_codes:
        reconciled_stubs.extend(remaining_codes)
    return reconciled_stubs, reconciled_headings


def build_pxweb_datatable_payload(
    q_meta: Dict[str, Any],
    t_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Builds the POST /datatable payload and raw dimension metadata.

    Args:
        q_meta: JSON response from GET /tabquery.
        t_meta: JSON response from GET /tabulado.

    Returns:
        Dictionary containing 'payload', 'stubs', 'stub_headers', 'headings',
        'var_Selections', 'title', and 'footnotes'.
    """
    q_obj = q_meta.get('query', {})
    q_stubs = (q_meta.get('stub') or
               (q_obj.get('stub') if isinstance(q_obj, dict) else None) or
               t_meta.get('stub', []))
    q_headings = (q_meta.get('heading') or
                  (q_obj.get('heading') if isinstance(q_obj, dict) else None) or
                  t_meta.get('heading', []))
    t_variables = t_meta.get('variables', [])

    stubs, headings = reconcile_variable_codes(q_stubs, q_headings, t_variables)
    stub_headers = list(q_stubs) if len(q_stubs) == len(stubs) else list(stubs)

    query_list: List[Dict[str, Any]] = []
    var_selections: Dict[str, List[Tuple[str, str]]] = {}
    footnotes: List[str] = []

    for var in t_variables:
        code = var['code']
        vals = var.get('values', [])
        texts = var.get('valueTexts', [])
        selected_codes: List[str] = []
        selected_pairs: List[Tuple[str, str]] = []

        for val_code, val_text in zip(vals, texts):
            str_code = str(val_code)
            str_text = str(val_text).strip()
            if is_footnote_value(str_code, str_text):
                if str_text:
                    footnotes.append(str_text)
                continue
            selected_codes.append(str_code)
            selected_pairs.append((str_code, str_text))

        var_selections[code] = selected_pairs
        query_list.append({
            'code': code,
            'variabletype': None,
            'selection': {
                'filter': 'item',
                'values': selected_codes,
            },
        })

    return {
        'payload': {
            'showdecimals': None,
            'file': q_meta.get('file', ''),
            'lang': 'es',
            'query': {
                'query': query_list,
                'response': {
                    'format': 'json-stat',
                    'params': None,
                },
            },
            'stub': stubs,
            'heading': headings,
            'agg': None,
        },
        'stubs': stubs,
        'stub_headers': stub_headers,
        'headings': headings,
        'var_Selections': var_selections,
        'title': str(t_meta.get('title', '')).strip(),
        'footnotes': footnotes,
    }


def unpack_pxweb_datatable(
    dt_resp: Dict[str, Any],
    payload_info: Dict[str, Any],
) -> List[List[str]]:
    """Unpacks a flat PxWeb /datatable response into raw INEGI table rows.

    Preserves the raw INEGI table layout (title rows, stub/heading headers with
    merged-cell blanks, raw data rows with continuation blanks on stub_0, and
    trailing footnote rows).

    Args:
        dt_resp: JSON response from POST /datatable.
        payload_info: Output from build_pxweb_datatable_payload().

    Returns:
        List of CSV rows representing the raw INEGI input table.

    Raises:
        ValueError: If the datatable response has fewer cells than expected.
    """
    stubs: List[str] = payload_info['stubs']
    stub_headers: List[str] = payload_info.get('stub_headers', stubs)
    headings: List[str] = payload_info['headings']
    var_selections: Dict[str, List[Tuple[str, str]]] = payload_info[
        'var_Selections']
    title: str = payload_info.get('title', '')
    footnotes: List[str] = payload_info.get('footnotes', [])

    stub_lists = [[text for _, text in var_selections[s]] for s in stubs]
    heading_lists = [[text for _, text in var_selections[h]] for h in headings]

    stub_tuples = list(itertools.product(*stub_lists))
    heading_tuples = list(itertools.product(*heading_lists))

    data_cells = dt_resp.get('data', [])
    expected_cells = len(stub_tuples) * len(heading_tuples)
    if len(data_cells) < expected_cells:
        raise ValueError(
            f'Expected {expected_cells} cells, got {len(data_cells)}')

    num_stubs = len(stubs)
    num_headings = len(headings)
    num_cols = num_stubs + len(heading_tuples)
    rows: List[List[str]] = []

    rows.append([_INEGI_HEADER_TITLE] + [''] * (num_cols - 1))
    rows.append([title] + [''] * (num_cols - 1))

    if num_headings == 1:
        rows.append(list(stub_headers) + [ht[0] for ht in heading_tuples])
    elif num_headings == 2:
        h0_row = list(stub_headers)
        prev_h0: Optional[str] = None
        for ht in heading_tuples:
            if ht[0] == prev_h0:
                h0_row.append('')
            else:
                h0_row.append(ht[0])
                prev_h0 = ht[0]
        h1_row = [''] * num_stubs + [ht[1] for ht in heading_tuples]
        rows.append(h0_row)
        rows.append(h1_row)
    else:
        raise ValueError(f'Unsupported number of headings: {num_headings}')

    cell_idx = 0
    prev_stub_0: Optional[str] = None
    for st in stub_tuples:
        row_cells: List[str] = []
        for _ in heading_tuples:
            raw_cell = str(data_cells[cell_idx])
            cell_idx += 1
            val_part = raw_cell.split('|')[0].replace(',', '').strip()
            row_cells.append(val_part)

        if num_stubs == 1:
            rows.append([st[0]] + row_cells)
        elif num_stubs == 2:
            first_col = '' if st[0] == prev_stub_0 else st[0]
            prev_stub_0 = st[0]
            rows.append([first_col, st[1]] + row_cells)
        else:
            raise ValueError(f'Unsupported number of stubs: {num_stubs}')

    for note in footnotes:
        rows.append([note] + [''] * (num_cols - 1))

    return rows


def fetch_pxweb_raw_table(
    session: requests.Session,
    base_url: str,
    dataset_cfg: Dict[str, Any],
) -> List[List[str]]:
    """Fetches and unpacks a raw PxWeb dataset via the 3-step INEGI API."""
    base = base_url.rstrip('/')
    pxq_id = dataset_cfg['pxq_id']

    tabquery_url = f'{base}/tabquery?pxq={pxq_id}'
    q_meta = _http_get_json(session, tabquery_url)

    file_id = q_meta.get('file') or dataset_cfg['file_id']
    tabulado_url = f'{base}/tabulado?lang=es&file={file_id}'
    t_meta = _http_get_json(session, tabulado_url)

    payload_info = build_pxweb_datatable_payload(q_meta, t_meta)

    datatable_url = f'{base}/datatable?lang=es&file={file_id}'
    dt_resp = _http_post_json(
        session,
        datatable_url,
        json_body=payload_info['payload'],
        headers={'Content-Type': 'application/json'},
    )

    return unpack_pxweb_datatable(dt_resp, payload_info)


def parse_cuadros_response(json_data: List[Dict[str, Any]]) -> List[List[str]]:
    """Parses ServicioCuadros JSON into raw quarterly unemployment table rows.

    Args:
        json_data: Parsed JSON list from ServicioCuadros endpoint.

    Returns:
        List of raw CSV rows with header
        ['Period', 'Total', 'With experience', 'Without experience'], year
        group rows, and Roman-numeral quarter rows ('I', 'II', 'III', 'IV').
    """
    indicator_map = {
        '446566': 'Total',
        '446713': 'With experience',
        '446718': 'Without experience',
    }
    by_year_quarter: Dict[str, Dict[str, Dict[str, str]]] = {}

    for block in json_data:
        for item in block.get('Data', []):
            ind_code = str(item.get('MetaData', {}).get('Indicador', ''))
            col_name = indicator_map.get(ind_code)
            if not col_name:
                continue
            obs_list = item.get('Serie', {}).get('Obs', [])
            for obs in obs_list:
                time_period = str(obs.get('TimePeriod', '')).strip()
                if '/' not in time_period:
                    continue
                year, q_code = time_period.split('/', 1)
                if q_code not in _QUARTER_TO_ROMAN:
                    continue

                raw_val = str(obs.get('CurrentValue', '')).replace(',',
                                                                   '').strip()
                no_num = str(obs.get('ValueNoNumeric', '')).strip()
                if raw_val:
                    try:
                        num_val = float(raw_val)
                        if num_val.is_integer():
                            clean_val = str(int(num_val))
                        else:
                            clean_val = str(num_val)
                    except ValueError:
                        clean_val = raw_val
                else:
                    clean_val = no_num

                by_year_quarter.setdefault(year, {}).setdefault(
                    q_code, {})[col_name] = clean_val

    rows: List[List[str]] = [[
        'Period',
        'Total',
        'With experience',
        'Without experience',
    ]]
    for year in sorted(by_year_quarter.keys()):
        rows.append([year, '', '', ''])
        quarters = by_year_quarter[year]
        for q_code in sorted(quarters.keys()):
            cols = quarters[q_code]
            rows.append([
                _QUARTER_TO_ROMAN[q_code],
                cols.get('Total', ''),
                cols.get('With experience', ''),
                cols.get('Without experience', ''),
            ])
    return rows


def fetch_cuadros_raw_table(
    session: requests.Session,
    base_url: str,
    dataset_cfg: Dict[str, Any],
) -> List[List[str]]:
    """Fetches and parses raw ServicioCuadros JSON data."""
    base = base_url.rstrip('/')
    indicators = dataset_cfg['indicators']
    start_year = dataset_cfg.get('start_year', '2019')
    current_year = str(datetime.date.today().year)
    url = (f'{base}/{indicators}/false/0700/es/json/'
           f'{start_year}/{current_year}/0/0/3')
    json_data = _http_get_json(session, url)
    return parse_cuadros_response(json_data)


def write_csv_rows(output_path: str, rows: List[List[str]]) -> None:
    """Atomically writes CSV rows to output_path via a temporary .tmp file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    temp_file = output_path + '.tmp'
    with open(temp_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows(rows)
    os.replace(temp_file, output_path)


def _extract_snapshot_year(rows: List[List[str]]) -> Optional[str]:
    """Extracts the 4-digit snapshot year from the INEGI table title row."""
    if len(rows) < 2 or not rows[1]:
        return None
    title_cell = str(rows[1][0]).strip()
    matches = re.findall(r'\b(19\d{2}|20\d{2})\b', title_cell)
    return matches[-1] if matches else None


def _parse_gcs_uri(gcs_uri: str) -> Tuple[str, str]:
    """Splits a gs://bucket/prefix URI into (bucket_name, prefix_without_trailing_slash)."""
    without_scheme = gcs_uri[len('gs://'):].strip('/')
    if '/' in without_scheme:
        bucket_name, prefix = without_scheme.split('/', 1)
        return bucket_name, prefix.strip('/')
    return without_scheme, ''


def _write_year_archived_dataset(
    ds_name: str,
    ds_cfg: Dict[str, Any],
    raw_rows: List[List[str]],
    output_dir: str,
    historical_override: Optional[str] = None,
) -> None:
    """Syncs historical year snapshots via historical_inputs/ (and GCS) and copies to output_dir."""
    hist_target = (historical_override or
                   ds_cfg.get('historical_dir', 'historical_inputs'))

    # Remove any legacy un-suffixed input file so globbing *_input.csv does not
    # process the latest snapshot twice.
    legacy_path = os.path.join(output_dir, f'{ds_name}_input.csv')
    if os.path.exists(legacy_path):
        os.remove(legacy_path)

    file_pattern = f'{ds_name}_*_input.csv'
    year = _extract_snapshot_year(raw_rows)
    out_filename = (f'{ds_name}_{year}_input.csv'
                    if year else f'{ds_name}_input.csv')
    out_path = os.path.join(output_dir, out_filename)

    if hist_target.startswith('gs://'):
        bucket_name, prefix = _parse_gcs_uri(hist_target)
        if not prefix.endswith('historical_inputs'):
            prefix = (f'{prefix}/historical_inputs'
                      if prefix else 'historical_inputs')
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob_prefix = f'{prefix}/{ds_name}_'

        local_hist_dir = os.path.join(_SCRIPT_DIR, 'historical_inputs')
        os.makedirs(local_hist_dir, exist_ok=True)

        # 1. Download all previously archived year snapshots from GCS
        #    (gs://.../historical_inputs/) into local historical_inputs/.
        for blob in bucket.list_blobs(prefix=blob_prefix):
            fname = os.path.basename(blob.name)
            if fnmatch.fnmatch(fname, file_pattern):
                hist_file_path = os.path.join(local_hist_dir, fname)
                blob.download_to_filename(hist_file_path)
                logging.info(
                    'Downloaded historical snapshot gs://%s/%s -> %s',
                    bucket_name,
                    blob.name,
                    hist_file_path,
                )

        # 2. Write the newly downloaded INEGI snapshot to local historical_inputs/
        #    and upload it back to gs://.../historical_inputs/.
        hist_out_path = os.path.join(local_hist_dir, out_filename)
        write_csv_rows(hist_out_path, raw_rows)
        if year:
            dest_blob_name = f'{prefix}/{out_filename}'
            dest_blob = bucket.blob(dest_blob_name)
            dest_blob.upload_from_filename(hist_out_path)
            logging.info(
                'Uploaded year snapshot %s -> gs://%s/%s',
                hist_out_path,
                bucket_name,
                dest_blob_name,
            )

        # 3. Copy all year snapshots from local historical_inputs/ to output_dir (input_files/).
        pattern = os.path.join(local_hist_dir, file_pattern)
        for hist_path in sorted(glob.glob(pattern)):
            dest_path = os.path.join(output_dir, os.path.basename(hist_path))
            if os.path.abspath(hist_path) != os.path.abspath(dest_path):
                shutil.copy2(hist_path, dest_path)
    else:
        hist_dir = (hist_target if os.path.isabs(hist_target) else os.path.join(
            _SCRIPT_DIR, hist_target))
        os.makedirs(hist_dir, exist_ok=True)
        hist_out_path = os.path.join(hist_dir, out_filename)
        write_csv_rows(hist_out_path, raw_rows)

        pattern = os.path.join(hist_dir, file_pattern)
        for hist_path in sorted(glob.glob(pattern)):
            dest_path = os.path.join(output_dir, os.path.basename(hist_path))
            if os.path.abspath(hist_path) != os.path.abspath(dest_path):
                shutil.copy2(hist_path, dest_path)

    logging.info(
        'Successfully wrote %s (%d rows).',
        out_path,
        len(raw_rows),
    )


def download_all_datasets(config_path: str) -> None:
    """Downloads all configured raw datasets and writes input_files/*_input.csv."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    pxweb_base = config.get('pxweb_api_base_url', '')
    cuadros_base = config.get('cuadros_api_base_url', '')
    if not pxweb_base or not cuadros_base:
        raise ValueError('API base URLs must be provided in config.json.')

    hist_default = config.get('historical_gcs_path')
    datasets_cfg: Dict[str, Dict[str, Any]] = config.get('datasets', {})

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    with create_http_session() as session:
        for ds_name in sorted(datasets_cfg.keys()):
            ds_cfg = datasets_cfg[ds_name]
            source_type = ds_cfg.get('source_type', 'pxweb')

            logging.info('Downloading raw data for %s (%s)...', ds_name,
                         source_type)
            if source_type == 'pxweb':
                raw_rows = fetch_pxweb_raw_table(session, pxweb_base, ds_cfg)
            elif source_type == 'cuadros':
                raw_rows = fetch_cuadros_raw_table(session, cuadros_base,
                                                   ds_cfg)
            else:
                raise ValueError(
                    f'Unsupported source_type for {ds_name}: {source_type}')

            if ds_cfg.get('archive_by_year'):
                _write_year_archived_dataset(
                    ds_name,
                    ds_cfg,
                    raw_rows,
                    _OUTPUT_DIR,
                    historical_override=hist_default,
                )
            else:
                out_path = os.path.join(_OUTPUT_DIR, f'{ds_name}_input.csv')
                write_csv_rows(out_path, raw_rows)
                logging.info(
                    'Successfully wrote %s (%d rows).',
                    out_path,
                    len(raw_rows),
                )


def main(argv: List[str]) -> None:
    """CLI entry point."""
    del argv
    download_all_datasets(config_path=FLAGS.config_path)


if __name__ == '__main__':
    app.run(main)
