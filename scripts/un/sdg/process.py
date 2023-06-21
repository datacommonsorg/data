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
'''Generates mcf and csv/tmcf for sdg-dataset data.

Produces:
* schema/ folder: 
- measurement_method.mcf
- schema.mcf (classes and enums)
- sdg.textproto (vertical spec)
- series.mcf (series mcf)
- sv.mcf
- unit.mcf
* csv/ folder: 
- [CODE].csv

Usage: python3 process.py
'''
import os
import pandas as pd

import util


def get_geography(code, type):
    '''Returns dcid of geography.

    Args:
        code: Geography code.
        type: Geography type.

    Returns:
        Geography dcid.
    '''

    # Currently only support Country and City.
    if type == 'Country' and code in util.PLACES:
        return 'dcs:country/' + util.PLACES[code]
    elif type == 'City' and code in util.CITIES and util.CITIES[code]:
        return 'dcs:' + util.CITIES[code]
    return ''


def get_unit(units, base_period):
    '''Returns dcid of unit.

    Args:
        unit: Unit.
        base_period: Base period of unit.

    Returns:
        Unit dcid.
    '''
    if util.is_valid(base_period):
        return f'[{units} {base_period}]'
    return 'dcs:SDG_' + units


def get_measurement_method(row):
    '''Returns dcid of measurement method.

    Args:
        row: Input DataFrame row.
    
    Returns:
        Measurement method dcid.
    '''
    mmethod = ''
    if util.is_valid(row['NATURE']):
        mmethod += '_' + str(row['NATURE'])
    if util.is_valid(row['OBSERVATION_STATUS']):
        mmethod += '_' + str(row['OBSERVATION_STATUS'])
    if util.is_valid(row['REPORTING_TYPE']):
        mmethod += '_' + str(row['REPORTING_TYPE'])
    return 'SDG' + mmethod


