# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
Generate MCF nodes for US Census Divisions and Regions

To run, download the codes from
https://www2.census.gov/programs-surveys/popest/geographies/2018/state-geocodes-v2018.xlsx
and save it as a csv file: 'geocodes.csv'.
Then run 'python3 census_divisions.py --census_divisions_csv=geocodes.csv'
to generate the mcf nodes in 'geo_CensusDivision.mcf'.
'''

import csv

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string('census_divisions_csv', 'census_region_geocodes.csv',
                    'CSV file with the US census division and region codes.')
flags.DEFINE_string(
    'output_mcf', 'geo_CensusDivision.mcf',
    'MCF file with the nodes for census divisions and regions.')

_COLUMNS = [
    'Region',
    'Division',
    'State (FIPS)',
    'Name',
]

_OUTPUT_PROPERTIES = ['#', 'Node', 'typeOf', 'name', 'fipsCode', 'containedIn']

_TEMPLATE_CENSUS_REGION = """Node: {dcid}
typeOf: dcs:CensusRegion
censusRegionId: "{region}"
containedIn: dcid:country/USA
"""

_TEMPLATE_CENSUS_DIVISION = """Node: {dcid}
typeOf: dcs:CensusDivision
censusDivisionId: "{division}"
containedIn: {region_dcid}
"""

_TEMPLATE_STATE = """# State: {name}
Node: {dcid}
typeOf: dcs:State
containedIn: {division_dcid}
"""


def _to_camelcase(name: str) -> str:
    '''Returns the text in CamelCase with spaces removed.'''
    name = name.strip()
    return ''.join([x.capitalize() for x in name.split(' ')])


def _get_state_dcid(code: int) -> str:
    '''Returns the DCID for the state.'''
    return f'dcid:geoId/{code:02}'


def _get_region_dcid(code: int, name: str, dcid_map: dict) -> str:
    '''Returns the DCID for the region and also adds it to the dcid_map.'''
    if name != '':
        name_str = _to_camelcase(name)
        dcid_map[f'r{code}'] = f'dcid:US{name_str}'
    return dcid_map[f'r{code}']


def _get_division_dcid(code: int, name: str, dcid_map: dict) -> str:
    '''Returns the DCID for the region and also adds it to the dcid map.'''
    if name != '':
        name_str = _to_camelcase(name)
        dcid_map[f'd{code}'] = f'dcid:US{name_str}'
    return dcid_map[f'd{code}']


def _generate_mcf(region: int, division: int, state: int, name: str,
                  dcid_map: dict) -> str:
    '''Returns the MCF nodes for the given codes and also adds the dcid to the map.
    '''
    mcf = []
    if state > 0:
        # Generate a contained in node for state.
        dcid = _get_state_dcid(state)
        return _TEMPLATE_STATE.format(name=name,
                                      dcid=dcid,
                                      division_dcid=_get_division_dcid(
                                          division, '', dcid_map))
    if division > 0:
        # Generate a node for the division.
        dcid = _get_division_dcid(division, name, dcid_map)
        return _TEMPLATE_CENSUS_DIVISION.format(name=name,
                                                dcid=dcid,
                                                division=division,
                                                region_dcid=_get_region_dcid(
                                                    region, '', dcid_map))
    if region > 0:
        # Generate a node for census region.
        dcid = _get_region_dcid(region, name, dcid_map)
        return _TEMPLATE_CENSUS_REGION.format(name=name,
                                              dcid=dcid,
                                              region=region)
    return ''


def process(csv_filename: str, output_filename: str):
    '''Generate the MCF file with nodes for census regions and divisions.

  Args:
     csv_filename: CSV file containing the census codes.
        Expected to have the following columns:
           Region: Region code in the range [1-4]
           Division: Division code in the range [0-9]
           State (FIPS): FIPS code for the state.
           Name
     output_mcf: Name of the MCF output file to be generated.
  '''
    mcf = []
    with open(csv_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        header = {}
        dcid_map = {}
        for row in csv_reader:
            # Skip header rows until the data.
            if len(header) == 0:
                if _COLUMNS[0] in row:
                    # Found the header row. Initialize column index.
                    for c in _COLUMNS:
                        header[c] = row.index(c)
                continue

            region = int(row[header['Region']])
            division = int(row[header['Division']])
            state = int(row[header['State (FIPS)']])
            name = row[header['Name']]
            mcf.append(_generate_mcf(region, division, state, name, dcid_map))

    with open(output_filename, 'w') as out_mcf:
        out_mcf.write('\n'.join(mcf))
    print(f'Generated {len(mcf)} nodes in "{output_filename}"')


def main(_):
    process(FLAGS.census_divisions_csv, FLAGS.output_mcf)


if __name__ == '__main__':
    app.run(main)
