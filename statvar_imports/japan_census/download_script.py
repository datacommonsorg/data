#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Download script for Japan Census and socio-economic datasets from e-Stat.

Downloads raw CSV tables as-is directly from https://www.e-stat.go.jp/dbview?sid=...
into input_files/ without any custom preprocessing or aggregation.
"""

import base64
import concurrent.futures
import gzip
import json
import os
import tempfile
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

_FLAGS = flags.FLAGS
if 'output_dir' not in _FLAGS:
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_MODULE_DIR, 'input_files'),
        'Directory path to save the downloaded CSV files.',
    )
if 'max_workers' not in _FLAGS:
    flags.DEFINE_integer(
        'max_workers',
        4,
        'Maximum number of parallel threads for e-Stat dbview requests.',
    )

ESTAT_DBVIEW_BASE_URL = 'https://www.e-stat.go.jp/dbview'
ESTAT_DASHBOARD_DOWNLOAD_URL = (
    'https://dashboard.e-stat.go.jp/download/dataSearch')

# Raw CSV tables downloaded directly from e-Stat dbview and Dashboard dataSearch
DBVIEW_CONFIGS: dict[str, dict[str, Any]] = {
    'jpn_gender_age_total_population.csv': {
        'sid': '0003410380',
        'select_filters': {
            '18': {'020'}
        },
        'exclude_filters': {
            '2': {'2015000010', '2020000010'}
        },
        'exclude_suffixes': {
            '2': ('000010',)
        },
    },
    'jpn_aa1_gender_age_total_population.csv': {
        'sid': '0003410381',
        'select_filters': {
            '18': {'020'}
        },
        'exclude_filters': {
            '2': {'2015000010', '2020000010'}
        },
        'exclude_suffixes': {
            '2': ('000010',)
        },
    },
    'jpn_aa1_aa2_age_gender_1980.csv': {
        'sid': '0003412413',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_1985.csv': {
        'sid': '0003412414',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_1990.csv': {
        'sid': '0003412415',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_1995.csv': {
        'sid': '0003412416',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_2000.csv': {
        'sid': '0003412417',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_2005.csv': {
        'sid': '0003412418',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_2010.csv': {
        'sid': '0003412419',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_2015.csv': {
        'sid': '0003412420',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_aa2_age_gender_2020.csv': {
        'sid': '0003448299',
        'select_filters': {
            '18': {'020'}
        },
    },
    'jpn_aa1_death.csv': {
        'sid': '0000010101',
        'select_filters': {
            '3': {'A4200', 'A420001', 'A420002'}
        },
        'pos_overrides': {
            '2': ('row', '2'),
        },
    },
    'jpn_aa1_teacher.csv': {
        'sid': '0000010105',
        'select_filters': {
            '3': {'E1301', 'E2401', 'E4401'}
        },
    },
    'jpn_student.csv': {
        'dashboard_params': {
            'IndicatorCode': ('1201050300000010000,1201050400000010000,'
                              '1201050500000010000,1201050800000010000'),
            'RegionCode': '00000',
            'Cycle': '3,4',
        },
    },
    'jpn_aa1_health.csv': {
        'sid': '0000010109',
        'select_filters': {
            '3': {'I9103', 'I9105', 'I9108'}
        },
    },
    'jpn_employment.csv': {
        'dashboard_params': {
            'IndicatorCode': ('0301010000010010010,0301010000020010010,'
                              '0301010000030010010'),
            'RegionCode': '00000',
            'Cycle': '3',
        },
    },
    'jpn_unemploymentrate.csv': {
        'dashboard_params': {
            'IndicatorCode': '0301010000020020010',
            'RegionCode': '00000',
            'Cycle': '3',
        },
    },
}


def _gz_b64(obj: Any) -> str:
    """Serializes obj to JSON, compresses with gzip, and encodes as base64."""
    raw = json.dumps(obj, separators=(',', ':')).encode('utf-8')
    return base64.b64encode(gzip.compress(raw)).decode('ascii')


def _create_retry_session() -> requests.Session:
    """Creates a requests.Session configured with automatic retries."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=2.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET', 'POST']),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def _is_non_retryable_http_error(err: Exception) -> bool:
    """Returns True for permanent 4xx HTTP errors (excluding 408 and 429)."""
    if not isinstance(err, requests.HTTPError) or err.response is None:
        return False
    status_code = err.response.status_code
    return 400 <= status_code < 500 and status_code not in (408, 429)


