import csv
import math
import os
import pandas as pd
import sys

from util import *

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

module_dir_ = os.path.dirname(__file__)

BASE_CONCEPTS = {'SERIES_CODE', 'SERIES_DESCRIPTION', 'VARIABLE_CODE',
       'VARIABLE_DESCRIPTION', 'GEOGRAPHY_CODE', 'GEOGRAPHY_NAME',
       'GEOGRAPHY_TYPE', 'GEO_AREA_CODE', 'GEO_AREA_NAME', 'CITIES',
       'SAMPLING_STATIONS', 'TIME_PERIOD', 'TIME_DETAIL', 'TIME_COVERAGE',
       'FREQ', 'VALUE', 'VALUE_TYPE', 'UPPER_BOUND',
       'LOWER_BOUND', 'UNITS', 'UNITMULTIPLIER', 'BASE_PERIOD', 'NATURE',
       'SOURCE', 'GEO_INFO_URL', 'FOOT_NOTE', 'REPORTING_TYPE',
       'OBSERVATION_STATUS', 'RELEASE_STATUS', 'RELEASE_NAME'}

# Create map of M49 -> ISO-alpha3 for countries.
with open(os.path.join(module_dir_, 'm49.csv')) as f:
    PLACES = {}
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if not row['ISO-alpha3 code']:  # Only countries for now.
            continue
        PLACES[int(row['M49 code'])] = row['ISO-alpha3 code']

# Create map of name -> dcid for supported cities.
with open(os.path.join(module_dir_, 'cities.csv')) as f:
    reader = csv.DictReader(f)
    CITIES = {row['name']: row['dcid'] for row in reader}

def get_dimensions(input_dir):
    dimensions = {}
    for root, _, files in os.walk(os.path.join(input_dir, 'code_lists')):
        for file in sorted(files):
            dimension = file.removeprefix('CL__').removesuffix('.xlsx')

            # Get names directly from observation files.
            if dimension in {'SERIES', 'VARIABLE'}:
                continue

            path = os.path.join(root, file)
            df = pd.read_excel(path)
            dimensions[dimension] = {str(row['EnumerationValue_Code']): row['EnumerationValue_Name'] for _, row in df.iterrows()}
    return dimensions

def is_valid(v):
    try:
        return not math.isnan(float(v))
    except ValueError:
        return v and not v == 'nan'

def format_variable_description(variable, series):
    parts = variable.split(series)
    return format_description(series) + parts[1] if len(parts) > 1 else format_description(series)

def format_variable_code(c):
    parts = c.split('?')
    return parts[0] + ':' + parts[1].replace('=', '--').replace('&', '+') if len(parts) > 1 else parts[0]

def format_title(s):
    return s.replace('_', ' ').title()

def format_property(s):
    return format_title(s).replace(' ', '')

def get_geography(code, type):

    # Currently only support Country and City.
    if type == 'Country' and code in PLACES:
        return 'dcs:country/' + PLACES[code] 
    elif type == 'City' and code in CITIES and CITIES[code]:
        return 'dcs:' + CITIES[code]
    return ''

def get_unit(units, base_period):
    if is_valid(base_period):
        return f'[{units} {base_period}]'
    return 'dcs:SDG_' + units

def get_measurement_method(row):
    mmethod = ''
    if is_valid(row['NATURE']):
        mmethod += '_' + str(row['NATURE'])
    if is_valid(row['OBSERVATION_STATUS']):
        mmethod += '_' + str(row['OBSERVATION_STATUS'])
    if is_valid(row['REPORTING_TYPE']):
        mmethod += '_' + str(row['REPORTING_TYPE'])
    return 'SDG' + mmethod

