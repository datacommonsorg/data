"""Output the MCF for FBI crime statistics.

Map cities to the corresponding geocodes.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import importlib
import os
import re
import csv
import states

# from absl import app
# from absl import flags
# from absl import logging
import logging

# from google3.datacommons.mcf.crime import states
# from google3.corp.sales.pylib import unicode_csv
# from google3.pyglib import gfile
# from google3.pyglib import resources

# FLAGS = flags.FLAGS

_INPUT_DIR = '/cns/jv-d/home/datcom/crime/'
_INPUT_DIR_LOCAL = '/usr/local/google/home/panesar/Documents/crime/'

_PLACES = ('/usr/local/google/home/panesar/Documents/census/gaz/place_national/'
           '2018_Gaz_place_national.txt')

_COUSUBS = ('/usr/local/google/home/panesar/Documents/census/gaz/cousubs/'
            '2018_Gaz_cousubs_national.txt')

_CRIME_CSV = (_INPUT_DIR + 'crime_city.csv')
_CRIME_CSV_LOCAL = (_INPUT_DIR_LOCAL + 'crime_city.csv')

_OUTPUT_PATH = '/cns/jv-d/home/datcom/panesar/test'
_OUTPUT_PATH_LOCAL = '/tmp/fbi'

_GEOCODE_FILE = 'city_geocodes.csv'
_GEOCODE_MANUAL = 'manual_geocodes.csv'

# dict_reader = importlib.import_module(
#     'google3.datacommons.import.tools.dict_reader')

_POSTFIXES_TO_DROP = set([
    'city', 'town', 'CDP', 'municipality', 'barrio', 'village', 'barrio-pueblo',
    '(balance)', 'County', 'urban', u'county', u'corporation', u'urbana',
    u'City', u'comunidad', u'government'
])
# 'borough', 'township'
# ['barrio-pueblo', 'barrio', 'purchase', 'borough',]
_COUSUBS_POSTFIXES_TO_DROP = set(['borough', 'town', 'city'])

_CRIME_FIELDS_FULL = [
    'Year', 'State', 'City', 'Population', 'Violent crime',
    'Murder and nonnegligent manslaughter', 'Rape (revised definition)1',
    'Rape (legacy definition)2', 'Robbery', 'Aggravated assault',
    'Property crime', 'Burglary', 'Larceny- theft', 'Motor vehicle theft',
    'Arson3'
]

_CRIME_FIELDS = [
    'Year',
    'State',
    'City',
    'Population',
    # Violent Crimes
    'Violent',
    'ViolentMurderAndNonNegligentManslaughter',
    'ViolentRape',
    'Rape2',
    'ViolentRobbery',
    'ViolentAggravatedAssault',
    # Property Crimes
    'Property',
    'PropertyBurglary',
    'PropertyLarcenyTheft',
    'PropertyMotorVehicleTheft',
    # Arson
    'PropertyArson',
]

_CITY_MAP = {'monroe township nj': 'monroe township gloucester county nj'}

# flags.DEFINE_boolean('test', False, 'Run a subset for test?')

_all_prefixes = set()


def canonicalize_city_name(name, state, type):
    # Canaonicalize name of place from Gaz
    # Type =
    # remove city from name
    try:
        n, postfix = name.rsplit(' ', 1)
    except ValueError:
        postfix = ''
        n = name
        print('value error {}'.format(name))

    # Drop postfix if it is in the postfix_list
    if type == 'Place':
        postfix_list = _POSTFIXES_TO_DROP
    elif type == 'Cousub':
        postfix_list = _COUSUBS_POSTFIXES_TO_DROP

    if postfix and postfix not in postfix_list:
        n = u'{} {}'.format(n, postfix)

    name_str = n.lower().strip()
    state = state.lower()
    return u'{} {}'.format(name_str, state)


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


def read_places(places, cities_all, place_type):
    # Place type is 'Place', 'Cousub', etc corr to gaz
    count_places = 0
    ignore_postfix = 0
    ignore_funcstat = 0
    ignore_total = 0

    for place in places:
        count_places += 1
        ignore_this_place = False

        # Active govt entities are A, B, C, E, G
        if place['FUNCSTAT'] not in ('A', 'B', 'C', 'E', 'G'):
            ignore_this_place = True
            ignore_funcstat += 1
        if ignore_this_place:
            ignore_total += 1
            # print(u'ignoring {} {}'.format(place['NAME'], place['FUNCSTAT']))
            continue
        cn = canonicalize_city_name(place['NAME'], place['USPS'], place_type)
        count_places += 1
        cities_all[cn] = place
    logging.info(
        'Total places {}, ignore {}, ignore name {}, ignore funcstat {}'.format(
            count_places, ignore_total, ignore_postfix, ignore_funcstat))


_POP_TEMPLATE = ('Node: FBI_{crime}_geoId_{geo}\n'
                 'typeOf: schema:StatisticalPopulation\n'
                 'populationType: schema:CriminalActivities\n'
                 'crimeType: schema:FBI_{crime}\n'
                 'location: dcid:geoId/{geo}\n')


def construct_pop(geo_id, crime_type):
    return _POP_TEMPLATE.format(crime=crime_type, geo=geo_id)


_OBS_TEMPLATE = ('Node: Obs_FBI_{crime}_geoId_{geo}_{year}\n'
                 'typeOf: schema:Observation\n'
                 'observationDate: "{year}"\n'
                 'observationPeriod: "P1Y"\n'
                 'measuredValue: {value}\n'
                 'measuredProperty: dcs:count\n'
                 'observedNode: l:FBI_{crime}_geoId_{geo}\n')

# Node: Obs_3_FBI_Property_geoId_2635480
# typeOf: schema:Observation
# observationDate: "2012"
# observationPeriod: "P1Y"
# measuredValue: 97
# measuredProperty: dcs:count
# observedNode: l:FBI_Property_geoId_2635480


def construct_obs(year, crime_type, geo_id, value):
    return _OBS_TEMPLATE.format(year=year,
                                crime=crime_type,
                                geo=geo_id,
                                value=value)


def write_mcf(geocode, crime_type, value, year, mcf_output_f, mcf_names):
    mcf_output_f.write(construct_pop(geo_id=geocode, crime_type=crime_type))
    pop_name = 'FBI_{crime}_geoId_{geo}'.format(crime=crime_type, geo=geocode)

    mcf_output_f.write('\n')
    mcf_output_f.write(
        construct_obs(geo_id=geocode,
                      crime_type=crime_type,
                      value=value,
                      year=year))
    obs_name = 'Obs_FBI_{crime}_geoId_{geo}_{year}'.format(crime=crime_type,
                                                           geo=geocode,
                                                           year=year)

    if obs_name in mcf_names:
        assert False, '{} {} {}'.format(crime_type, geocode, year)
    mcf_names.add(obs_name)
    mcf_output_f.write('\n')


def int_from_field(f):
    # Convert a field to int value. If field is empty or non-convertible, return 0.
    try:
        f = float(f)
        f = int(f)
        return f
    except ValueError as err:
        return 0


def compute_totals(r):
    # Return the violent, property, arson crimes
    # If a field is empty, it is treated as 0

    # Category 1: Violent Crimes
    violent = int_from_field(r['Violent'])

    murder = int_from_field(r['ViolentMurderAndNonNegligentManslaughter'])
    rape = int_from_field(r['ViolentRape'])
    rape2 = int_from_field(r['Rape2'])
    robbery = int_from_field(r['ViolentRobbery'])
    assault = int_from_field(r['ViolentAggravatedAssault'])
    # Fix rape value
    rape += rape2

    # Add the values back as ints
    r['ViolentMurderAndNonNegligentManslaughter'] = murder
    r['ViolentRape'] = rape
    r['ViolentRobbery'] = robbery
    r['ViolentAggravatedAssault'] = assault

    violent_computed = murder + rape + robbery + assault
    if violent_computed != violent:
        print('{} {} {} violent mismatch {} {}'.format(r['Year'], r['City'],
                                                       r['State'], violent,
                                                       violent_computed))
    #print('violent {} = murder {} + rape {} + robbery {} + assault {}'.format(
    #    violent_computed, murder, rape, robbery, assault))

    # Category 2: Property Crime
    property = int_from_field(r['Property'])

    burglary = int_from_field(r['PropertyBurglary'])
    theft = int_from_field(r['PropertyLarcenyTheft'])
    motor = int_from_field(r['PropertyMotorVehicleTheft'])

    # Add the property crime values as ints.
    r['PropertyBurglary'] = burglary
    r['PropertyLarcenyTheft'] = theft
    r['PropertyMotorVehicleTheft'] = motor

    # Compute totals
    property_computed = burglary + theft + motor

    if property_computed != property:
        print('property mismatch {} {}'.format(property, property_computed))
        print('property {} = burgulary {} + theft {} + motor {}'.format(
            property_computed, burglary, theft, motor))

    # Category 3: Arson
    arson = int_from_field(r['PropertyArson'])
    r['PropertyArson'] = arson

    total = violent_computed + property_computed + arson

    # print('total {} = violent {} + property {} + arson {}'.
    #      format(total, violent_computed, property_computed, arson))

    # Write back the totals
    r['Total'] = total
    r['Violent'] = violent_computed
    r['Property'] = property_computed


def write_geocodes():
    place_f = gfile.Open(_PLACES)
    cosubs_f = gfile.Open(_COUSUBS)

    places = dict_reader.DictReader(place_f)
    cosubs = dict_reader.DictReader(cosubs_f)
    cities_all = {}
    read_places(places, cities_all, 'Place')
    cosubs_all = {}
    read_places(cosubs, cosubs_all, 'Cousub')

    count_city = 0
    count_cousub = 0

    geocode_file = gfile.Open(os.path.join(_INPUT_DIR, _GEOCODE_FILE), 'w')
    names = set()
    # writer = unicode_csv.Writer(geocode_file)
    for place, info in cities_all.items():
        if place in names:
            logging.error('{} exists'.format(place))
        else:
            names.add(place)
        geocode_file.write(u'{},{}\n'.format(place, info['GEOID']))
        count_city += 1
    for place, info in cosubs_all.items():
        if place not in names:
            names.add(place)
            geocode_file.write(u'{},{}\n'.format(place, info['GEOID']))
            count_cousub += 1
    logging.info('cities = {}, cousub = {}'.format(count_city, count_cousub))
    geocode_file.close()


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


def read_crime_csv(geo_codes, crime_csv):
    with open(crime_csv) as crime_f:
        with open('fbi.mcf', 'w') as mcf_output_f:
            all_states = get_all_states()

            crimes = csv.DictReader(crime_f, fieldnames=_CRIME_FIELDS)

            cities_not_found = []
            count_cities_not_found = 0
            fbi_cities = 0
            count_pop_obs = 0
            count_no_obs = 0

            mcf_names = set()
            found_set = set()
            cities_not_found_set = set()

            for crime in crimes:
                try:
                    state_parts = crime['State'].split()
                    state_parts_1 = [p.capitalize() for p in state_parts]
                    # print(crime['State'])
                    # print(state_parts_1)
                    lookup_name = ''.join(state_parts_1)
                    state = all_states[lookup_name].lower()
                except KeyError:
                    logging.error('{} state not found {}'.format(
                        crime['State'], lookup_name))
                    continue
                city = normalize_fbi_city(crime['City'], state)
                year = crime['Year'].lower().strip()
                city_state = '{} {}'.format(city, state)
                one_city = {
                    'City': city,
                    'State': state,
                }

                city_state = remap_ambiguous_cities(city_state)
                fbi_cities += 1

                # Compute the geocode of the city.
                try:
                    geocode = geo_codes[city_state]
                    found_set.add('{}, {}'.format(state, city))
                except KeyError:
                    one_city['Population'] = crime['Population']
                    # if year == '2017':
                    cities_not_found.append(one_city)
                    cities_not_found_set.add('{}, {}'.format(state, city))
                    continue
                one_city['geocode'] = geocode

                # Sum the violent crimes
                compute_totals(crime)

                for k, value in crime.items():
                    if k in ['Year', 'State', 'City', 'Population', 'Rape2']:
                        continue

                    if crime[k] != '':
                        write_mcf(geocode, k, value, year, mcf_output_f,
                                  mcf_names)
                        count_pop_obs += 1
                    else:
                        print('No obs for {} {} {}'.format(year, city_state, k))
                        count_no_obs += 1

            # Output the cities not_found
            with open('city_not_found.txt', 'w') as cities_not_found_f:
                count_not_found = len(cities_not_found)
                for s in cities_not_found:
                    city = s['City']
                    state = s['State']
                    cities_not_found_f.write('{},{},{}\n'.format(
                        s['Population'], state, city))

            print('US src_cities = {}, cities_not_found = {}'.format(
                len(found_set), len(cities_not_found_set)))
            print('Count pob+obs {}, no_obs {}'.format(count_pop_obs,
                                                       count_no_obs))


# def main(argv):
#   if len(argv) > 1:
#     raise app.UsageError('Too many command-line arguments.')
#   # write_geocodes()
#   # print(geo_codes['springdale pa'])
#   # print(geo_codes['san jose ca'])

#   if FLAGS.test:
#     geo_codes = read_geocodes('google3/datacommons/mcf/crime')
#     read_crime_csv(geo_codes, _CRIME_CSV_LOCAL, _OUTPUT_PATH_LOCAL)
#   else:
#     geo_codes = read_geocodes(_INPUT_DIR)
#     read_crime_csv(geo_codes, _CRIME_CSV, _OUTPUT_PATH)

if __name__ == '__main__':
    app.run(main)
