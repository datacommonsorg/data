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
"""Downloads and extracts Argentina Census datasets from INDEC into CSVs.

This script downloads official INDEC Excel/ZIP publications for:
1. Population by single age, 5-year age group, and sex (1980, 1991, 2001, 2010, 2022)
2. Urban and rural population by age and sex (1980, 1991, 2001, 2010)
3. Department (AA2) total population (2001, 2010, 2022)
4. Literacy and illiteracy for population aged 10+ years (2010)
5. Infant mortality rate per 1,000 live births (2005-2023)

The extracted CSV files are written atomically to `input_files/` ready for
processing by `tools/statvar_importer/stat_var_processor.py`.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import io
import os
import re
import unicodedata
import zipfile

from absl import app
from absl import flags
from absl import logging
import openpyxl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xlrd

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input_files'),
    'Directory where extracted CSV input files will be saved.',
)
flags.DEFINE_integer('max_workers', 16,
                     'Maximum number of concurrent HTTP downloads.')

BASE_FTP_URL = 'https://www.indec.gob.ar/ftp'
POBLACION_FTP_URL = f'{BASE_FTP_URL}/cuadros/poblacion'

# Canonical Jurisdiction Metadata:
# (canonical_name, code_2001, zip_slug_1980, g2_slug_1980, c02_code_1980,
#  p2_slug_1991, p2_slug_2010, p1_slug_2010, c1_url_2022, c4_url_2022)
JURISDICTIONS = [
    (
        'Total del país',
        '01',
        'pv_80_totalpais',
        'totalpaís',
        None,
        'Total_pais/C91_P2_Total_Pais',
        'Total_pais/P2-P_Total_pais',
        None,
        None,
        f'{POBLACION_FTP_URL}/c2022_tp_est_c4.xlsx',
    ),
    (
        'Buenos Aires',
        '07',
        'plv_80_buenosaires',
        'buenosaires',
        '06',
        'C91_P2_Buenos_Aires',
        'P2-P_Buenos_Aires',
        'P1-P_Buenos_Aires',
        f'{POBLACION_FTP_URL}/c2022_bsas_est_c1_2.xlsx',
        f'{POBLACION_FTP_URL}/c2022_bsas_est_c4_2.xlsx',
    ),
    (
        'Catamarca',
        '10',
        'plv_80_catamarca',
        'catamarca',
        '10',
        'C91_P2_Catamarca',
        'P2-P_Catamarca',
        'P1-P_Catamarca',
        f'{POBLACION_FTP_URL}/c2022_catamarca_est_c1_3.xlsx',
        f'{POBLACION_FTP_URL}/c2022_catamarca_est_c4_3.xlsx',
    ),
    (
        'Chaco',
        '22',
        'plv_80_chaco',
        'chaco',
        '22',
        'C91_P2_Chaco',
        'P2-P_Chaco',
        'P1-P_Chaco',
        f'{POBLACION_FTP_URL}/c2022_chaco_est_c1_4.xlsx',
        f'{POBLACION_FTP_URL}/c2022_chaco_est_c4_4.xlsx',
    ),
    (
        'Chubut',
        '26',
        'plv_80_chubut',
        'chubut',
        '26',
        'C91_P2_Chubut',
        'P2-P_Chubut',
        'P1-P_Chubut',
        f'{POBLACION_FTP_URL}/c2022_chubut_est_c1_5.xlsx',
        f'{POBLACION_FTP_URL}/c2022_chubut_est_c4_5.xlsx',
    ),
    (
        'Córdoba',
        '14',
        'plv_80_cordoba',
        'cordoba',
        '14',
        'C91_P2_Cordoba',
        'P2-P_Cordoba',
        'P1-P_Cordoba',
        f'{POBLACION_FTP_URL}/c2022_cordoba_est_c1_6.xlsx',
        f'{POBLACION_FTP_URL}/c2022_cordoba_est_c4_6.xlsx',
    ),
    (
        'Corrientes',
        '18',
        'plv_80_corrientes',
        'corrientes',
        '18',
        'C91_P2_Corrientes',
        'P2-P_Corrientes',
        'P1-P_Corrientes',
        f'{POBLACION_FTP_URL}/c2022_corrientes_est_c1_7.xlsx',
        f'{POBLACION_FTP_URL}/c2022_corrientes_est_c4_7.xlsx',
    ),
    (
        'Entre Ríos',
        '30',
        'plv_80_entrerios',
        'entrerios',
        '30',
        'C91_P2_Entre_Rios',
        'P2-P_Entre_rios',
        'P1-P_Entre_rios',
        f'{POBLACION_FTP_URL}/c2022_entrerios_est_c1_8.xlsx',
        f'{POBLACION_FTP_URL}/c2022_entrerios_est_c4_8.xlsx',
    ),
    (
        'Formosa',
        '34',
        'plv_80_formosa',
        'formosa',
        '34',
        'C91_P2_Formosa',
        'P2-P_Formosa',
        'P1-P_Formosa',
        f'{POBLACION_FTP_URL}/c2022_formosa_est_c1_9.xlsx',
        f'{POBLACION_FTP_URL}/c2022_formosa_est_c4_9.xlsx',
    ),
    (
        'Jujuy',
        '38',
        'plv_80_jujuy',
        'jujuy',
        '38',
        'C91_P2_Jujuy',
        'P2-P_Jujuy',
        'P1-P_Jujuy',
        f'{POBLACION_FTP_URL}/c2022_jujuy_est_c1_10.xlsx',
        f'{POBLACION_FTP_URL}/c2022_jujuy_est_c4_10.xlsx',
    ),
    (
        'La Pampa',
        '42',
        'plv_80_lapampa',
        'lapampa',
        '42',
        'C91_P2_La_Pampa',
        'P2-P_La_pampa',
        'P1-P_La_pampa',
        f'{POBLACION_FTP_URL}/c2022_lapampa_est_c1_11.xlsx',
        f'{POBLACION_FTP_URL}/c2022_lapampa_est_c4_11.xlsx',
    ),
    (
        'La Rioja',
        '46',
        'plv_80_larioja',
        'larioja',
        '46',
        'C91_P2_La_Rioja',
        'P2-P_La_rioja',
        'P1-P_La_rioja',
        f'{POBLACION_FTP_URL}/c2022_larioja_est_c1_12.xlsx',
        f'{POBLACION_FTP_URL}/c2022_larioja_est_c4_12.xlsx',
    ),
    (
        'Mendoza',
        '50',
        'plv_80_mendoza',
        'mendoza',
        '50',
        'C91_P2_Mendoza',
        'P2-P_Mendoza',
        'P1-P_Mendoza',
        f'{POBLACION_FTP_URL}/c2022_mendoza_est_c1_13.xlsx',
        f'{POBLACION_FTP_URL}/c2022_mendoza_est_c4_13.xlsx',
    ),
    (
        'Misiones',
        '54',
        'plv_80_misiones',
        'misiones',
        '54',
        'C91_P2_Misiones',
        'P2-P_Misiones',
        'P1-P_Misiones',
        f'{POBLACION_FTP_URL}/c2022_misiones_est_c1_14.xlsx',
        f'{POBLACION_FTP_URL}/c2022_misiones_est_c4_14.xlsx',
    ),
    (
        'Neuquén',
        '58',
        'plv_80_neuquen',
        'neuquen',
        '58',
        'C91_P2_Neuquen',
        'P2-P_Neuquen',
        'P1-P_Neuquen',
        f'{POBLACION_FTP_URL}/c2022_neuquen_est_c1_15.xlsx',
        f'{POBLACION_FTP_URL}/c2022_neuquen_est_c4_15.xlsx',
    ),
    (
        'Río Negro',
        '62',
        'plv_80_rionegro',
        'rionegro',
        '62',
        'C91_P2_Rio_Negro',
        'P2-P_Rio_negro',
        'P1-P_Rio_negro',
        f'{POBLACION_FTP_URL}/c2022_rionegro_est_c1_16.xlsx',
        f'{POBLACION_FTP_URL}/c2022_rionegro_est_c4_16.xlsx',
    ),
    (
        'Salta',
        '66',
        'plv_80_salta',
        'salta',
        '66',
        'C91_P2_Salta',
        'P2-P_Salta',
        'P1-P_Salta',
        f'{POBLACION_FTP_URL}/c2022_salta_est_c1_17.xlsx',
        f'{POBLACION_FTP_URL}/c2022_salta_est_c4_17.xlsx',
    ),
    (
        'San Juan',
        '70',
        'plv_80_sanjuan',
        'sanjuan',
        '70',
        'C91_P2_San_Juan',
        'P2-P_San_juan',
        'P1-P_San_juan',
        f'{POBLACION_FTP_URL}/c2022_sanjuan_est_c1_18.xlsx',
        f'{POBLACION_FTP_URL}/c2022_sanjuan_est_c4_18.xlsx',
    ),
    (
        'San Luis',
        '74',
        'plv_80_sanluis',
        'sanluis',
        '74',
        'C91_P2_San_Luis',
        'P2-P_San_luis',
        'P1-P_San_luis',
        f'{POBLACION_FTP_URL}/c2022_sanluis_est_c1_19.xlsx',
        f'{POBLACION_FTP_URL}/c2022_sanluis_est_c4_19.xlsx',
    ),
    (
        'Santa Cruz',
        '78',
        'plv_80_santacruz',
        'santacruz',
        '78',
        'C91_P2_Santa_Cruz',
        'P2-P_Santa_cruz',
        'P1-P_Santa_cruz',
        f'{POBLACION_FTP_URL}/c2022_santacruz_est_c1_20.xlsx',
        f'{POBLACION_FTP_URL}/c2022_santacruz_est_c4_20.xlsx',
    ),
    (
        'Santa Fe',
        '82',
        'plv_80_santafe',
        'santafe',
        '82',
        'C91_P2_Santa_Fe',
        'P2-P_Santa_fe',
        'P1-P_Santa_fe',
        f'{POBLACION_FTP_URL}/c2022_santafe_est_c1_21.xlsx',
        f'{POBLACION_FTP_URL}/c2022_santafe_est_c4_21.xlsx',
    ),
    (
        'Santiago del Estero',
        '86',
        'plv_80_santiago',
        'santiago',
        '86',
        'C91_P2_Santiago_Del_Estero',
        'P2-P_Santiago_del_estero',
        'P1-P_Santiago_del_estero',
        f'{POBLACION_FTP_URL}/c2022_santiago_est_c1_22.xlsx',
        f'{POBLACION_FTP_URL}/c2022_santiago_est_c4_22.xlsx',
    ),
    (
        'Tierra del Fuego, Antártida e Islas del Atlántico Sur',
        '94',
        'plv_80_tierradelfuego',
        'tierradelfuego',
        '94',
        'C91_P2_Tierra_Del_Fuego',
        'P2-P_Tierra_del_fuego',
        'P1-P_Tierra_del_fuego',
        f'{POBLACION_FTP_URL}/c2022_tdf_est_c1_23.xlsx',
        f'{POBLACION_FTP_URL}/c2022_tdf_est_c4_23.xlsx',
    ),
    (
        'Tucumán',
        '90',
        'plv_80_tucuman',
        'tucuman',
        '90',
        'C91_P2_Tucuman',
        'P2-P_Tucuman',
        'P1-P_Tucuman',
        f'{POBLACION_FTP_URL}/c2022_tucuman_est_c1_24.xlsx',
        f'{POBLACION_FTP_URL}/c2022_tucuman_est_c4_24.xlsx',
    ),
]

VALID_AGES = ({'Total', '85 y más', '95 y más', '99 y más', '100 y más'} |
              {f'{i}-{i+4}' for i in range(0, 100, 5)} |
              {str(i) for i in range(100)})


def _strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')


def _norm_key(text: str) -> str:
    s = _strip_accents(text.strip().lower())
    s = re.sub(r'\(\d+\)', '', s)
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return s


PROVINCE_NORM_MAP = {_norm_key(j[0]): j[0] for j in JURISDICTIONS}
PROVINCE_NORM_MAP['tierra del fuego'] = (
    'Tierra del Fuego, Antártida e Islas del Atlántico Sur')


def create_session(retries: int = 3,
                   pool_maxsize: int = 16) -> requests.Session:
    """Creates a requests.Session with connection pooling and retry backoff."""
    session = requests.Session()
    session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (DataCommons-StatVarImporter)'})
    retry_strategy = Retry(
        total=retries,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET', 'HEAD'],
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_maxsize,
        pool_maxsize=pool_maxsize,
    )
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def fetch_url(url: str,
              session: requests.Session | None = None,
              retries: int = 3) -> bytes:
    """Downloads bytes from an HTTP/HTTPS URL with retries and validation."""
    own_session = session is None
    sess = session if session is not None else create_session(retries=retries)
    try:
        logging.info('GET %s', url)
        resp = sess.get(url, timeout=45)
        if resp.status_code != 200:
            raise RuntimeError(
                f'HTTP {resp.status_code} when downloading {url}')
        data = resp.content
        if not data or data[:15].lstrip().startswith((b'<!DOCTYPE', b'<html')):
            raise RuntimeError(
                f'Received HTML error or empty payload for {url}')
        return data
    finally:
        if own_session:
            sess.close()


def fetch_all_urls(urls: list[str], max_workers: int = 16) -> dict[str, bytes]:
    """Downloads a list of URLs concurrently and returns {url: bytes}."""
    unique_urls = sorted(set(urls))
    logging.info('Downloading %d unique files from INDEC...', len(unique_urls))
    results = {}
    with create_session(retries=3, pool_maxsize=max_workers) as session:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            fut_to_url = {
                executor.submit(fetch_url, u, session): u for u in unique_urls
            }
            for fut in as_completed(fut_to_url):
                url = fut_to_url[fut]
                results[url] = fut.result()
    logging.info('Successfully downloaded %d files.', len(results))
    return results


def _write_csv_atomically(target_path: str, header: list[str],
                          rows: list[tuple]) -> None:
    """Writes CSV rows atomically via a temporary file and verifies non-empty output."""
    if not rows:
        raise RuntimeError(f'Refusing to write empty dataset to {target_path}')
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    tmp_path = f'{target_path}.tmp'
    try:
        with open(tmp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise RuntimeError(f'Temporary CSV {tmp_path} is empty')
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def normalize_age_label(raw_val) -> str:
    """Normalizes an age cell value from INDEC tables."""
    if isinstance(raw_val, float):
        if raw_val.is_integer():
            return str(int(raw_val))
        return str(raw_val)
    if isinstance(raw_val, int):
        return str(raw_val)
    s = ' '.join(str(raw_val).strip().split())
    s = re.sub(r'\s*-\s*', '-', s)
    if s.lower().startswith('total'):
        return 'Total'
    if s in ('85 y mas', '85 y más'):
        return '85 y más'
    if s in ('95 y mas', '95 y más'):
        return '95 y más'
    if s in ('99 y mas', '99 y más'):
        return '99 y más'
    if s in ('100 y mas', '100 y más'):
        return '100 y más'
    return s


def fmt_num(val) -> str:
    """Formats a numeric value as integer or float string."""
    if val is None or val == '':
        return ''
    if isinstance(val, (int, float)):
        if float(val).is_integer():
            return str(int(round(float(val))))
        return str(round(float(val), 4))
    s = str(val).strip().replace(' ', '')
    if not s or s in ('-', '...', '///', 's/d'):
        return ''
    s = s.replace(',', '.')
    try:
        f = float(s)
        if f.is_integer():
            return str(int(round(f)))
        return str(round(f, 4))
    except ValueError:
        return ''


def parse_age_sex_sheet_xls(
        xls_bytes: bytes,
        fix_1991_70_74: bool = False) -> list[tuple[str, str, str, str]]:
    """Parses a standard INDEC P2/C61/c80b age-by-sex XLS sheet."""
    wb = xlrd.open_workbook(file_contents=xls_bytes)
    sh = wb.sheet_by_index(0)
    rows_out = []
    in_70_74_block = 0
    for rx in range(sh.nrows):
        raw_age = sh.cell_value(rx, 0)
        age = normalize_age_label(raw_age)
        v_tot = fmt_num(sh.cell_value(rx, 1)) if sh.ncols > 1 else ''
        v_male = fmt_num(sh.cell_value(rx, 2)) if sh.ncols > 2 else ''
        v_fem = fmt_num(sh.cell_value(rx, 3)) if sh.ncols > 3 else ''
        if not (v_tot or v_male or v_fem):
            continue
        if fix_1991_70_74:
            if age == '70-74':
                in_70_74_block = 1
                rows_out.append((age, v_tot, v_male, v_fem))
                continue
            elif 1 <= in_70_74_block <= 5:
                age = str(69 + in_70_74_block)
                in_70_74_block += 1
                rows_out.append((age, v_tot, v_male, v_fem))
                continue
        if age in VALID_AGES:
            rows_out.append((age, v_tot, v_male, v_fem))
    return rows_out


def parse_age_sex_2022_xlsx(
    xlsx_bytes: bytes,) -> list[tuple[str, str, str, str]]:
    """Parses 2022 Census Cuadro 4 XLSX (col 0=Edad, col 1=Total, col 2=Mujer, col 3=Varón)."""
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
    cuadro_sheets = [s for s in wb.sheetnames if s.lower().startswith('cuadro')]
    sh = wb[cuadro_sheets[0] if cuadro_sheets else wb.sheetnames[-1]]
    rows_out = []
    for row in sh.iter_rows(values_only=True):
        if not row or len(row) < 4:
            continue
        raw_age = row[0]
        if raw_age is None:
            continue
        age = normalize_age_label(raw_age)
        if age not in VALID_AGES:
            continue
        v_tot = fmt_num(row[1])
        v_fem = fmt_num(row[2])
        v_male = fmt_num(row[3])
        if v_tot or v_male or v_fem:
            rows_out.append((age, v_tot, v_male, v_fem))
    return rows_out


def extract_xls_from_zip(zip_bytes: bytes, suffix: str) -> bytes:
    """Finds and returns an XLS file inside a ZIP archive matching suffix."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if name.lower().endswith(suffix.lower()):
                return zf.read(name)
        norm_suffix = _strip_accents(suffix.lower())
        for name in zf.namelist():
            if _strip_accents(name.lower()).endswith(norm_suffix):
                return zf.read(name)
        if suffix.endswith('_g2.xls'):
            for name in zf.namelist():
                if name.lower().endswith('g2.xls'):
                    return zf.read(name)
    raise KeyError(f'Could not find {suffix} in zip archive')


