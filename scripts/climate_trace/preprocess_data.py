"""This script processes Climate Trace data for ingestion into Data Commons.

It imports data from Climate Trace URLs and creates a cleaned 'output.csv'
"""
import csv
import datetime
import requests
from .statvar_mapping import *

YEAR = datetime.date.today().year
URL = 'https://api.dev.climatetrace.org/v3/emissions/timeseries/sectors{sector}?since=2010&to={year}{continents}{countries}'

FIELDNAMES = [
    'observation_about', 'observation_date', 'variable_measured', 'value'
]


def get_definition(param):
    """Fetches definition for given parameter.

    Args:
        param: Input parameter.

    Returns:
        JSON of API response.
    """
    return requests.get(
        f'https://api.dev.climatetrace.org/v3/definitions/{param}').json()


CONTINENTS = get_definition('continents')
COUNTRIES = [x['alpha3'] for x in get_definition('countries')]
S = SECTORS.copy()
S.update(SUBSECTORS)


def get_observation_about(name):
    """Returns formatted place DCID.

    Args:
        name: Input place name.

    Returns:
        Formatted DCID or empty string if not found.
    """
    if name == 'all':
        return 'dcid:Earth'
    elif name in CONTINENTS:
        return 'dcid:' + name.lower().replace(' ', '')
    elif name in COUNTRIES:
        return 'dcid:country/' + name
    else:
        print(f'No dcid found for {name}.')
        return ''


def get_variable_measured(s, gas):
    """Returns formatted statistical variable DCID.

    Args:
        s: Input sector/subsector.
        gas: Input gas.

    Returns:
        Formatted DCID or empty string if not found.
    """
    if s not in S or gas not in GASES:
        print(f'No dcid found for {s} and {gas}.')
        return ''
    return f'dcid:Annual_Emissions_{GASES[gas]}_{S[s]}'


def fetch_data(sector, continents, countries):
    """Returns emissions data for given parameters.

    Args:
        sector: Input sector.
        continents: Comma-separated list of continents.
        countries: Comma-separated list of countries

    Returns:
        JSON of API response.
    """
    url = URL.format_map({
        'sector': '/' + sector if sector else '',
        'year': YEAR,
        'continents': f'&continents={continents}' if continents else '',
        'countries': f'&countries={countries}' if countries else '',
    })
    return requests.get(url).json()


def write_emissions(writer, data):
    """Writes cleaned CSV rows of data.

    Args:
        writer: CSV DictWriter.
        data: JSON of input data.
    """
    for entry in data:
        observation_about = get_observation_about(entry['name'])
        if not observation_about:  # No place
            continue
        for s in entry['data']:
            for emission in s['emissions']:
                if not emission['year']:  # No date
                    continue
                for gas in GASES:
                    if gas in emission:
                        variable_measured = get_variable_measured(
                            s['name'], gas)
                        if not variable_measured:  # No SV
                            continue
                        if not emission[gas]:  # No value
                            continue
                        writer.writerow({
                            'observation_about': observation_about,
                            'observation_date': emission['year'],
                            'variable_measured': variable_measured,
                            'value': emission[gas]
                        })


if __name__ == "__main__":
    with open('output.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        continents = ','.join(CONTINENTS)
        countries = ','.join(COUNTRIES)

        for sector in [''] + list(SECTORS.keys()):
            # 'fluorinated-gases' is both a sector and subsector, so don't duplicate.
            if sector == 'fluorinated-gases':
                continue

            # Earth
            write_emissions(writer, fetch_data(sector, '', ''))

            # Continents
            write_emissions(writer, fetch_data(sector, continents, ''))

            # Countries
            write_emissions(writer, fetch_data(sector, '', countries))
