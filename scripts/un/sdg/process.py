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
  * measurement_method.mcf
  * schema.mcf (classes and enums)
  * sdg.textproto (vertical spec)
  * series.mcf (series mcf)
  * sv.mcf
  * unit.mcf
* csv/ folder: 
  * [CODE].csv

Usage: python3 process.py
'''
import collections
import os
import pandas as pd
import shutil
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import util


def get_geography(code, type):
    '''Returns dcid of geography.

    Args:
        code: Geography code.
        type: Geography type.

    Returns:
        Geography dcid.
    '''

    # Currently only support Country, City, and select Regions .
    if code in util.REGIONS:
        return 'dcs:' + util.REGIONS[code]
    elif type == 'Country' and code in util.PLACES:
        return 'dcs:country/' + util.PLACES[code]
    elif type == 'City':
        # Remove country prefix for now.
        city = '_'.join(code.split('_')[1:])
        if city in util.CITIES and util.CITIES[city]:
            return 'dcs:' + util.CITIES[city]
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
    if util.is_valid(row['OBS_STATUS']):
        mmethod += '_' + str(row['OBS_STATUS'])
    if util.is_valid(row['REPORTING_TYPE']):
        mmethod += '_' + str(row['REPORTING_TYPE'])
    return 'SDG' + mmethod


def process(input_dir, schema_dir, csv_dir):
    '''Generates mcf, csv/tmcf artifacts.

    Produces:
    * schema/ folder: 
      * measurement_method.mcf
      * schema.mcf (classes and enums)
      * sdg.textproto (vertical spec)
      * series.mcf (series mcf)
      * sv.mcf
      * unit.mcf
    * csv/ folder: 
      * [CODE].csv
    
    Args:
        input_dir: Path to input xlsx files.
        schema_dir: Path to output schema files.
        csv_dir: Path to output csv files.
    '''
    with open(os.path.join(schema_dir, 'series.mcf'), 'w') as f_series:
        with open(os.path.join(schema_dir, 'sdg.textproto'), 'w') as f_vertical:
            df = pd.read_csv(os.path.join(input_dir, 'SDG_hierarchy.csv'))
            descriptions = {}
            for _, row in df.iterrows():
                if not util.is_valid(row['SeriesCode']):
                    continue
                descriptions[str(row['SeriesCode'])] = util.format_description(
                    row['SeriesDescription'])
                f_vertical.write('spec: {\n'
                                 '  pop_type: "SDG_' + str(row['SeriesCode']) +
                                 '"\n'
                                 '  obs_props { mprop: "value" }\n'
                                 '  vertical: "SDG_' +
                                 str(row['IndicatorRefCode']) + '"\n'
                                 '}\n')
            for code in sorted(descriptions):
                f_series.write(
                    util.SERIES_TEMPLATE.format_map({
                        'dcid': 'SDG_' + code,
                        'description': descriptions[code]
                    }))

    # Process dimensions.
    dimensions = collections.defaultdict(dict)
    df = pd.read_csv(os.path.join(input_dir, 'SDG_enumerations.csv'))

    # Replace buggy input text.
    df = df.replace('CIT_ OF_WROCLAW', 'CITY_OF_WROCLAW')

    for _, row in df.iterrows():
        if str(row['Enumeration_Code_SDMX']) != 'CUST_BREAKDOWN' and str(
                row['Enumeration_Code_SDMX']) != 'COMPOSITE_BREAKDOWN':
            dimensions[str(row['Enumeration_Code_SDMX'])][str(
                row['EnumerationValue_Code_SDMX'])] = str(
                    row['EnumerationValue_Name'])
        else:
            dimensions[str(row['Enumeration_Code2'])][str(
                row['EnumerationValue_Code2'])] = str(
                    row['EnumerationValue_Name'])

    sv_frames = []
    measurement_method_frames = []
    units = set()
    for root, _, files in os.walk(os.path.join(input_dir, 'observations')):
        for file in sorted(files):
            print(file)
            df = pd.read_csv(os.path.join(root, file))
            if df.empty:
                continue

            properties = list(
                filter(lambda x: x not in util.BASE_DIMENSIONS, df.columns))

            # Drop rows with nan.
            df = df.dropna(subset=[
                'VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'OBS_VALUE'
            ])
            if df.empty:
                continue

            # Drop invalid values.
            df['OBS_VALUE'] = df['OBS_VALUE'].apply(lambda x: x
                                                    if util.is_float(x) else '')
            df = df[df['OBS_VALUE'] != '']
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
                lambda x: util.format_variable_description(
                    x['VARIABLE_DESCRIPTION'], x['SERIES_DESCRIPTION']),
                axis=1)
            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(
                lambda x: util.format_variable_code(x))

            # Replace buggy input text.
            df = df.replace(
                'SG_SCP_PROCN_LS.LEVEL_STATUS--DEG_MLOW__GOVERNMENT_NAME--CIT_OF_WROCLAW',
                'SG_SCP_PROCN_LS.LEVEL_STATUS--DEG_MLOW__GOVERNMENT_NAME--CITY_OF_WROCLAW'
            )

            sv_frames.append(df.loc[:,
                                    ['VARIABLE_CODE', 'VARIABLE_DESCRIPTION'] +
                                    properties].drop_duplicates())
            measurement_method_frames.append(
                df.loc[:, ['NATURE', 'OBS_STATUS', 'REPORTING_TYPE']].
                drop_duplicates())
            units.update(set(df['UNIT_MEASURE'].unique()))

            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(
                lambda x: 'dcs:sdg/' + x)
            df['UNIT_MEASURE'] = df.apply(
                lambda x: get_unit(x['UNIT_MEASURE'], x['BASE_PERIOD']), axis=1)
            df['MEASUREMENT_METHOD'] = df.apply(
                lambda x: 'dcs:' + get_measurement_method(x), axis=1)

            # Retain only columns for cleaned csv.
            df = df.loc[:, [
                'VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'OBS_VALUE',
                'UNIT_MEASURE', 'UNIT_MULT', 'MEASUREMENT_METHOD'
            ]]

            df.to_csv(os.path.join(csv_dir,
                                   file.split('observations_')[1]),
                      index=False)

    with open(os.path.join(schema_dir, 'sv.mcf'), 'w') as f:
        for df in sv_frames:
            for _, row in df.iterrows():
                cprops = ''
                for dimension in sorted(df.columns[2:]):
                    # Skip totals.
                    if row[dimension] == util.TOTAL:
                        continue

                    # Remove leading _.
                    val = str(row[dimension])
                    if val[0] == '_':
                        val = val[1:]

                    # Remove buggy input text.
                    val = val.replace('CIT_ OF_WROCLAW', 'CITY_OF_WROCLAW')

                    enum = util.format_property(dimension)
                    if dimension in util.MAPPED_DIMENSIONS:
                        prop = util.MAPPED_DIMENSIONS[dimension]
                    else:
                        prop = 'sdg_' + enum[0].lower() + enum[1:]

                    val = 'SDG_' + enum + 'Enum_' + val
                    cprops += f'\n{prop}: dcs:{val}'
                f.write(
                    util.SV_TEMPLATE.format_map({
                        'dcid':
                            'sdg/' + row['VARIABLE_CODE'],
                        'popType':
                            'SDG_' + row['VARIABLE_CODE'].split(
                                util.SV_CODE_SEPARATOR)[0],
                        'name':
                            '"' + row['VARIABLE_DESCRIPTION'] + '"',
                        'cprops':
                            cprops,
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

                # Remove leading _.
                if k[0] == '_':
                    k = k[1:]

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
                    'description': description + ' | '.join(pvs) + ']'
                }))

    with open(os.path.join(schema_dir, 'unit.mcf'), 'w') as f:
        for unit in sorted(units):
            f.write(
                util.UNIT_TEMPLATE.format_map({
                    'dcid': 'SDG_' + unit,
                    'name': dimensions['UNIT_MEASURE'][unit]
                }))


if __name__ == '__main__':
    if os.path.exists('schema'):
        shutil.rmtree('schema')
    os.makedirs('schema')
    if os.path.exists('csv'):
        shutil.rmtree('csv')
    os.makedirs('csv')
    process('sdg-dataset/output', 'schema', 'csv')
