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
import datacommons as dc
import datetime
import os
import re
import requests
import requests_cache
import sys

from absl import app
from absl import flags
from inspect import getframeinfo, stack
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
flags.DEFINE_list('existing_chemicals', 'existing-chemicals-inchikey.csv',
                  'Pre-existing chemicals and their properties')
flags.DEFINE_boolean('download', True, 'Download properties from pubChem.')
flags.DEFINE_string('dcid_column', 'IUPACName',
                    'Output columns to be used as DCID.')
flags.DEFINE_integer('debug_level', 0,
                     'Print debug message upto the given level.')

# URL to fetch properties by element atomic number
_URL_ELEMENT = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/element/{atomic_number}/JSON'

# URL to lookup compound by name
_URL_COMPOUND_NAME_LOOKUP = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IUPACName,MolecularFormula,InChI,InChIKey,Title/JSON"

# URL to fetch properties of compound by the CID
_URL_COMPOUND_BY_ID = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"

# Character used to separate multiple values for a property
# that doesn't appear within any property value.
_DELIMITER = '|'

_OUTPUT_COLUMNS = [
    'InChIKey',  # Should be the first column for 'get_existing_chemicals.sh'
    'dcid',
    'IUPACName',
    'Name',
    'CommonName',
    'TypeOf',
    'Symbol',
    'InChI',
    'Type',
    'AtomicNumber',
    'CID',
    'SameAs',
    'Input',
]

_TEMPLATE_MCF = '''
Node: E:Substance->E0
typeOf: C:Substance->TypeOf
dcid: C:Substance->dcid
name: C:Substance->Name
iupacName: C:Substance->IUPACName
molecularFormula: C:Substance->Symbol
atomicNumber: C:Substance->AtomicNumber
chemicalSubstanceType: C:Substance->Type
iupacInternationalChemicalID: C:Substance->InChI
inChIKey: C:Substance->InChIKey
sameAs: C:Substance->SameAs
'''

# List of existing chemicals.
# Obtained by running get_existing_chemicals.sh
_EXISTING_CHEMICALS = {}

# Existing DCIDS used fr other entities already.
# The inChIKey will be used for these.
_EXISTING_DCIDS = {'Zinc'}

# Global settings
_CONFIG = {}


def _print_debug(debug_level: int, *args):
    if _CONFIG.get('debug_level', 0) >= debug_level:
        caller = getframeinfo(stack()[1][0])
        print(
            f'[{datetime.datetime.now()}:{os.path.basename(caller.filename)}:{caller.lineno}]',
            *args,
            file=sys.stderr)


def str_to_dcid(name: str) -> str:
    '''
    Get the dcid converting first character to uppercase and removing any extra chars.
    '''
    if name is None or len(name) == 0:
        return name
    # Remove any namespace prefix.
    name = name[name.find(':') + 1:]
    # Remove any special characters like []();, and commas and
    # capitalize the next letter.
    name = re.sub('[^A-Za-z0-9_/()-]', ' ', name)
    name = '_'.join(
        [w[0].upper() + w[1:] for w in name.split(' ') if len(w) > 0])
    return name[0].upper() + name[1:]


def get_dcids_for_key(key: str, dcid: str, existing_chemcials: dict) -> set:
    '''Returns any existing dcids different from the given dcid.'''
    if key not in existing_chemcials:
        return {}

    # Existing chemical with key present.
    # Return dcids if any other than given dcid.
    props = existing_chemcials[key]
    if 'dcid' in props:
        dcids = set(props['dcid'].replace(_DELIMITER, ',').split(','))
        existing_dcids = set(
            map(lambda x: x if x.find(':') > 0 else 'dcid:' + x, dcids))
        if dcid in existing_dcids:
            existing_dcids.remove(dcid)
        dcid = dcid[dcid.find(':') + 1:]
        if dcid in existing_dcids:
            existing_dcids.remove(dcid)
        dcid = 'dcid:' + dcid
        if dcid in existing_dcids:
            existing_dcids.remove(dcid)
        return existing_dcids


