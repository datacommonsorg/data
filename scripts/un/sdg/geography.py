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
'''Generates geographies for UN places.

Produces:
* un_places.mcf (place definitions)
* un_containment.mcf (place containment triples)
* place_mappings.csv (SDG code -> dcid)

Usage: python3 geography.py
'''
import collections
import csv
import json
import os

# Output folder.
FOLDER = 'geography'

PLACE_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:{type}
name: "{name}"
unDataCode: "{code}"
unDataLabel: "{label}"
'''
CONTAINMENT_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcid:{type}{containment}
'''

# Curated map of SDG GEOGRAPHY_CODE to UN data code.
FIXED = {
    'africa': '2',
    'undata-geo/G99999999': '952',
}

# Map of SDG code -> SDG type.
SDG2TYPE = {}
with open('sdg-dataset/output/SDG_geographies.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        SDG2TYPE[row['GEOGRAPHY_CODE']] = row['GEOGRAPHY_TYPE']

UN2SDG = {}  # Map of UN code -> SDG code.
SDG2UN = {}  # Map of SDG code -> UN code.
with open('sssom-mappings/output_mappings/undata-geo__sdg-geo.csv',
          encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subject = row['subject_id']  # UN code.
        object = row['object_id'].removeprefix('sdg-geo:')  # SDG code.
        if not subject or not object:
            continue
        UN2SDG[subject] = object
        SDG2UN[object] = subject

# Map of UN code -> curated (dcid, DC type, DC name).
UN2DC = {}
with open(os.path.join(FOLDER, 'places.csv')) as f:
    reader = csv.DictReader(f)
    for row in reader:

        # Skip unmapped places.
        if row['unDataCode'] == 'x':
            continue

        # Add missing type for NorthernEurope.
        if row['dcid'] == 'NorthernEurope':
            type = 'UNGeoRegion'

        else:
            type = json.loads(row['typeOf'].replace("'", '"'))[0]['dcid']
        UN2DC[row['unDataCode']] = (row['dcid'], type, row['dc_name'])


def should_include_containment(s_type, s_dcid, o_type, o_dcid):
    '''Returns whether triple should be included in containment.

    Args: 
        s_type: Type of triple subject.
        s_dcid: Dcid of triple subject.
        o_type: Type of triple object.
        o_dcid: Type of triple object.

    Returns:
        Whether triple should be included in containment.
    '''
    if (s_type == 'GeoRegion' or s_type == 'UNGeoRegion') and o_dcid == 'Earth':
        return True
    elif (s_type == 'GeoRegion' or
          s_type == 'UNGeoRegion') and o_type == 'Continent':
        return True
    elif (s_type == 'GeoRegion' or
          s_type == 'UNGeoRegion') and (o_type == 'GeoRegion' or
                                        o_type == 'UNGeoRegion'):
        return True
    elif s_type == 'Country' and (o_type == 'GeoRegion' or
                                  o_type == 'UNGeoRegion'):
        return True
    elif s_type == 'SamplingStation' and o_type == 'Country':
        return True
    elif s_type == 'City' and s_dcid.startswith(
            'undata-geo') and o_type == 'Country':
        return True
    return False


def write_un_places(input_geos, output):
    '''Writes UN places to output and computes new places.

    Args: 
        input_geos: Path to input UN geography file.
        output: Path to output file.

    Returns:
        - Map of generated (dcid, DC type, DC name).
        - Set of (dcid, type) for new places.
    '''
    un2dc2 = {}
    new_subjects = set()
    with open(input_geos) as f_in:
        with open(output, 'w') as f_out:
            reader = csv.DictReader(f_in)
            for row in reader:
                subject = row['subject_id']
                if subject in UN2DC:
                    dcid = UN2DC[subject][0]
                    type = UN2DC[subject][1]
                    name = UN2DC[subject][2]
                else:
                    dcid = row['subject_id'].replace(':', '/')
                    if row['subject_id'] in UN2SDG and UN2SDG[
                            row['subject_id']] in SDG2TYPE:
                        sdg_type = SDG2TYPE[UN2SDG[row['subject_id']]]
                        if sdg_type == 'SamplingStation' or sdg_type == 'City':
                            type = sdg_type
                        else:
                            type = 'GeoRegion'
                    else:
                        type = 'GeoRegion'
                    name = row['subject_label'].split('_')[-1]
                    un2dc2[subject] = (dcid, type, name)

                # Add non-UN-specific places to new_subjects.
                if type == 'GeoRegion' or type == 'UNGeoRegion' or type == 'SamplingStation' or (
                        type == 'City' and dcid.startswith('undata-geo')):
                    new_subjects.add((dcid, type))

                f_out.write(
                    PLACE_TEMPLATE.format_map({
                        'dcid': dcid,
                        'type': type,
                        'name': name,
                        'code': row['subject_id'],
                        'label': row['subject_label']
                    }))
    return un2dc2, new_subjects


def process_containment(input_containment, un2dc2):
    '''Filters UN geography containment triples.

    Args:
        input_containment: Path to input containment file.
        un2dc2: Map of UN code -> generated (dcid, DC type, DC name)

    Returns:
        - Map of (subject dcid, subject type) -> list of containing object dcids.
    '''
    containment = collections.defaultdict(list)
    with open(input_containment, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject = 'undata-geo:' + row['subject_id']
            if subject in UN2DC:
                s_dcid = UN2DC[subject][0]
                s_type = UN2DC[subject][1]
            elif subject in un2dc2:
                s_dcid = un2dc2[subject][0]
                s_type = un2dc2[subject][1]
            else:
                print('Missing subject: ', subject)
            object = 'undata-geo:' + row['object_id']
            if object in UN2DC:
                o_dcid = UN2DC[object][0]
                o_type = UN2DC[object][1]
            elif object in un2dc2:
                o_dcid = un2dc2[object][0]
                o_type = un2dc2[object][1]
            else:
                print('Missing object: ', object)
            if should_include_containment(s_type, s_dcid, o_type, o_dcid):
                containment[(s_dcid, s_type)].append(o_dcid)
    return containment


def write_un_containment(output, containment, new_subjects):
    '''Writes containment triples to output.

    Args:
        output: Path to output file.
        containment: Map of (subject dcid, subject type) -> list of containing
            object dcids.
        new_subjects: Set of (dcid, type) for new places.

    '''
    with open(output, 'w') as f:
        for s in sorted(containment):
            c = ''
            for o in containment[s]:
                c += '\ncontainedInPlace: dcs:' + o
            f.write(
                CONTAINMENT_TEMPLATE.format_map({
                    'dcid': s[0],
                    'type': s[1],
                    'containment': c
                }))

        # For new places with no specified containment, add containment in
        # Earth.
        for s in sorted(new_subjects):
            if s in containment:
                continue
            c = '\ncontainedInPlace: dcs:Earth'
            f.write(
                CONTAINMENT_TEMPLATE.format_map({
                    'dcid': s[0],
                    'type': s[1],
                    'containment': c
                }))


def write_place_mappings(output, un2dc2):
    '''Writes SDG code -> dcid mappings to output.

    Args:
        output: Path to output file.
        un2dc2: Map of UN code -> generated (dcid, DC type, Dc name).
    '''
    with open(output, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['sdg', 'dcid'])
        writer.writeheader()
        for code in SDG2UN:
            un = SDG2UN[code]
            if un in UN2DC:
                dcid = UN2DC[un][0]
            elif un in un2dc2:
                dcid = un2dc2[un][0]
            else:
                continue

            # Filter duplicates.
            if dcid in FIXED and code != FIXED[dcid]:
                continue

            writer.writerow({'sdg': code, 'dcid': dcid})


if __name__ == '__main__':
    un2dc2, new_subjects = write_un_places(
        os.path.join(FOLDER, 'geographies.csv'),
        os.path.join(FOLDER, 'un_places.mcf'))
    containment = process_containment(
        'sssom-mappings/data/enumerations/undata/geography_hierarchy.csv',
        un2dc2)
    write_un_containment(os.path.join(FOLDER, 'un_containment.mcf'),
                         containment, new_subjects)
    write_place_mappings(os.path.join(FOLDER, 'place_mappings.csv'), un2dc2)
