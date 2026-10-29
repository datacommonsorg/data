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
"""Downloads Sweden Census Category 3 (Education 16-74 Years) data from SCB PxWeb API.

Queries Statistics Sweden (SCB) table UF0506B/Utbildning across all available
years (1985-latest, automatically picking up any future years added upstream),
aggregates individual ages into the 6 standard 10-year brackets + total (16-74),
rolls up Swedish counties into NUTS3, NUTS2, and NUTS1, and writes the 17 raw
input CSVs into `input_files/`.

Uses `urllib3.util.retry.Retry` + `requests.adapters.HTTPAdapter` for resilient
HTTP requests against the SCB PxWeb API.
"""

import collections
import csv
import json
import os
import time
from typing import Dict, List, Optional, Tuple
from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'output_dir',
    os.path.join(_SCRIPT_DIR, 'input_files'),
    'Directory to save downloaded raw input CSV files.',
)
flags.DEFINE_integer(
    'start_year',
    1985,
    'Start year to fetch from SCB PxWeb API (default: 1985 for full history).',
)
flags.DEFINE_integer(
    'end_year',
    None,
    'Optional end year. Defaults to None (automatically fetches up to the '
    'latest available year in SCB API, e.g. 2025+ in future runs).',
)

# Swedish SCB PxWeb API endpoint for Education (UF0506B/Utbildning)
SCB_API_URL = (
    'https://api.scb.se/OV0104/v1/doris/sv/ssd/START/UF/UF0506/UF0506B/Utbildning'
)

# The 6 mapped SUN 2020 education levels used in the Sweden_Census import
# (Note: "2" and "US" are intentionally excluded to match the existing schema/PVMap)
EDUCATION_LEVELS: List[Tuple[str, str]] = [
    ('1', 'förgymnasial utbildning kortare än 9 år'),
    ('3', 'gymnasial utbildning, högst 2 år'),
    ('4', 'gymnasial utbildning, 3 år'),
    ('5', 'eftergymnasial utbildning, mindre än 3 år'),
    ('6', 'eftergymnasial utbildning, 3 år eller mer'),
    ('7', 'forskarutbildning'),
]

# Sex codes in SCB API
SEX_LEVELS: List[Tuple[str, str]] = [
    ('1', 'män'),
    ('2', 'kvinnor'),
]

# Age groups in Sweden Education import
AGE_GROUPS: List[Tuple[str, List[str]]] = [
    ('16-24 år', [str(a) for a in range(16, 25)]),
    ('25-34 år', [str(a) for a in range(25, 35)]),
    ('35-44 år', [str(a) for a in range(35, 45)]),
    ('45-54 år', [str(a) for a in range(45, 55)]),
    ('55-64 år', [str(a) for a in range(55, 65)]),
    ('65-74 år', [str(a) for a in range(65, 75)]),
]
TOTAL_AGE_LABEL = 'totalt 16-74 år'