def _get_alpha_string(input_string: str) -> str:
    '''Returns a capitalized string with only alphabets.'''
    if input_string is None:
        return None
    clean_str = [
        s if s.isalpha() and s.isascii() else ' ' for s in input_string
    ]
    joined_str = ''.join(clean_str)
    return ''.join(
        [w[0].upper() + w[1:] for w in joined_str.split(' ') if len(w) > 0])


def _get_property_name(prop: str) -> str:
    '''Returns the property name matching the output column.'''
    # Strip out any spaces and 'Element'
    return prop.replace(' ', '').replace('Element', '')


def _add_value_to_property(prop: str, value: str, pvs: dict):
    '''Adds a value to a property if it doesn't exist already.'''
    if prop is None or value is None:
        return
    value = str(value)
    current_value = str(pvs.get(prop, ''))
    if current_value:
        # Property already exists. Check if value exists too.
        if value.lower() not in current_value.lower():
            pvs[prop] = current_value + _DELIMITER + value
    else:
        pvs[prop] = value
    _print_debug(3, f'Added value {value} to {prop}: {pvs[prop]}')


def _get_property_value_for_key(pvs: dict, key: str, prop: str) -> str:
    '''Returns the value for property in the dict if it exists, else empty string.'''
    if key in pvs:
        if prop in pvs[key]:
            return pvs[key][prop]
    return ''


def _add_quotes_to_values(pvs: dict) -> dict:
    '''Adds quotes to any string values that contain brackets.
    This is needed as '[' are interpreted as complex values
    unless delimited by an escaped quote \".
    Quoting such values will force the csv_writer to escape quotes
    with the options DictWriter(doublequote=False, escapechar='\\')
    '''
    for p, v in pvs.items():
        if v is not None and isinstance(v, str) and '[' in v and '"' not in v:
            values = [f'"{value}"' for value in v.split(_DELIMITER)]
            pvs[p] = _DELIMITER.join(values)
    return pvs


def _get_first_value_for_property(pvs: dict, prop: str) -> str:
    '''Returns the first value in a comma separated list of values for a property.'''
    if prop not in pvs:
        return ''
    value = pvs.get(prop, '')
    if isinstance(value, str):
        return pvs[prop].split(_DELIMITER)[0]
    return value


def _add_properties_from_section(section: dict, output_props: dict):
    '''Add properties from the section to the output_props dictionary.'''
    if 'TOCHeading' in section:
        prop = _get_property_name(section['TOCHeading'])
        _print_debug(3, f'Processing section {prop}')
        if 'Information' in section:
            info = section['Information']
            for info_rec in info:
                if 'Name' in info_rec:
                    prop = _get_property_name(info_rec['Name'])
                    _print_debug(3, f'Reading section {prop}')
                if 'Value' in info_rec:
                    if 'StringWithMarkup' in info_rec['Value']:
                        str_values = info_rec['Value']['StringWithMarkup']
                        if len(str_values) > 0:
                            value = str(str_values[0].get('String'))
                            _add_value_to_property(prop, value, output_props)
    # Process child Sections, if any.
    if 'Section' in section:
        for sec in section['Section']:
            _add_properties_from_section(sec, output_props)
    return output_props


def add_properties_from_json(json: dict, output_props: dict) -> dict:
    if 'Record' in json:
        record = json['Record']
        if 'RecordType' in record and 'RecordNumber' in record:
            rec_type = record['RecordType']
            rec_num = record['RecordNumber']
            _add_value_to_property(rec_type, rec_num, output_props)
        if 'Section' in record:
            sections = record['Section']
            for section in sections:
                _add_properties_from_section(section, output_props)
    return output_props


