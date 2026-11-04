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
"""Downloads and processes BEA GDP and Regional Price Parity (RPP) datasets.

Consolidates County & Metro Real/Nominal GDP, Real GDP Growth Rate, and
State & Metro Regional Price Parities (CAGDP1, CAGDP11, MARPP, SARPP) into
a single standardized CSV for Data Commons ingestion.
"""

import csv
import io
import os
import time
from typing import Dict, List, Optional, Tuple
import urllib.error
import urllib.request
import zipfile

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'input_dir',
    'input_files',
    'Directory containing raw BEA ZIP files (or where to download them) '
    'and optional cns_baseline directory.',
)
flags.DEFINE_string(
    'output_csv',
    'output/bea_gdp_rpp.csv',
    'Output CSV file path.',
)
flags.DEFINE_bool(
    'download',
    False,
    'Whether to download BEA ZIP files if not already present in input_dir.',
)

BEA_URLS = {
    'CAGDP1.zip': 'https://apps.bea.gov/regional/zip/CAGDP1.zip',
    'CAGDP11.zip': 'https://apps.bea.gov/regional/zip/CAGDP11.zip',
    'MARPP.zip': 'https://apps.bea.gov/regional/zip/MARPP.zip',
    'SARPP.zip': 'https://apps.bea.gov/regional/zip/SARPP.zip',
}

RPP_LINE_CODE_TO_SV = {
    '1': 'dcid:RegionalPriceParity_AllItems',
    '2': 'dcid:RegionalPriceParity_Goods',
    '3': 'dcid:RegionalPriceParity_Services_Rents',
    '4': 'dcid:RegionalPriceParity_Services_Other',
    '5': 'dcid:RegionalPriceParity_Services_Housing',
}

# Key: (observationAbout, variableMeasured, observationDate, measurementMethod, unit)
RecordKey = Tuple[str, str, str, str, str]

OUTPUT_COLUMNS = [
    'observationAbout',
    'variableMeasured',
    'observationDate',
    'value',
    'measurementMethod',
    'unit',
]


def is_valid_value(raw_val: Optional[str]) -> bool:
    """Returns True if raw_val is a valid numeric observation."""
    if raw_val is None:
        return False
    val = raw_val.strip()
    if not val:
        return False
    if val.startswith('(') and val.endswith(')'):
        return False
    try:
        float(val.replace(',', ''))
        return True
    except ValueError:
        return False


def format_number(val: float) -> str:
    """Formats a float cleanly without unnecessary trailing .0 for integers."""
    if val.is_integer():
        return str(int(val))
    return f'{val:.6f}'.rstrip('0').rstrip('.')


def normalize_county_or_state_geofips(raw_geofips: str) -> Optional[str]:
    """Normalizes BEA GeoFIPS from CAGDP/SARPP into Data Commons place DCID."""
    geofips = raw_geofips.strip().strip('"').strip()
    if not geofips or not geofips.isdigit():
        return None
    if geofips == '00000':
        return 'dcid:country/USA'
    if len(geofips) == 5 and geofips.endswith('000'):
        state_code = int(geofips[:2])
        if 1 <= state_code <= 56:
            return f'dcid:geoId/{geofips[:2]}'
        return None
    if len(geofips) == 5:
        state_code = int(geofips[:2])
        if 1 <= state_code <= 56:
            return f'dcid:geoId/{geofips}'
    return None


def normalize_msa_geofips(raw_geofips: str) -> Optional[str]:
    """Normalizes BEA MSA GeoFIPS from MARPP into Data Commons MSA DCID."""
    geofips = raw_geofips.strip().strip('"').strip()
    if not geofips or not geofips.isdigit():
        return None
    if geofips == '00000':
        return None
    if len(geofips) == 5:
        return f'dcid:geoId/C{geofips}'
    return None


