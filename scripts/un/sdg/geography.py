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
typeOf: dcs:{type}{containment}
'''

# Curated map of dcid to SDG code to avoid duplicates.
FIXED = {
    # Africa.
    'africa': '2',
    # Source geographies without a corresponding geography in UNdata.
    'undata-geo/G99999999': '952',
}

# Geography types.
CITY = 'City'
CONTINENT = 'Continent'
COUNTRY = 'Country'
GEO_REGION = 'GeoRegion'
SAMPLING_STATION = 'SamplingStation'
UN_GEO_REGION = 'UNGeoRegion'

# UN geography prefix.
UN_PREFIX = 'undata-geo'


# Simplified representation of DC MCF Node.
class Node:

    def __init__(self, dcid, type, name):
        self.dcid = dcid
        self.type = type
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented

        return self.dcid == other.dcid and self.type == other.type and self.name == other.name

    def __str__(self):
        return self.dcid + self.type + self.name

    def __hash__(self):
        return (hash(str(self)))

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented

        return str(self) < str(other)


def get_sdg2type(file):
    '''Produces map of SDG code -> SDG type.

    Args:
        file: Input file path.

    Returns:
        Map of SDG code -> SDG type.
    '''
    sdg2type = {}
    with open(file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sdg2type[row['GEOGRAPHY_CODE']] = row['GEOGRAPHY_TYPE']
    return sdg2type


def get_sdg_un_maps(file):
    '''Produces maps of UN code -> SDG code & SDG code -> UN code.

    Args:
        file: Input file path.

    Returns: 
        - Map of UN code -> SDG code.
        - Map of SDG code -> UN code.
    '''
    un2sdg = {}  # Map of UN code -> SDG code.
    sdg2un = {}  # Map of SDG code -> UN code.

    # Use special encoding to parse UN input file.
    with open(file, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject = row['subject_id']  # UN code.
            object = row['object_id'].removeprefix('sdg-geo:')  # SDG code.
            if not subject or not object:
                continue
            un2sdg[subject] = object
            sdg2un[object] = subject
    return un2sdg, sdg2un


def get_un2dc_curated(file):
    '''Produces map of UN code -> curated Node.

    Args:
        file: Input file path.

    Returns:
        Map of UN code -> curated Node.
    '''
    un2dc_curated = {}
    with open(file, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:

            # Skip unmapped places.
            if row['unDataCode'] == 'x':
                continue

            # Add missing type for NorthernEurope.
            if row['dcid'] == 'NorthernEurope':
                type = UN_GEO_REGION

            else:
                type = json.loads(row['typeOf'].replace("'", '"'))[0]['dcid']
            un2dc_curated[row['unDataCode']] = Node(row['dcid'], type,
                                                    row['dc_name'])
    return un2dc_curated


def should_include_containment(s, o):
    '''Returns whether triple should be included in containment.

    Args: 
        s: Subject node.
        o: Object node.

    Returns:
        Whether triple should be included in containment.
    '''
    # Skip triples where a place is contained within itself.
    if s.dcid == o.dcid:
        return False

    if (s.type == GEO_REGION or s.type == UN_GEO_REGION) and o.dcid == 'Earth':
        return True
    elif (s.type == GEO_REGION or
          s.type == UN_GEO_REGION) and o.type == CONTINENT:
        return True
    elif (s.type == GEO_REGION or
          s.type == UN_GEO_REGION) and (o.type == GEO_REGION or
                                        o.type == UN_GEO_REGION):
        return True
    elif s.type == COUNTRY and (o.type == GEO_REGION or
                                o.type == UN_GEO_REGION):
        return True
    elif s.type == SAMPLING_STATION and o.type == COUNTRY:
        return True
    elif s.type == CITY and s.dcid.startswith(UN_PREFIX) and o.type == COUNTRY:
        return True
    return False


def write_un_places(input_geos, output, sdg2type, un2sdg, un2dc_curated):
    '''Writes UN places to output and computes new places.

    Args: 
        input_geos: Path to input UN geography file.
        output: Path to output file.
        sdg2type: Map of SDG code -> SDG type.
        un2sdg: Map of UN code -> SDG code.
        un2dc_curated: Map of UN code -> curated Node.

    Returns:
        - Map of UN code -> generated Node.
        - List of (dcid, type) for new places.
    '''
    un2dc_generated = {}
    new_subjects = []
    with open(input_geos, encoding='utf-8-sig') as f_in:
        with open(output, 'w', encoding='utf-8') as f_out:
            reader = csv.DictReader(f_in)
            for row in reader:
                subject = UN_PREFIX + ':' + row['undata_geo_id']
                if subject in un2dc_curated:
                    dcid = un2dc_curated[subject].dcid
                    type = un2dc_curated[subject].type
                    name = un2dc_curated[subject].name
                else:
                    dcid = subject.replace(':', '/')
                    if subject in un2sdg and un2sdg[subject] in sdg2type:
                        sdg_type = sdg2type[un2sdg[subject]]
                        if sdg_type == SAMPLING_STATION or sdg_type == CITY:
                            type = sdg_type
                        else:
                            type = GEO_REGION
                    else:
                        type = GEO_REGION
                    name = row['undata_geo_desc'].split('_')[-1]
                    un2dc_generated[subject] = Node(dcid, type, name)

                # Add non-UN-specific places to new_subjects.
                if type == GEO_REGION or type == UN_GEO_REGION or type == SAMPLING_STATION or (
                        type == CITY and dcid.startswith(UN_PREFIX)):
                    new_subjects.append(Node(dcid, type, name))

                f_out.write(
                    PLACE_TEMPLATE.format_map({
                        'dcid': dcid,
                        'type': type,
                        'name': name,
                        'code': subject,
                        'label': row['undata_geo_desc']
                    }))
    return un2dc_generated, new_subjects


def process_containment(input_containment, un2dc_curated, un2dc_generated):
    '''Filters UN geography containment triples.

    Args:
        input_containment: Path to input containment file.
        un2dc_curated: Map of UN code -> curated Node.
        un2dc_generated: Map of UN code -> generated Node.

    Returns:
        - Map of child Node -> list of containing object dcids.
    '''
    containment = collections.defaultdict(list)

    # Use special encoding to parse UN input file.
    with open(input_containment, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject = UN_PREFIX + ':' + row['subject_id']
            if subject in un2dc_curated:
                s = un2dc_curated[subject]
            elif subject in un2dc_generated:
                s = un2dc_generated[subject]
            else:
                print('Missing subject: ', subject)
            object = UN_PREFIX + ':' + row['object_id']
            if object in un2dc_curated:
                o = un2dc_curated[object]
            elif object in un2dc_generated:
                o = un2dc_generated[object]
            else:
                print('Missing object: ', object)
            if should_include_containment(s, o):
                containment[s].append(o.dcid)
    return containment


def write_un_containment(output, containment, new_subjects):
    '''Writes containment triples to output.

    Args:
        output: Path to output file.
        containment: Map of child Node -> list of containing object dcids.
        new_subjects: List of Nodes for new places.

    '''
    with open(output, 'w', encoding='utf-8') as f:
        for s in sorted(containment):
            c = ''
            for o in containment[s]:
                c += '\ncontainedInPlace: dcid:' + o
            f.write(
                CONTAINMENT_TEMPLATE.format_map({
                    'dcid': s.dcid,
                    'type': s.type,
                    'containment': c
                }))

        # For new places with no specified containment, add containment in
        # Earth.
        for s in sorted(new_subjects):
            if s in containment:
                continue
            c = '\ncontainedInPlace: dcid:Earth'
            f.write(
                CONTAINMENT_TEMPLATE.format_map({
                    'dcid': s.dcid,
                    'type': s.type,
                    'containment': c
                }))


def write_place_mappings(output, sdg2un, un2dc_curated, un2dc_generated):
    '''Writes SDG code -> dcid mappings to output.

    Args:
        output: Path to output file.
        sdg2un: Map of SDG code -> UN code.
        un2dc_curated: Map of UN code -> curated Node.
        un2dc_generated: Map of UN code -> generated Node.
    '''
    with open(output, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['sdg', 'dcid'])
        writer.writeheader()
        for code in sorted(sdg2un):
            un = sdg2un[code]
            if un in un2dc_curated:
                dcid = un2dc_curated[un].dcid
            elif un in un2dc_generated:
                dcid = un2dc_generated[un].dcid
            else:
                continue

            # Filter duplicates.
            if dcid in FIXED and code != FIXED[dcid]:
                continue

            writer.writerow({'sdg': code, 'dcid': dcid})


if __name__ == '__main__':

    # Read input geography mappings.
    sdg2type = get_sdg2type('sdg-dataset/output/SDG_geographies.csv')
    un2sdg, sdg2un = get_sdg_un_maps(
        'sssom-mappings/output_mappings/undata-geo__sdg-geo.csv')
    un2dc_curated = get_un2dc_curated(os.path.join(FOLDER, 'places.csv'))

    un2dc_generated, new_subjects = write_un_places(
        'sssom-mappings/data/enumerations/undata/geography.csv',
        os.path.join(FOLDER, 'un_places.mcf'), sdg2type, un2sdg, un2dc_curated)
    containment = process_containment(
        'sssom-mappings/data/enumerations/undata/geography_hierarchy.csv',
        un2dc_curated, un2dc_generated)
    write_un_containment(os.path.join(FOLDER, 'un_containment.mcf'),
                         containment, new_subjects)
    write_place_mappings(os.path.join(FOLDER, 'place_mappings.csv'), sdg2un,
                         un2dc_curated, un2dc_generated)