def add_existing_chemical_props(output_props: dict) -> dict:
    '''Add any properties from existing chemicals such as 'sameAs' to other dcids.
    '''
    # Look for existing chemicals with same InChIKey or commonName
    in_chi = _get_first_value_for_property(output_props, 'InChI')
    in_chi_key = _get_first_value_for_property(output_props, 'InChIKey')
    dcid = _get_first_value_for_property(output_props, 'dcid')
    for prop in ['InChIKey', 'CommonName']:
        if prop in output_props:
            keys = output_props[prop]
            for key in keys.split(_DELIMITER):
                existing_dcids = get_dcids_for_key(key, dcid,
                                                   _EXISTING_CHEMICALS)
                for old_dcid in existing_dcids:
                    old_dcid = old_dcid[old_dcid.find(':') + 1:]
                    old_inchi = _get_property_value_for_key(
                        _EXISTING_CHEMICALS, key, 'InChI')
                    old_inchi_key = _get_property_value_for_key(
                        _EXISTING_CHEMICALS, key, 'InChIKey')
                    if in_chi in old_inchi and in_chi_key in old_inchi_key:
                        _add_value_to_property('SameAs', 'dcid:' + old_dcid,
                                               output_props)
                        _print_debug(
                            2,
                            f'Adding {old_dcid} with InChIKey:{old_inchi_key}, InChI: {old_inchi} for new dcid: {dcid} InChIKey: {in_chi_key}, InChI: {in_chi}'
                        )
                    else:
                        _print_debug(
                            2,
                            f'Ignoring {old_dcid} with InChIKey:{old_inchi_key}, InChI: {old_inchi} for new dcid: {dcid} InChIKey: {in_chi_key}, InChI: {in_chi}'
                        )
    return output_props


def set_dcid_for_node(pv: dict, dcid_column: str) -> str:
    '''Sets and returns the dcid for a set of property values.'''
    dcid = pv.get('dcid', '')
    dcid = dcid[dcid.find(':') + 1:]
    if dcid != '' and dcid not in _EXISTING_DCIDS:
        return dcid
    # Get the dcid if it is not already used, else use the inChiKey.
    for dcid_column in [dcid_column, 'InChIKey']:
        dcid = str_to_dcid(_get_first_value_for_property(pv, dcid_column))
        if dcid not in _EXISTING_DCIDS:
            break
    if 'Name' not in dcid_column and dcid != '':
        # Add the property prefix for non-name dcids.
        prefix = str_to_dcid(dcid_column)
        prefix = prefix[0].lower() + prefix[1:]
        dcid = prefix + '/' + dcid
    if dcid == '':
        sameas = pv.get('SameAs', '')
        if sameas != '':
            # Having existing chemical, but unable to get new chemical id.
            # Use the dcid of the existing chemical for this node.
            new_dcids = sameas.split(_DELIMITER)
            dcid = new_dcids.pop(0)
            dcid = dcid[dcid.find(':') + 1:]
            pv['SameAs'] = _DELIMITER.join(new_dcids)
            _print_debug(1, f'Using existing {dcid} for {output_props}')
        else:
            dcid = pv.get('Name', '')
    pv['dcid'] = dcid
    return dcid


def add_required_properties(name: str, output_props: dict,
                            dcid_column: str) -> dict:
    # Get the element type if it exists.
    if 'GroupNumber' in output_props:
        element_type = _get_alpha_string(output_props['GroupNumber'])
        if element_type == '':
            element_type = _get_alpha_string(output_props['Classification'])
        if element_type != '':
            output_props['Type'] = 'dcs:' + element_type

    if 'Symbol' not in output_props:
        if 'MolecularFormula' in output_props:
            output_props['Symbol'] = output_props['MolecularFormula']
    if 'IUPACName' not in output_props:
        if 'Name' in output_props:
            output_props['IUPACName'] = _get_first_value_for_property(
                output_props, 'Name')
        else:
            output_props['IUPACName'] = ''
    if 'Name' not in output_props:
        if 'IUPACName' in output_props:
            output_props['Name'] = _get_first_value_for_property(
                output_props, 'IUPACName')
    if 'CommonName' not in output_props:
        if 'Name' in output_props:
            output_props['CommonName'] = output_props['Name'].upper()
    if 'TypeOf' not in output_props:
        output_props['TypeOf'] = 'dcs:ChemicalSubstance'
    if name is not None:
        _add_value_to_property('Name', _get_alpha_string(name), output_props)

    if _get_first_value_for_property(output_props, 'AtomicNumber') != '':
        output_props['TypeOf'] = 'dcs:ChemicalElement'

    add_existing_chemical_props(output_props)
    set_dcid_for_node(output_props, dcid_column)
    # Add empty value for any missing output columns
    for col in _OUTPUT_COLUMNS:
        if col not in output_props:
            output_props[col] = ''
    dcid = output_props['dcid']
    return output_props