def normalize_place_dcid(raw_place: str, is_msa: bool = False) -> Optional[str]:
    """Normalizes a baseline geoId/GeoFips string into a dcid: prefixed string."""
    place = (raw_place or '').strip().strip('"').strip()
    if not place:
        return None
    if place.startswith('dcid:'):
        return place
    if place.startswith('geoId/') or place.startswith('country/'):
        return f'dcid:{place}'
    if place.startswith('C') and len(place) == 6 and place[1:].isdigit():
        return f'dcid:geoId/{place}'
    if is_msa and len(place) == 5 and place.isdigit():
        return f'dcid:geoId/C{place}'
    if len(place) in (2, 5) and place.isdigit():
        return f'dcid:geoId/{place}'
    return None


def get_year_columns(fieldnames: List[str]) -> List[str]:
    """Returns sorted 4-digit year columns from a CSV header."""
    years = []
    for col in fieldnames:
        if col and col.strip().isdigit() and len(col.strip()) == 4:
            years.append(col.strip())
    return sorted(years)


def read_csv_from_zip_or_dir(input_dir: str, zip_name: str,
                             file_prefix: str) -> List[csv.DictReader]:
    """Opens matching CSV file(s) from either a ZIP archive or extracted dir."""
    readers = []
    zip_path = os.path.join(input_dir, zip_name)
    if os.path.exists(zip_path) and zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            all_areas = [
                name for name in zf.namelist() if
                name.upper().endswith('.CSV') and 'ALL_AREAS' in name.upper()
            ]
            target_names = (all_areas if all_areas else [
                name for name in zf.namelist()
                if name.upper().endswith('.CSV') and
                os.path.basename(name).upper().startswith(file_prefix.upper())
            ])
            for name in sorted(target_names):
                raw_bytes = zf.read(name)
                text = raw_bytes.decode('latin-1')
                readers.append(csv.DictReader(io.StringIO(text)))
        return readers

    if os.path.isdir(input_dir):
        for fname in sorted(os.listdir(input_dir)):
            if fname.upper().endswith('.CSV') and fname.upper().startswith(
                    file_prefix.upper()):
                fpath = os.path.join(input_dir, fname)
                with open(fpath, 'r', encoding='latin-1') as f:
                    text = f.read()
                readers.append(csv.DictReader(io.StringIO(text)))
    return readers


def process_cagdp1(input_dir: str, records: Dict[RecordKey, str]) -> int:
    """Processes CAGDP1 (Real GDP LineCode 1 and Nominal GDP LineCode 3)."""
    count = 0
    readers = read_csv_from_zip_or_dir(input_dir, 'CAGDP1.zip', 'CAGDP1')
    for reader in readers:
        if not reader.fieldnames:
            continue
        year_cols = get_year_columns(list(reader.fieldnames))
        for row in reader:
            place = normalize_county_or_state_geofips(row.get('GeoFIPS', ''))
            if not place:
                continue
            line_code = (row.get('LineCode') or '').strip()
            if line_code not in ('1', '3'):
                continue
            for yr in year_cols:
                raw_val = row.get(yr, '')
                if not is_valid_value(raw_val):
                    continue
                scaled_val = float(raw_val.strip().replace(',', '')) * 1000.0
                formatted_val = format_number(scaled_val)
                if line_code == '1':
                    # Emit both schema.org Real GDP and StatisticalVariable dc/c3wwfwyx45v5h
                    key1 = (
                        place,
                        'dcs:grossDomesticProduct',
                        yr,
                        'dcs:BEASurvey',
                        'dcs:USDollar',
                    )
                    records[key1] = formatted_val
                    key2 = (
                        place,
                        'dcid:dc/c3wwfwyx45v5h',
                        yr,
                        'dcs:BEASurvey',
                        'dcs:USDollar',
                    )
                    records[key2] = formatted_val
                    count += 2
                elif line_code == '3':
                    key = (
                        place,
                        'dcs:nominalGrossDomesticProduct',
                        yr,
                        'dcs:BEAGDPMeasure',
                        'dcs:USDollar',
                    )
                    records[key] = formatted_val
                    count += 1
    return count


