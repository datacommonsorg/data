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
"""Downloads Indonesia Demographic Population data from BPS WebAPI."""

import csv
import html
import json
import os
import re
import sys
from typing import Any

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

import download_util
import file_util
from absl import app, flags, logging
from google.api_core import exceptions as api_core_exceptions
from google.cloud import storage

DEFAULT_API_KEY_GCS_PATH = (
    'gs://unresolved_mcf/country/indonesia/demographic/api_key.json')

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(_CODEDIR, 'input_files'),
    'Directory path to save the downloaded input CSV files.',
)
flags.DEFINE_string(
    'historical_gcs_dir',
    'gs://unresolved_mcf/country/indonesia/demographic/historical',
    'GCS directory containing the consolidated historical CSV files.',
)
flags.DEFINE_string(
    'historical_output_dir',
    os.path.join(_CODEDIR, 'output_files'),
    'Directory path to copy the historical CSV and TMCF files into.',
)
flags.DEFINE_string(
    'population_filename',
    'idn_population.csv',
    'Filename for the total population CSV table.',
)
flags.DEFINE_string(
    'age_gender_filename',
    'idn_age_gender.csv',
    'Filename for the age and gender population CSV table.',
)
flags.DEFINE_string(
    'domain',
    '0000',
    'BPS domain code (0000 for national/all-province/regency tables).',
)
flags.DEFINE_integer(
    'total_var_id',
    2790,
    'BPS variable ID for Total Population by Regency/City and Age Group.',
)
flags.DEFINE_integer(
    'male_var_id',
    2791,
    'BPS variable ID for Male Population by Regency/City and Age Group.',
)
flags.DEFINE_integer(
    'female_var_id',
    2792,
    'BPS variable ID for Female Population by Regency/City and Age Group.',
)
flags.DEFINE_integer(
    'start_year',
    2023,
    'Minimum observation year to include in the downloaded CSV files.',
)
flags.DEFINE_string(
    'api_key',
    os.environ.get('BPS_API_KEY', ''),
    'BPS WebAPI key (defaults to BPS_API_KEY environment variable).',
)
flags.DEFINE_string(
    'api_key_gcs_path',
    DEFAULT_API_KEY_GCS_PATH,
    'GCS or local JSON path containing {"api_key": "..."} used when '
    '--api_key / BPS_API_KEY is not set.',
)

BPS_API_BASE_URL = 'https://webapi.bps.go.id/v1/api/list'
MAX_YEARS_PER_REQUEST = 3
HISTORICAL_CSVS = (
    'idn_population_historical_1971_2022.csv',
    'idn_age_gender_historical_2010_2022.csv',
)

PROVINCE_SUFFIX_BY_CODE: dict[int, str] = {
    1100: 'Aceh',
    1200: 'Sumatera Utara',
    1300: 'Sumatera Barat',
    1400: 'Riau',
    1500: 'Jambi',
    1600: 'Sumatera Selatan',
    1700: 'Bengkulu',
    1800: 'Lampung',
    1900: 'Kep. Bangka Belitung',
    2100: 'Kepulauan Riau',
    3100: 'DKI Jakarta',
    3200: 'Jawa Barat',
    3300: 'Jawa Tengah',
    3400: 'DI Yogyakarta',
    3500: 'Jawa Timur',
    3600: 'Banten',
    5100: 'Bali',
    5200: 'Nusa Tenggara Barat',
    5300: 'Nusa Tenggara Timur',
    6100: 'Kalimantan Barat',
    6200: 'Kalimantan Tengah',
    6300: 'Kalimantan Selatan',
    6400: 'Kalimantan Timur',
    6500: 'Kalimantan Utara',
    7100: 'Sulawesi Utara',
    7200: 'Sulawesi Tengah',
    7300: 'Sulawesi Selatan',
    7400: 'Sulawesi Tenggara',
    7500: 'Gorontalo',
    7600: 'Sulawesi Barat',
    8100: 'Maluku',
    8200: 'Maluku Utara',
    9100: 'Papua Barat',
    9200: 'Papua Barat Daya',
    9400: 'Papua',
    9500: 'Papua Selatan',
    9600: 'Papua Tengah',
    9700: 'Papua Pegunungan',
}

