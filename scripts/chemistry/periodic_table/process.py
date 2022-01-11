# Copyright 2021 Google LLC
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
Generate nodes for all elements in the periodic table.
'''

import csv
import requests
import requests_cache

from absl import app
from absl import flags
from ratelimit import limits, sleep_and_retry

FLAGS = flags.FLAGS
flags.DEFINE_integer('start_element', 1,
                     'First atomic number of a range of elements to download')
flags.DEFINE_integer('end_element', 118,
                     'Last atomic number of a range of elements to download')
flags.DEFINE_string('compounds', 'compounds.txt',
                    'List of compounds to process.')
flags.DEFINE_string('output_prefix', 'substance',
                    'Output path for csv and tmcf files.')

_URL_ELEMENT = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/element/{atomic_number}/JSON'

_URL_COMPOUND_NAME_LOOKUP="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IUPACName,MolecularFormula,InChI,InChIKey,Title/JSON"

_OUTPUT_COLUMNS = [
    'Name',
    'IUPACName',
    'TypeOf',
    'Symbol',
    'InChI',
    'InChIKey',
    'Type',
    'AtomicNumber',
    'Input',
]

_TEMPLATE_MCF = '''
Node: E:Substance->E0
typeOf: C:Substance->TypeOf
dcid: C:Substance->IUPACName
name: C:Substance->Name
iupacName: C:Substance->IUPACName
molecularFormula: C:Substance->Symbol
atomicNumber: C:Substance->AtomicNumber
chemicalSubstanceType: C:Substance->Type
iupacInternationalChemicalID: C:Substance->InChI
inChIKey: C:Substance->InChIKey
'''


def _get_alpha_string(input_string: str) -> str:
    '''Returns a capitalized string with only alphabets.'''
    clean_str = [s if s.isalpha() else ' ' for s in input_string]
    joined_str = ''.join(clean_str)
    return ''.join(
        [w[0].upper() + w[1:] for w in joined_str.split(' ') if len(w) > 0])


def _get_property_name(prop: str) -> str:
    '''Returns the property name matching the output column.'''
    # Strip out any spaces and 'Element'
    return prop.replace(' ', '').replace('Element', '')


def _add_properties_from_section(section: dict, output_props: dict):
    '''Add properties from the section to the output_props dictionary.'''
    if 'TOCHeading' in section:
        prop = _get_property_name(section['TOCHeading'])
        print(f'Processing section {prop}')
        if 'Information' in section:
            info = section['Information']
            for info_rec in info:
                if 'Name' in info_rec:
                    prop = _get_property_name(info_rec['Name'])
                    print(f'Reading section {prop}')
                if prop in output_props:
                    # Already have a value for this property. Skip rest.
                    break
                if 'Value' in info_rec:
                    if 'StringWithMarkup' in info_rec['Value']:
                        str_values = info_rec['Value']['StringWithMarkup']
                        if len(str_values) > 0:
                            value = str_values[0].get('String')
                            if value is not None:
                                output_props[prop] = value
    # Process child Sections, if any.
    if 'Section' in section:
        for sec in section['Section']:
            _add_properties_from_section(sec, output_props)
    return output_props


def add_properties_from_json(json: dict, output_props: dict) -> dict:
    if 'Record' in json:
        record = json['Record']
        if 'Section' in record:
            sections = record['Section']
            for section in sections:
                _add_properties_from_section(section, output_props)
    return output_props

def add_required_properties(output_props: dict) -> dict:
    # Get the element type if it exists.
    if 'GroupNumber' in output_props:
        element_type = _get_alpha_string(output_props['GroupNumber'])
        if element_type == '':
            element_type = _get_alpha_string(output_props['Classification'])
        if element_type != '':
            output_props['Type'] = element_type

    if 'Symbol' not in output_props:
      if 'MolecularFormula' in output_props:
        output_props['Symbol'] = output_props['MolecularFormula']

    if 'IUPACName' not in output_props:
        if 'Name' in output_props:
            output_props['IUPACName'] = output_props['Name']
    if 'Name' not in output_props:
        if 'IUPACName' in output_props:
            output_props['Name'] = _get_alpha_string(output_props['IUPACName'])
    if 'TypeOf' not in output_props:
        output_props['TypeOf'] = 'dcs:ChemicalSubstance'
    return output_props


@sleep_and_retry
@limits(calls=30, period=60)
def download_pubchem_record(url: str) -> dict:
    resp = requests.get(url)
    return resp.json()

def download_element(atomic_number: int) -> dict:
    '''Download and return the JSON for a specific element.'''
    return download_pubchem_record(_URL_ELEMENT.format(atomic_number=atomic_number))

def download_compound_by_name(compound_name: str) -> dict:
    '''Download the PubChem record for a chemical compound.'''
    # Lookup the record by chemical name
    return download_pubchem_record(_URL_COMPOUND_NAME_LOOKUP.format(name=compound_name))

def get_element_properties(atomic_number: int, json: dict = None) -> dict:
    '''
  Returns a dictionary of properties for an element.

  Args:
    atomic_number: Atomic number of the element.
    json: JSON dictionary for a given element.
        If not provided, the JSON is downloaded.

  Returns:
    dict with the following keys:
      AtomicNumber
      Name
      Symbol
      InChI
      InChIKey
      Type
  '''
    if json is None:
        json = download_element(atomic_number)
    element_props =  add_properties_from_json(json, {
        'AtomicNumber': atomic_number,
        'TypeOf': 'dcs:ChemicalElement',
        'Input': atomic_number,
    })
    return add_required_properties(element_props)

def get_compound_properties(compound_name: str) -> dict:
  '''Returns a dictionary with properties of a chemical compound.'''
  # Lookup properties by compound name.
  output_props = {'Input': compound_name, 'TypeOf': 'dcs:ChemicalCompound'}
  props_json = download_compound_by_name(compound_name)
  print(f'Download {compound_name} returned {props_json}')
  if not 'PropertyTable' in props_json:
    return None
  if not 'Properties' in props_json['PropertyTable']:
    return None
  chemical_props = props_json['PropertyTable']['Properties']
  if len(chemical_props) == 0:
    return None
  output_props.update(chemical_props[0])
  return add_required_properties(output_props)

def process_elements(elements: list, csv_writer):
    '''Generates a csv file with properties for a set of element with gievn atomic numbers.'''
    if elements is None or len(elements) == 0:
        elements = list(range(1, 118))
    # Generate csv for all elements.
    for atomic_number in elements:
        output_props = get_element_properties(atomic_number)
        if 'Name' in output_props:
            csv_writer.writerow(output_props)

def process(elements: list, compounds_file: str, output_prefix: str):
    csv_file = output_prefix + '.csv'
    with open(csv_file, 'w', newline='') as f_out_csv:
        csv_writer = csv.DictWriter(f_out_csv,
                                    fieldnames=_OUTPUT_COLUMNS,
                                    extrasaction='ignore',
                                    lineterminator='\n')
        csv_writer.writeheader()
        if len(elements) > 0:
            process_elements(elements, csv_writer)

        if compounds_file != '':
           with open(compounds_file) as in_file:
             for line in in_file:
               name = line.strip()
               if len(name) > 0 and name[0] != '#':
                  output_props = get_compound_properties(name)
                  print(f'Props for {name}: {output_props}')
                  if output_props is not None and 'Name' in output_props:
                     csv_writer.writerow(output_props)


    # Generate the tMCF file
    tmcf_file_path = output_prefix + '.tmcf'
    with open(tmcf_file_path, 'w', newline='') as f_out_tmcf:
        f_out_tmcf.write(_TEMPLATE_MCF)


def main(_) -> None:
    requests_cache.install_cache('pubchem_cache')
    process(list(range(FLAGS.start_element, FLAGS.end_element)),
            FLAGS.compounds,
            FLAGS.output_prefix)


if __name__ == '__main__':
    app.run(main)
