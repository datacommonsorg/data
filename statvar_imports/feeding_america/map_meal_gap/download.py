#!/usr/bin/env python3
"""Downloads Feeding America Map the Meal Gap data (2020+) from map.feedingamerica.org/mapdata and merges with 2018-2019 baseline."""

import csv
import html
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_HOME_URL = 'https://map.feedingamerica.org/'
MAPDATA_URL = 'https://map.feedingamerica.org/mapdata?maptype=county&year={year}&type={dtype}'
BASELINE_GCS = 'gs://unresolved_mcf/feeding_america/map_meal_gap/input_files/FeedingAmerica_MMG_baseline_2018_2019.csv'
BASELINE_LOCAL = os.path.join(_SCRIPT_DIR, 'input_files',
                              'FeedingAmerica_MMG_baseline_2018_2019.csv')
OUTPUT_INPUT_CSV = os.path.join(_SCRIPT_DIR, 'input_files',
                                'feedingamerica_mapmealgap_input.csv')
DEFAULT_YEARS = ['2020', '2021', '2022', '2023', '2024']
MAX_RETRIES = 5

FIELDNAMES = [
    'dcid',
    'observationDate',
    'Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_EligibleForAllFederalBenefits',
    'Count_Person_FoodInsecure_EligibleForSomeFederalBenefits',
    'Count_Person_FoodInsecure_IneligibleForFederalBenefits',
    'Count_Child_FoodInsecure',
    'Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits',
    'Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits',
    'Mean_MealCost_Person_FoodSecure',
    'Annual_FoodBudgetShortfall',
]


def fetch_json(url, max_retries=MAX_RETRIES):
    """Fetches JSON from url with exponential backoff on transient HTTP/network errors."""
    last_err = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (DataCommons Import)',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError) as e:
            last_err = e
            wait_secs = 2**attempt
            print(
                f'Warning: request to {url} failed (attempt {attempt + 1}/{max_retries}: {e});'
                f' retrying in {wait_secs}s...')
            time.sleep(wait_secs)
    raise RuntimeError(
        f'Failed to fetch {url} after {max_retries} attempts: {last_err}'
    ) from last_err


