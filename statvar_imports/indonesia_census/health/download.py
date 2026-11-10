# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads Indonesia Census — 2. Health datasets from BPS WebAPI.

Covers the four Health sub-domains:
  1. Mortality (Life Expectancy by Regency/City & Gender, Infant Mortality Rate)
  2. Disease (Disease Cases by Type, Malaria Incidence, Tuberculosis Incidence,
     AIDS Cases & Deaths, Health Complaints)
  3. Risk Factors (Smoked Tobacco, Obesity by Urban/Rural, Obesity by Gender,
     Contraception Method)
  4. Utilization (Hospitals & Public Health Centers, Outpatient Treatment by
     Gender & Facility Type, Unmet Need of Health Services)

Uses the common Data Commons download utility (util/download_util.py) to query
the BPS WebAPI (https://webapi.bps.go.id/v1/api) and serialize CSV files into
input_files/.
"""

import csv
import html
from html.parser import HTMLParser
import os
import re
import sys

from absl import app
from absl import flags
from absl import logging

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

import download_util  # pylint: disable=wrong-import-position

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'output_dir',
    os.path.join(_CODEDIR, 'input_files'),
    'Output directory for downloaded CSV files.',
)
flags.DEFINE_string('domain', '0000',
                    'BPS domain code (0000 for national/provincial).')
flags.DEFINE_string(
    'api_key',
    os.environ.get('BPS_API_KEY', 'dc6660972b3db647a0d48eba65fba051'),
    'BPS WebAPI key. Can also be provided via BPS_API_KEY env variable.',
)
flags.DEFINE_list(
    'datasets',
    None,
    'Optional comma-separated list of dataset keys to download. '
    'Defaults to downloading all Health datasets.',
)

BPS_API_BASE = 'https://webapi.bps.go.id/v1/api'
MAX_YEARS_PER_REQUEST = 3

# Dynamic table configurations (BPS model/data endpoint) across the 4 Health
# sub-domains: Mortality, Disease, Risk Factors, and Utilization.
DYNAMIC_DATASETS = {
    # --- 1. Mortality ---
    'life_expectancy': {
        'category': 'mortality',
        'var_id': '455',
        'lang': 'eng',
        'filename': 'life_expectancy_by_regency_city_and_gender.csv',
        'title': 'Life Expectancy Rate By Regency/City and Gender (Year)',
        'place_col': 'Province',
        'multi_turvar': True,
        'include_title_row': True,
        'place_label_overrides': {
            'Gorontalo': 'Kab. Gorontalo',
            'D I YOGYAKARTA': 'DI YOGYAKARTA',
        },
    },
    'infant_mortality_rate': {
        'category': 'mortality',
        'var_id': '1584',
        'lang': 'eng',
        'filename': 'infant_mortality_rate_by_province.csv',
        'title': 'Infant Mortality Rate (IMR) Per 1000 Live Births by Province',
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 0,
    },
    # --- 2. Disease ---
    'disease_cases': {
        'category': 'disease',
        'var_id': '42',
        'lang': 'eng',
        'filename': 'disease_cases_by_province.csv',
        'title': None,
        'place_col': 'Provinsi',
        'multi_turvar': True,
        'include_title_row': False,
    },
    'malaria_incidence': {
        'category': 'disease',
        'var_id': '1393',
        'lang': 'eng',
        'filename': 'malaria_incidence_per_1000_population.csv',
        'title': 'Malaria Incidence per 1,000 population',
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 0,
    },
    'tuberculosis_incidence': {
        'category': 'disease',
        'var_id': '1763',
        'lang': 'eng',
        'filename': 'tuberculosis_incidence_per_100000_population.csv',
        'title': 'Tuberculosis Incidence per 100,000 population',
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 0,
        'place_label_overrides': {
            'Incident': 'INDONESIA'
        },
    },
    # --- 3. Risk Factors ---
    'smoked_tobacco': {
        'category': 'risk_factors',
        'var_id': '1435',
        'lang': 'eng',
        'filename': 'smoked_tobacco_by_province.csv',
        'title': ('Percentage of Population Aged 15 Years and Older Who Smoked '
                  'Tobacco by Province (Percent)'),
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 1,
    },
    'obesity_by_urban_rural': {
        'category': 'risk_factors',
        'var_id': '1481',
        'lang': 'eng',
        'filename': 'obesity_prevalence_by_urban_rural.csv',
        'title':
            ('Prevalence of Obesity Among Population Aged 18 Years and Older'),
        'place_col': 'Classification',
        'multi_turvar': False,
        'title_col_offset': 0,
    },
    'obesity_by_gender': {
        'category': 'risk_factors',
        'var_id': '1781',
        'lang': 'eng',
        'filename': 'obesity_prevalence_by_gender.csv',
        'title':
            ('Prevalence of Obesity Among Population Aged 18 Years and Older '
             'by Sex'),
        'place_col': 'Sex',
        'multi_turvar': False,
        'title_col_offset': 0,
    },
    'contraception_method': {
        'category': 'risk_factors',
        'var_id': '218',
        'lang': 'eng',
        'filename': 'contraception_method_by_province.csv',
        'title': ('Percentage of Married Women Aged 15-49 Years Old Currently '
                  'Using Contraception Method (Percent)'),
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 1,
    },
    # --- 4. Utilization ---
    'hospitals_and_health_centers': {
        'category': 'utilization',
        'var_id': '232',
        'lang': 'eng',
        'filename': 'hospitals_and_public_health_centers_by_province.csv',
        'title': None,
        'place_col': 'Provinsi',
        'multi_turvar': True,
        'include_title_row': False,
    },
    'unmet_need_health_services': {
        'category': 'utilization',
        'var_id': '1402',
        'lang': 'eng',
        'filename': 'unmet_need_of_health_services_by_province.csv',
        'title': 'Unmet Need of Health Services by Province (Percent)',
        'place_col': 'Province',
        'multi_turvar': False,
        'title_col_offset': 0,
    },
}

# Static table configurations (BPS model/statictable endpoint).
STATIC_DATASETS = {
    'aids_cases': {
        'category': 'disease',
        'table_id': '1569',
        'lang': 'ind',
        'filename': 'aids_cases_by_province.csv',
    },
    'health_complaint': {
        'category': 'disease',
        'table_id': '1617',
        'lang': 'ind',
        'filename': 'health_complaint_by_province.csv',
    },
    'outpatient_treatment': {
        'category': 'utilization',
        'table_id': '1620',
        'lang': 'ind',
        'male_filename': 'outpatient_treatment_male_by_province.csv',
        'female_filename': 'outpatient_treatment_female_by_province.csv',
    },
}


class _HTMLTableGridParser(HTMLParser):
    """Parses an HTML <table> into a 2D list of strings expanding spans."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._in_row = False
        self._in_cell = False
        self._current_row = []
        self._current_cell_parts = []
        self._current_colspan = 1
        self._current_rowspan = 1

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower == 'tr':
            self._in_row = True
            self._current_row = []
        elif tag_lower in ('td', 'th') and self._in_row:
            self._in_cell = True
            self._current_cell_parts = []
            attr_dict = dict(attrs)
            try:
                self._current_colspan = max(1, int(attr_dict.get('colspan', 1)))
            except (TypeError, ValueError):
                self._current_colspan = 1
            try:
                self._current_rowspan = max(1, int(attr_dict.get('rowspan', 1)))
            except (TypeError, ValueError):
                self._current_rowspan = 1

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell_parts.append(data)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ('td', 'th') and self._in_cell:
            text = ' '.join(''.join(self._current_cell_parts).split())
            self._current_row.append(
                (text, self._current_rowspan, self._current_colspan))
            self._in_cell = False
        elif tag_lower == 'tr' and self._in_row:
            if self._current_row:
                self.rows.append(self._current_row)
            self._in_row = False

    def to_grid(self) -> list[list[str]]:
        """Expands rowspans and colspans into a rectangular 2D string grid."""
        grid = {}
        max_row = len(self.rows)
        max_col = 0
        for r_idx, row in enumerate(self.rows):
            c_idx = 0
            for text, rowspan, colspan in row:
                while (r_idx, c_idx) in grid:
                    c_idx += 1
                for dr in range(rowspan):
                    for dc in range(colspan):
                        target_r = r_idx + dr
                        target_c = c_idx + dc
                        grid[(target_r, target_c)] = text
                        max_row = max(max_row, target_r + 1)
                        max_col = max(max_col, target_c + 1)
                c_idx += colspan
        return [[grid.get((r, c), '')
                 for c in range(max_col)]
                for r in range(max_row)]


def clean_label(raw_label: str) -> str:
    """Strips HTML tags, unescapes HTML entities, and normalizes whitespace."""
    if raw_label is None:
        return ''
    unescaped = html.unescape(str(raw_label))
    no_tags = re.sub(r'<[^>]+>', '', unescaped)
    return ' '.join(no_tags.split())


def normalize_numeric_cell(val: str) -> str:
    """Normalizes Indonesian-formatted numeric cells (e.g. '12,34' -> '12.34')."""
    cleaned = val.strip()
    if cleaned in ('-', '--', '–', '—', '...', 'n.a', 'N/A', 'NA'):
        return ''
    # Convert comma decimal separator to dot for numeric tokens.
    if re.fullmatch(r'-?\d+,\d+', cleaned):
        return cleaned.replace(',', '.')
    return cleaned


def fetch_available_years(domain: str,
                          var_id: str,
                          api_key: str,
                          lang: str = 'eng') -> list[dict]:
    """Fetches all available period (th) records for a given BPS variable ID."""
    years = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        url = (f'{BPS_API_BASE}/list/model/th/domain/{domain}/var/{var_id}/'
               f'lang/{lang}/page/{page}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not resp or resp.get('status') != 'OK' or 'data' not in resp:
            raise RuntimeError(
                f'Failed to fetch available years for var {var_id} (page {page}):'
                f' {resp}')
        pagination, items = resp['data']
        total_pages = int(pagination.get('pages', 1))
        years.extend(items)
        page += 1

    years.sort(key=lambda item: int(item['th_id']))
    return years


def fetch_dynamic_table(
    domain: str,
    var_id: str,
    api_key: str,
    lang: str = 'eng',
    place_label_overrides: dict | None = None,
) -> tuple[list[str], list[str], list[str], dict]:
    """Fetches all years of data for a BPS dynamic variable in 3-year batches.

  Args:
    domain: BPS domain code (e.g. '0000').
    var_id: BPS variable ID.
    api_key: BPS WebAPI key.
    lang: Language code ('eng' or 'ind').
    place_label_overrides: Optional mapping to rename specific vervar labels.

  Returns:
    A tuple of (places, categories, year_labels, data_map) where:
      - places: Ordered list of cleaned vervar place/row labels.
      - categories: Ordered list of cleaned turvar category labels.
      - year_labels: Ordered list of year strings (e.g. ['2015', '2016']).
      - data_map: Dict mapping (place_label, category_label, year_label) -> val.
  """
    available_years = fetch_available_years(domain, var_id, api_key, lang=lang)
    if not available_years:
        raise RuntimeError(f'No available years found for var_id={var_id}')

    places = []
    places_seen = set()
    categories = []
    categories_seen = set()
    year_labels = []
    years_seen = set()
    data_map = {}
    overrides = place_label_overrides or {}

    for i in range(0, len(available_years), MAX_YEARS_PER_REQUEST):
        batch = available_years[i:i + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(item['th_id']) for item in batch)
        url = (f'{BPS_API_BASE}/list/model/data/domain/{domain}/var/{var_id}/'
               f'th/{th_param}/lang/{lang}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not resp or resp.get('status') != 'OK':
            raise RuntimeError(
                f'Failed to fetch data for var {var_id} (th={th_param}): {resp}'
            )

        var_list = resp.get('var') or []
        if not var_list:
            raise RuntimeError(f'Missing var metadata for var {var_id}: {resp}')
        vid = var_list[0]['val']
        vervar_list = resp.get('vervar') or []
        turvar_list = resp.get('turvar') or [{'val': '0', 'label': ''}]
        tahun_list = sorted(resp.get('tahun') or [],
                            key=lambda x: int(x['val']))
        turtahun_list = resp.get('turtahun') or [{'val': '0', 'label': ''}]
        tt_val = turtahun_list[0]['val']
        datacontent = resp.get('datacontent') or {}

        for ty in tahun_list:
            y_label = clean_label(ty.get('label', ''))
            if y_label not in years_seen:
                years_seen.add(y_label)
                year_labels.append(y_label)

        for tv in turvar_list:
            cat_label = clean_label(tv.get('label', ''))
            if cat_label not in categories_seen:
                categories_seen.add(cat_label)
                categories.append(cat_label)

        for vv in vervar_list:
            raw_place = clean_label(vv.get('label', ''))
            place_label = overrides.get(raw_place, raw_place)
            if place_label not in places_seen:
                places_seen.add(place_label)
                places.append(place_label)

            for tv in turvar_list:
                tv_val = tv['val']
                cat_label = clean_label(tv.get('label', ''))
                for ty in tahun_list:
                    y_label = clean_label(ty.get('label', ''))
                    cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                    val = datacontent.get(cell_key)
                    cell_tuple = (place_label, cat_label, y_label)
                    if val is not None:
                        data_map[cell_tuple] = val
                    elif cell_tuple not in data_map:
                        data_map[cell_tuple] = ''

    return places, categories, year_labels, data_map


def write_single_turvar_csv(
    output_path: str,
    title: str,
    place_col: str,
    places: list[str],
    categories: list[str],
    years: list[str],
    data_map: dict,
    title_col_offset: int = 0,
) -> None:
    """Writes a single-category dynamic BPS dataset to CSV."""
    cat_label = categories[0] if categories else ''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if title_col_offset == 1 and years:
            title_row = ['', title] + [''] * (len(years) - 1)
        else:
            title_row = [title] + [''] * len(years)
        writer.writerow(title_row)
        writer.writerow([place_col] + years)
        for place in places:
            row = [place] + [
                data_map.get((place, cat_label, year), '') for year in years
            ]
            writer.writerow(row)
    logging.info('Wrote %s (%d places, %d years)', output_path, len(places),
                 len(years))


def write_multi_turvar_csv(
    output_path: str,
    title: str | None,
    place_col: str,
    places: list[str],
    categories: list[str],
    years: list[str],
    data_map: dict,
    include_title_row: bool = False,
) -> None:
    """Writes a multi-category dynamic BPS dataset to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    total_data_cols = len(categories) * len(years)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if include_title_row and title:
            writer.writerow([title] + [''] * total_data_cols)
            writer.writerow([place_col] +
                            [cat for cat in categories for _ in years])
            writer.writerow([''] + years * len(categories))
        else:
            writer.writerow([''] + [cat for cat in categories for _ in years])
            writer.writerow([place_col] + years * len(categories))

        for place in places:
            row = [place]
            for cat in categories:
                for year in years:
                    row.append(data_map.get((place, cat, year), ''))
            writer.writerow(row)
    logging.info(
        'Wrote %s (%d places, %d categories, %d years)',
        output_path,
        len(places),
        len(categories),
        len(years),
    )


def fetch_static_table_grid(domain: str,
                            table_id: str,
                            api_key: str,
                            lang: str = 'ind') -> list[list[str]]:
    """Fetches a BPS static table and parses its HTML table into a 2D grid."""
    url = (f'{BPS_API_BASE}/view/domain/{domain}/model/statictable/'
           f'lang/{lang}/id/{table_id}/key/{api_key}/')
    resp = download_util.request_url(url=url, output='json')
    if not resp or resp.get('status') != 'OK' or 'data' not in resp:
        raise RuntimeError(f'Failed to fetch static table {table_id}: {resp}')
    raw_html = html.unescape(resp['data'].get('table', ''))
    parser = _HTMLTableGridParser()
    parser.feed(raw_html)
    return parser.to_grid()


def process_aids_static_table(grid: list[list[str]], output_path: str) -> None:
    """Formats BPS static table 1569 (AIDS cases & deaths by province) to CSV."""
    if len(grid) < 4:
        raise RuntimeError('Unexpected grid layout for AIDS static table 1569')

    # Locate the metric category header row (first row with non-empty cells in
    # columns 1+ where at least one cell is not a 4-digit year).
    metric_idx = 1
    for idx in range(1, len(grid) - 1):
        non_empty = [c.strip() for c in grid[idx][1:] if c.strip()]
        if non_empty and not all(re.match(r'^\d{4}', c) for c in non_empty):
            metric_idx = idx
            break

    metric_row = ['Provinsi'] + [cell.strip() for cell in grid[metric_idx][1:]]
    year_row = ['']
    for cell in grid[metric_idx + 1][1:]:
        # Strip trailing footnote digits such as '2008 2' -> '2008'.
        match = re.match(r'^(\d{4})', cell.strip())
        year_row.append(match.group(1) if match else cell.strip())

    data_rows = []
    for row in grid[metric_idx + 2:]:
        if not row or not row[0].strip():
            continue
        first_col = row[0].strip()
        if first_col.lower().startswith(
            ('catatan', 'sumber', 'note', 'source')):
            break
        if first_col.lower() == 'jumlah':
            first_col = 'INDONESIA'
        cleaned_vals = [normalize_numeric_cell(cell) for cell in row[1:]]
        if any(cleaned_vals):
            data_rows.append([first_col] + cleaned_vals)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(metric_row)
        writer.writerow(year_row)
        writer.writerows(data_rows)
    logging.info('Wrote %s (%d rows)', output_path, len(data_rows))


def process_health_complaint_static_table(grid: list[list[str]],
                                          output_path: str) -> None:
    """Formats BPS static table 1617 (Health Complaints by province) to CSV."""
    if len(grid) < 5:
        raise RuntimeError(
            'Unexpected grid layout for Health Complaint static table 1617')

    # Locate the year header row (first row with 4-digit years in columns 1+).
    year_idx = 1
    for idx in range(1, len(grid) - 2):
        non_empty = [c.strip() for c in grid[idx][1:] if c.strip()]
        if non_empty and all(re.match(r'^\d{4}$', c) for c in non_empty):
            year_idx = idx
            break

    year_row = ['P R O V I N S I'] + [c.strip() for c in grid[year_idx][1:]]
    gender_row = [''] + [
        c.strip().replace('LAKI-LAKI', 'LAKILAKI')
        for c in grid[year_idx + 1][1:]
    ]
    area_row = [''] + [
        re.sub(r'\s*\+\s*', '+', c.strip()) for c in grid[year_idx + 2][1:]
    ]

    data_rows = []
    for row in grid[year_idx + 3:]:
        if not row or not row[0].strip():
            continue
        first_col = row[0].strip()
        if first_col.lower().startswith(
            ('catatan', 'sumber', 'note', 'source')):
            break
        cleaned_vals = [normalize_numeric_cell(cell) for cell in row[1:]]
        if any(cleaned_vals):
            data_rows.append([first_col] + cleaned_vals)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(year_row)
        writer.writerow(gender_row)
        writer.writerow(area_row)
        writer.writerows(data_rows)
    logging.info('Wrote %s (%d rows)', output_path, len(data_rows))


def process_outpatient_static_table(grid: list[list[str]],
                                    male_output_path: str,
                                    female_output_path: str) -> None:
    """Splits BPS static table 1620 (Outpatient Treatment) into Male & Female CSVs."""
    sections = []
    current_section = None

    for row in grid:
        if not row:
            continue
        first_col = row[0].strip()
        upper_first = first_col.upper()
        if 'PENDUDUK LAKI-LAKI' in upper_first:
            current_section = {'gender': 'male', 'rows': []}
            sections.append(current_section)
            continue
        if 'PENDUDUK PEREMPUAN' in upper_first:
            current_section = {'gender': 'female', 'rows': []}
            sections.append(current_section)
            continue
        if current_section is not None:
            if first_col.lower().startswith(
                ('catatan', 'sumber', 'note', 'source')):
                current_section = None
                continue
            if any(cell.strip() for cell in row):
                current_section['rows'].append(row)

    if len(sections) < 2:
        raise RuntimeError(
            'Expected both Male and Female sections in static table 1620')

    for section, out_path in (
        (sections[0], male_output_path),
        (sections[1], female_output_path),
    ):
        sec_rows = section['rows']
        if len(sec_rows) < 3:
            raise RuntimeError(
                f"Insufficient rows in {section['gender']} section of table 1620"
            )
        gender_label = ('PENDUDUK LAKI-LAKI' if section['gender'] == 'male' else
                        'PENDUDUK PEREMPUAN')
        year_row = ['Provinsi'] + [c.strip() for c in sec_rows[0][1:]]
        facility_row = [gender_label] + [c.strip() for c in sec_rows[1][1:]]
        data_rows = []
        for row in sec_rows[2:]:
            place = row[0].strip()
            if not place:
                continue
            if place.replace(' ', '').upper() == 'INDONESIA':
                place = 'Indonesia'
            cleaned_vals = [normalize_numeric_cell(cell) for cell in row[1:]]
            if any(cleaned_vals):
                data_rows.append([place] + cleaned_vals)

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(year_row)
            writer.writerow(facility_row)
            writer.writerows(data_rows)
        logging.info('Wrote %s (%d rows)', out_path, len(data_rows))


def download_all_health_datasets(
    output_dir: str,
    domain: str,
    api_key: str,
    selected_datasets: list[str] | None = None,
) -> list[str]:
    """Downloads all (or selected) Indonesia Census Health datasets to CSV."""
    os.makedirs(output_dir, exist_ok=True)
    written_files = []
    selected = set(selected_datasets) if selected_datasets else None

    for key, cfg in DYNAMIC_DATASETS.items():
        if selected is not None and key not in selected:
            continue
        logging.info(
            'Downloading dynamic dataset %s (var_id=%s, category=%s)...',
            key,
            cfg['var_id'],
            cfg['category'],
        )
        places, categories, years, data_map = fetch_dynamic_table(
            domain=domain,
            var_id=cfg['var_id'],
            api_key=api_key,
            lang=cfg.get('lang', 'eng'),
            place_label_overrides=cfg.get('place_label_overrides'),
        )
        output_path = os.path.join(output_dir, cfg['filename'])
        if cfg.get('multi_turvar'):
            write_multi_turvar_csv(
                output_path=output_path,
                title=cfg.get('title'),
                place_col=cfg['place_col'],
                places=places,
                categories=categories,
                years=years,
                data_map=data_map,
                include_title_row=cfg.get('include_title_row', False),
            )
        else:
            write_single_turvar_csv(
                output_path=output_path,
                title=cfg['title'],
                place_col=cfg['place_col'],
                places=places,
                categories=categories,
                years=years,
                data_map=data_map,
                title_col_offset=cfg.get('title_col_offset', 0),
            )
        written_files.append(output_path)

    for key, cfg in STATIC_DATASETS.items():
        if selected is not None and key not in selected:
            continue
        logging.info(
            'Downloading static dataset %s (table_id=%s, category=%s)...',
            key,
            cfg['table_id'],
            cfg['category'],
        )
        grid = fetch_static_table_grid(
            domain=domain,
            table_id=cfg['table_id'],
            api_key=api_key,
            lang=cfg.get('lang', 'ind'),
        )
        if key == 'aids_cases':
            out_path = os.path.join(output_dir, cfg['filename'])
            process_aids_static_table(grid, out_path)
            written_files.append(out_path)
        elif key == 'health_complaint':
            out_path = os.path.join(output_dir, cfg['filename'])
            process_health_complaint_static_table(grid, out_path)
            written_files.append(out_path)
        elif key == 'outpatient_treatment':
            male_path = os.path.join(output_dir, cfg['male_filename'])
            female_path = os.path.join(output_dir, cfg['female_filename'])
            process_outpatient_static_table(grid, male_path, female_path)
            written_files.extend([male_path, female_path])

    return written_files


def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    if not FLAGS.api_key:
        raise ValueError(
            'BPS API key is required. Pass --api_key or set BPS_API_KEY.')

    files = download_all_health_datasets(
        output_dir=FLAGS.output_dir,
        domain=FLAGS.domain,
        api_key=FLAGS.api_key,
        selected_datasets=FLAGS.datasets,
    )
    logging.info('Successfully generated %d Health CSV files.', len(files))


if __name__ == '__main__':
    app.run(main)