def build_datasets(cache: dict[str, bytes], output_dir: str) -> None:
    """Extracts all 5 datasets from downloaded bytes into CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. Population by Age and Sex (1980, 1991, 2001, 2010, 2022)
    # -------------------------------------------------------------------------
    pop_rows = []
    for (
            j_name,
            code_2001,
            zip_1980,
            g2_1980,
            c02_1980,
            p2_1991,
            p2_2010,
            _,
            _,
            c4_url_2022,
    ) in JURISDICTIONS:
        # 1980
        zip_url = f'{BASE_FTP_URL}/cuadros/poblacion/{zip_1980}.zip'
        if c02_1980 is None:
            xls_1980 = extract_xls_from_zip(cache[zip_url],
                                            f'c80b_{g2_1980}_g2.xls')
        else:
            xls_1980 = extract_xls_from_zip(cache[zip_url],
                                            f'c80b_{c02_1980}_02.xls')
        for age, v_tot, v_male, v_fem in parse_age_sex_sheet_xls(xls_1980):
            pop_rows.append((age, '1980', j_name, v_tot, v_male, v_fem))

        # 1991
        url_1991 = f'{BASE_FTP_URL}/censos/1991/cuadrosDefinitivos/{p2_1991}.xls'
        for age, v_tot, v_male, v_fem in parse_age_sex_sheet_xls(
                cache[url_1991], fix_1991_70_74=(j_name == 'Total del país')):
            pop_rows.append((age, '1991', j_name, v_tot, v_male, v_fem))

        # 2001
        sub_2001 = 'nacionales' if code_2001 == '01' else 'provinciales'
        url_2001 = (
            f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000C61.xls'
        )
        for age, v_tot, v_male, v_fem in parse_age_sex_sheet_xls(
                cache[url_2001]):
            pop_rows.append((age, '2001', j_name, v_tot, v_male, v_fem))

        # 2010
        url_2010 = (
            f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/{p2_2010}.xls')
        for age, v_tot, v_male, v_fem in parse_age_sex_sheet_xls(
                cache[url_2010]):
            pop_rows.append((age, '2010', j_name, v_tot, v_male, v_fem))

        # 2022 (Refreshed)
        for age, v_tot, v_male, v_fem in parse_age_sex_2022_xlsx(
                cache[c4_url_2022]):
            pop_rows.append((age, '2022', j_name, v_tot, v_male, v_fem))

    pop_csv_path = os.path.join(output_dir, 'argentina_population.csv')
    _write_csv_atomically(
        pop_csv_path,
        [
            'Edad',
            'Year',
            'Jurisdiccion',
            'Total de poblacion',
            'Varones',
            'Mujeres',
        ],
        pop_rows,
    )
    logging.info('Wrote %d rows to %s', len(pop_rows), pop_csv_path)

    # -------------------------------------------------------------------------
    # 2. Urban and Rural Population (1980, 1991, 2001, 2010)
    # -------------------------------------------------------------------------
    ur_rows = []
    for (
            j_name,
            code_2001,
            zip_1980,
            g2_1980,
            _,
            _,
            _,
            _,
            _,
            _,
    ) in JURISDICTIONS:
        # 1980 Urban/Rural from c80b_{g2_1980}_g2.xls (cols 4..6 Urbana, 7..9 Rural)
        zip_url = f'{BASE_FTP_URL}/cuadros/poblacion/{zip_1980}.zip'
        xls_g2 = extract_xls_from_zip(cache[zip_url], f'c80b_{g2_1980}_g2.xls')
        wb = xlrd.open_workbook(file_contents=xls_g2)
        sh = wb.sheet_by_index(0)
        for rx in range(sh.nrows):
            age = normalize_age_label(sh.cell_value(rx, 0))
            if age not in VALID_AGES or sh.ncols < 10:
                continue
            u_tot, u_m, u_f = (
                fmt_num(sh.cell_value(rx, 4)),
                fmt_num(sh.cell_value(rx, 5)),
                fmt_num(sh.cell_value(rx, 6)),
            )
            r_tot, r_m, r_f = (
                fmt_num(sh.cell_value(rx, 7)),
                fmt_num(sh.cell_value(rx, 8)),
                fmt_num(sh.cell_value(rx, 9)),
            )
            if u_tot and u_m and u_f:
                ur_rows.append(('Urbana', age, '1980', j_name, u_tot, u_m, u_f))
            if r_tot and r_m and r_f:
                ur_rows.append(('Rural', age, '1980', j_name, r_tot, r_m, r_f))

        # 1991 Urban/Rural Total from {code_2001}000C101.xls
        sub_2001 = 'nacionales' if code_2001 == '01' else 'provinciales'
        url_c101 = f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000C101.xls'
        wb_101 = xlrd.open_workbook(file_contents=cache[url_c101])
        sh_101 = wb_101.sheet_by_index(0)
        for rx in range(sh_101.nrows):
            lbl = str(sh_101.cell_value(rx, 0)).strip().lower()
            val_1991 = fmt_num(sh_101.cell_value(rx, 1))
            if not val_1991:
                continue
            if lbl.startswith('urbana'):
                ur_rows.append(
                    ('Urbana', 'Total', '1991', j_name, val_1991, '', ''))
            elif lbl.startswith('rural'):
                ur_rows.append(
                    ('Rural', 'Total', '1991', j_name, val_1991, '', ''))

        # 2001 Urban/Rural by Age and Sex from C104 (Total), C105 (Varones), C106 (Mujeres)
        url_c104 = f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000C104.xls'
        url_c105 = f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000C105.xls'
        url_c106 = f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000C106.xls'
        sh_tot = xlrd.open_workbook(
            file_contents=cache[url_c104]).sheet_by_index(0)
        sh_m = xlrd.open_workbook(
            file_contents=cache[url_c105]).sheet_by_index(0)
        sh_f = xlrd.open_workbook(
            file_contents=cache[url_c106]).sheet_by_index(0)
        age_headers = ['Total'] + [
            normalize_age_label(sh_tot.cell_value(3, cx))
            for cx in range(2, sh_tot.ncols)
        ]
        for area_name, rx in [('Urbana', 6), ('Rural', 7)]:
            for idx_c, age in enumerate(age_headers, start=1):
                if not age:
                    continue
                vt = fmt_num(sh_tot.cell_value(rx, idx_c))
                vm = fmt_num(sh_m.cell_value(rx, idx_c))
                vf = fmt_num(sh_f.cell_value(rx, idx_c))
                if vt or vm or vf:
                    out_age = '0-1' if age == '1-4' else age
                    ur_rows.append(
                        (area_name, out_age, '2001', j_name, vt, vm, vf))

    # 2010 Urban/Rural Total from n020210.xls (Refreshed)
    url_ur_2010 = f'{BASE_FTP_URL}/cuadros/poblacion/n020210.xls'
    sh_ur10 = xlrd.open_workbook(
        file_contents=cache[url_ur_2010]).sheet_by_index(0)
    for rx in range(sh_ur10.nrows):
        raw_j = str(sh_ur10.cell_value(rx, 0)).strip()
        nk = _norm_key(raw_j)
        if nk in PROVINCE_NORM_MAP and sh_ur10.ncols >= 5:
            j_name = PROVINCE_NORM_MAP[nk]
            u_2010 = fmt_num(sh_ur10.cell_value(rx, 2))
            r_2010 = fmt_num(sh_ur10.cell_value(rx, 4))
            if u_2010:
                ur_rows.append(
                    ('Urbana', 'Total', '2010', j_name, u_2010, '', ''))
            if r_2010:
                ur_rows.append(
                    ('Rural', 'Total', '2010', j_name, r_2010, '', ''))

    ur_csv_path = os.path.join(output_dir, 'argentina_urban_rural.csv')
    _write_csv_atomically(
        ur_csv_path,
        [
            'Area',
            'Edad',
            'Year',
            'Jurisdiccion',
            'Total de poblacion',
            'Varones',
            'Mujeres',
        ],
        ur_rows,
    )
    logging.info('Wrote %d rows to %s', len(ur_rows), ur_csv_path)

    # -------------------------------------------------------------------------
    # 3. AA2 Department Population (2001, 2010, and Refreshed 2022)
    # -------------------------------------------------------------------------
    places_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'argentina_places_resolved.csv',
    )
    resolved_aa2_norm = {}
    if os.path.exists(places_path):
        with open(places_path, encoding='utf-8') as pf:
            for row in csv.DictReader(pf):
                pname = row.get('place_name') or row.get('name', '')
                if '__' in pname:
                    p_part, d_part = pname.split('__', 1)
                    resolved_aa2_norm[(p_part, _norm_key(d_part))] = pname

    aa2_rows = []
    for (
            j_name,
            _,
            _,
            _,
            _,
            _,
            _,
            p1_2010,
            c1_url_2022,
            _,
    ) in JURISDICTIONS:
        if not p1_2010:
            continue
        url_p1 = f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/{p1_2010}.xls'
        sh_p1 = xlrd.open_workbook(
            file_contents=cache[url_p1]).sheet_by_index(0)
        for rx in range(sh_p1.nrows):
            lbl = ' '.join(str(sh_p1.cell_value(rx, 0)).strip().split())
            if not lbl or lbl.lower().startswith((
                    'total',
                    'departamento',
                    'partido',
                    'fuente',
                    'nota',
                    '(',
                    '24 ',
                    'resto',
            )):
                continue
            v2001 = fmt_num(sh_p1.cell_value(rx, 1))
            v2010 = fmt_num(sh_p1.cell_value(rx, 2))
            if v2010 == '2010':
                continue
            if (j_name, _norm_key(lbl)) not in resolved_aa2_norm:
                continue
            dept_key = resolved_aa2_norm[(j_name, _norm_key(lbl))]
            if v2001:
                aa2_rows.append(('2001', dept_key, v2001))
            if v2010:
                aa2_rows.append(('2010', dept_key, v2010))

        # 2022 AA2 Department population
        if c1_url_2022:
            wb_c1 = openpyxl.load_workbook(io.BytesIO(cache[c1_url_2022]),
                                           data_only=True)
            c1_sheets = [
                s for s in wb_c1.sheetnames if s.lower().startswith('cuadro')
            ] or [wb_c1.sheetnames[-1]]
            seen_2022_depts = set()
            for sname in c1_sheets:
                sh_c1 = wb_c1[sname]
                for row in sh_c1.iter_rows(values_only=True):
                    if not row or len(row) < 4:
                        continue
                    raw_d = row[1] if row[1] is not None else row[0]
                    if raw_d is None:
                        continue
                    d_lbl = ' '.join(str(raw_d).strip().split())
                    nk = _norm_key(d_lbl)
                    if (j_name, nk) in resolved_aa2_norm:
                        dept_key = resolved_aa2_norm[(j_name, nk)]
                        if dept_key in seen_2022_depts:
                            continue
                        v2022 = (fmt_num(row[3]) if len(row) > 3 and
                                 fmt_num(row[3]) else fmt_num(row[2]))
                        if v2022 and v2022 not in ('2010', '2022'):
                            seen_2022_depts.add(dept_key)
                            aa2_rows.append(('2022', dept_key, v2022))

    aa2_csv_path = os.path.join(output_dir, 'argentina_population_aa2.csv')
    _write_csv_atomically(
        aa2_csv_path,
        ['Year', 'Jurisdiccion', 'Total de poblacion'],
        aa2_rows,
    )
    logging.info('Wrote %d rows to %s', len(aa2_rows), aa2_csv_path)

    # -------------------------------------------------------------------------
    # 4. Literacy / Illiteracy 10+ Years (2010)
    # -------------------------------------------------------------------------
    lit_rows = []
    url_p7 = f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/Total_pais/P7-P_Total_pais.xls'
    sh_p7 = xlrd.open_workbook(file_contents=cache[url_p7]).sheet_by_index(0)
    for rx in range(sh_p7.nrows):
        raw_j = ' '.join(str(sh_p7.cell_value(rx, 0)).strip().split())
        nk = _norm_key(raw_j)
        if nk in PROVINCE_NORM_MAP and sh_p7.ncols >= 6:
            j_name = PROVINCE_NORM_MAP[nk]
            v_tot10 = fmt_num(sh_p7.cell_value(rx, 1))
            v_lit = fmt_num(sh_p7.cell_value(rx, 2))
            v_illit = fmt_num(sh_p7.cell_value(rx, 5))
            if v_tot10 and v_lit and v_illit:
                v_pct = fmt_num(
                    round(float(v_illit) * 100.0 / float(v_tot10), 1))
                lit_rows.append(
                    ('2010', j_name, v_tot10, v_lit, v_illit, v_pct))

    lit_csv_path = os.path.join(output_dir, 'argentina_literacy.csv')
    _write_csv_atomically(
        lit_csv_path,
        [
            'Year',
            'Jurisdiccion',
            'Poblacion de 10 anos y mas',
            'Alfabetos',
            'Analfabetos',
            'Porcentaje de analfabetos',
        ],
        lit_rows,
    )
    logging.info('Wrote %d rows to %s', len(lit_rows), lit_csv_path)

    # -------------------------------------------------------------------------
    # 5. Infant Mortality Rate (2005-2023, refreshed from 2012-2019)
    # -------------------------------------------------------------------------
    im_rows = []
    url_im = f'{BASE_FTP_URL}/cuadros/sociedad/010506_2025.xlsx'
    wb_im = openpyxl.load_workbook(io.BytesIO(cache[url_im]), data_only=True)
    sh_im = wb_im[wb_im.sheetnames[0]]
    im_matrix = list(sh_im.iter_rows(values_only=True))
    years_im = []
    for row in im_matrix[:10]:
        yr_candidates = [(idx, fmt_num(c))
                         for idx, c in enumerate(row)
                         if len(fmt_num(c)) == 4 and fmt_num(c).isdigit() and
                         int(fmt_num(c)) >= 2000]
        if len(yr_candidates) >= 5:
            years_im = yr_candidates
            break

    for row in im_matrix:
        if not row or row[0] is None:
            continue
        nk = _norm_key(str(row[0]))
        if nk in PROVINCE_NORM_MAP:
            j_name = PROVINCE_NORM_MAP[nk]
            for col_idx, yr_str in years_im:
                if col_idx < len(row):
                    val = fmt_num(row[col_idx])
                    if val:
                        im_rows.append((yr_str, j_name, val))

    im_csv_path = os.path.join(output_dir, 'argentina_infant_mortality.csv')
    _write_csv_atomically(
        im_csv_path,
        ['Year', 'Jurisdiccion', 'Tasa de mortalidad infantil'],
        im_rows,
    )
    logging.info('Wrote %d rows to %s', len(im_rows), im_csv_path)


def collect_required_urls() -> list[str]:
    """Returns the complete list of INDEC source URLs required."""
    urls = [
        f'{BASE_FTP_URL}/cuadros/poblacion/n020210.xls',
        f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/Total_pais/P7-P_Total_pais.xls',
        f'{BASE_FTP_URL}/cuadros/sociedad/010506_2025.xlsx',
    ]
    for (
            _,
            code_2001,
            zip_1980,
            _,
            _,
            p2_1991,
            p2_2010,
            p1_2010,
            c1_url_2022,
            c4_url_2022,
    ) in JURISDICTIONS:
        urls.append(f'{BASE_FTP_URL}/cuadros/poblacion/{zip_1980}.zip')
        urls.append(
            f'{BASE_FTP_URL}/censos/1991/cuadrosDefinitivos/{p2_1991}.xls')
        sub_2001 = 'nacionales' if code_2001 == '01' else 'provinciales'
        for tbl in ('C61', 'C101', 'C104', 'C105', 'C106'):
            urls.append(
                f'{BASE_FTP_URL}/censos/2001/{sub_2001}/Datos/{code_2001}000{tbl}.xls'
            )
        urls.append(
            f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/{p2_2010}.xls')
        if p1_2010:
            urls.append(
                f'{BASE_FTP_URL}/censos/2010/CuadrosDefinitivos/{p1_2010}.xls')
        if c1_url_2022:
            urls.append(c1_url_2022)
        if c4_url_2022:
            urls.append(c4_url_2022)
    return urls


def main(_):
    try:
        urls = collect_required_urls()
        cache = fetch_all_urls(urls, max_workers=FLAGS.max_workers)
        build_datasets(cache, FLAGS.output_dir)
    except Exception as e:  # pylint: disable=broad-except
        logging.fatal('Failed to download and build Argentina Census data: %s',
                      e)


if __name__ == '__main__':
    app.run(main)