def discover_years():
    years = set(DEFAULT_YEARS)
    try:
        req = urllib.request.Request(
            MAP_HOME_URL,
            headers={'User-Agent': 'Mozilla/5.0 (DataCommons Import)'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            page = resp.read().decode('utf-8', errors='ignore')
        m = re.search(
            r'data-page="app"\s+type="application/json">(.*?)</script>', page)
        if not m:
            m = re.search(r'data-page="([^"]+)"', page)
            payload = json.loads(html.unescape(m.group(1))) if m else {}
        else:
            payload = json.loads(m.group(1))
        for item in payload.get('props', {}).get('filters',
                                                 {}).get('years', []):
            yr = str(item.get('year', '')).strip()
            if yr.isdigit() and int(yr) >= 2020:
                years.add(yr)
    except Exception as e:
        print(f'Warning: dynamic year discovery fallback to defaults ({e})')
    return sorted(years)


def _to_float(val):
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        print(f'Warning: ignoring non-numeric value {val!r}')
        return None


def resolve_bands(low_band, mid_band, high_band):
    """Restores 0.0 when the complementary band(s) sum to 100% (1.0) and API serialized 0% as null."""
    low_val = _to_float(low_band)
    mid_val = _to_float(mid_band)
    high_val = _to_float(high_band)
    if high_val is None and low_val is not None:
        if round(low_val + (mid_val or 0.0), 4) >= 0.999:
            high_val = 0.0
    if low_val is None and high_val is not None:
        if round(high_val + (mid_val or 0.0), 4) >= 0.999:
            low_val = 0.0
    return low_val, mid_val, high_val


def compute_product(pop, band):
    pop_val = _to_float(pop)
    band_val = _to_float(band)
    if pop_val is None or band_val is None:
        return ''
    return round(pop_val * band_val, 2)


def format_dcid(level, fips):
    if not fips or not str(fips).strip().isdigit():
        return None
    code = int(str(fips).strip())
    if level == 'state':
        return f'dcid:geoId/{code:02d}'
    elif level == 'county':
        return f'dcid:geoId/{code:05d}'
    return None


def ensure_baseline():
    os.makedirs(os.path.join(_SCRIPT_DIR, 'input_files'), exist_ok=True)
    if not os.path.exists(BASELINE_LOCAL):
        if shutil.which('gsutil'):
            subprocess.run(['gsutil', 'cp', BASELINE_GCS, BASELINE_LOCAL],
                           check=True)
        else:
            raise FileNotFoundError(
                f'Baseline file {BASELINE_LOCAL} is missing and gsutil is not '
                'available to download it.')
    if not os.path.exists(BASELINE_LOCAL):
        raise FileNotFoundError(
            f'Baseline file {BASELINE_LOCAL} is missing after download.')


def main():
    ensure_baseline()
    rows_by_key = {}

    # 1. Load 2018-2019 historical baseline verbatim
    with open(BASELINE_LOCAL, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dcid = row['dcid'].strip()
            if not dcid.startswith('dcid:'):
                dcid = f'dcid:{dcid}'
            row['dcid'] = dcid
            year = row['observationDate'].strip()
            rows_by_key[(dcid, year)] = {k: row.get(k, '') for k in FIELDNAMES}

    # 2. Fetch 2020+ data live from map.feedingamerica.org/mapdata
    for year in discover_years():
        overall_data = fetch_json(MAPDATA_URL.format(year=year,
                                                     dtype='overall'))
        child_data = fetch_json(MAPDATA_URL.format(year=year, dtype='child'))

        for level in ('state', 'county'):
            overall_by_fips = {
                str(item.get('fips')).strip(): item
                for item in overall_data.get(level, [])
                if item.get('fips')
            }
            child_by_fips = {
                str(item.get('fips')).strip(): item
                for item in child_data.get(level, [])
                if item.get('fips')
            }
            for fips in sorted(set(overall_by_fips) | set(child_by_fips)):
                dcid = format_dcid(level, fips)
                if not dcid:
                    continue
                ov = overall_by_fips.get(fips, {})
                ch = child_by_fips.get(fips, {})
                ov_pop = ov.get('population')
                ch_pop = ch.get('population')
                ov_low, ov_mid, ov_high = resolve_bands(ov.get('low_band'),
                                                        ov.get('mid_band'),
                                                        ov.get('high_band'))
                ch_low, _, ch_high = resolve_bands(ch.get('low_band'), None,
                                                   ch.get('high_band'))
                cost_val = _to_float(ov.get('cost_per_meal'))
                rows_by_key[(dcid, year)] = {
                    'dcid':
                        dcid,
                    'observationDate':
                        year,
                    'Count_Person_FoodInsecure':
                        '' if ov_pop is None else ov_pop,
                    'Count_Person_FoodInsecure_EligibleForAllFederalBenefits':
                        (compute_product(ov_pop, ov_low)),
                    'Count_Person_FoodInsecure_EligibleForSomeFederalBenefits':
                        (compute_product(ov_pop, ov_mid)),
                    'Count_Person_FoodInsecure_IneligibleForFederalBenefits':
                        (compute_product(ov_pop, ov_high)),
                    'Count_Child_FoodInsecure':
                        '' if ch_pop is None else ch_pop,
                    'Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits':
                        (compute_product(ch_pop, ch_low)),
                    'Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits':
                        (compute_product(ch_pop, ch_high)),
                    'Mean_MealCost_Person_FoodSecure':
                        ('' if cost_val is None else round(cost_val, 2)),
                    'Annual_FoodBudgetShortfall':
                        ('' if ov.get('money_needed') is None else
                         ov.get('money_needed')),
                }

    with open(OUTPUT_INPUT_CSV, 'w', newline='', encoding='utf-8') as out_fp:
        writer = csv.DictWriter(out_fp, fieldnames=FIELDNAMES)
        writer.writeheader()
        for (_, _), row in sorted(rows_by_key.items()):
            writer.writerow(row)
    print(f'Wrote {len(rows_by_key)} rows to {OUTPUT_INPUT_CSV}')


if __name__ == '__main__':
    main()
