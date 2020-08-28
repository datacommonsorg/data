# Copyright 2020 Google LLC
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
"""Generates the xref to dcid conversion files

Warning: This file takes a very long time to run (at least 3 hours).

(PharmGKB --> Chembl) and (PubChem Compound ID --> Chembl) both use UniChem API.
For more info: https://www.ebi.ac.uk/unichem/info/webservices#GetSrcCpdIds

(InChI --> InChI Key) uses InChI API. For more info:
https://www.chemspider.com/InChI.asmx?op=InChIToInChIKey

(InChI Key --> Chembl) uses chembl Python API. For more info:
https://github.com/chembl/chembl_webresource_client

Requirements:
    pip install chembl_webresource_client
"""
import sys
from xml.etree import ElementTree
import requests
import pandas as pd
from chembl_webresource_client.new_client import new_client


def pharm_to_chembl(pharm_ids):
    """Return list of chembl ids that positionally map to pharm ids."""
    # pharmgkb accession id to chembl id via unichem
    chembls = []
    for pharm_id in pharm_ids:
        if pd.isnull(pharm_id):
            chembls.append('')
            continue
        url = 'https://www.ebi.ac.uk/unichem/rest/src_compound_id/' + pharm_id + '/17/1'
        res = requests.get(url)
        if res.status_code == 200 and res.json():
            print('pharm_id: ' + pharm_id)
            print(res.json())
            chembl_id = res.json()[0]['src_compound_id']
            chembls.append(chembl_id)
            print(chembl_id)
        else:
            chembls.append('')
    return chembls


def write_pharm_to_chembls(pharm_ids, chembls):
    """Writes pharm_id_to_chembl_combined.csv."""

    print(len(pharm_ids) == len(chembls))
    # write chembl ids and pahrmgkb ids to csv
    chembl_dict = {
        'PharmGKB ID': pharm_ids,
        'ChEMBL ID': chembls,
    }
    pharm_id_to_chembl_df = pd.DataFrame(chembl_dict)
    pharm_id_to_chembl_df.to_csv('./pharm_id_to_chembl_combined.csv')


def pubchem_to_chembl(pubchem_ids):
    """Return list of chembl ids that positionally map to pubchem ids."""
    # pubchem id to chembl id via unichem
    chembls = []
    for pubchem_id in pubchem_ids:
        if pd.isnull(pubchem_id):
            chembls.append('')
            continue
        url = 'https://www.ebi.ac.uk/unichem/rest/src_compound_id/' + pubchem_id + '/22/1'
        res = requests.get(url)
        if res.status_code == 200 and res.json():
            print('pubchem: ' + pubchem_id)
            print(res.json())
            chembl_id = res.json()[0]['src_compound_id']
            chembls.append(chembl_id)
            print(chembl_id)
        else:
            chembls.append('')
    return chembls


def write_pubchem_to_chembls(pubchem_ids, chembls):
    """Writes pubchem_id_to_chembl_combined.csv."""
    print(len(pubchem_ids) == len(chembls))
    # write chembl ids and pahrmgkb ids to csv
    chembl_dict = {
        'PubChem ID': pubchem_ids,
        'ChEMBL ID': chembls,
    }
    pubchem_id_to_chembl_df = pd.DataFrame(chembl_dict)
    pubchem_id_to_chembl_df.to_csv('./pubchem_id_to_chembl_combined.csv')


def inchi_to_inchi_key(inchis):
    """Return list of inchi keys that positionally map to inchis."""

    inchi_keys = []
    for inchi in inchis:
        if pd.isnull(inchi):
            inchi_keys.append('')
            continue
        res = requests.get(
            'http://www.chemspider.com/InChI.asmx/InChIToInChIKey?inchi=' +
            inchi)
        if res.status_code == 200:
            tree = ElementTree.fromstring(res.content)
            inchi_keys.append(tree.text)
            print(tree.text)
        else:
            inchi_keys.append('')
    return inchi_keys


def write_inchi_to_inchi_keys(inchis, inchi_keys):
    """Writes inchi_to_inchi_key_combined.csv."""

    print(len(inchis) == len(inchi_keys))

    inchi_dict = {'InChI': inchis, 'InChI Key': inchi_keys}
    inchi_to_inchi_key_df = pd.DataFrame(inchi_dict)
    inchi_to_inchi_key_df.to_csv('./inchi_to_inchi_key_combined.csv')


def inchi_key_to_chembl(inchi_keys):
    """Return list of chembl ids that positionally map to inchi keys."""

    molecule = new_client.molecule
    chembl_mols = []

    for inchi_key in inchi_keys:
        if pd.isnull(inchi_key):
            chembl_mols.append('')
            continue
        try:
            mol = molecule.get(inchi_key)
            if mol and mol['molecule_chembl_id']:
                chembl_mols.append(mol['molecule_chembl_id'])
                print(mol['molecule_chembl_id'])
            else:
                chembl_mols.append('')
        except:
            chembl_mols.append('')
            print('in error: ' + inchi_key)
    return chembl_mols


def write_inchi_key_to_chembl(inchi_keys, chembl_mols):
    """Writes inchi_key_to_chembl_combined.csv."""

    if len(chembl_mols) != len(inchi_keys):
        print('Error occurred inchi_keys len != chembl_mols len')
        return

    # write chembl ids and inchi keys to csv
    chembl_dict = {
        'InChI Key': inchi_keys,
        'ChEMBL ID': chembl_mols,
    }
    inchi_key_to_chembl_df = pd.DataFrame(chembl_dict)
    inchi_key_to_chembl_df.to_csv('./inchi_key_to_chembl_combined.csv')


def main():
    """Write id conversion files, from pharm, pubchem, and inchi to chembl."""
    c_df = pd.read_csv('../raw_data/chemicals/chemicals.tsv', sep='\t')
    d_df = pd.read_csv('../raw_data/drugs/drugs.tsv', sep='\t')

    drugs_df = d_df.append(c_df, ignore_index=True)
    drugs_df = drugs_df.drop_duplicates()

    print('converting pharm ids to chembl....')

    pharm_ids = drugs_df['PharmGKB Accession Id'].tolist()
    chembls = pharm_to_chembl(pharm_ids)
    write_pharm_to_chembls(pharm_ids, chembls)

    print('converting pubchem compound ids to chembl....')

    pubchem_ids = drugs_df['PubChem Compound Identifiers'].tolist()
    chembls = pubchem_to_chembl(pubchem_ids)
    write_pubchem_to_chembls(pubchem_ids, chembls)

    print('converting inchis to inchi keys....')

    inchis = drugs_df['InChI'].tolist()
    inchi_keys = inchi_to_inchi_key(inchis)
    write_inchi_to_inchi_keys(inchis, inchi_keys)

    print('converting inchi keys to chembl....')

    chembl_mols = inchi_key_to_chembl(inchi_keys)
    write_inchi_key_to_chembl(inchi_keys, chembl_mols)


if __name__ == '__main__':
    QUESTION_STR = 'Are you sure you want to generate id conversion files? (y/n)'
    if input(QUESTION_STR) != "y":
        sys.exit()
    main()
