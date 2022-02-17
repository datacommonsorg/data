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
Generate Place nodes for US Census divisions and regions.
using data from:
https://www2.census.gov/programs-surveys/popest/geographies/2018/state-geocodes-v2018.xlsx
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

_OUTPUT_PROPERTIES = ['#', 'Node', 'typeOf', 'geoId', 'name', 'containedIn']


def _get_region_dcid(code: int) -> str:
    '''Returns the DCID for the region.'''
    return f'dcid:geoId/reg{code}'


def _get_division_dcid(code: int) -> str:
    '''Returns the DCID for the region.'''
    return f'dcid:geoId/div{code}'


def _get_mcf_for_dict(node: dict) -> str:
    '''Returns an MCF node with all property values in the dict.'''
    mcf = []
    # Add output properties in order
    node_props = list(node.keys())
    for p in _OUTPUT_PROPERTIES:
        if p in node:
            mcf.append(f'{p}: {node[p]}')
            node_props.remove(p)
    # Add any remaining properties.
    for p in node_props:
        mcf.append(f'{p}: {node[p]}')
    return '\n'.join(mcf)


def _generate_mcf(region: int, division: int, state: int, name: str) -> str:
    '''Returns the MCF nodes for the given codes.
    '''
    mcf = []
    if state > 0:
        # Generate a contained in node for state.
        return _get_mcf_for_dict({
            '#': f'State: {name}',
            'Node': f'dcid:geoId/{state:02}',
            'typeOf': 'dcs:State',
            'containedIn': _get_division_dcid(division),
        })
    if division > 0:
        # Generate a node for the division.
        dcid = _get_division_dcid(division)
        geoid = dcid.split('/')[1]
        return _get_mcf_for_dict({
            'Node': dcid,
            'typeOf': 'dcs:CensusDivision',
            'geoId': f'"{geoid}"',
            'containedIn': _get_region_dcid(region),
            'name': f'"{name}"',
        })
    if region > 0:
        # Generate a node for census region.
        dcid = _get_region_dcid(region)
        geoid = dcid.split('/')[1]
        return _get_mcf_for_dict({
            'Node': dcid,
            'typeOf': 'dcs:CensusRegion',
            'geoId': f'"{geoid}"',
            'containedIn': 'dcid:country/USA',
            'name': f'"{name}"',
        })
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
            mcf.append(_generate_mcf(region, division, state, name))

    with open(output_filename, 'w') as out_mcf:
        out_mcf.write('\n\n'.join(mcf))
    print(f'Generated {len(mcf)} nodes in "{output_filename}"')

def main(_):
  process(FLAGS.census_divisions_csv, FLAGS.output_mcf)

if __name__ == '__main__':
    app.run(main)
