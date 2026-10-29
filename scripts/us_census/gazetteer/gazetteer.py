"""
Standardized 2025 Gazetteer Parser.
Retains rich fields (location, usCensusGeoId).
Matches historical schema prefixes (including schema:City for Places).
Removes country containment from ZCTAs.
"""

import os
import re
import glob


# Configuration
class Flags:
    input_pattern = 'gazetteer/raw_data_2025/2025_Gaz_*.txt'
    output_path = 'gazetteer/output_mcf'


_FLAGS = Flags()

_STATE_FIPS = {
    'AL': '01',
    'AK': '02',
    'AZ': '04',
    'AR': '05',
    'CA': '06',
    'CO': '08',
    'CT': '09',
    'DE': '10',
    'DC': '11',
    'FL': '12',
    'GA': '13',
    'HI': '15',
    'ID': '16',
    'IL': '17',
    'IN': '18',
    'IA': '19',
    'KS': '20',
    'KY': '21',
    'LA': '22',
    'ME': '23',
    'MD': '24',
    'MA': '25',
    'MI': '26',
    'MN': '27',
    'MS': '28',
    'MO': '29',
    'MT': '30',
    'NE': '31',
    'NV': '32',
    'NH': '33',
    'NJ': '34',
    'NM': '35',
    'NY': '36',
    'NC': '37',
    'ND': '38',
    'OH': '39',
    'OK': '40',
    'OR': '41',
    'PA': '42',
    'RI': '44',
    'SC': '45',
    'SD': '46',
    'TN': '47',
    'TX': '48',
    'UT': '49',
    'VT': '50',
    'VA': '51',
    'WA': '53',
    'WV': '54',
    'WI': '55',
    'WY': '56',
    'AS': '60',
    'GU': '66',
    'MP': '69',
    'PR': '72',
    'UM': '74',
    'VI': '78',
}

_BLOCKLIST_FILES = frozenset([
    '2025_Gaz_aiannh_ORTL_national.txt', '2025_Gaz_aiannh_hhl.txt',
    '2025_Gaz_aiannh_national.txt', '2025_Gaz_aiannhr_national.txt',
    '2025_Gaz_aiannhrt_national.txt', '2025_Gaz_sldl_national.txt',
    '2025_Gaz_sldu_national.txt', '2025_Gaz_ua_national.txt'
])

_FILE_TO_ITEM_TYPE_MAP = {
    '119CD': 'dcs:CongressionalDistrict',
    'cbsa': 'dcs:CensusCoreBasedStatisticalArea',
    'cousubs': 'dcs:CensusCountyDivision',
    'counties': 'dcs:County',
    'elsd': 'dcs:ElementarySchoolDistrict',
    'place': 'schema:City',  # RESTORED to schema:City
    'scsd': 'dcs:HighSchoolDistrict',
    'tract': 'dcs:CensusTract',
    'unsd': 'dcs:SchoolDistrict',
    'zcta': 'dcs:CensusZipCodeTabulationArea',
    'sdadm': 'dcs:SchoolDistrict'
}

_CENSUS_PROPS = {
    'INTPTLAT': 'latitude',
    'INTPTLONG': 'longitude',
    'LSAD': 'censusAreaDescriptionCode',
    'NAME': 'name',
    'FUNCSTAT': 'censusFunctionalStatusCode',
    'USPS': 'statePostalCode',
    'AWATER': 'waterArea',
    'AWATER_SQMI': None,
    'HIGRADE': 'highestGrade',
    'LOGRADE': 'lowestGrade',
    'ALAND': 'landArea',
    'ALAND_SQMI': None,
    'ANSICODE': 'ansiCode',
    'GEOID': 'geoId',
    'CBSA_TYPE': 'statisticalAreaType',
    'CSAFP': 'combinedStatisticalAreaCode',
    'UATYPE': 'urbanAreaType',
    'GEOIDFQ': 'usCensusGeoId'
}

# RESTORED to schema:City
_LSAD_TYPES = {
    '25': 'schema:City',
    '35': 'schema:City',
    '37': 'schema:City',
    '55': 'schema:City',
    '57': 'schema:City',
    '62': 'schema:City',
    '43': 'schema:City, dcs:Town',
    '47': 'schema:City, dcs:Village',
    '21': 'schema:City, dcs:Borough'
}

