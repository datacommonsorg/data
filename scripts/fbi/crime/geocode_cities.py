"""Output the MCF for FBI crime statistics.

Map cities to the corresponding geocodes.
"""

import importlib
import os
import re
import csv
import states

import logging

_CITY_MAP = {'monroe township nj': 'monroe township gloucester county nj'}

# flags.DEFINE_boolean('test', False, 'Run a subset for test?')

_all_prefixes = set()


def normalize_fbi_city(name, state):
    new_name = name
    # Remove any trailing digit due to footnote
    new_name = new_name.lower().strip()
    new_name = re.sub(r'[\s\d]+$', '', new_name)
    # if state in set(['pa', 'mi']):
    # new_name = re.sub('town$', '', name).strip()
    return new_name


def get_all_states():
    return states.get_states()


def int_from_field(f):
    # Convert a field to int value. If field is empty or non-convertible, return 0.
    try:
        f = float(f)
        f = int(f)
        return f
    except ValueError as err:
        return 0


def init_geocodes_from_file(csv_reader, city):
    count_lines = 0
    for a in csv_reader:
        if a[0] in city.keys():
            assert False, 'Duplicate city found {}'.format(a)
        city[a[0]] = a[1]
        count_lines += 1
    logging.info('Lines read from geocode file {}'.format(count_lines))


def read_geocodes():
    city = {}
    with open('city_geocodes.csv', encoding="utf8") as csvfile:
        csv_reader = csv.reader(csvfile)
        init_geocodes_from_file(csv_reader, city)

    with open('manual_geocodes.csv', encoding="utf8") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter="\t")
        init_geocodes_from_file(csv_reader, city)

    return city


def remap_ambiguous_cities(city):
    new_city = city
    try:
        new_city = _CITY_MAP[city]
    except KeyError:
        pass
    return new_city


def update_crime_geocode(crime, geo_codes, found_set, cities_not_found_set):
    try:
        state_parts = crime['State'].split()
        state_parts_1 = [p.capitalize() for p in state_parts]
        lookup_name = ''.join(state_parts_1)
        all_states = get_all_states()
        state = all_states[lookup_name].lower()
    except KeyError:
        logging.error('{} state not found {}'.format(crime['State'],
                                                     lookup_name))
        return false
    city = normalize_fbi_city(crime['City'], state)
    city_state = '{} {}'.format(city, state)
    city_state = remap_ambiguous_cities(city_state)

    # Compute the geocode of the city.
    try:
        geocode = geo_codes[city_state]
        # In case of duplicate, assert.
        # Found the duplicate rows and update preprocess._shouldSkipSpecialLine.
        if city_state in found_set:
            assert False, 'duplicate city state {} for {}'.format(
                city_state, crime['Year'].lower().strip())
        found_set.add(city_state)
    except KeyError:
        cities_not_found_set.add('{}, {}, {}'.format(state, city,
                                                     crime['Population']))
        return False
    crime['Geocode'] = geocode
    return True