@sleep_and_retry
@limits(calls=30, period=60)
def download_pubchem_record(url: str) -> dict:
    resp = requests.get(url)
    _print_debug(2, f'Got response for {url}: {resp}')
    return resp.json()


def download_element(atomic_number: int) -> dict:
    '''Download and return the JSON for a specific element.'''
    return download_pubchem_record(
        _URL_ELEMENT.format(atomic_number=atomic_number))


def download_compound_by_name(compound_name: str) -> dict:
    '''Download the PubChem record for a chemical compound.
    Looks up the record by name to get the id and then
    uses the pubChem ID to lookup all  properties.'''
    # Lookup the record by chemical name
    json_record = download_pubchem_record(
        _URL_COMPOUND_NAME_LOOKUP.format(name=compound_name))
    if 'PropertyTable' in json_record:
        if 'Properties' in json_record['PropertyTable']:
            records = json_record['PropertyTable']['Properties']
            if len(records) > 0:
                if 'CID' in records[0]:
                    return download_pubchem_record(
                        _URL_COMPOUND_BY_ID.format(cid=records[0]['CID']))
    _print_debug(
        1,
        f'Unable to find id for compound {compound_name}, got JSON: {json_record}'
    )
    return {}


def get_element_properties(atomic_number: int,
                           dcid_column: str,
                           json: dict = None) -> dict:
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
    element_props = add_properties_from_json(
        json, {
            'AtomicNumber': atomic_number,
            'TypeOf': 'dcs:ChemicalElement',
            'Input': atomic_number,
        })
    return add_required_properties(name=None,
                                   output_props=element_props,
                                   dcid_column=dcid_column)


def get_compound_properties(compound_name: str, output_props: dict,
                            dcid_column: str, download: bool) -> dict:
    '''Returns a dictionary with properties of a chemical compound.'''
    if output_props is None:
        output_props = {}
    if 'Input' not in output_props:
        _add_value_to_property('Input', compound_name, output_props)
    if 'TypeOf' not in output_props:
        _add_value_to_property('TypeOf', 'dcs:ChemicalCompound', output_props)
    # Lookup properties by compound name.
    if download is True:
        props_json = download_compound_by_name(compound_name)
        _print_debug(2, f'Got properties for {compound_name}: {props_json}')
        if len(props_json) == 0:
            return output_props
        output_props = add_properties_from_json(props_json, output_props)
    return add_required_properties(name=compound_name,
                                   output_props=output_props,
                                   dcid_column=dcid_column)


def process_elements(elements: list, dcid_column: str, csv_writer):
    '''Generates a csv file with properties for a set of element with gievn atomic numbers.'''
    if elements is None or len(elements) == 0:
        elements = list(range(1, 118))
    # Generate csv for all elements.
    for atomic_number in elements:
        output_props = get_element_properties(atomic_number, dcid_column)
        if 'dcid' in output_props:
            csv_writer.writerow(_add_quotes_to_values(output_props))