def process(input_dir, schema_dir, csv_dir):
    with open(os.path.join(schema_dir, 'series.mcf'), 'w') as f_series:
        with open(os.path.join(schema_dir, 'sdg.textproto'), 'w') as f_vertical:
            df = pd.read_excel(os.path.join(input_dir, 'sdg_hierarchy.xlsx'))
            for _, row in df.iterrows():
                f_series.write(SERIES_TEMPLATE.format_map({
                    'dcid': 'SDG_' + str(row['SeriesCode']),
                    'description': format_description(str(row['SeriesDescription']))
                }))
                f_vertical.write(
                    'spec: {\n'
                    '  pop_type: "SDG_' + str(row['SeriesCode']) + '"\n'
                    '  obs_props { mprop: "value" }\n'
                    '  vertical: "SDG_' + str(row['IndicatorRefCode']) + '"\n'
                    '}\n'
                )

    dimensions = get_dimensions(input_dir)
    with open(os.path.join(schema_dir, 'sv.mcf'), 'w') as f:
        for df in sv_frames:
            for _, row in df.iterrows():
                cprops = ''
                for dimension in sorted(df.columns[2:]):
                    
                    # Skip totals.
                    if row[dimension] == TOTAL:
                        continue

                    enum = format_property(dimension)
                    if dimension in MAPPED_CONCEPTS:
                        prop = MAPPED_CONCEPTS[dimension] 
                    else:
                        prop = 'sdg_' + enum[0].lower() + enum[1:]
                    val = 'SDG_' + enum + 'Enum_' + str(row[dimension])
                    cprops += f'\n{prop}: dcs:{val}'
                f.write(SV_TEMPLATE.format_map({
                    'dcid': 'sdg/' + row['VARIABLE_CODE'],
                    'popType': 'SDG_' + row['VARIABLE_CODE'].split(':')[0],
                    'name': '"' + row['VARIABLE_DESCRIPTION'] + '"',
                    'cprops': cprops,
                }))

    sv_frames = []
    measurement_method_frames = []
    units = set()
    for root, _, files in os.walk(os.path.join(input_dir, 'observations')):
        for file in sorted(files):
            print(file)
            df = pd.read_excel(os.path.join(root, file))
            if df.empty:
                continue

            properties = list(filter(lambda x: x not in BASE_CONCEPTS, df.columns))

            # Drop rows with nan.
            df = df.dropna(subset=['VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'VALUE'])
            if df.empty:
                continue

            # Drop invalid values.
            df['VALUE'] = df['VALUE'].apply(lambda x: x if is_float(x) else '')
            df = df[df['VALUE'] != '']
            if df.empty:
                continue

            # Format places.
            df['GEOGRAPHY_CODE'] = df.apply(lambda x: get_geography(x['GEOGRAPHY_CODE'], x['GEOGRAPHY_TYPE']), axis=1)
            df = df[df['GEOGRAPHY_CODE'] != '']
            if df.empty: 
                continue
            
            # Special curation of names.
            df['VARIABLE_DESCRIPTION'] = df.apply(lambda x: format_variable_description(x['VARIABLE_DESCRIPTION'], x['SERIES_DESCRIPTION']), axis=1)
            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(lambda x: format_variable_code(x))

            sv_frames.append(df.loc[:, ['VARIABLE_CODE', 'VARIABLE_DESCRIPTION'] + properties].drop_duplicates())
            measurement_method_frames.append(df.loc[:, ['NATURE', 'OBSERVATION_STATUS', 'REPORTING_TYPE']].drop_duplicates())
            units.update(set(df['UNITS'].unique()))

            df['VARIABLE_CODE'] = df['VARIABLE_CODE'].apply(lambda x: 'dcs:sdg/' + x)
            df['UNITS'] = df.apply(lambda x: get_unit(x['UNITS'], x['BASE_PERIOD']), axis=1)
            df['MEASUREMENT_METHOD'] = df.apply(lambda x: 'dcs:' + get_measurement_method(x), axis=1)

            # Retain only columns for cleaned csv.
            df = df.loc[:, ['VARIABLE_CODE', 'GEOGRAPHY_CODE', 'TIME_PERIOD', 'VALUE', 'UNITS', 'UNITMULTIPLIER', 'MEASUREMENT_METHOD']]

            code = file.removeprefix('observations_').removesuffix('.xlsx')
            df.to_csv(os.path.join(csv_dir, f'{code}.csv'), index=False)

    with open(os.path.join(schema_dir, 'schema.mcf'), 'w') as f:
        for d in sorted(dimensions):
            if d in BASE_CONCEPTS or d == 'GEOGRAPHY':
                continue
            prop = format_property(d)
            enum = prop + 'Enum'
            if d not in MAPPED_CONCEPTS:
                f.write(
                    PROPERTY_TEMPLATE.format_map({
                        'dcid': prop[0].lower() + prop[1:],
                        'name': format_title(d),
                        'enum': enum
                    }))
            f.write(ENUM_TEMPLATE.format_map({'enum': enum}))
            for k in sorted(dimensions[d]):  

                # Skip totals.
                if k == TOTAL:
                    continue  
            
                v = dimensions[d][k]
                f.write(
                    VALUE_TEMPLATE.format_map({
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
                if not is_valid(row[dimension]):
                    continue
                pvs.append(format_title(dimension) + ' = ' + dimensions[dimension][row[dimension]])
            f.write(MMETHOD_TEMPLATE.format_map({
                'dcid': dcid,
                'description': description + ', '.join(pvs) + ']'
            }))

    with open(os.path.join(schema_dir, 'unit.mcf'), 'w') as f:
        for unit in sorted(units):
            f.write(UNIT_TEMPLATE.format_map({
                'dcid': 'SDG_' + unit,
                'name': dimensions['UNITS'][unit]
            }))

if __name__ == '__main__':
    if not os.path.exists('schema'):
        os.makedirs('schema')
    if not os.path.exists('csv'):
        os.makedirs('csv')
    process('sdg-dataset/output', 'schema', 'csv')
