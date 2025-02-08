# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Generates cleaned CSVs for HUD Income Limits data.

Produces: 
* csv/output_[YEAR].csv

Usage:
python3 process.py
'''
import csv
import datetime
import os
import pandas as pd
from absl import app
from absl import flags
from absl import logging
from typing import IO, Iterator
import python_calamine
import requests
from retry import retry

FLAGS = flags.FLAGS
flags.DEFINE_string('income_output_dir', 'output',
                    'Path to write cleaned CSVs.')
flags.DEFINE_string('input_files', 'input', 'Path to download input CSVs.')
flags.DEFINE_string('mode', '',
                    'Mode: "download", "process", or both (default: both).')

URL_PREFIX = 'https://www.huduser.gov/portal/datasets/il/il'


def get_url(year):
    '''Returns xls url for year.'''
    if year < 2006:
        return ''
    suffix = str(year)[-2:]
    if year >= 2016:
        return f'{URL_PREFIX}{suffix}/Section8-FY{suffix}.xlsx'
    elif year == 2015:
        return f'{URL_PREFIX}15/Section8_Rev.xlsx'
    elif year == 2014:
        return f'{URL_PREFIX}14/Poverty.xls'
    elif year == 2011:
        return f'{URL_PREFIX}11/Section8_v3.xls'
    elif year >= 2009:
        return f'{URL_PREFIX}{suffix}/Section8.xls'
    elif year == 2008:
        return f'{URL_PREFIX}08/Section8_FY08.xls'
    elif year == 2007:
        return f'{URL_PREFIX}07/Section8-rev.xls'
    elif year == 2006:
        return f'{URL_PREFIX}06/Section8FY2006.xls'
    return ''


@retry(tries=5, delay=5, backoff=2)
def download_with_retry(url):
    '''Retries downloading a file up to 5 times with exponential backoff.'''
    logging.info(f"Downloading URL: {url}")
    return requests.get(url, verify=False)


def download_file(url: str, filename: str, input_folder: str):
    '''Download file and save it locally.'''
    try:
        if not os.path.exists(input_folder):
            os.makedirs(input_folder)
        file_path = os.path.join(input_folder, filename)
        response = download_with_retry(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded file: {file_path}")
        else:
            logging.fatal(
                f"Failed to download from {url}, status code {response.status_code}"
            )
    except Exception as e:
        logging.fatal(f"Failed to download {url}: {str(e)}")


def iter_excel_calamine(file: IO[bytes]) -> Iterator[dict[str, object]]:
    '''Reads Excel file using python_calamine.'''
    workbook = python_calamine.CalamineWorkbook.from_filelike(file)
    rows = iter(workbook.get_sheet_by_index(0).to_python())
    headers = list(map(str, next(rows)))
    for row in rows:
        yield dict(zip(headers, row))


def process(year, matches, input_folder):
    '''Generate cleaned CSV.'''
    url = get_url(year)
    filename = f"Section8-FY{year}.xlsx" if year > 2016 else f"Section8-FY{year}.xls"
    try:
        with open(os.path.join(input_folder, filename), 'rb') as f:
            rows = iter_excel_calamine(f)
            data = list(rows)
        df = pd.DataFrame(data)
    except Exception as e:
        logging.fatal(f'Error in processing {year}: {url} {e}.')
        return None

    if 'fips2010' in df:
        df = df.rename(columns={'fips2010': 'fips'})
    df = df.loc[:, ['fips'] + [f'l80_{i}' for i in range(1, 9)]]
    df['fips'] = df['fips'].apply(lambda x: f'dcs:geoId/{str(x).zfill(5)}')
    df['fips'] = df['fips'].apply(lambda x: x[:-5] if x[-5:] == '99999' else x)
    for i in range(1, 9):
        df[f'l150_{i}'] = df[f'l80_{i}'] * 1.875
    df['year'] = year
    df_match = df[df['fips'].isin(matches)].copy()
    if not df_match.empty:
        df_match['fips'] = df_match['fips'].map(matches)
        df = pd.concat([df, df_match])
    return df


def process_all():
    '''Processes all years based on mode flag.'''
    with open('match_bq.csv') as f:
        reader = csv.DictReader(f)
        matches = {'dcs:' + row['fips']: 'dcs:' + row['city'] for row in reader}

    today = datetime.date.today()
    input_folder = FLAGS.input_files
    output_data = []

    if FLAGS.mode == "" or FLAGS.mode == "download":
        logging.info("Starting download phase...")
        for year in range(2006, today.year):
            url = get_url(year)
            if url:
                filename = f"Section8-FY{year}.xlsx" if year > 2016 else f"Section8-FY{year}.xls"
                download_file(url, filename, input_folder)

    if FLAGS.mode == "" or FLAGS.mode == "process":
        logging.info("Starting processing phase...")
        for year in range(2006, today.year):
            if not os.path.exists(
                    os.path.join(
                        input_folder, f"Section8-FY{year}.xlsx"
                        if year > 2016 else f"Section8-FY{year}.xls")):
                logging.warning(f"File not found for year {year}")
                continue
            df = process(year, matches, input_folder)
            if df is not None:
                output_data.append(df)

        if output_data:
            final_df = pd.concat(output_data, ignore_index=True)
            os.makedirs(FLAGS.income_output_dir, exist_ok=True)
            final_df.to_csv(os.path.join(FLAGS.income_output_dir,
                                         'output_all_years.csv'),
                            index=False)
            logging.info(
                f'Merged data saved to {FLAGS.income_output_dir}/output_all_years.csv'
            )


def main(argv):
    process_all()


if __name__ == '__main__':
    app.run(main)