def process(elements: list, compounds_file: str, output_prefix: str,
            dcid_column: str, download: bool, config: dict):
    if config:
        _CONFIG.update(config)
    csv_file = output_prefix + '.csv'
    chemicals = {}
    if compounds_file != '':
        # Generating properties for chemical compounds.
        # Get the list of chemicals to process
        if download is True:
            # Get chemical names from the file.
            with open(compounds_file) as in_file:
                for line in in_file:
                    name = line.strip()
                    if len(name) > 0 and name[0] != '#':
                        chemicals[name] = {'Input': name}
        else:
            # Adding properties for existing chemicals.
            with open(compounds_file) as in_file:
                csv_reader = csv.DictReader(in_file, delimiter=_DELIMITER)
                for row in csv_reader:
                    chemicals[row['Input']] = row
    with open(csv_file, 'w', newline='') as f_out_csv:
        csv_writer = csv.DictWriter(
            f_out_csv,
            fieldnames=_OUTPUT_COLUMNS,
            extrasaction='ignore',
            lineterminator='\n',
            delimiter=_DELIMITER,
            doublequote=False,
            escapechar='\\',
        )
        csv_writer.writeheader()
        if len(elements) > 0 and elements[0] > 0:
            print(f'Fetching properties for {len(elements)} elements...')
            process_elements(elements, dcid_column, csv_writer)

        print(f'Fetching properties for {len(chemicals)} compounds...')
        for name in chemicals.keys():
            output_props = get_compound_properties(name, chemicals[name],
                                                   dcid_column, download)
            _print_debug(2, f'Props for {name}: {output_props}')
            if output_props is not None and 'dcid' in output_props:
                csv_writer.writerow(_add_quotes_to_values(output_props))

    # Generate the tMCF file
    tmcf_file_path = output_prefix + '.tmcf'
    with open(tmcf_file_path, 'w', newline='') as f_out_tmcf:
        f_out_tmcf.write(_TEMPLATE_MCF)


def load_chemicals_csv(filenames: list, chemicals: dict, key='key') -> dict:
    '''Loads a list of known chemicals with InChIKey property.'''
    if filenames is None:
        return chemicals

    # Read CSV file and save properties.
    for filename in filenames:
        with open(filename, 'r') as chem_props:
            for props in csv.DictReader(chem_props):
                _print_debug(3, f'Adding existing chemical: {props}')
                if key in props:
                    key_str = props[key]
                    if key_str not in chemicals:
                        chemicals[key_str] = props
                    else:
                        # Entry already exists for this key. Merge properties.
                        for p, v in props.items():
                            _add_value_to_property(p, v, chemicals[key_str])
                else:
                    _print_debug(
                        1,
                        f'Missing key {key} in row for existing chemical: {props}'
                    )
    # fetch_dc_property_for_ids(chemicals)
    return chemicals


def fetch_dc_property_for_ids(
        chemicals: dict,
        properties=['InChIKey', 'iupacInternationalChemicalID']) -> dict:
    '''Fetch the datacommon propeorties for existing chemicals dcids.'''
    keys = list(chemicals.keys())
    for key in keys:
        dcids = chemicals[key]['dcid'].replace(_DELIMITER, ',').split(',')
        for prop in properties:
            pvs = dc.get_property_values(dcids, prop)
            for dcid in pvs.keys():
                values = pvs[dcid]
                value = _DELIMITER.join(values)
                if dcid not in chemicals:
                    chemicals[dcid] = {}
                _print_debug(3, f'Adding dcid: {dcid}, {prop}: {value}')
                _add_value_to_property(prop, value, chemicals[dcid])
    return chemicals


def main(_) -> None:
    requests_cache.install_cache('pubchem_cache')
    load_chemicals_csv(FLAGS.existing_chemicals, _EXISTING_CHEMICALS)
    process(list(range(FLAGS.start_element,
                       FLAGS.end_element + 1)), FLAGS.compounds,
            FLAGS.output_prefix, FLAGS.dcid_column, FLAGS.download, {
                'debug_level': FLAGS.debug_level,
            })


if __name__ == '__main__':
    app.run(main)