PRE_2022_PAPUA_PROVINCE_CODES: frozenset[int] = frozenset({9100, 9400})
POST_2022_PAPUA_PROVINCE_CODES: frozenset[int] = frozenset(
    {9200, 9500, 9600, 9700})

# 26 regencies/cities carved out of Papua Barat (9100) and Papua (9400) into
# Papua Barat Daya (9200), Papua Selatan (9500), Papua Tengah (9600), and
# Papua Pegunungan (9700) in late 2022. BPS WebAPI returns both legacy 91xx/94xx
# and current 92xx/95xx/96xx/97xx codes for these regencies.
SPLIT_PAPUA_REGENCY_NAMES: frozenset[str] = frozenset({
    # Moved from Papua Barat (9100) to Papua Barat Daya (9200)
    'Sorong',
    'Sorong Selatan',
    'Raja Ampat',
    'Tambrauw',
    'Maybrat',
    'Kota Sorong',
    # Moved from Papua (9400) to Papua Selatan (9500)
    'Merauke',
    'Boven Digoel',
    'Mappi',
    'Asmat',
    # Moved from Papua (9400) to Papua Tengah (9600)
    'Nabire',
    'Puncak Jaya',
    'Mimika',
    'Paniai',
    'Puncak',
    'Dogiyai',
    'Intan Jaya',
    'Deiyai',
    # Moved from Papua (9400) to Papua Pegunungan (9700)
    'Jayawijaya',
    'Pegunungan Bintang',
    'Yahukimo',
    'Tolikara',
    'Mamberamo Tengah',
    'Yalimo',
    'Lanny Jaya',
    'Nduga',
})


def _validate_api_key(api_key: str) -> str:
    """Validates that a non-empty BPS WebAPI key is provided."""
    if not api_key or not api_key.strip():
        raise ValueError(
            'BPS WebAPI key is required. Set the BPS_API_KEY environment '
            'variable, pass --api_key, or provide --api_key_gcs_path.')
    return api_key.strip()


def _load_api_key_from_path(api_key_gcs_path: str) -> str:
    """Loads the BPS WebAPI key from a JSON file in GCS or local disk."""
    if not api_key_gcs_path or not api_key_gcs_path.strip():
        return ''
    path = api_key_gcs_path.strip()
    try:
        if path.startswith('gs://'):
            bucket_and_blob = path[len('gs://'):].split('/', 1)
            if len(bucket_and_blob) != 2 or not all(bucket_and_blob):
                logging.warning('Invalid GCS path for BPS API key: %s', path)
                return ''
            bucket_name, blob_path = bucket_and_blob
            blob = storage.Client().bucket(bucket_name).blob(blob_path)
            raw = blob.download_as_text(encoding='utf-8').strip()
        else:
            with file_util.FileIO(path) as fp:
                raw = fp.read().strip()
        if not raw:
            return ''
        payload = json.loads(raw)
        if isinstance(payload, dict):
            val = payload.get('api_key')
            return val.strip() if isinstance(val, str) else ''
        return ''
    except (
            OSError,
            ValueError,
            RuntimeError,
            api_core_exceptions.GoogleAPIError,
    ) as exc:
        logging.warning('Unable to load BPS API key from %s: %s', path, exc)
        return ''


def _resolve_api_key(
    api_key: str,
    api_key_gcs_path: str = DEFAULT_API_KEY_GCS_PATH,
) -> str:
    """Resolves BPS WebAPI key from explicit arg/env or GCS/local JSON fallback."""
    if api_key and api_key.strip():
        return api_key.strip()
    fallback_key = _load_api_key_from_path(api_key_gcs_path)
    if fallback_key:
        return fallback_key
    return _validate_api_key(api_key)


def _sanitize_url(url: str, api_key: str) -> str:
    """Redacts the BPS WebAPI key from a URL string before logging/raising."""
    if api_key:
        return url.replace(api_key, '<REDACTED>')
    return url