def fetch_dbview_csv(
    sid: str,
    select_filters: dict[str, set[str]] | None = None,
    exclude_filters: dict[str, set[str]] | None = None,
    exclude_suffixes: dict[str, tuple[str, ...]] | None = None,
    pos_overrides: dict[str, tuple[str, str]] | None = None,
    timeout: int = 60,
) -> str:
    """Downloads a raw CSV table from https://www.e-stat.go.jp/dbview?sid=<sid>.

    Executes the 4-step e-Stat dbview session workflow:
      1. GET /dbview?sid=<sid> to initialize session cookies.
      2. POST /dbview/api_get_model?sid=<sid> to retrieve table dimensions.
      3. POST /dbview/api_get_result?sid=<sid> to apply layout and item filters.
      4. GET /dbview/file-download, POST /dbview/api_download_create, and
         POST /dbview/api_download_run to generate and download the raw CSV.

    Args:
        sid: The e-Stat statsDataId (e.g. '0003410380').
        select_filters: Optional map of matterId -> set of allowed item codes.
        exclude_filters: Optional map of matterId -> set of excluded item codes.
        exclude_suffixes: Optional map of matterId -> excluded code suffixes.
        pos_overrides: Optional map of matterId -> (position, positionNum).
        timeout: HTTP request timeout in seconds.

    Returns:
        Raw UTF-8 CSV content string as returned by e-Stat dbview.

    Raises:
        RuntimeError: If the e-Stat dbview endpoint fails after retries.
    """
    last_err: Exception | None = None
    for attempt in range(4):
        session = _create_retry_session()
        try:
            init_url = f'{ESTAT_DBVIEW_BASE_URL}?sid={sid}'
            logging.info('GET %s (attempt %d/4)', init_url, attempt + 1)
            init_resp = session.get(init_url, timeout=timeout)
            init_resp.raise_for_status()

            model_url = f'{ESTAT_DBVIEW_BASE_URL}/api_get_model?sid={sid}'
            logging.info('POST %s (payload_bytes=0)', model_url)
            model_resp = session.post(
                model_url,
                data=b'',
                timeout=timeout,
            )
            model_resp.raise_for_status()
            model = model_resp.json()
            if not isinstance(model, dict) or 'matters' not in model:
                raise RuntimeError(
                    f'Invalid model payload from dbview for sid={sid}')

            rows_r, cols_r, tops_r, api_tops_r = [], [], [], []
            rows, cols, tops, view_tops, tops_all = [], [], [], [], []
            for matter in model['matters'].values():
                m_id = str(matter['matterId'])
                pos = str(matter['position'])
                pos_num = str(matter['positionNum'])
                if pos_overrides and m_id in pos_overrides:
                    pos, pos_num = pos_overrides[m_id]

                w = {
                    'matterId': matter['matterId'],
                    'tableName': matter['tableName'],
                    'dispTableName': matter['dispTableName'],
                    'positionNum': pos_num,
                    'listData': [],
                    'allSelected': 1,
                }
                x = dict(w, listData=[])
                h = {
                    'matterId': matter['matterId'],
                    'tableName': matter['tableName'],
                    'dispTableName': matter['dispTableName'],
                    'positionNum': pos_num,
                    'matterName': matter['matterName'],
                    'initDisp': matter['initDisp'],
                    'listData': [],
                    'allListData': [],
                    'allSelected': 1,
                    'allDataSelected': 1,
                }
                allowed = (select_filters.get(m_id) if select_filters else None)
                excluded = (exclude_filters.get(m_id)
                            if exclude_filters else None)
                excluded_sfx = (exclude_suffixes.get(m_id)
                                if exclude_suffixes else None)

                def _is_selected(
                    item: dict[str, Any],
                    allowed_codes: set[str] | None = allowed,
                    excluded_codes: set[str] | None = excluded,
                    suffixes: tuple[str, ...] | None = excluded_sfx,
                ) -> bool:
                    code = str(item.get('code', ''))
                    if excluded_codes and code in excluded_codes:
                        return False
                    if suffixes and code.endswith(suffixes):
                        return False
                    if allowed_codes is not None:
                        return code in allowed_codes
                    return bool(item.get('selected'))

                if pos in ('row', 'col'):
                    for item in matter['listData'].values():
                        if _is_selected(item):
                            w['listData'].append({
                                'name': item['name'],
                                'code': item['code'],
                                'unit': item.get('unitName'),
                                'explanation': item.get('explanation'),
                            })
                            h['listData'].append({
                                'name': item['name'],
                                'code': item['code'],
                                'unit': item.get('unitName'),
                            })
                        else:
                            w['allSelected'] = 0
                            h['allSelected'] = 0
                    (rows_r if pos == 'row' else cols_r).append(w)
                    (rows if pos == 'row' else cols).append(h)
                elif pos == 'top':
                    sel_items = [
                        r for r in matter['listData'].values()
                        if _is_selected(r)
                    ]
                    first = (sel_items[0] if sel_items else next(
                        iter(matter['listData'].values())))
                    w['listData'].append({
                        'name': first['name'],
                        'code': first['code'],
                    })
                    h['listData'].append({
                        'name': first['name'],
                        'code': first['code'],
                    })
                    for item in matter['listData'].values():
                        if _is_selected(item):
                            x['listData'].append({
                                'name': item['name'],
                                'code': item['code'],
                                'unit': item.get('unitName'),
                                'explanation': item.get('explanation'),
                            })
                            h['allListData'].append({
                                'name': item['name'],
                                'code': item['code'],
                                'unit': item.get('unitName'),
                            })
                        else:
                            h['allDataSelected'] = 0
                    api_tops_r.append(x)
                    tops_r.append(w)
                    tops.append(h)
                    if h['initDisp'] != 0:
                        view_tops.append(h)
                    tops_all.append(h)

            res_payload = {
                'tops': _gz_b64(tops_r),
                'rows': _gz_b64(rows_r),
                'cols': _gz_b64(cols_r),
                'apiTops': _gz_b64(api_tops_r),
                'annotationFlg': model['annotationFlg'],
                'rowNoDataDispFlg': model['rowNoDataDispFlg'],
                'colNoDataDispFlg': model['colNoDataDispFlg'],
                'commaType': model['commaType'],
                'replaceSpChars': model['replaceSpChars'],
                'graphAxis': model['graphAxis'],
                'graphBasis': model['graphBasis'],
                'graphSort': model['graphSort'],
                'graphTitle': model['graphTitle'],
                'graphType': model['graphType'],
                'inputNumberOfCols': model['inputNumberOfCols'],
                'inputNumberOfRows': model['inputNumberOfRows'],
                'movementId': model['movementId'],
                'leftMoveFlg': model['leftMoveFlg'],
                'rightMoveFlg': model['rightMoveFlg'],
                'underMoveFlg': model['underMoveFlg'],
                'upMoveFlg': model['upMoveFlg'],
                'currentCols': '',
                'currentRows': '',
                'mode': 'table',
                'layoutName': '',
            }
            ajax_headers = {
                'Content-Type':
                    'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With':
                    'XMLHttpRequest',
                'Referer':
                    f'{ESTAT_DBVIEW_BASE_URL}/file-download?sid={sid}',
            }
            res_url = f'{ESTAT_DBVIEW_BASE_URL}/api_get_result?sid={sid}'
            logging.info(
                'POST %s (rows=%d, cols=%d, tops=%d)',
                res_url,
                len(rows_r),
                len(cols_r),
                len(tops_r),
            )
            res_resp = session.post(
                res_url,
                data=res_payload,
                headers=ajax_headers,
                timeout=timeout,
            )
            res_resp.raise_for_status()

            dl_page_url = f'{ESTAT_DBVIEW_BASE_URL}/file-download?sid={sid}'
            logging.info('GET %s', dl_page_url)
            dl_page_resp = session.get(
                dl_page_url,
                timeout=timeout,
            )
            dl_page_resp.raise_for_status()

            create_payload = {
                'rows': _gz_b64(rows),
                'cols': _gz_b64(cols),
                'tops': _gz_b64(tops),
                'viewTops': _gz_b64(view_tops),
                'topsAll': _gz_b64(tops_all),
                'annotationFlg': '0',
                'rowNoDataDispFlg': '0',
                'colNoDataDispFlg': '0',
                'commaType': '2',
                'replaceSpChars': '3',
                'currentCols': '',
                'currentRows': '',
                'downloadRange': '0',
                'fileFormat': '0',
                'charset': 'UTF-8',
                'bom': '0',
                'titleDispFlg': '1',
                'codeDispFlg': '1',
                'auxiliaryCodeDispFlg': '0',
                'legendDispFlg': '0',
                'levelCodeDispFlg': '0',
                'totalCellSelected': '1',
                'totalCellSelectedCount': '1000',
                'totalCellCount': '1000',
                'totalColSelected': '10',
                'title': 'e-Stat',
                'statCode': '',
                'startNumber': '1',
                'totalNum': '',
                'toNum': '',
            }
            create_url = f'{ESTAT_DBVIEW_BASE_URL}/api_download_create?sid={sid}'
            logging.info(
                'POST %s (charset=%s, fileFormat=%s)',
                create_url,
                create_payload['charset'],
                create_payload['fileFormat'],
            )
            create_resp = session.post(
                create_url,
                data=create_payload,
                headers=ajax_headers,
                timeout=timeout,
            )
            create_resp.raise_for_status()
            create_json = create_resp.json()
            if (not isinstance(create_json, list) or not create_json or
                    'fileList' not in create_json[0] or
                    not create_json[0]['fileList']):
                raise RuntimeError(
                    f'api_download_create returned invalid payload for sid={sid}: {create_json}'
                )
            finfo = create_json[0]['fileList'][0]
            run_payload = {
                'index': finfo['fileNo'],
                'path1': create_json[0]['filePath'],
                'name1': finfo['fileName'],
            }
            run_url = f'{ESTAT_DBVIEW_BASE_URL}/api_download_run?sid={sid}'
            logging.info(
                'POST %s (index=%s, name1=%s)',
                run_url,
                run_payload['index'],
                run_payload['name1'],
            )
            run_resp = session.post(
                run_url,
                data=run_payload,
                headers=ajax_headers,
                timeout=timeout,
            )
            run_resp.raise_for_status()
            text = run_resp.content.decode('utf-8')
            if not text.strip():
                raise RuntimeError(f'Downloaded empty CSV for sid={sid}')
            return text
        except Exception as err:  # pylint: disable=broad-except
            last_err = err
            if _is_non_retryable_http_error(err):
                break
            if attempt < 3:
                sleep_sec = 2.0 * (attempt + 1)
                logging.warning(
                    'dbview download attempt %d/4 for sid=%s failed: %s; retrying in %.1fs',
                    attempt + 1,
                    sid,
                    err,
                    sleep_sec,
                )
                time.sleep(sleep_sec)
        finally:
            session.close()
    raise RuntimeError(
        f'Failed to download dbview CSV for sid={sid}: {last_err}'
    ) from last_err