_GRADE_MAP = {
    'PK': 'PreKindergarten',
    'KG': 'Kindergarten',
    '01': 'SchoolGrade1',
    '02': 'SchoolGrade2',
    '03': 'SchoolGrade3',
    '04': 'SchoolGrade4',
    '05': 'SchoolGrade5',
    '06': 'SchoolGrade6',
    '07': 'SchoolGrade7',
    '08': 'SchoolGrade8',
    '09': 'SchoolGrade9',
    '10': 'SchoolGrade10',
    '11': 'SchoolGrade11',
    '12': 'SchoolGrade12',
    '13': 'SchoolGrade13'
}

# EXACT HISTORICAL PROPERTY ORDERINGS (Updated with schema:City)
_PROPERTY_ORDER = {
    'dcs:CongressionalDistrict': [
        'typeOf', 'dcid', 'waterArea', 'landArea', 'containedInPlace',
        'longitude', 'geoId', 'latitude'
    ],
    'dcs:County': [
        'typeOf', 'name', 'dcid', 'ansiCode', 'waterArea', 'landArea',
        'containedInPlace', 'longitude', 'geoId', 'latitude'
    ],
    'dcs:CensusCountyDivision': [
        'typeOf', 'name', 'dcid', 'landArea', 'geoId', 'latitude',
        'censusFunctionalStatusCode', 'containedInPlace', 'waterArea',
        'longitude', 'ansiCode'
    ],
    'dcs:ElementarySchoolDistrict': [
        'typeOf', 'name', 'dcid', 'landArea', 'waterArea', 'geoId',
        'highestGrade', 'latitude', 'longitude', 'lowestGrade',
        'containedInPlace'
    ],
    'schema:City': [
        'typeOf', 'name', 'dcid', 'latitude', 'censusFunctionalStatusCode',
        'geoId', 'containedInPlace', 'longitude', 'landArea',
        'censusAreaDescriptionCode', 'ansiCode', 'waterArea'
    ],
    'dcs:HighSchoolDistrict': [
        'typeOf', 'name', 'dcid', 'landArea', 'waterArea', 'geoId',
        'highestGrade', 'latitude', 'longitude', 'lowestGrade',
        'containedInPlace'
    ],
    'dcs:SchoolDistrict': [
        'typeOf', 'name', 'dcid', 'landArea', 'waterArea', 'geoId',
        'highestGrade', 'latitude', 'longitude', 'lowestGrade',
        'containedInPlace'
    ],
    'dcs:CensusTract': [
        'typeOf', 'dcid', 'waterArea', 'landArea', 'containedInPlace',
        'longitude', 'geoId', 'latitude'
    ],
    'dcs:CensusZipCodeTabulationArea': [
        'typeOf', 'name', 'dcid', 'waterArea', 'landArea', 'longitude', 'geoId',
        'latitude'
    ],
    'dcs:CensusCoreBasedStatisticalArea': [
        'dcid', 'landArea', 'waterArea', 'statisticalAreaType', 'geoId',
        'latitude', 'longitude', 'name', 'containedInPlace', 'overlapsWith',
        'typeOf'
    ]
}


def _gazetteer_file_to_item_type(filename):
    fname = os.path.basename(filename)
    for key, val in _FILE_TO_ITEM_TYPE_MAP.items():
        if key in fname:
            return val
    return 'dcs:CensusPlace'


def _import_gazetteer_file(file_name, item_type, geoids):
    with open(file_name, 'r', encoding='utf-8', errors='replace') as f:
        first_line = f.readline().strip()
        delim = '|' if '|' in first_line else '\t'
        headers = first_line.split(delim)

        for l in f:
            items = [item.strip() for item in l.split(delim)]
            geoid_idx = next((i for i, h in enumerate(headers) if h == 'GEOID'),
                             None)
            if geoid_idx is None or geoid_idx >= len(items):
                continue

            geoid = items[geoid_idx]
            if not geoid:
                continue

            pv = {'typeOf': item_type}
            if 'zcta' in file_name:
                pv['NAME'] = geoid

            for n, h in enumerate(headers):
                if n < len(items) and items[n]:
                    prop = _CENSUS_PROPS.get(h)
                    if prop:
                        pv[h] = items[n]
                    if h == 'LSAD' and items[n] in _LSAD_TYPES:
                        pv['typeOf'] = _LSAD_TYPES[items[n]]

            geoids[geoid] = pv


def _trim_name(name):
    remove_list = [
        ' city and borough$', ' city$', ' borough$', ' village$', ' district$',
        ' township$', ' town$', ' state$', ' CDP$', ' barrio-pueblo$',
        ' barrio$'
    ]
    remove_regex = '(' + '|'.join(remove_list) + ')'
    return re.sub(remove_regex, '', str(name)).strip()


