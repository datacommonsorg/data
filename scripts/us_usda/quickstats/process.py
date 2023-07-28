import requests
import json
import csv

API_BASE = 'https://quickstats.nass.usda.gov/api'


def get_data(api_key, source, year, state):
    params = {'key': api_key, 'source_desc': source, 'year': year, 'state_name': state}
    return requests.get(f'{API_BASE}/api_GET', params=params).json()


'''Converts a quickstats data row to a DC CSV row.

data = quickstats data row
svs = {name: {name: ..., sv: ..., unit: ...}}

returns = {variableMeasured: ..., observationAbout: ..., value: ..., unit: ...}
'''


def to_csv_row(data_row, svs):
    name = data_row['short_desc']
    if data_row['domaincat_desc']:
        name = f"{name}%%{data_row['domaincat_desc']}"

    if name not in svs:
        print('No SV mapped for', name)
        return None

    sv = svs[name]

    return {
        'variableMeasured': sv['sv'],
        'observationAbout': f"dcid:geoId/{data_row['state_fips_code']}{data_row['county_code']}" if data_row[
            'state_fips_code'] else 'dcid:country/USA',
        'value': int(data_row['value'].replace(',', '')),
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


if __name__ == '__main__':
    svs = load_svs()
    data = get_data('569256A0-9CF4-34F0-86F3-FC477003330A', 'SURVEY', 2022, 'CALIFORNIA')
    print(len(data['data']))
    print(to_csv_rows(data, svs))