def process(input_dir, schema_dir, csv_dir):
    '''Generates mcf, csv/tmcf artifacts.
    
    Args:
        input_dir: Path to input xlsx files.
        schema_dir: Path to output schema files.
        csv_dir: Path to output csv files.
    '''
    with open(os.path.join(schema_dir, 'series.mcf'), 'w') as f_series:
        with open(os.path.join(schema_dir, 'sdg.textproto'), 'w') as f_vertical:
            df = pd.read_excel(os.path.join(input_dir, 'sdg_hierarchy.xlsx'))
            for _, row in df.iterrows():
                f_series.write(
                    util.SERIES_TEMPLATE.format_map({
                        'dcid':
                            'SDG_' + str(row['SeriesCode']),
                        'description':
                            util.format_description(str(row['SeriesDescription']))
                    }))
                f_vertical.write('spec: {\n'
                                 '  pop_type: "SDG_' + str(row['SeriesCode']) +
                                 '"\n'
                                 '  obs_props { mprop: "value" }\n'
                                 '  vertical: "SDG_' +
                                 str(row['IndicatorRefCode']) + '"\n'
                                 '}\n')

    # Process dimensions.
    dimensions = {}
    for root, _, files in os.walk(os.path.join(input_dir, 'code_lists')):
        for file in sorted(files):
            dimension = file.removeprefix('CL__').removesuffix('.xlsx')

            # Get names directly from observation files.
            if dimension in {'SERIES', 'VARIABLE'}:
                continue

            path = os.path.join(root, file)
            df = pd.read_excel(path)
            dimensions[dimension] = {
                str(row['EnumerationValue_Code']): row['EnumerationValue_Name']
                for _, row in df.iterrows()
            }

    sv_frames = []
    measurement_method_frames = []
    units = set()
    for root, _, files in os.walk(os.path.join(input_dir, 'observations')):
        for file in sorted(files):
            print(file)
            df = pd.read_excel(os.path.join(root, file))
            if df.empty:
                continue

            properties = list(
                filter(lambda x: x not in util.BASE_DIMENSIONS, df.columns))

            # Drop rows with nan.
            df = df.dropna(subset=[
                'VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'VALUE'
            ])
            if df.empty:
                continue

            # Drop invalid values.
            df['VALUE'] = df['VALUE'].apply(lambda x: x if util.is_float(x) else '')
            df = df[df['VALUE'] != '']
            if df.empty:
                continue

            # Format places.
            df['GEOGRAPHY_CODE'] = df.apply(lambda x: get_geography(
                x['GEOGRAPHY_CODE'], x['GEOGRAPHY_TYPE']),
                                            axis=1)
            df = df[df['GEOGRAPHY_CODE'] != '']
            if df.empty:
                continue

            # Special curation of names.
            df['VARIABLE_DESCRIPTION'] = df.apply(
                lambda x: util.format_variable_description(x['VARIABLE_DESCRIPTION'],
                                                      x['SERIES_DESCRIPTION']),
                axis=1)
            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(
                lambda x: util.format_variable_code(x))

            sv_frames.append(df.loc[:,
                                    ['VARIABLE_CODE', 'VARIABLE_DESCRIPTION'] +
                                    properties].drop_duplicates())
            measurement_method_frames.append(
                df.loc[:, ['NATURE', 'OBSERVATION_STATUS', 'REPORTING_TYPE']].
                drop_duplicates())
            units.update(set(df['UNITS'].unique()))

            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(
                lambda x: 'dcs:sdg/' + x)
            df['UNITS'] = df.apply(
                lambda x: get_unit(x['UNITS'], x['BASE_PERIOD']), axis=1)
            df['MEASUREMENT_METHOD'] = df.apply(
                lambda x: 'dcs:' + get_measurement_method(x), axis=1)

            # Retain only columns for cleaned csv.
            df = df.loc[:, [
                'VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'VALUE',
                'UNITS', 'UNITMULTIPLIER', 'MEASUREMENT_METHOD'
            ]]

            code = file.removeprefix('observations_').removesuffix('.xlsx')
            df.to_csv(os.path.join(csv_dir, f'{code}.csv'), index=False)

    with open(os.path.join(schema_dir, 'sv.mcf'), 'w') as f:
        for df in sv_frames:
            for _, row in df.iterrows():
                cprops = ''
                for dimension in sorted(df.columns[2:]):
                    # Skip totals.
                    if row[dimension] == util.TOTAL:
                        continue

                    enum = util.format_property(dimension)
                    if dimension in util.MAPPED_DIMENSIONS:
                        prop = util.MAPPED_DIMENSIONS[dimension]
                    else:
                        prop = 'sdg_' + enum[0].lower() + enum[1:]
                    val = 'SDG_' + enum + 'Enum_' + str(row[dimension])
                    cprops+= f'\n{prop}: dcs:{val}'
                f.write(
                    util.SV_TEMPLATE.format_map({
                        'dcid': 'sdg/' + row['VARIABLE_CODE'],
                        'popType': 'SDG_' + row['VARIABLE_CODE'].split(':')[0],
                        'name': '"' + row['VARIABLE_DESCRIPTION'] + '"',
                        'cprops': cprops,
                    }))

    with open(os.path.join(schema_dir, 'schema.mcf'), 'w') as f:
        for d in sorted(dimensions):
            if d in util.BASE_DIMENSIONS or d == 'GEOGRAPHY':
                continue
            prop = util.format_property(d)
            enum = prop + 'Enum'
            if d not in util.MAPPED_DIMENSIONS:
                f.write(
                    util.PROPERTY_TEMPLATE.format_map({
                        'dcid': prop[0].lower() + prop[1:],
                        'name': util.format_title(d),
                        'enum': enum
                    }))
            f.write(util.ENUM_TEMPLATE.format_map({'enum': enum}))
            for k in sorted(dimensions[d]):

                # Skip totals.
                if k == util.TOTAL:
                    continue

                v = dimensions[d][k]
                f.write(
                    util.VALUE_TEMPLATE.format_map({
                        'dcid': k,
                        'enum': enum,
                        'name': v,
                    }))

    with open(os.path.join(schema_dir, 'measurement_method.mcf'), 'w') as f:
        df = pd.concat(measurement_method_frames).drop_duplicates()
        for _, row in df.iterrows():
            dcid = get_measurement_method(row)
            if not dcid:
                continue
            description = 'SDG Measurement Method: ['
            pvs = []
            for dimension in sorted(df.columns):
                if not util.is_valid(row[dimension]):
                    continue
                pvs.append(
                    util.format_title(dimension) + ' = ' +
                    dimensions[dimension][row[dimension]])
            f.write(
                util.MMETHOD_TEMPLATE.format_map({
                    'dcid': dcid,
                    'description': description + ', '.join(pvs) + ']'
                }))

    with open(os.path.join(schema_dir, 'unit.mcf'), 'w') as f:
        for unit in sorted(units):
            f.write(
                util.UNIT_TEMPLATE.format_map({
                    'dcid': 'SDG_' + unit,
                    'name': dimensions['UNITS'][unit]
                }))


if __name__ == '__main__':
    if not os.path.exists('schema'):
        os.makedirs('schema')
    if not os.path.exists('csv'):
        os.makedirs('csv')
    process('sdg-dataset/output', 'schema', 'csv')
