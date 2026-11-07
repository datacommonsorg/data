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
"""Downloads Indonesia Crime by Police Territorial Jurisdiction data from BPS WebAPI."""

import csv
import html
import os
import sys
from typing import Any

_CODEDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_CODEDIR, '../../../util/'))

from absl import app
from absl import flags
from absl import logging
import download_util

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(_CODEDIR, 'input_files'),
    'Directory path to save the downloaded input CSV file.',
)
flags.DEFINE_string(
    'output_filename',
    'crime_according_to_police_territorial_jurisdiction.csv',
    'Filename for the combined crime CSV table.',
)
flags.DEFINE_string(
    'domain',
    '0000',
    'BPS domain code (0000 for national/all-province tables).',
)
flags.DEFINE_integer(
    'var_id',
    101,
    'BPS variable ID for Number Of Crime According To Police Territorial Jurisdiction.',
)
flags.DEFINE_string(
    'api_key',
    os.environ.get('BPS_API_KEY', 'dc6660972b3db647a0d48eba65fba051'),
    'BPS WebAPI key.',
)

BPS_API_BASE_URL = 'https://webapi.bps.go.id/v1/api/list'
MAX_YEARS_PER_REQUEST = 3
TABLE_TITLE = 'Number Of Crime According To Police Territorial Jurisdiction'
JURISDICTION_HEADER = 'Police Territorial Jurisdiction'


def fetch_available_years(
    domain: str,
    var_id: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """Fetches all available year definitions (th_id, th) for a BPS variable."""
    years: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (f'{BPS_API_BASE_URL}/model/th/lang/eng/domain/{domain}'
               f'/var/{var_id}/page/{page}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            logging.fatal(
                'Failed to fetch available years from BPS WebAPI (page %d): %s',
                page,
                resp,
            )
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


def fetch_crime_table(
    domain: str,
    var_id: int,
    api_key: str,
) -> tuple[list[str], list[str], dict[tuple[str, str], str]]:
    """Downloads all year chunks for the crime table and returns ordered headers and values."""
    years = fetch_available_years(domain=domain, var_id=var_id, api_key=api_key)
    if not years:
        logging.fatal('No years returned for BPS var_id=%d.', var_id)

    jurisdictions: list[str] = []
    seen_jurisdictions: set[str] = set()
    year_labels: list[str] = [str(y['th']).strip() for y in years]
    values_by_place_year: dict[tuple[str, str], str] = {}

    for idx in range(0, len(years), MAX_YEARS_PER_REQUEST):
        chunk = years[idx:idx + MAX_YEARS_PER_REQUEST]
        th_param = ';'.join(str(y['th_id']) for y in chunk)
        url = (f'{BPS_API_BASE_URL}/model/data/lang/eng/domain/{domain}'
               f'/var/{var_id}/th/{th_param}/key/{api_key}/')
        resp = download_util.request_url(url=url, output='json')
        if not isinstance(resp, dict) or resp.get('status') != 'OK':
            logging.fatal('Failed to fetch crime data for th=%s: %s', th_param,
                          resp)

        var_list = resp.get('var', [])
        turvar_list = resp.get('turvar', [])
        turtahun_list = resp.get('turtahun', [])
        vervar_list = resp.get('vervar', [])
        tahun_list = resp.get('tahun', [])
        datacontent = resp.get('datacontent', {})

        if not (var_list and turvar_list and turtahun_list):
            logging.fatal('Incomplete metadata in BPS response for th=%s.',
                          th_param)

        vid = var_list[0]['val']
        tv_val = turvar_list[0]['val']
        tt_val = turtahun_list[0]['val']

        for vv in vervar_list:
            place_label = html.unescape(str(vv['label'])).strip()
            if place_label not in seen_jurisdictions:
                seen_jurisdictions.add(place_label)
                jurisdictions.append(place_label)
            for ty in tahun_list:
                year_str = str(ty['label']).strip()
                cell_key = f"{vv['val']}{vid}{tv_val}{ty['val']}{tt_val}"
                raw_val = datacontent.get(cell_key)
                if raw_val is not None and str(raw_val).strip() != '':
                    if isinstance(raw_val, float) and raw_val.is_integer():
                        values_by_place_year[(place_label,
                                              year_str)] = str(int(raw_val))
                    else:
                        values_by_place_year[(place_label,
                                              year_str)] = str(raw_val).strip()

    return jurisdictions, year_labels, values_by_place_year


def write_crime_csv(
    output_path: str,
    jurisdictions: list[str],
    year_labels: list[str],
    values_by_place_year: dict[tuple[str, str], str],
) -> None:
    """Writes the wide-format crime CSV compatible with stat_var_processor.py."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as fp:
        writer = csv.writer(fp)
        # Row 1: Table title in column 0 followed by empty cells
        writer.writerow([TABLE_TITLE] + [''] * len(year_labels))
        # Row 2: Column header for jurisdiction followed by year columns
        writer.writerow([JURISDICTION_HEADER] + year_labels)
        # Rows 3+: One row per police territorial jurisdiction
        for place in jurisdictions:
            row = [place]
            for year in year_labels:
                row.append(values_by_place_year.get((place, year), ''))
            writer.writerow(row)
    logging.info(
        'Wrote %d jurisdictions across %d years (%s-%s) to %s',
        len(jurisdictions),
        len(year_labels),
        year_labels[0] if year_labels else 'N/A',
        year_labels[-1] if year_labels else 'N/A',
        output_path,
    )


def main(_) -> None:
    logging.set_verbosity(logging.INFO)
    jurisdictions, year_labels, values_by_place_year = fetch_crime_table(
        domain=_FLAGS.domain,
        var_id=_FLAGS.var_id,
        api_key=_FLAGS.api_key,
    )
    output_path = os.path.join(_FLAGS.output_dir, _FLAGS.output_filename)
    write_crime_csv(
        output_path=output_path,
        jurisdictions=jurisdictions,
        year_labels=year_labels,
        values_by_place_year=values_by_place_year,
    )


if __name__ == '__main__':
    app.run(main)