def _write_text_atomically(output_filepath: str, content: str) -> None:
    """Writes raw text content atomically to output_filepath."""
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.tmp_jpn_',
                                    suffix='.csv',
                                    dir=output_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        if not (os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0):
            raise RuntimeError(
                f'Atomic write failed: {tmp_path} is empty or missing.')
        os.replace(tmp_path, output_filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def fetch_dashboard_csv(
    dashboard_params: dict[str, str],
    timeout: int = 60,
) -> str:
    """Downloads a raw CSV table from https://dashboard.e-stat.go.jp/download/dataSearch."""
    last_err: Exception | None = None
    for attempt in range(4):
        session = _create_retry_session()
        try:
            params = {
                'IndicatorCode':
                    dashboard_params['IndicatorCode'],
                'RegionCode':
                    dashboard_params['RegionCode'],
                'Cycle':
                    dashboard_params['Cycle'],
                'TimeFrom':
                    dashboard_params.get('TimeFrom', ''),
                'TimeTo':
                    dashboard_params.get('TimeTo', ''),
                'IsSeasonalAdjustment':
                    dashboard_params.get('IsSeasonalAdjustment', '1'),
            }
            logging.info(
                'GET %s (params=%s, attempt=%d/4)',
                ESTAT_DASHBOARD_DOWNLOAD_URL,
                params,
                attempt + 1,
            )
            resp = session.get(
                ESTAT_DASHBOARD_DOWNLOAD_URL,
                params=params,
                timeout=timeout,
            )
            resp.raise_for_status()
            csv_text = resp.content.decode('utf-8-sig')
            if not csv_text.strip():
                raise RuntimeError(
                    'Empty CSV content returned from dashboard dataSearch.')
            return csv_text
        except Exception as err:  # pylint: disable=broad-except
            last_err = err
            if _is_non_retryable_http_error(err):
                break
            if attempt < 3:
                sleep_sec = 2.0 * (attempt + 1)
                logging.warning(
                    'Dashboard dataSearch attempt %d/4 failed: %s; retrying in %.1fs',
                    attempt + 1,
                    err,
                    sleep_sec,
                )
                time.sleep(sleep_sec)
        finally:
            session.close()
    raise RuntimeError(
        f'Failed to download dashboard CSV for {dashboard_params}: {last_err}'
    ) from last_err


def download_dbview_dataset(
    output_filepath: str,
    sid: str | None = None,
    select_filters: dict[str, set[str]] | None = None,
    exclude_filters: dict[str, set[str]] | None = None,
    exclude_suffixes: dict[str, tuple[str, ...]] | None = None,
    pos_overrides: dict[str, tuple[str, str]] | None = None,
    dashboard_params: dict[str, str] | None = None,
) -> int:
    """Downloads a raw e-Stat CSV table and writes it atomically."""
    if dashboard_params is not None:
        logging.info(
            'Downloading dashboard dataSearch table -> %s',
            os.path.basename(output_filepath),
        )
        csv_text = fetch_dashboard_csv(dashboard_params=dashboard_params)
    elif sid is not None:
        logging.info('Downloading dbview table sid=%s -> %s', sid,
                     os.path.basename(output_filepath))
        csv_text = fetch_dbview_csv(
            sid=sid,
            select_filters=select_filters,
            exclude_filters=exclude_filters,
            exclude_suffixes=exclude_suffixes,
            pos_overrides=pos_overrides,
        )
    else:
        raise ValueError('Either sid or dashboard_params must be provided.')
    _write_text_atomically(output_filepath, csv_text)
    line_count = len(csv_text.splitlines())
    logging.info('Saved %d lines to %s', line_count, output_filepath)
    return line_count


def _cleanup_stale_csvs(output_dir: str) -> None:
    """Removes any stale CSV files in output_dir not in DBVIEW_CONFIGS."""
    expected_files = set(DBVIEW_CONFIGS.keys())
    for entry in os.listdir(output_dir):
        if not entry.endswith('.csv'):
            continue
        if entry not in expected_files:
            stale_path = os.path.join(output_dir, entry)
            if os.path.isfile(stale_path):
                logging.info('Removing stale CSV file: %s', stale_path)
                os.remove(stale_path)


def download_all(
    output_dir: str,
    max_workers: int = 4,
) -> None:
    """Downloads all 17 raw Japan Census and annual CSV files from e-Stat."""
    os.makedirs(output_dir, exist_ok=True)
    _cleanup_stale_csvs(output_dir)
    total_lines = 0

    if max_workers > 1 and len(DBVIEW_CONFIGS) > 1:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    download_dbview_dataset,
                    os.path.join(output_dir, filename),
                    cfg.get('sid'),
                    cfg.get('select_filters'),
                    cfg.get('exclude_filters'),
                    cfg.get('exclude_suffixes'),
                    cfg.get('pos_overrides'),
                    cfg.get('dashboard_params'),
                ) for filename, cfg in DBVIEW_CONFIGS.items()
            ]
            for fut in futures:
                total_lines += fut.result()
    else:
        for filename, cfg in DBVIEW_CONFIGS.items():
            output_filepath = os.path.join(output_dir, filename)
            total_lines += download_dbview_dataset(
                output_filepath=output_filepath,
                sid=cfg.get('sid'),
                select_filters=cfg.get('select_filters'),
                exclude_filters=cfg.get('exclude_filters'),
                exclude_suffixes=cfg.get('exclude_suffixes'),
                pos_overrides=cfg.get('pos_overrides'),
                dashboard_params=cfg.get('dashboard_params'),
            )

    _cleanup_stale_csvs(output_dir)
    logging.info(
        'Successfully downloaded all %d raw datasets (%d total lines) to %s',
        len(DBVIEW_CONFIGS),
        total_lines,
        output_dir,
    )


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    output_dir = (_FLAGS.output_dir if os.path.isabs(_FLAGS.output_dir) else
                  os.path.join(_MODULE_DIR, _FLAGS.output_dir))
    download_all(
        output_dir,
        max_workers=_FLAGS.max_workers,
    )


if __name__ == '__main__':
    app.run(main)
