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
'''This script does not use the most up-to-date schema format. 
It should only be used as an illustration of the SDMX -> MCF mapping.
Do not actually run!

Produces CSV/TMCF + schema for UN Stats data.

Produces:
* output/output.csv: cleaned CSV
* output/measurement_method.csv: measurement methods
* output/schema.mcf: properties and classes
* output/sv.mcf: statistical variables
* output/unit.mcf: units
Usage: python3 preprocess.py
'''
import collections
import csv
import os
import sys

from util import *

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

module_dir_ = os.path.dirname(__file__)

# Create map of M49 -> ISO-alpha3 for countries.
with open(os.path.join(module_dir_, 'm49.tsv')) as f:
    PLACES = {}
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if not row['ISO-alpha3 code']:  # Only countries for now.
            continue
        PLACES[int(row['M49 code'])] = row['ISO-alpha3 code']

# Create map of name -> dcid for supported cities.
with open(os.path.join(module_dir_, 'preprocessed/cities.csv')) as f:
    reader = csv.DictReader(f)
    CITIES = {row['name']: row['dcid'] for row in reader}


def write_templates(file, templates):
    '''Write templates to file.
    Args:
        file: Input file path.
        templates: Template strings.
    '''
    with open(file, 'w') as f:
        for template in sorted(templates):
            f.write(template)


def add_concepts(file, concepts):
    '''Adds concepts from file.
    Args:
        file: Input file path.
        concepts: Dictionary of concepts: concept -> code -> (name, formatted code).
    '''
    with open(file) as f:
        reader = csv.reader(f)
        for row in reader:

            # Skip totals (as indicated by SDMX).
            if row[3] == '_T':
                continue
            concepts[row[0]][row[1]] = (row[2], make_value(row[1]))


def get_observation_about(country_code, country_name, city):
    '''Returns dcid for place.
    Args:
        country_code: M49 for country.
        country_name: Name of country.
        city: Name of city.
    Returns:
        Dcid of place if found, else empty string.
    '''
    if city:
        formatted_city = city.replace('_', ' ').title() + ', ' + country_name
        if formatted_city in CITIES and CITIES[formatted_city]:
            return 'dcs:' + CITIES[formatted_city]
        else:
            return ''
    if country_code in PLACES:
        return 'dcs:country/' + PLACES[country_code]
    else:
        return ''


def get_variable_measured(row, properties, concepts):
    '''Returns templated string for variable_measured.
    Args:
        row: Input csv dict row.
        properties: List of properties for row.
        concepts: Dictionary of concepts.
    Returns:
        Templated string.
    '''
    value_ids = []
    value_descriptions = []
    cprops = ''
    for i in properties:
        field = i[1:-1]
        if not row[i] or field not in concepts or row[i] not in concepts[field]:
            continue
        value_ids.append(concepts[field][row[i]][1])
        value_descriptions.append(concepts[field][row[i]][0])
        enum = make_property(field)
        if field in MAPPED_CONCEPTS:
            prop = MAPPED_CONCEPTS[field]
        else:
            prop = 'sdg_' + enum[0].lower() + enum[1:]
        val = enum + 'Enum_' + value_ids[-1]
        cprops += f'\n{prop}: dcs:SDG_{val}'
    sv = 'sdg/' + '_'.join([row['SeriesCode']] + value_ids)
    pvs = ', '.join(value_descriptions)
    description = format_description(row['SeriesDescription'])
    if pvs:
        description += ': ' + pvs
    template = SV_TEMPLATE.format_map({
        'dcid': sv,
        'popType': 'SDG_' + row['SeriesCode'],
        'name': '"' + description + '"',
        'cprops': cprops
    })
    return template


def get_measurement_method(row, concepts):
    '''Returns templated string for measurement_method.
    Args:
        row: Input csv dict row.
        concepts: Dictionary of concepts.
    Returns:
        Templated string.
    '''
    mmethod = ''
    description = []
    for concept in [
            '[Nature]', '[Observation Status]', '[Report Ordinal]',
            '[Reporting Type]'
    ]:
        field = concept[1:-1]
        if concept in row:
            mmethod += '_' + row[concept]
            if field in concepts and row[concept] in concepts[field]:
                description.append(concepts[field][row[concept]][0])
    if not mmethod:
        return ''
    mmethod = 'SDG' + mmethod
    description = 'SDG Measurement Method: ' + ', '.join(
        description) if description else ''
    template = MMETHOD_TEMPLATE.format_map({
        'dcid': mmethod,
        'description': description
    })
    return template


