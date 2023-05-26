import collections
import csv
import os
import re
import requests

from util import *


def get_observation_about(country_code, country_name, city, concepts, places):
    if city:
        formatted_city = city.replace('_', ' ').title() + ', ' + country_name
        if formatted_city in cities and cities[formatted_city]:
            return 'dcs:' + cities[formatted_city]
        else:
            return ''
    if country_code in places:
        return 'dcs:country/' + places[country_code]
    else: 
        return ''

def get_measurement_method(row, concepts):
    mmethod = ''
    description = []
    for concept in ['[Nature]', '[Observation Status]', '[Report Ordinal]', '[Reporting Type]']:
        field = concept[1:-1]
        if concept in row:
            mmethod += '_' + row[concept]
            if field in concepts and row[concept] in concepts[field]:
                description.append(concepts[field][row[concept]][0])
    if mmethod:
        mmethod = 'SDG' + mmethod
    description = 'SDG Measurement Method: ' + ', '.join(description) if description else ''
    return (mmethod, description)


concepts = collections.defaultdict(dict)
with open('preprocessed/attributes.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        if row[3] == '_T':
            continue
        concepts[row[0]][row[1]] = (row[2], make_value(row[1]))

with open('preprocessed/dimensions.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        if row[3] == '_T':
            continue
        concepts[row[0]][row[1]] = (row[2], make_value(row[1]))

with open('output/schema.mcf', 'w') as f:
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

with open('m49.csv') as f:
    places = {}
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if not row['ISO-alpha3 code']:  # Only countries for now.
            continue
        places[int(row['M49 code'])] = row['ISO-alpha3 code']

with open('preprocessed/cities.csv') as f:
    reader = csv.DictReader(f)
    cities = {row['name']: row['dcid'] for row in reader}




measurement_methods = set()
scaling_factors = set()
units = set()
with open('output/sv.mcf', 'w') as f_sv:
    with open('output/output.csv', 'w') as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=['variable_measured', 'observation_about', 'observation_date', 'value', 'measurement_method', 'unit'])
        writer.writeheader()
        svs = set()
        for file in sorted(os.listdir('input')):
            code = file.removesuffix('.csv')
            print(f'Starting {code}')
            with open('input/' + file) as f_in:
                reader = csv.DictReader(f_in)
                properties = sorted([
                    field for field in reader.fieldnames
                    if field[0] == '[' and field[1:-1] not in SKIPPED_CONCEPTS
                ])
                try:
                    for row in reader:
                        if not int(row['GeoAreaCode']) in places:
                            continue
                        if not is_float(row['Value']) or row['Value'] == 'NaN' or row['Value'] == 'Nan':
                            continue
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
                        observation_about = get_observation_about(int(row['GeoAreaCode']), row['GeoAreaName'], row['[Cities]'] if '[Cities]' in reader.fieldnames else '', concepts, places)
                        if not observation_about:
                            continue
                        measurement_method = get_measurement_method(row, concepts)
                        if measurement_method[0]:
                            measurement_methods.add(measurement_method)
                        scaling_factor = row['[UnitMultiplier]'] if '[UnitMultiplier]' in reader.fieldnames else ''
                        if scaling_factor:
                            scaling_factors.add(scaling_factor)
                        unit = row['[Units]'].replace('^', '') if '[Units]' in reader.fieldnames else ''
                        if unit:
                            units.add(unit)
                        writer.writerow({
                            'variable_measured': 'dcid:' + sv,
                            'observation_about': observation_about,
                            'observation_date': row['TimePeriod'],
                            'value': row['Value'],
                            'measurement_method': 'dcs:' + measurement_method[0] if measurement_method[0] else '',
                            'unit': 'dcs:' + unit if unit else '',
                        })
                        if sv in svs:
                            continue
                        svs.add(sv)
                        description = format_description(row['SeriesDescription'])
                        pvs = ', '.join(value_descriptions)
                        if pvs:
                            description += ': ' + pvs
                        f_sv.write(
                            SV_TEMPLATE.format_map({
                                'dcid': sv,
                                'popType': 'SDG_' + row['SeriesCode'],
                                'name': '"' + description + '"',
                                'cprops': cprops,
                            }))
                except:
                    print(f'Finished processing {code}')


with open('output/supplementary_schema.mcf', 'w') as f:
    for scaling_factor in sorted(scaling_factors):
        print(scaling_factor)
    for mmethod in sorted(measurement_methods):
        f.write(MMETHOD_TEMPLATE.format_map({
            'dcid': mmethod[0],
            'description': mmethod[1]
        }))
    for unit in sorted(units):
        f.write(UNIT_TEMPLATE.format_map({
            'dcid': unit,
            'name': format_unit_name(unit)
        }))