def process_cagdp11(input_dir: str, records: Dict[RecordKey, str]) -> int:
    """Processes CAGDP11 (Real GDP Growth Rate LineCode 1)."""
    count = 0
    readers = read_csv_from_zip_or_dir(input_dir, 'CAGDP11.zip', 'CAGDP11')
    for reader in readers:
        if not reader.fieldnames:
            continue
        year_cols = get_year_columns(list(reader.fieldnames))
        for row in reader:
            place = normalize_county_or_state_geofips(row.get('GeoFIPS', ''))
            if not place:
                continue
            line_code = (row.get('LineCode') or '').strip()
            if line_code != '1':
                continue
            for yr in year_cols:
                raw_val = row.get(yr, '')
                if not is_valid_value(raw_val):
                    continue
                val = float(raw_val.strip().replace(',', ''))
                formatted_val = format_number(val)
                key = (
                    place,
                    'dcid:dc/p9w3tzjzyqrr',
                    yr,
                    'dcs:BEASurvey',
                    '',
                )
                records[key] = formatted_val
                count += 1
    return count


def process_rpp_zip(
    input_dir: str,
    zip_name: str,
    file_prefix: str,
    is_msa: bool,
    records: Dict[RecordKey, str],
) -> int:
    """Processes MARPP (MSA RPP) or SARPP (State RPP) LineCodes 1..5."""
    count = 0
    readers = read_csv_from_zip_or_dir(input_dir, zip_name, file_prefix)
    for reader in readers:
        if not reader.fieldnames:
            continue
        year_cols = get_year_columns(list(reader.fieldnames))
        for row in reader:
            table_name = (row.get('TableName') or '').strip().upper()
            if table_name and table_name not in ('MARPP', 'SARPP'):
                continue
            raw_geofips = row.get('GeoFIPS', '')
            place = (normalize_msa_geofips(raw_geofips) if is_msa else
                     normalize_county_or_state_geofips(raw_geofips))
            if not place or place == 'dcid:country/USA':
                continue
            line_code = (row.get('LineCode') or '').strip()
            sv = RPP_LINE_CODE_TO_SV.get(line_code)
            if not sv:
                continue
            for yr in year_cols:
                raw_val = row.get(yr, '')
                if not is_valid_value(raw_val):
                    continue
                val = float(raw_val.strip().replace(',', ''))
                key = (place, sv, yr, '', '')
                records[key] = format_number(val)
                count += 1
    return count


def _open_dict_reader_auto_delim(
    path: str,) -> Tuple[csv.DictReader, io.TextIOBase]:
    """Opens a CSV/TSV file and auto-detects tab vs comma delimiter."""
    f = open(path, 'r', encoding='utf-8')
    first_line = f.readline()
    f.seek(0)
    delim = '\t' if '\t' in first_line else ','
    return csv.DictReader(f, delimiter=delim), f


