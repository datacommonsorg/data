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

FLAGS = flags.FLAGS
flags.DEFINE_string('income_output_dir', 'csv', 'Path to write cleaned CSVs.')

URL_PREFIX = 'https://www.huduser.gov/portal/datasets/il/il'


def get_url(year):
    '''Return xls url for year.

  Args:
    year: Input year.

  Returns:
    xls url for given year.
  '''
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
    else:
        return ''


def compute_150(df, person):
    '''Compute 150th percentile income in-place.

  Args:
    df: Input dataframe (will be modified).
    person: Number of people in household.
  '''
    df[f'l150_{person}'] = df.apply(
        lambda x: round(x[f'l80_{person}'] / 80 * 150), axis=1)


def process(year, matches, output_dir):
    '''Generate cleaned CSV.

  Args:
    year: Input year.
    matches: Map of fips dcid -> city dcid.
    output_dir: Directory to write cleaned CSV.
  '''
    url = get_url(year)
    try:
        df = pd.read_excel(url)
    except:
        print(f'No file found for {url}.')
        return
    if 'fips2010' in df:
        df = df.rename(columns={'fips2010': 'fips'})

    # Filter to 80th percentile income stats for each household size.
    df = df.loc[:, [
        'fips', 'l80_1', 'l80_2', 'l80_3', 'l80_4', 'l80_5', 'l80_6', 'l80_7',
        'l80_8'
    ]]

    df['fips'] = df.apply(lambda x: 'dcs:geoId/' + str(x['fips']).zfill(10),
                          axis=1)
    df['fips'] = df.apply(lambda x: x['fips'][:-5]
                          if x['fips'][-5:] == '99999' else x['fips'],
                          axis=1)
    for i in range(1, 9):
        compute_150(df, i)
    df['year'] = [year for i in range(len(df))]

    # Add stats for matching dcids.
    df_match = df.copy().loc[df['fips'].isin(matches)]
    if not df_match.empty:
        df_match['fips'] = df_match.apply(lambda x: matches[x['fips']], axis=1)
        df = pd.concat([df, df_match])

    df.to_csv(os.path.join(output_dir, f'output_{year}.csv'), index=False)


def main(argv):
    with open('match_bq.csv') as f:
        reader = csv.DictReader(f)
        matches = {'dcs:' + row['fips']: 'dcs:' + row['city'] for row in reader}
    if not os.path.exists(FLAGS.income_output_dir):
        os.makedirs(FLAGS.income_output_dir)
    today = datetime.date.today()
    for year in range(2006, today.year):
        print(year)
        process(year, matches, FLAGS.income_output_dir)


if __name__ == '__main__':
    app.run(main)
