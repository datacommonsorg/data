import csv
import datetime
import os
import pandas as pd
from absl import app
from absl import flags
from typing import IO, Iterator
import python_calamine

FLAGS = flags.FLAGS
flags.DEFINE_string('income_output_dir', 'csv', 'Path to write cleaned CSVs.')

URL_PREFIX = 'https://www.huduser.gov/portal/datasets/il/il'


def get_url(year):
    '''Return xls url for year.'''
    if year < 2006:
        return ''
    suffix = str(year)[-2:]
    if year == 2023:
        return 'Section8-FY23.xlsx'  # Directly reference 2023 file for download
    elif year == 2024:
        return 'Section8-FY24.xlsx'  # Directly reference 2024 file for download
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


def iter_excel_calamine(file: IO[bytes]) -> Iterator[dict[str, object]]:
    '''Reads Excel file using python_calamine.'''
    workbook = python_calamine.CalamineWorkbook.from_filelike(
        file)  # type: ignore[arg-type]
    rows = iter(workbook.get_sheet_by_index(0).to_python())
    headers = list(map(str, next(rows)))  # Get headers from the first row
    for row in rows:
        yield dict(zip(headers, row))


def compute_150(df, person):
    '''Compute 150th percentile income in-place.'''
    df[f'l150_{person}'] = df.apply(
        lambda x: round(x[f'l80_{person}'] / 80 * 150), axis=1)


def process(year, matches, output_data):
    '''Generate cleaned data and accumulate it in output_data.'''
    url = get_url(year)

    # Handle 2023 and 2024 separately (read from file using python_calamine)
    if year == 2023 or year == 2024:
        try:
            with open(url, 'rb') as f:
                rows = iter_excel_calamine(f)
                data = [row for row in rows
                       ]  # Collect all rows as a list of dicts
            df = pd.DataFrame(data)
        except FileNotFoundError:
            print(f'No file found for {year}: {url}.')
            return
    else:
        # For other years, download via URL
        try:
            df = pd.read_excel(url)
        except:
            print(f'No file found for {url}.')
            return

    # Process the DataFrame (common code for all years)
    if 'fips2010' in df:
        df = df.rename(columns={'fips2010': 'fips'})

    # Filter to 80th percentile income stats for each household size
    df = df.loc[:, [
        'fips', 'l80_1', 'l80_2', 'l80_3', 'l80_4', 'l80_5', 'l80_6', 'l80_7',
        'l80_8'
    ]]

    # Format FIPS codes
    df['fips'] = df.apply(lambda x: 'dcs:geoId/' + str(x['fips']).zfill(10),
                          axis=1)
    df['fips'] = df.apply(lambda x: x['fips'][:-5]
                          if x['fips'][-5:] == '99999' else x['fips'],
                          axis=1)

    # Compute 150th percentile for each household size
    for i in range(1, 9):
        compute_150(df, i)

    # Add year column
    df['year'] = [year for _ in range(len(df))]

    # Add stats for matching dcids
    df_match = df.copy().loc[df['fips'].isin(matches)]
    if not df_match.empty:
        df_match['fips'] = df_match.apply(lambda x: matches[x['fips']], axis=1)
        df = pd.concat([df, df_match])

    # Append this year's data to the output_data list
    output_data.append(df)


def main(argv):
    '''Main function to process data for all years and merge into a single CSV.'''
    with open('match_bq.csv') as f:
        reader = csv.DictReader(f)
        matches = {'dcs:' + row['fips']: 'dcs:' + row['city'] for row in reader}

    # Ensure the output directory exists
    if not os.path.exists(FLAGS.income_output_dir):
        os.makedirs(FLAGS.income_output_dir)

    today = datetime.date.today()

    # List to accumulate all data
    output_data = []

    # Process data for years 2006 to the current year
    for year in range(2006, today.year + 1):
        print(year)
        process(year, matches, output_data)

    # Concatenate all DataFrames in output_data into one single DataFrame
    final_df = pd.concat(output_data, ignore_index=True)

    # Save the merged data to a single CSV
    final_df.to_csv(os.path.join(FLAGS.income_output_dir,
                                 'output_all_years.csv'),
                    index=False)
    print(
        f'Merged data saved to {FLAGS.income_output_dir}/output_all_years.csv')


if __name__ == '__main__':
    app.run(main)