def load_cns_baseline(baseline_dir: str, records: Dict[RecordKey, str]) -> int:
    """Loads optional CNS baseline CSVs so historical series are preserved."""
    if not os.path.isdir(baseline_dir):
        return 0
    count = 0

    # 1. county_gdp_all.csv
    county_gdp_path = os.path.join(baseline_dir, 'county_gdp_all.csv')
    if os.path.exists(county_gdp_path):
        reader, f = _open_dict_reader_auto_delim(county_gdp_path)
        with f:
            for row in reader:
                naics = (row.get('naics') or '').strip()
                line_code = (row.get('LineCode') or '').strip()
                if naics and naics != 'NAICS/10':
                    continue
                if line_code and line_code != '1':
                    continue
                place = normalize_place_dcid(
                    row.get('geoid') or row.get('GeoFips') or '')
                yr = (row.get('year') or row.get('Year') or '').strip()
                val_str = (row.get('grossDomesticProduct') or
                           row.get('GrossDomesticProduct') or '').strip()
                if not place or not yr or not is_valid_value(val_str):
                    continue
                val = float(val_str.replace(',', ''))
                # Legacy GeoFips format is in thousands; CNS geoid format is in dollars
                if 'GeoFips' in row and 'geoid' not in row:
                    val *= 1000.0
                records[(
                    place,
                    'dcs:grossDomesticProduct',
                    yr,
                    'dcs:BEASurvey',
                    'dcs:USDollar',
                )] = format_number(val)
                count += 1

    # 2. county_gdp_growth_all.csv
    county_growth_path = os.path.join(baseline_dir, 'county_gdp_growth_all.csv')
    if os.path.exists(county_growth_path):
        reader, f = _open_dict_reader_auto_delim(county_growth_path)
        with f:
            for row in reader:
                naics = (row.get('naics') or '').strip()
                line_code = (row.get('LineCode') or '').strip()
                if naics and naics != 'NAICS/10':
                    continue
                if line_code and line_code != '1':
                    continue
                place = normalize_place_dcid(
                    row.get('geoid') or row.get('GeoFips') or '')
                yr = (row.get('year') or row.get('Year') or '').strip()
                val_str = (row.get('growthRate') or
                           row.get('GrossDomesticProductGrowth') or '').strip()
                if not place or not yr or not is_valid_value(val_str):
                    continue
                val = float(val_str.replace(',', ''))
                records[(
                    place,
                    'dcid:dc/p9w3tzjzyqrr',
                    yr,
                    'dcs:BEASurvey',
                    '',
                )] = format_number(val)
                count += 1

    # 3. metro_gdp.csv
    metro_gdp_path = os.path.join(baseline_dir, 'metro_gdp.csv')
    if os.path.exists(metro_gdp_path):
        reader, f = _open_dict_reader_auto_delim(metro_gdp_path)
        with f:
            for row in reader:
                line_code = (row.get('LineCode') or '').strip()
                if line_code and line_code != '1':
                    continue
                place = normalize_place_dcid(row.get('geoid') or
                                             row.get('GeoFips') or '',
                                             is_msa=True)
                yr = (row.get('year') or row.get('Year') or '').strip()
                gdp_str = (row.get('grossDomesticProduct') or
                           row.get('GrossDomesticProduct') or '').strip()
                growth_str = (row.get('growthRate') or row.get('GrowthRate') or
                              '').strip()
                if not place or not yr:
                    continue
                has_gdp = is_valid_value(gdp_str)
                has_growth = is_valid_value(growth_str)
                if has_gdp:
                    gdp_val = float(gdp_str.replace(',', ''))
                    if 'GeoFips' in row and 'geoid' not in row:
                        gdp_val *= 1000.0
                    formatted_gdp = format_number(gdp_val)
                    if has_growth:
                        records[(
                            place,
                            'dcid:dc/c3wwfwyx45v5h',
                            yr,
                            'dcs:BEASurvey',
                            'dcs:USDollar',
                        )] = formatted_gdp
                        records[(
                            place,
                            'dcs:grossDomesticProduct',
                            yr,
                            'dcs:BEASurvey',
                            'dcs:USDollar',
                        )] = formatted_gdp
                        count += 2
                    else:
                        records[(
                            place,
                            'dcs:grossDomesticProduct',
                            yr,
                            'dcs:BEASurvey',
                            'dcs:USDollar',
                        )] = formatted_gdp
                        count += 1
                if has_growth:
                    growth_val = float(growth_str.replace(',', ''))
                    records[(
                        place,
                        'dcid:dc/p9w3tzjzyqrr',
                        yr,
                        'dcs:BEASurvey',
                        'dcs:USDollar',
                    )] = format_number(growth_val)
                    count += 1

    # 4. metro_nominal_gdp.csv
    metro_nom_path = os.path.join(baseline_dir, 'metro_nominal_gdp.csv')
    if os.path.exists(metro_nom_path):
        reader, f = _open_dict_reader_auto_delim(metro_nom_path)
        with f:
            for row in reader:
                line_code = (row.get('LineCode') or '').strip()
                if line_code and line_code != '1':
                    continue
                place = normalize_place_dcid(row.get('geoid') or
                                             row.get('GeoFips') or '',
                                             is_msa=True)
                yr = (row.get('year') or row.get('Year') or '').strip()
                gdp_str = (row.get('grossDomesticProduct') or
                           row.get('GrossDomesticProduct') or '').strip()
                if not place or not yr or not is_valid_value(gdp_str):
                    continue
                gdp_val = float(gdp_str.replace(',', ''))
                if 'GeoFips' in row and 'geoid' not in row:
                    gdp_val *= 1000.0
                records[(
                    place,
                    'dcs:nominalGrossDomesticProduct',
                    yr,
                    'dcs:BEAGDPMeasure',
                    'dcs:USDollar',
                )] = format_number(gdp_val)
                count += 1

    # 5. marpp_clean.csv
    marpp_path = os.path.join(baseline_dir, 'marpp_clean.csv')
    if os.path.exists(marpp_path):
        reader, f = _open_dict_reader_auto_delim(marpp_path)
        with f:
            for row in reader:
                place = normalize_place_dcid(row.get('geoId') or '')
                sv = (row.get('consumable') or '').strip()
                yr = (row.get('year') or '').strip()
                val_str = (row.get('data') or '').strip()
                if not place or not sv or not yr or not is_valid_value(val_str):
                    continue
                if not sv.startswith('dcid:'):
                    sv = f'dcid:{sv}'
                val = float(val_str.replace(',', ''))
                records[(place, sv, yr, '', '')] = format_number(val)
                count += 1

    return count


