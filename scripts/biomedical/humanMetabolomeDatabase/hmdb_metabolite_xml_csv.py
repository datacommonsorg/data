# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Author: Suhana Bedi
Date: 07/23/2021
Name: hmdb_metabolite_xml_csv.py
Description: Parses the metabolite xml file downloaded
from the hmdb official website, into a csv
@file_input: input .xml from hmdb website
@file_output: parsed .csv file
"""
import sys
import csv
from io import StringIO
from lxml import etree


## Taken from http://www.metabolomics-forum.com/index.php?topic=1588.0
def hmdbextract(name, file):
    """
    Parses the xml into csv using the required properties
    """
    ns = {'hmdb': 'http://www.hmdb.ca'}
    context = etree.iterparse(name, tag='{http://www.hmdb.ca}metabolite')
    csvfile = open(file, 'w')
    fieldnames = [
        'accession', 'monisotopic_molecular_weight', 'iupac_name', 'name',
        'chemical_formula', 'InChIKey', 'cas_registry_number', 'smiles',
        'drugbank', 'chebi_id', 'pubchem', 'phenol_explorer_compound_id',
        'food', 'knapsack', 'chemspider', 'kegg', 'meta_cyc', 'bigg',
        'metlin_id', 'pdb_id', 'logpexp', 'kingdom', 'direct_parent',
        'super_class', 'class', 'sub_class', 'molecular_framework', 'vmh_id'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for event, elem in context:

        def hmdbproperty(path):
            if (path == 'hmdb:name/text()'):
                var = elem.xpath('hmdb:name/text()',
                                 namespaces=ns)[0].encode('utf-8')
            else:
                try:
                    var = elem.xpath(path, namespaces=ns)[0]
                except:
                    var = 'NA'
            return var

        accession = elem.xpath('hmdb:accession/text()', namespaces=ns)[0]
        monisotopic_molecular_weight = hmdbproperty(
            'hmdb:monisotopic_molecular_weight/text()')
        iupac_name = hmdbproperty('hmdb:iupac_name/text()')
        name = hmdbproperty('hmdb:name/text()')
        chemical_formula = hmdbproperty('hmdb:chemical_formula/text()')
        inchikey = hmdbproperty('hmdb:inchikey/text()')
        cas_registry_number = hmdbproperty('hmdb:cas_registry_number/text()')
        smiles = hmdbproperty('hmdb:smiles/text()')
        drugbank = hmdbproperty('hmdb:drugbank_id/text()')
        chebi_id = hmdbproperty('hmdb:chebi_id/text()')
        pubchem = hmdbproperty('hmdb:pubchem_compound_id/text()')
        phenol_explorer_compound_id = hmdbproperty(
            'hmdb:phenol_explorer_compound_id/text()')
        food = hmdbproperty('hmdb:foodb_id/text()')
        knapsack = hmdbproperty('hmdb:knapsack_id/text()')
        chemspider = hmdbproperty('hmdb:chemspider_id/text()')
        kegg = hmdbproperty('hmdb:kegg_id/text()')
        meta_cyc = hmdbproperty('hmdb:meta_cyc_id/text()')
        bigg = hmdbproperty('hmdb:bigg_id/text()')
        metlin_id = hmdbproperty('hmdb:metlin_id/text()')
        pdb_id = hmdbproperty('hmdb:pdb_id/text()')
        logpexp = hmdbproperty(
            'hmdb:experimental_properties/hmdb:property[hmdb:kind = "logp"]/hmdb:value/text()'
        )
        kingdom = hmdbproperty('hmdb:taxonomy/hmdb:kingdom/text()')
        direct_parent = hmdbproperty('hmdb:taxonomy/hmdb:direct_parent/text()')
        super_class = hmdbproperty('hmdb:taxonomy/hmdb:super_class/text()')
        classorg = hmdbproperty('hmdb:taxonomy/hmdb:class/text()')
        sub_class = hmdbproperty('hmdb:taxonomy/hmdb:sub_class/text()')
        molecular_framework = hmdbproperty(
            'hmdb:taxonomy/hmdb:molecular_framework/text()')
        vmh_id = hmdbproperty('hmdb:vmh_id/text()')
        writer.writerow({
            'accession': accession,
            'monisotopic_molecular_weight': monisotopic_molecular_weight,
            'iupac_name': iupac_name,
            'name': name,
            'chemical_formula': chemical_formula,
            'InChIKey': inchikey,
            'cas_registry_number': cas_registry_number,
            'smiles': smiles,
            'drugbank': drugbank,
            'chebi_id': chebi_id,
            'pubchem': pubchem,
            'phenol_explorer_compound_id': phenol_explorer_compound_id,
            'food': food,
            'knapsack': knapsack,
            'chemspider': chemspider,
            'kegg': kegg,
            'meta_cyc': meta_cyc,
            'bigg': bigg,
            'metlin_id': metlin_id,
            'pdb_id': pdb_id,
            'logpexp': logpexp,
            'kingdom': kingdom,
            'direct_parent': direct_parent,
            'super_class': super_class,
            'class': classorg,
            'sub_class': sub_class,
            'molecular_framework': molecular_framework,
            'vmh_id': vmh_id
        })
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context
    return


def main():
    file_input = sys.argv[1]
    hmdbextract(file_input, 'hmdb_metabolites.csv')


if __name__ == '__main__':
    main()