def _get_cbsa_containment(name):
    parts = str(name).split(',', 1)
    if len(parts) < 2:
        return []
    states_part = parts[1].strip().split(' ', 1)[0]

    overlaps = []
    for s in states_part.split('-'):
        if s in _STATE_FIPS:
            overlaps.append(f'overlapsWith: dcid:geoId/{_STATE_FIPS[s]}\n')
    return overlaps


def _output_mcf(outfile, geoids):
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile), exist_ok=True)

    geoid_prefix = ''
    is_cbsa = False
    prefix = 'geoId/'

    if any(x in outfile for x in ['elsd', 'unsd', 'scsd', 'sdadm']):
        prefix = 'geoId/sch'
        geoid_prefix = '' if 'sdadm' in outfile else 'sch'
    elif 'zcta' in outfile:
        prefix = 'zip/'
        geoid_prefix = 'zip/'
    elif 'cbsa' in outfile:
        prefix = 'geoId/C'
        geoid_prefix = 'C'
        is_cbsa = True

    with open(outfile, 'w', encoding='utf-8') as f:
        for geo in sorted(geoids):
            pv = geoids[geo]
            node_type = pv["typeOf"].split(',')[0].strip()

            lines = {}

            if is_cbsa:
                lines['Node'] = f'\nNode: geoId/{geoid_prefix}{geo}\n'
            else:
                lines['Node'] = f'\nNode: dcid:{prefix}{geo}\n'

            lines['dcid'] = f'dcid: "{prefix}{geo}"\n'
            lines['typeOf'] = f'typeOf: {pv["typeOf"]}\n'

            if 'containedInPlace' in pv and not is_cbsa:
                lines[
                    'containedInPlace'] = f'containedInPlace: {pv["containedInPlace"]}\n'

            for p in pv.keys():
                if p in ['typeOf', 'containedInPlace']:
                    continue
                ps = _CENSUS_PROPS.get(p)
                if not ps:
                    continue

                if p == 'USPS':
                    if 'sdadm' in outfile:
                        lines[
                            'containedInPlace'] = f'containedInPlace: dcid:geoId/sch{_STATE_FIPS[pv[p]]}\n'
                    else:
                        lines[
                            'containedInPlace'] = f'containedInPlace: dcid:geoId/{_STATE_FIPS[pv[p]]}\n'
                elif ps in ['waterArea', 'landArea']:
                    lines[ps] = f'{ps}: [SquareMeter {pv[p]}]\n'
                elif ps == 'name':
                    lines[ps] = f'name: "{_trim_name(pv[p])}"\n'
                    if is_cbsa:
                        overlaps = _get_cbsa_containment(pv[p])
                        if overlaps:
                            lines[
                                'containedInPlace'] = 'containedInPlace: dcid:country/USA\n'
                            lines['overlapsWith'] = "".join(overlaps)
                elif ps == 'geoId':
                    val = f"{geoid_prefix}{geo}"
                    lines[ps] = f'geoId: "{val}"\n'
                elif ps in ['lowestGrade', 'highestGrade']:
                    grade = _GRADE_MAP.get(pv[p])
                    if grade:
                        lines[ps] = f'{ps}: dcs:{grade}\n'
                else:
                    lines[ps] = f'{ps}: "{pv[p]}"\n'

            if 'INTPTLAT' in pv and 'INTPTLONG' in pv:
                lines[
                    'location'] = f'location: [LatLong {pv["INTPTLAT"]} {pv["INTPTLONG"]}]\n'

            mcf_block = lines.pop('Node')
            # Look up the ordering map, default to schema:City order if not found
            order = _PROPERTY_ORDER.get(node_type,
                                        _PROPERTY_ORDER['schema:City'])

            for prop in order:
                if prop in lines:
                    mcf_block += lines.pop(prop)

            for prop, line in sorted(lines.items()):
                mcf_block += line

            f.write(mcf_block)


def main():
    if not os.path.exists(_FLAGS.output_path):
        os.makedirs(_FLAGS.output_path)

    for in_file in glob.glob(_FLAGS.input_pattern):
        if os.path.basename(in_file) in _BLOCKLIST_FILES:
            continue

        geoids = {}
        item_type = _gazetteer_file_to_item_type(in_file)
        out_base = os.path.basename(in_file).replace('.txt', '.mcf')
        out_file = os.path.join(_FLAGS.output_path, out_base)

        print(f"Processing {in_file} -> {out_file} (Base Type: {item_type})")
        _import_gazetteer_file(in_file, item_type, geoids)
        _output_mcf(out_file, geoids)


if __name__ == "__main__":
    main()