def clean_bps_label(raw_label: Any) -> str:
    """Strips HTML tags and normalizes whitespace in BPS labels."""
    text = html.unescape(str(raw_label))
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_legacy_split_papua_regency(
    code: int,
    raw_label: Any,
    post_split_regencies: set[str] | frozenset[str] = SPLIT_PAPUA_REGENCY_NAMES,
) -> bool:
    """Returns True if code is a pre-2022 91xx/94xx code for a split Papua regency."""
    if code == 9999 or code % 100 == 0:
        return False
    prov_code = (code // 100) * 100
    if prov_code not in PRE_2022_PAPUA_PROVINCE_CODES:
        return False
    return clean_bps_label(raw_label) in post_split_regencies


def format_place_name(code: int, raw_label: Any) -> str:
    """Formats a BPS region code and label to match idn_places_resolved.csv."""
    label = clean_bps_label(raw_label)
    if code == 9999 or label.upper() == 'INDONESIA':
        return 'INDONESIA'
    if code % 100 == 0:
        return f'{label.upper()}, INDONESIA'
    prov_code = (code // 100) * 100
    prov_name = PROVINCE_SUFFIX_BY_CODE.get(prov_code, '')
    if prov_name:
        return f'{label}, {prov_name}, Indonesia'
    return f'{label}, Indonesia'


def format_thousand_comma(exact_persons: float | str) -> str:
    """Formats an exact person count into thousands with comma decimal separator.

    Matches idn_population_pvmap.csv (`number_decimal, ","` and `#Multiply, 1000`)
    so that StatVarProcessor restores the exact integer person count.
    """
    val_int = round(float(exact_persons))
    whole = val_int // 1000
    rem = val_int % 1000
    if rem == 0:
        return str(whole)
    rem_str = f'{rem:03d}'.rstrip('0')
    return f'{whole},{rem_str}'


def fetch_available_years(
    domain: str,
    var_id: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Fetches all available year definitions (th_id, th) for a BPS variable."""
    api_key = _validate_api_key(api_key)
    years: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (f'{BPS_API_BASE_URL}/model/th/lang/ind/domain/{domain}'
               f'/var/{var_id}/page/{page}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            safe_url = _sanitize_url(url, api_key)
            raise RuntimeError(
                'Failed to fetch available years from BPS WebAPI '
                f'(var_id={var_id}, page={page}, url={safe_url}): {resp}')
        data = resp.get('data')
        if not isinstance(data, list) or len(data) < 2:
            break
        meta, items = data[0], data[1]
        if isinstance(items, list):
            years.extend(items)
        total_pages = int(meta.get('pages', 1)) if isinstance(meta, dict) else 1
        if page >= total_pages:
            break
        page += 1

    years.sort(key=lambda item: int(item['th_id']))
    return years


def fetch_variable_data(
    domain: str,
    var_id: int,
    api_key: str,
    start_year: int = 2023,
) -> tuple[list[tuple[int, str]], list[str], list[str], dict[tuple[int, str,
                                                                   str], str]]:
    """Downloads year chunks for a BPS demographic variable.

    Returns:
      places: Ordered list of (region_code, formatted_place_name).
      age_groups: Ordered list of age group labels (including 'TOTAL').
      year_labels: Ordered list of year strings.
      values: Dict mapping (region_code, age_group_label, year_str) -> value str.
    """
    api_key = _validate_api_key(api_key)
    all_years = fetch_available_years(domain=domain,
                                      var_id=var_id,
                                      api_key=api_key)
    if not all_years:
        raise ValueError(f'No years returned for BPS var_id={var_id}.')

    years = [
        y for y in all_years if str(y.get('th', '')).strip().isdigit() and
        int(str(y['th']).strip()) >= start_year
    ]
    if not years:
        raise ValueError(
            f'No available years >= {start_year} found for BPS var_id={var_id}.'
        )

    places: list[tuple[int, str]] = []
    seen_codes: set[int] = set()
    age_groups: list[str] = []
    seen_ages: set[str] = set()
    year_labels: list[str] = [str(y['th']).strip() for y in years]
    values: dict[tuple[int, str, str], str] = {}

    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/model/data/lang/ind/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            safe_url = _sanitize_url(url, api_key)
            raise RuntimeError(
                f'Failed to fetch demographic data for var={var_id} '
                f'th={th_param} (url={safe_url}): {resp}')

        var_list = resp.get('var', [])
        turvar_list = resp.get('turvar', [])
        turtahun_list = resp.get('turtahun', [])
        vervar_list = resp.get('vervar', [])
        tahun_list = resp.get('tahun', [])
        datacontent = resp.get('datacontent', {})

        if not (var_list and turvar_list and turtahun_list):
            safe_url = _sanitize_url(url, api_key)
            raise RuntimeError(
                f'Incomplete metadata in BPS response for var={var_id} '
                f'th={th_param} (url={safe_url}).')

        vid = var_list[0]['val']
        tt_val = turtahun_list[0]['val']

        for tv in turvar_list:
            age_label = clean_bps_label(tv['label'])
            if age_label not in seen_ages:
                seen_ages.add(age_label)
                age_groups.append(age_label)

        post_split_regencies = set(SPLIT_PAPUA_REGENCY_NAMES)
        for vv in vervar_list:
            vv_code = int(vv['val'])
            if (vv_code != 9999 and vv_code % 100 != 0 and
                (vv_code // 100) * 100 in POST_2022_PAPUA_PROVINCE_CODES):
                post_split_regencies.add(clean_bps_label(vv['label']))

        for vv in vervar_list:
            code = int(vv['val'])
            if is_legacy_split_papua_regency(code, vv['label'],
                                             post_split_regencies):
                continue
            place_name = format_place_name(code, vv['label'])
            if code not in seen_codes:
                seen_codes.add(code)
                places.append((code, place_name))
            for tv in turvar_list:
                age_label = clean_bps_label(tv['label'])
                tv_val = tv['val']
                for ty in tahun_list:
                    year_str = str(ty['label']).strip()
                    cell_key = f'{code}{vid}{tv_val}{ty["val"]}{tt_val}'
                    raw_val = datacontent.get(cell_key)
                    if raw_val is not None and str(raw_val).strip() != '':
                        if isinstance(raw_val, float) and raw_val.is_integer():
                            values[(code, age_label,
                                    year_str)] = str(int(raw_val))
                        else:
                            values[(code, age_label,
                                    year_str)] = str(raw_val).strip()

    return places, age_groups, year_labels, values


def write_population_csv(
    output_path: str,
    places: list[tuple[int, str]],
    year_labels: list[str],
    total_values: dict[tuple[int, str, str], str],
) -> None:
    """Writes idn_population.csv matching idn_population_pvmap.csv."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow([
            'observationAbout',
            'observationDate',
            'Jumlah Penduduk (Ribu)',
        ])
        row_count = 0
        for code, place_name in places:
            for year in year_labels:
                raw_val = total_values.get((code, 'TOTAL', year))
                if raw_val is None or raw_val == '':
                    continue
                writer.writerow([
                    place_name,
                    year,
                    format_thousand_comma(raw_val),
                ])
                row_count += 1
    logging.info('Wrote %d total population rows to %s', row_count, output_path)


def write_age_gender_csv(
    output_path: str,
    places: list[tuple[int, str]],
    age_groups: list[str],
    year_labels: list[str],
    total_values: dict[tuple[int, str, str], str],
    male_values: dict[tuple[int, str, str], str],
    female_values: dict[tuple[int, str, str], str],
) -> None:
    """Writes idn_age_gender.csv matching idn_age_gender_pvmap.csv."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        writer.writerow([
            'observationAbout',
            'observationDate',
            'Kelompok Umur',
            'Penduduk (Laki-Laki)',
            'Penduduk (Perempuan)',
            'Penduduk (Laki-Laki + Perempuan)',
        ])
        row_count = 0
        for code, place_name in places:
            for year in year_labels:
                for age_label in age_groups:
                    m_val = male_values.get((code, age_label, year), '')
                    f_val = female_values.get((code, age_label, year), '')
                    t_val = total_values.get((code, age_label, year), '')
                    if not (m_val or f_val or t_val):
                        continue
                    if age_label.upper() == 'TOTAL':
                        # Emit gender totals (Count_Person_Male / Count_Person_Female)
                        # without an age bracket; leave total column empty here so
                        # Count_Person is not duplicated across both CSVs, or emit if needed.
                        writer.writerow([
                            place_name,
                            year,
                            'TOTAL',
                            m_val,
                            f_val,
                            '',
                        ])
                    else:
                        writer.writerow([
                            place_name,
                            year,
                            age_label,
                            m_val,
                            f_val,
                            t_val,
                        ])
                    row_count += 1
    logging.info('Wrote %d age/gender rows to %s', row_count, output_path)


def download_demographic_data(
    domain: str,
    total_var_id: int,
    male_var_id: int,
    female_var_id: int,
    api_key: str,
    output_dir: str,
    population_filename: str,
    age_gender_filename: str,
    start_year: int = 2023,
    api_key_gcs_path: str = DEFAULT_API_KEY_GCS_PATH,
) -> tuple[str, str]:
    """Downloads BPS demographic tables and writes both input CSV files."""
    api_key = _resolve_api_key(api_key, api_key_gcs_path)
    places, age_groups, year_labels, total_values = fetch_variable_data(
        domain=domain,
        var_id=total_var_id,
        api_key=api_key,
        start_year=start_year,
    )
    _, _, _, male_values = fetch_variable_data(
        domain=domain,
        var_id=male_var_id,
        api_key=api_key,
        start_year=start_year,
    )
    _, _, _, female_values = fetch_variable_data(
        domain=domain,
        var_id=female_var_id,
        api_key=api_key,
        start_year=start_year,
    )

    pop_path = os.path.join(output_dir, population_filename)
    write_population_csv(
        output_path=pop_path,
        places=places,
        year_labels=year_labels,
        total_values=total_values,
    )

    ag_path = os.path.join(output_dir, age_gender_filename)
    write_age_gender_csv(
        output_path=ag_path,
        places=places,
        age_groups=age_groups,
        year_labels=year_labels,
        total_values=total_values,
        male_values=male_values,
        female_values=female_values,
    )
    return pop_path, ag_path


COMMON_TMCF_CONTENT = (
    'Node: E:idn_demographic->E0\n'
    'typeOf: dcs:StatVarObservation\n'
    'observationAbout: C:idn_demographic->observationAbout\n'
    'observationDate: C:idn_demographic->observationDate\n'
    'value: C:idn_demographic->value\n'
    'variableMeasured: C:idn_demographic->variableMeasured\n')


def copy_historical_files_from_gcs(
    historical_gcs_dir: str,
    historical_output_dir: str,
) -> None:
    """Copies consolidated historical CSVs from GCS and writes common_tmcf.tmcf into output_files."""
    if not historical_gcs_dir:
        return
    os.makedirs(historical_output_dir, exist_ok=True)
    dst_tmcf = os.path.join(historical_output_dir, 'common_tmcf.tmcf')
    with open(dst_tmcf, mode='w', encoding='utf-8') as tmcf_f:
        tmcf_f.write(COMMON_TMCF_CONTENT)
    logging.info('Wrote historical TMCF to %s', dst_tmcf)

    gcs_base = historical_gcs_dir.rstrip('/')
    for fname in HISTORICAL_CSVS:
        src_gcs = f'{gcs_base}/{fname}'
        dst_local = os.path.join(historical_output_dir, fname)
        logging.info('Copying historical CSV from %s to %s', src_gcs, dst_local)
        file_util.file_copy(src_gcs, dst_local)


def main(_) -> None:
    logging.set_verbosity(logging.INFO)
    copy_historical_files_from_gcs(
        historical_gcs_dir=_FLAGS.historical_gcs_dir,
        historical_output_dir=_FLAGS.historical_output_dir,
    )
    download_demographic_data(
        domain=_FLAGS.domain,
        total_var_id=_FLAGS.total_var_id,
        male_var_id=_FLAGS.male_var_id,
        female_var_id=_FLAGS.female_var_id,
        api_key=_FLAGS.api_key,
        output_dir=_FLAGS.output_dir,
        population_filename=_FLAGS.population_filename,
        age_gender_filename=_FLAGS.age_gender_filename,
        start_year=_FLAGS.start_year,
        api_key_gcs_path=_FLAGS.api_key_gcs_path,
    )


if __name__ == '__main__':
    app.run(main)
