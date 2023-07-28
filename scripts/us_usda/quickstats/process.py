import requests
import sys
import csv
import multiprocessing
from itertools import repeat
import os
import datetime

API_BASE = 'https://quickstats.nass.usda.gov/api'

API_KEY = '569256A0-9CF4-34F0-86F3-FC477003330A'

CSV_COLUMNS = [
    'variableMeasured',
    'observationDate',
    'observationAbout',
    'value',
    'unit',
]

SKIPPED_VALUES = {'(D)', '(Z)'}


def process_survey_data(year, svs, out_dir):
    start = datetime.datetime.now()
    print('Start', start)

    parts_dir = f'{out_dir}/parts'
    os.makedirs(parts_dir, exist_ok=True)

    print('Processing survey data for year', year)

    print('Getting county names')
    county_names = get_param_values('county_name')
    print('# counties =', len(county_names))

    with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
        pool.starmap(fetch_and_write, zip(county_names, repeat(year), repeat(svs), repeat(parts_dir)))

    write_aggregate_csv(year, out_dir)

    end = datetime.datetime.now()
    print('End', end)
    print('Duration', str(end - start))


def write_aggregate_csv(year, out_dir):
    parts_dir = f'{out_dir}/parts'
    part_files = os.listdir(parts_dir)
    out_file = f"{out_dir}/ag-{year}.csv"

    print('Writing aggregate CSV', out_file)

    with open(out_file, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
        csv_writer.writeheader()
        for part_file in part_files:
            if part_file.endswith(".csv"):
                with open(f"{parts_dir}/{part_file}", 'r') as part:
                    csv_writer.writerows(csv.DictReader(part))


def fetch_and_write(county_name, year, svs, parts_dir):
    out_file = f"{parts_dir}/{county_name.replace('[^a-zA-Z0-9]', '')}-{year}.csv"
    api_data = get_survey_county_data(year, county_name)
    county_csv_rows = to_csv_rows(api_data, svs)
    print('Writing', len(county_csv_rows), 'rows for county', county_name, 'to file', out_file)
    with open(out_file, 'w', newline='') as out:
        csv_writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
        csv_writer.writeheader()
        csv_writer.writerows(county_csv_rows)


def get_survey_county_data(year, county):
    print('Getting', year, 'survey data for county', county)
    params = {'key': API_KEY, 'source_desc': "SURVEY", 'year': year, 'county_name': county}
    response = get_data(params)

    if 'data' not in response:
        eprint('No api records found for county', county)
        return {'data': []}

    print('# api records for', county, '=', len(response['data']))
    return response


def get_data(params):
    return requests.get(f'{API_BASE}/api_GET', params=params).json()


def get_param_values(param):
    params = {'key': API_KEY, 'param': param}
    response = requests.get(f'{API_BASE}/get_param_values', params=params).json()
    return [] if param not in response else response[param]


'''Converts a quickstats data row to a DC CSV row.

data = quickstats data row
svs = {name: {name: ..., sv: ..., unit: ...}}

returns = {variableMeasured: ..., observationAbout: ..., value: ..., unit: ...}
'''


def to_csv_row(data_row, svs):
    name = data_row['short_desc']
    if data_row['domaincat_desc'] and data_row['domaincat_desc'] != 'NOT SPECIFIED':
        name = f"{name}%%{data_row['domaincat_desc']}"

    if name not in svs:
        eprint('SKIPPED, No SV mapped for', name)
        return None

    value = (data_row['value'] if 'value' in data_row else data_row['Value']).strip().replace(',', '')
    if value in SKIPPED_VALUES:
        eprint('SKIPPED, Invalid value', f"'{value}'", 'for', name)
        return None
    value = int(value)

    observation_about = f"dcid:geoId/{data_row['state_fips_code']}{data_row['county_code']}" if data_row[
        'state_fips_code'] else 'dcid:country/USA'

    sv = svs[name]

    return {
        'variableMeasured': sv['sv'],
        'observationDate': data_row['year'],
        'observationAbout': observation_about,
        'value': value,
        'unit': sv['unit'],
    }


def to_csv_rows(api_data, svs):
    csv_rows = []

    for data_row in api_data['data']:
        csv_row = to_csv_row(data_row, svs)
        if csv_row:
            csv_rows.append(csv_row)

    return csv_rows


def load_svs():
    svs = {}
    with open("sv.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            svs[row['name']] = row
    return svs


def write_csv(out, rows):
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_all_counties():
    svs = load_svs()
    process_survey_data(2023, svs, "output")


if __name__ == '__main__':
    get_all_counties()