def _download_with_retries(
    url: str,
    target_path: str,
    max_retries: int = 3,
    timeout_secs: int = 120,
) -> int:
    """Downloads url to target_path with exponential backoff retries."""
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0 DataCommons/1.0'})
            with urllib.request.urlopen(req, timeout=timeout_secs) as resp:
                data = resp.read()
            if not data:
                raise RuntimeError(f'Empty response body downloaded from {url}')
            with open(target_path, 'wb') as out_f:
                out_f.write(data)
            return len(data)
        except (urllib.error.URLError, OSError, RuntimeError) as err:
            last_err = err
            wait_secs = 2**attempt
            logging.warning(
                'Attempt %d/%d failed for %s (%s); retrying in %ds...',
                attempt + 1,
                max_retries,
                url,
                err,
                wait_secs,
            )
            if attempt + 1 < max_retries:
                time.sleep(wait_secs)
    raise RuntimeError(
        f'Failed to download {url} after {max_retries} attempts: {last_err}')


def download_missing_zips(input_dir: str) -> None:
    """Downloads BEA ZIP files into input_dir if not already present."""
    os.makedirs(input_dir, exist_ok=True)
    for zip_name, url in BEA_URLS.items():
        target_path = os.path.join(input_dir, zip_name)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            logging.info('Using existing %s', target_path)
            continue
        logging.info('Downloading %s from %s ...', zip_name, url)
        num_bytes = _download_with_retries(url, target_path)
        logging.info('Downloaded %s (%d bytes)', target_path, num_bytes)


def process_all(input_dir: str, output_csv: str, download: bool = False) -> int:
    """Runs the full BEA GDP & RPP processing pipeline and writes output_csv."""
    if download:
        download_missing_zips(input_dir)

    records: Dict[RecordKey, str] = {}
    baseline_dir = os.path.join(input_dir, 'cns_baseline')
    baseline_count = load_cns_baseline(baseline_dir, records)
    logging.info('Loaded %d records from CNS baseline.', baseline_count)

    cagdp1_count = process_cagdp1(input_dir, records)
    logging.info('Processed %d records from CAGDP1.', cagdp1_count)

    cagdp11_count = process_cagdp11(input_dir, records)
    logging.info('Processed %d records from CAGDP11.', cagdp11_count)

    marpp_count = process_rpp_zip(input_dir,
                                  'MARPP.zip',
                                  'MARPP',
                                  is_msa=True,
                                  records=records)
    logging.info('Processed %d records from MARPP.', marpp_count)

    sarpp_count = process_rpp_zip(input_dir,
                                  'SARPP.zip',
                                  'SARPP',
                                  is_msa=False,
                                  records=records)
    logging.info('Processed %d records from SARPP.', sarpp_count)

    if not records:
        raise RuntimeError(
            f'No valid BEA GDP/RPP records produced from {input_dir}')

    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for key in sorted(records.keys()):
            place, sv, yr, mm, unit = key
            writer.writerow({
                'observationAbout': place,
                'variableMeasured': sv,
                'observationDate': yr,
                'value': records[key],
                'measurementMethod': mm,
                'unit': unit,
            })

    logging.info('Wrote %d unique records to %s', len(records), output_csv)
    return len(records)


def main(_):
    process_all(FLAGS.input_dir, FLAGS.output_csv, download=FLAGS.download)


if __name__ == '__main__':
    app.run(main)