def get_unit(row):
    '''Returns templated string for unit.
    Args:
        row: Input csv dict row.
    Returns:
        Templated string.
    '''
    if not '[Units]' in row:
        return ''
    unit = row['[Units]'].replace('^', '')
    template = UNIT_TEMPLATE.format_map({
        'dcid': unit,
        'name': format_unit_name(unit)
    })
    return template


def write_schema(file, concepts):
    '''Writes schema from concepts to file.
    Args:
        file: Input file path.
        concepts: Dictionary of concepts.
    '''
    with open(file, 'w') as f:
        for concept in sorted(concepts):
            if concept in SKIPPED_CONCEPTS:
                continue
            prop = make_property(concept)
            enum = prop + 'Enum'
            if concept not in MAPPED_CONCEPTS:
                f.write(
                    PROPERTY_TEMPLATE.format_map({
                        'dcid': prop[0].lower() + prop[1:],
                        'name': concept,
                        'enum': enum
                    }))
            f.write(ENUM_TEMPLATE.format_map({'enum': enum}))
            for k in sorted(concepts[concept]):
                v = concepts[concept][k]
                f.write(
                    VALUE_TEMPLATE.format_map({
                        'dcid': v[1],
                        'enum': enum,
                        'name': v[0][0].upper() + v[0][1:],
                    }))


def process_input_file(file, writer, concepts, svs, measurement_methods, units):
    '''Processes one input file and write csv rows.
    Args:
        file: Input file path.
        writer: Csv DictWriter object.
        concepts: Dictionary of concepts.
        svs: Set of statistical variables.
        measurement_methods: Set of measurement methods.
        units: Set of units.
    '''
    print(f'Starting {file}')
    with open(file) as f_in:
        reader = csv.DictReader(f_in)
        properties = sorted([
            field for field in reader.fieldnames
            if field[0] == '[' and field[1:-1] not in SKIPPED_CONCEPTS
        ])
        try:
            for row in reader:
                if not int(row['GeoAreaCode']) in PLACES:
                    continue
                if not is_float(row['Value']) or row['Value'] == 'NaN' or row[
                        'Value'] == 'Nan':
                    continue
                observation_about = get_observation_about(
                    int(row['GeoAreaCode']), row['GeoAreaName'],
                    row['[Cities]'] if '[Cities]' in reader.fieldnames else '')
                if not observation_about:
                    continue
                sv = get_variable_measured(row, properties, concepts)
                svs.add(sv)
                measurement_method = get_measurement_method(row, concepts)
                if measurement_method:
                    measurement_methods.add(measurement_method)
                unit = get_unit(row)
                if unit:
                    units.add(unit)
                writer.writerow({
                    'variable_measured':
                        'dcid:' + get_dcid(sv),
                    'observation_about':
                        observation_about,
                    'observation_date':
                        row['TimePeriod'],
                    'value':
                        row['Value'],
                    'measurement_method':
                        'dcs:' + get_dcid(measurement_method)
                        if measurement_method else '',
                    'unit':
                        'dcs:' + get_dcid(unit) if unit else '',
                    'scaling_factor':
                        row['[UnitMultiplier]']
                        if '[UnitMultiplier]' in reader.fieldnames else '',
                })
        except:
            print(f'Finished processing {file}')


if __name__ == '__main__':
    concepts = collections.defaultdict(dict)
    add_concepts('preprocessed/attributes.csv', concepts)
    add_concepts('preprocessed/dimensions.csv', concepts)
    write_schema('output/schema.mcf', concepts)

    svs = set()
    measurement_methods = set()
    units = set()
    with open('output/output.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for file in sorted(os.listdir('input')):
            process_input_file(os.path.join('input', file), writer, concepts,
                               svs, measurement_methods, units)

    write_templates('output/measurement_method.mcf', measurement_methods)
    write_templates('output/sv.mcf', svs)
    write_templates('output/unit.mcf', units)