# Mapping from 2-digit SCB County code -> (NUTS3 label, NUTS2 label, NUTS1 label)
COUNTY_TO_NUTS: Dict[str, Tuple[str, str, str]] = {
    '01': ('SE110 Stockholms län', 'SE11 Stockholm', 'SE1 Östra Sverige'),
    '03': ('SE121 Uppsala län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '04': ('SE122 Södermanlands län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '05': ('SE123 Östergötlands län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '18': ('SE124 Örebro län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '19': ('SE125 Västmanlands län', 'SE12 Östra Mellansverige', 'SE1 Östra Sverige'),
    '06': ('SE211 Jönköpings län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '07': ('SE212 Kronobergs län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '08': ('SE213 Kalmar län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '09': ('SE214 Gotlands län', 'SE21 Småland med öarna', 'SE2 Södra Sverige'),
    '10': ('SE221 Blekinge län', 'SE22 Sydsverige', 'SE2 Södra Sverige'),
    '12': ('SE224 Skåne län', 'SE22 Sydsverige', 'SE2 Södra Sverige'),
    '13': ('SE231 Hallands län', 'SE23 Västsverige', 'SE2 Södra Sverige'),
    '14': ('SE232 Västra Götalands län', 'SE23 Västsverige', 'SE2 Södra Sverige'),
    '17': ('SE311 Värmlands län', 'SE31 Norra Mellansverige', 'SE3 Norra Sverige'),
    '20': ('SE312 Dalarnas län', 'SE31 Norra Mellansverige', 'SE3 Norra Sverige'),
    '21': ('SE313 Gävleborgs län', 'SE31 Norra Mellansverige', 'SE3 Norra Sverige'),
    '22': ('SE321 Västernorrlands län', 'SE32 Mellersta Norrland', 'SE3 Norra Sverige'),
    '23': ('SE322 Jämtlands län', 'SE32 Mellersta Norrland', 'SE3 Norra Sverige'),
    '24': ('SE331 Västerbottens län', 'SE33 Övre Norrland', 'SE3 Norra Sverige'),
    '25': ('SE332 Norrbottens län', 'SE33 Övre Norrland', 'SE3 Norra Sverige'),
}

NUTS1_ORDER: List[str] = [
    'SE1 Östra Sverige',
    'SE2 Södra Sverige',
    'SE3 Norra Sverige',
]

NUTS2_ORDER: List[str] = [
    'SE11 Stockholm',
    'SE12 Östra Mellansverige',
    'SE21 Småland med öarna',
    'SE22 Sydsverige',
    'SE23 Västsverige',
    'SE31 Norra Mellansverige',
    'SE32 Mellersta Norrland',
    'SE33 Övre Norrland',
]

NUTS3_ORDER: List[str] = [
    'SE110 Stockholms län',
    'SE121 Uppsala län',
    'SE122 Södermanlands län',
    'SE123 Östergötlands län',
    'SE124 Örebro län',
    'SE125 Västmanlands län',
    'SE211 Jönköpings län',
    'SE212 Kronobergs län',
    'SE213 Kalmar län',
    'SE214 Gotlands län',
    'SE221 Blekinge län',
    'SE224 Skåne län',
    'SE231 Hallands län',
    'SE232 Västra Götalands län',
    'SE311 Värmlands län',
    'SE312 Dalarnas län',
    'SE313 Gävleborgs län',
    'SE321 Västernorrlands län',
    'SE322 Jämtlands län',
    'SE331 Västerbottens län',
    'SE332 Norrbottens län',
]


def _create_retry_session(
    retries: int = 5, backoff_factor: float = 1.0
) -> requests.Session:
  """Creates a requests.Session configured with standard Data Commons retry logic."""
  session = requests.Session()
  retry_strategy = Retry(
      total=retries,
      read=retries,
      connect=retries,
      backoff_factor=backoff_factor,
      status_forcelist=[429, 500, 502, 503, 504],
      allowed_methods=['HEAD', 'GET', 'OPTIONS'],
  )
  adapter = HTTPAdapter(max_retries=retry_strategy)
  session.mount('https://', adapter)
  session.mount('http://', adapter)
  return session


def fetch_metadata(session: requests.Session) -> Dict:
  """Fetches table metadata from SCB PxWeb API using the retry-configured session."""
  logging.info('Fetching metadata from %s', SCB_API_URL)
  response = session.get(SCB_API_URL, timeout=60)
  response.raise_for_status()
  return json.loads(response.content.decode('utf-8-sig'))


def query_scb_chunk(
    session: requests.Session,
    regions: List[str],
    ages: List[str],
    edu_codes: List[str],
    sex_codes: List[str],
    years: List[str],
    contents_code: str,
) -> List[Dict]:
  """Executes a JSON-POST query against SCB PxWeb API with retry logic."""
  payload = {
      'query': [
          {'code': 'Region', 'selection': {'filter': 'item', 'values': regions}},
          {'code': 'Alder', 'selection': {'filter': 'item', 'values': ages}},
          {
              'code': 'UtbildningsNiva',
              'selection': {'filter': 'item', 'values': edu_codes},
          },
          {'code': 'Kon', 'selection': {'filter': 'item', 'values': sex_codes}},
          {
              'code': 'ContentsCode',
              'selection': {'filter': 'item', 'values': [contents_code]},
          },
          {'code': 'Tid', 'selection': {'filter': 'item', 'values': years}},
      ],
      'response': {'format': 'json'},
  }

  max_attempts = 5
  last_exc: Optional[Exception] = None
  for attempt in range(max_attempts):
    try:
      logging.info(
          'POST %s (regions=%d, ages=%d, years=%s..%s, attempt=%d/%d)',
          SCB_API_URL,
          len(regions),
          len(ages),
          years[0],
          years[-1],
          attempt + 1,
          max_attempts,
      )
      resp = session.post(SCB_API_URL, json=payload, timeout=120)
      if resp.status_code == 429:
        if attempt < max_attempts - 1:
          wait_sec = 2**attempt
          logging.warning('Rate limited (429). Sleeping %ds...', wait_sec)
          time.sleep(wait_sec)
          continue
      if 400 <= resp.status_code < 500 and resp.status_code != 429:
        resp.raise_for_status()
      resp.raise_for_status()
      # Handle UTF-8 BOM if present in SCB JSON response
      text = resp.content.decode('utf-8-sig')
      resp_json = json.loads(text)
      cols = [
          col['code']
          for col in resp_json.get('columns', [])
          if col.get('type') != 'c'
      ]
      data = resp_json.get('data', [])
      logging.info('Received %d records from SCB API.', len(data))
      results = []
      for row in data:
        row_dict = dict(zip(cols, row['key']))
        row_dict['value'] = row['values'][0]
        results.append(row_dict)
      return results
    except requests.HTTPError as e:
      if (
          e.response is not None
          and 400 <= e.response.status_code < 500
          and e.response.status_code != 429
      ):
        raise
      last_exc = e
    except Exception as e:  # pylint: disable=broad-except
      last_exc = e

    if attempt < max_attempts - 1:
      wait_sec = 2**attempt
      logging.warning(
          'Attempt %d/%d failed (%s). Retrying in %ds...',
          attempt + 1,
          max_attempts,
          last_exc,
          wait_sec,
      )
      time.sleep(wait_sec)
  raise RuntimeError(
      f'Failed to query SCB PxWeb API after {max_attempts} attempts.'
  ) from last_exc


def write_wide_csv(
    filepath: str,
    title: str,
    include_gender: bool,
    regions: List[str],
    age_labels: List[str],
    years: List[str],
    data_store: Dict,
) -> int:
  """Writes a raw wide-format CSV matching the legacy Sweden Education PVMap."""
  os.makedirs(os.path.dirname(filepath), exist_ok=True)
  tmp_filepath = f'{filepath}.tmp'
  rows_written = 0
  with open(tmp_filepath, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # Row 1: Title, Row 2: Blank, Row 3: Header (header_rows=3 in metadata.csv)
    writer.writerow([title])
    writer.writerow([])
    if include_gender:
      writer.writerow(['region', 'ålder', 'utbildningsnivå', 'kön'] + years)
    else:
      writer.writerow(['region', 'ålder', 'utbildningsnivå'] + years)

    for reg in regions:
      for age_label in age_labels:
        for edu_code, edu_text in EDUCATION_LEVELS:
          if include_gender:
            for sex_code, sex_text in SEX_LEVELS:
              year_vals = [
                  data_store.get((reg, age_label, edu_code, sex_code, yr), 0)
                  for yr in years
              ]
              writer.writerow([reg, age_label, edu_text, sex_text] + year_vals)
              rows_written += 1
          else:
            year_vals = [
                data_store.get((reg, age_label, edu_code, 'TOT', yr), 0)
                for yr in years
            ]
            writer.writerow([reg, age_label, edu_text] + year_vals)
            rows_written += 1

  if not os.path.exists(tmp_filepath) or os.path.getsize(tmp_filepath) == 0:
    raise RuntimeError(f'Generated empty CSV file: {tmp_filepath}')
  os.replace(tmp_filepath, filepath)
  logging.info('Wrote %d data rows to %s', rows_written, filepath)
  return rows_written


def main(argv):
  del argv
  session = _create_retry_session()
  meta = fetch_metadata(session)

  var_map = {v['code']: v for v in meta['variables']}
  # Dynamically detect all available years >= start_year (and <= end_year if specified)
  all_years = sorted(
      [
          y
          for y in var_map['Tid']['values']
          if int(y) >= FLAGS.start_year
          and (FLAGS.end_year is None or int(y) <= FLAGS.end_year)
      ],
      key=int,
  )
  if not all_years:
    logging.fatal(
        'No years found in SCB metadata matching start_year=%s',
        FLAGS.start_year,
    )
  logging.info(
      'Dynamically discovered available years: %s..%s (%d years)',
      all_years[0],
      all_years[-1],
      len(all_years),
  )

  # Dynamically detect ContentsCode (e.g. UF0506A1 / UF0506B1) from API metadata
  contents_code = var_map['ContentsCode']['values'][0]
  logging.info('Using ContentsCode: %s', contents_code)

  # Separate 2-digit county codes (21 counties) and 4-digit municipality codes (290 municipalities)
  reg_values = var_map['Region']['values']
  reg_texts = var_map['Region']['valueTexts']
  county_codes: List[str] = []
  muni_codes: List[str] = []
  muni_code_to_label: Dict[str, str] = {}

  for code, text in zip(reg_values, reg_texts):
    if code == '00':
      continue
    elif len(code) == 2 and code in COUNTY_TO_NUTS:
      county_codes.append(code)
    elif len(code) == 4:
      muni_codes.append(code)
      muni_code_to_label[code] = f'{code} {text}'

  logging.info(
      'Found %d counties and %d municipalities.',
      len(county_codes),
      len(muni_codes),
  )

  edu_codes = [code for code, _ in EDUCATION_LEVELS]
  sex_codes = [code for code, _ in SEX_LEVELS]

  # Map individual ages '16'..'74' -> age bracket label
  age_to_bracket: Dict[str, str] = {}
  individual_ages: List[str] = []
  for bracket_label, ages in AGE_GROUPS:
    for a in ages:
      age_to_bracket[a] = bracket_label
      individual_ages.append(a)

  # Data store keyed by: (region_label, age_label, edu_code, sex_code_or_TOT, year) -> int count
  data_store: Dict[Tuple[str, str, str, str, str], int] = collections.defaultdict(
      int
  )

  # 1. Fetch County-level data (21 counties) for individual ages 16..74 + tot16-74
  # Roll up into NUTS3, NUTS2, and NUTS1 across all 4 marginal views.
  # Chunk by 5 years at a time to stay well below SCB PxWeb's 150,000-cell limit:
  # 21 counties * 60 ages * 6 edu * 2 sex * 5 years = 75,600 cells per request.
  logging.info('Downloading County-level data (for NUTS1, NUTS2, NUTS3)...')
  ages_with_total = individual_ages + ['tot16-74']
  year_chunk_size = 5
  for i in range(0, len(all_years), year_chunk_size):
    yr_chunk = all_years[i : i + year_chunk_size]
    logging.info('  Fetching counties for years %s...', yr_chunk)
    rows = query_scb_chunk(
        session,
        county_codes,
        ages_with_total,
        edu_codes,
        sex_codes,
        yr_chunk,
        contents_code,
    )
    for row in rows:
      reg_code = row['Region']
      age_code = row['Alder']
      edu_code = row['UtbildningsNiva']
      sex_code = row['Kon']
      yr = row['Tid']
      val_str = row['value']
      val = int(val_str) if val_str not in ('..', '.', '-', '') else 0

      nuts3_label, nuts2_label, nuts1_label = COUNTY_TO_NUTS[reg_code]
      target_age = (
          TOTAL_AGE_LABEL
          if age_code == 'tot16-74'
          else age_to_bracket[age_code]
      )

      for nuts_label in (nuts1_label, nuts2_label, nuts3_label):
        data_store[(nuts_label, target_age, edu_code, sex_code, yr)] += val
        data_store[(nuts_label, target_age, edu_code, 'TOT', yr)] += val
    time.sleep(1.2)

  # 2. Fetch Municipality-level data (290 municipalities)
  # Municipalities are needed for:
  #   - Total (tot16-74, summed over sex)
  #   - Gender (tot16-74, by sex)
  #   - Age (6 age brackets, summed over sex)
  # Chunk by 30 municipalities and 5 years per request:
  # 30 munis * 60 ages * 6 edu * 2 sex * 5 years = 108,000 cells per request.
  logging.info('Downloading Municipality-level data (290 municipalities)...')
  muni_chunk_size = 30
  for m_idx in range(0, len(muni_codes), muni_chunk_size):
    m_chunk = muni_codes[m_idx : m_idx + muni_chunk_size]
    for y_idx in range(0, len(all_years), year_chunk_size):
      yr_chunk = all_years[y_idx : y_idx + year_chunk_size]
      logging.info(
          '  Fetching municipalities %s..%s for years %s..%s...',
          m_chunk[0],
          m_chunk[-1],
          yr_chunk[0],
          yr_chunk[-1],
      )
      rows = query_scb_chunk(
          session,
          m_chunk,
          ages_with_total,
          edu_codes,
          sex_codes,
          yr_chunk,
          contents_code,
      )
      for row in rows:
        reg_code = row['Region']
        age_code = row['Alder']
        edu_code = row['UtbildningsNiva']
        sex_code = row['Kon']
        yr = row['Tid']
        val_str = row['value']
        val = int(val_str) if val_str not in ('..', '.', '-', '') else 0

        muni_label = muni_code_to_label[reg_code]
        target_age = (
            TOTAL_AGE_LABEL
            if age_code == 'tot16-74'
            else age_to_bracket[age_code]
        )
        data_store[(muni_label, target_age, edu_code, sex_code, yr)] += val
        data_store[(muni_label, target_age, edu_code, 'TOT', yr)] += val
      time.sleep(1.2)

  # 3. Write out the 17 raw CSV files into output_dir (cleaning stale CSVs first)
  out_dir = FLAGS.output_dir
  os.makedirs(out_dir, exist_ok=True)
  for existing_file in os.listdir(out_dir):
    if existing_file.endswith('.csv') or existing_file.endswith('.tmp'):
      os.remove(os.path.join(out_dir, existing_file))
  muni_labels_sorted = [muni_code_to_label[c] for c in muni_codes]
  age_bracket_labels = [label for label, _ in AGE_GROUPS]

  title_no_sex = 'Befolkning efter region, ålder, utbildningsnivå och år'
  title_with_sex = 'Befolkning efter region, ålder, utbildningsnivå, kön och år'

  # Group 1: Total by Education Level (4 files)
  write_wide_csv(
      os.path.join(out_dir, 'education_nuts1.csv'),
      title_no_sex,
      False,
      NUTS1_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_nuts2.csv'),
      title_no_sex,
      False,
      NUTS2_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_nuts3.csv'),
      title_no_sex,
      False,
      NUTS3_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_municipality.csv'),
      title_no_sex,
      False,
      muni_labels_sorted,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )

  # Group 2: By Education Level & Gender (4 files)
  write_wide_csv(
      os.path.join(out_dir, 'education_gender_nuts1.csv'),
      title_with_sex,
      True,
      NUTS1_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_gender_nuts2.csv'),
      title_with_sex,
      True,
      NUTS2_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_gender_nuts3.csv'),
      title_with_sex,
      True,
      NUTS3_ORDER,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_gender_municipality.csv'),
      title_with_sex,
      True,
      muni_labels_sorted,
      [TOTAL_AGE_LABEL],
      all_years,
      data_store,
  )

  # Group 3: By Education Level & Age Group (6 files)
  write_wide_csv(
      os.path.join(out_dir, 'education_age_nuts1.csv'),
      title_no_sex,
      False,
      NUTS1_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_nuts2.csv'),
      title_no_sex,
      False,
      NUTS2_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_nuts3.csv'),
      title_no_sex,
      False,
      NUTS3_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )
  # Split municipalities into 3 parts (107, 96, 87; 86 after skipping 2463 Åsele)
  write_wide_csv(
      os.path.join(out_dir, 'education_age_municipality_1.csv'),
      title_no_sex,
      False,
      muni_labels_sorted[:107],
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_municipality_2.csv'),
      title_no_sex,
      False,
      muni_labels_sorted[107:203],
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_municipality_3.csv'),
      title_no_sex,
      False,
      muni_labels_sorted[203:],
      age_bracket_labels,
      all_years,
      data_store,
  )

  # Group 4: By Education Level, Age Group & Gender (3 files)
  write_wide_csv(
      os.path.join(out_dir, 'education_age_gender_nuts1.csv'),
      title_with_sex,
      True,
      NUTS1_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_gender_nuts2.csv'),
      title_with_sex,
      True,
      NUTS2_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )
  write_wide_csv(
      os.path.join(out_dir, 'education_age_gender_nuts3.csv'),
      title_with_sex,
      True,
      NUTS3_ORDER,
      age_bracket_labels,
      all_years,
      data_store,
  )

  logging.info(
      'Successfully generated all 17 Sweden Education raw input CSVs in %s',
      out_dir,
  )


if __name__ == '__main__':
  app.run(main)
