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
'''Process OECD datasets.

Produces: 
* output/<CODE>.csv: Folder of cleaned csvs.
* schema/svg.mcf: SVG custom hierarchy.
* schema/measurement_method.mcf
* schema/unit.mcf
* sv/<CODE>.csv: Folder of stat var mcf.

Usage: python3 process.py
'''
import csv
import json
import os

FIELDNAMES = [
    'observation_about', 'variable_measured', 'value', 'observation_date',
    'observation_period', 'measurement_method', 'unit', 'scaling_factor'
]
SKIPPED = {
    'AMOUNTTYPE',  # Use UNIT instead.
    'FREQUENCY',  # Use TIME_FORMAT instead.
}
with open('countries') as f:
    COUNTRIES = set(f.read().split())
SV_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
measuredProperty: dcid:{dcid}
memberOf: dcs:{svg}
name: "{name}"
populationType: dcs:Thing
statType: dcs:measuredValue
'''
SVG_ROOT = '''
Node: dcid:oecd/g/OECD
typeOf: dcs:StatVarGroup
name: "Organisation for Economic Co-operation and Development"
specializationOf: dcs:dc/g/Root
'''
SVG_TEMPLATE = '''
Node: dcid:oecd/g/{dcid}
typeOf: dcs:StatVarGroup
name: "{name}"
specializationOf: dcs:oecd/g/OECD
'''
MEASUREMENT_METHOD_CLASS = '''
Node: dcid:OECD_MeasurementMethodEnum
typeOf: schema:Class
name: "OECD_MeasurementMethodEnum"
subClassOf: dcs:Enumeration
'''
MEASUREMENT_METHOD_TEMPLATE = '''
Node: dcid:OECD_{dcid}
typeOf: dcs:OECD_MeasurementMethodEnum
name: "{dcid}"
description: "OECD Measurement Method: {name}"
'''
UNIT_TEMPLATE = '''
Node: dcid:OECD_{dcid}
typeOf: dcs:UnitOfMeasure
name: "{dcid}"
description: "OECD Unit: {name}"
'''


def get_value(a, idx, key, prop):
    '''Fetches value for given index, key, and property.

    Args:
        a: Input structure (dimensions or attributes).
        idx: Index of concept.
        key: List of concept keys.
        prop: Property.

    Returns: 
        Corresponding value, if it exists.
    '''
    if not a[idx]['values']:
        return ''
    if key[idx] is None:
        return ''
    return a[idx]['values'][key[idx]][prop]


def make_sv(code, series, dim, attr, dim_idx, attr_idx, dim_key, attr_key):
    '''Generates stat var.

    Args:
        code: Series code.
        series: Series name.
        dim: Dimensions structure.
        attr: Attributes structure.
        dim_idx: List of dimension indices to keep.
        attr_idx: List of attribute indices to keep.
        dim_key: List of dimension keys.
        attr_key: List of attribute keys.

    Returns:
        Tuple of stat var (dcid, name, series code).
    '''
    dcid = 'oecd/' + code
    name = series
    values = []
    for idx in dim_idx:
        i = get_value(dim, idx, dim_key, 'id')
        if i:
            dcid += '_' + i
            values.append(get_value(dim, idx, dim_key, 'name').strip())
    for idx in attr_idx:
        i = get_value(attr, idx, attr_key, 'id')
        if i:
            dcid += '_' + i
            values.append(get_value(attr, idx, attr_key, 'name').strip())
    if values:
        name += ': ' + ', '.join(values)
    return (dcid, name, code)


def make_date(s):
    '''Formats date.

    Args:
        s: Input string.

    Returns:
        Formatted date.
    '''
    date = s.replace('B1', '01')
    date = date.replace('B2', '06')
    date = date.replace('Q1', '01')
    date = date.replace('Q2', '03')
    date = date.replace('Q3', '06')
    return date.replace('Q4', '09')


def write_schema(file, prefix, items, template):
    '''Writes mcf to file.

    Args:
        file: Output file path.
        prefix: Optional prefix MCF.
        items: Set of MCF to write.
        template: Template string to match.
    '''
    with open(file, 'w') as f:
        f.write(prefix)
        for x in sorted(items):
            f.write(template.format_map({
                'dcid': x[0],
                'name': x[1],
            }))


if __name__ == '__main__':
    if not os.path.exists('output'):
        os.makedirs('output')
    if not os.path.exists('sv'):
        os.makedirs('sv')
    if not os.path.exists('schema'):
        os.makedirs('schema')

    svgs = set()
    measurement_methods = set()
    units = set()
    for file in sorted(os.listdir('input')):
        with open(f'input/{file}') as f_in:
            code = file.removesuffix('.json')
            print(code)
            try:
                data = json.load(f_in)
            except:
                print('Error loading:', file)
                continue

            s = data['structure']

            dimensions = []
            location_idx = None
            dates = []
            dim_idx = []
            for x in s['dimensions']:
                for y in s['dimensions'][x]:
                    if 'keyPosition' in y:
                        dimensions.insert(int(y['keyPosition']), y)
                    if y['id'] == 'LOCATION':
                        location_idx = y['keyPosition']
                    elif y['id'] == 'TIME_PERIOD':
                        dates = [make_date(date['id']) for date in y['values']]
                    elif y['id'] not in SKIPPED:
                        dim_idx.append(y['keyPosition'])

            # Only support LOCATION for observation_about for now.
            if location_idx is None:
                continue

            # Only support TIME_PERIOD for observation_date for now.
            if not dates:
                continue

            attributes = s['attributes']['series']
            observation_period_idx = None
            unit_idx = None
            scaling_factor_idx = None
            attr_idx = []
            for i, x in enumerate(attributes):
                if x['id'] == 'TIME_FORMAT':
                    observation_period_idx = i
                elif x['id'] == 'UNIT':
                    unit_idx = i
                elif x['id'] == 'POWERCODE':
                    scaling_factor_idx = i
                elif x['id'] not in SKIPPED:
                    attr_idx.append(i)

            if observation_period_idx is None:
                continue

            obs_status = []
            for x in s['attributes']['observation']:
                if x['id'] == 'OBS_STATUS':
                    obs_status = x['values']
                else:
                    print('Additional observation attribute:', x['id'], code)

            svs = set()
            with open(f'output/{code}.csv', 'w') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=FIELDNAMES)
                writer.writeheader()
                d = data['dataSets'][0]
                for dimension_key in d['series']:
                    dim_key = [int(x) for x in dimension_key.split(':')]
                    observation_about = get_value(dimensions, location_idx,
                                                  dim_key, 'id')

                    # Only support countries for now.
                    if observation_about not in COUNTRIES:
                        continue

                    attr_key = d['series'][dimension_key]['attributes']
                    sv = make_sv(code, s['name'], dimensions, attributes,
                                 dim_idx, attr_idx, dim_key, attr_key)

                    observation_period = get_value(attributes,
                                                   observation_period_idx,
                                                   attr_key, 'id')
                    if not observation_period:
                        continue

                    unit = get_value(attributes, unit_idx, attr_key,
                                     'id') if unit_idx is not None else ''
                    scaling_factor = get_value(
                        attributes, scaling_factor_idx, attr_key,
                        'id') if scaling_factor_idx is not None else ''

                    obs = d['series'][dimension_key]['observations']
                    for date_key in obs:
                        value = obs[date_key][0]
                        if not value:
                            continue

                        measurement_method = obs_status[
                            obs[date_key][1]] if obs_status and len(
                                obs[date_key]) > 1 and obs[date_key][1] else ''
                        writer.writerow({
                            'observation_about':
                                f'dcs:country/{observation_about}',
                            'variable_measured':
                                'dcs:' + sv[0],
                            'value':
                                value,
                            'observation_date':
                                dates[int(date_key)],
                            'observation_period':
                                observation_period,
                            'measurement_method':
                                'dcs:OECD_' +
                                measurement_method['id'].replace('; ', '_')
                                if measurement_method else '',
                            'unit':
                                f'dcs:OECD_{unit}' if unit else '',
                            'scaling_factor':
                                scaling_factor,
                        })

                        if measurement_method:
                            measurement_methods.add(
                                (measurement_method['id'].replace('; ', '_'),
                                 measurement_method['name']))

                    svs.add(sv)
                    svgs.add((code, s['name']))
                    if unit:
                        units.add((unit,
                                   get_value(attributes, unit_idx, attr_key,
                                             'name')))

            if svs:
                with open(f'sv/{code}.mcf', 'w') as f_out:
                    for x in sorted(svs):
                        f_out.write(
                            SV_TEMPLATE.format_map({
                                'dcid': x[0],
                                'name': x[1].replace('"', '\''),
                                'svg': 'oecd/g/' + x[2],
                            }))

    if svgs:
        write_schema('schema/svg.mcf', SVG_ROOT, svgs, SVG_TEMPLATE)

    if measurement_methods:
        write_schema('schema/measurement_method.mcf', MEASUREMENT_METHOD_CLASS,
                     measurement_methods, MEASUREMENT_METHOD_TEMPLATE)

    if units:
        write_schema('schema/unit.mcf', '', units, UNIT_TEMPLATE)
