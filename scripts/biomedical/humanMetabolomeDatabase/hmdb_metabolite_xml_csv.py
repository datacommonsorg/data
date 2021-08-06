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
        accession = elem.xpath('hmdb:accession/text()', namespaces=ns)[0]
        try:
            monisotopic_molecular_weight = elem.xpath(
                'hmdb:monisotopic_molecular_weight/text()', namespaces=ns)[0]
        except:
            monisotopic_molecular_weight = 'NA'
        try:
            iupac_name = elem.xpath('hmdb:iupac_name/text()',
                                    namespaces=ns)[0].encode('utf-8')
        except:
            iupac_name = 'NA'
        name = elem.xpath('hmdb:name/text()', namespaces=ns)[0].encode('utf-8')
        try:
            chemical_formula = elem.xpath('hmdb:chemical_formula/text()',
                                          namespaces=ns)[0]
        except:
            chemical_formula = 'NA'
        try:
            inchikey = elem.xpath('hmdb:inchikey/text()', namespaces=ns)[0]
        except:
            inchikey = 'NA'
        try:
            cas_registry_number = elem.xpath('hmdb:cas_registry_number/text()',
                                             namespaces=ns)[0]
        except:
            cas_registry_number = 'NA'
        try:
            smiles = elem.xpath('hmdb:smiles/text()', namespaces=ns)[0]
        except:
            smiles = 'NA'
        try:
            drugbank = elem.xpath('hmdb:drugbank_id/text()', namespaces=ns)[0]
        except:
            drugbank = 'NA'
        try:
            chebi_id = elem.xpath('hmdb:chebi_id/text()', namespaces=ns)[0]
        except:
            chebi_id = 'NA'
        try:
            pubchem = elem.xpath('hmdb:pubchem_compound_id/text()',
                                 namespaces=ns)[0]
        except:
            pubchem = 'NA'
        try:
            phenol_explorer_compound_id = elem.xpath(
                'hmdb:phenol_explorer_compound_id/text()', namespaces=ns)[0]
        except:
            phenol_explorer_compound_id = 'NA'
        try:
            food = elem.xpath('hmdb:foodb_id/text()', namespaces=ns)[0]
        except:
            food = 'NA'
        try:
            knapsack = elem.xpath('hmdb:knapsack_id/text()', namespaces=ns)[0]
        except:
            knapsack = 'NA'
        try:
            chemspider = elem.xpath('hmdb:chemspider_id/text()',
                                    namespaces=ns)[0]
        except:
            chemspider = 'NA'
        try:
            kegg = elem.xpath('hmdb:kegg_id/text()', namespaces=ns)[0]
        except:
            kegg = 'NA'
        try:
            meta_cyc = elem.xpath('hmdb:meta_cyc_id/text()', namespaces=ns)[0]
        except:
            meta_cyc = 'NA'
        try:
            bigg = elem.xpath('hmdb:bigg_id/text()', namespaces=ns)[0]
        except:
            bigg = 'NA'
        try:
            metlin_id = elem.xpath('hmdb:metlin_id/text()', namespaces=ns)[0]
        except:
            metlin_id = 'NA'
        try:
            pdb_id = elem.xpath('hmdb:pdb_id/text()', namespaces=ns)[0]
        except:
            pdb_id = 'NA'
        try:
            logpexp = elem.xpath(
                'hmdb:experimental_properties/hmdb:property[hmdb:kind = "logp"]/hmdb:value/text()',
                namespaces=ns)[0]
        except:
            logpexp = 'NA'
        try:
            kingdom = elem.xpath('hmdb:taxonomy/hmdb:kingdom/text()',
                                 namespaces=ns)[0]
        except:
            kingdom = 'NA'
        try:
            direct_parent = elem.xpath(
                'hmdb:taxonomy/hmdb:direct_parent/text()', namespaces=ns)[0]
        except:
            direct_parent = 'NA'
        try:
            super_class = elem.xpath('hmdb:taxonomy/hmdb:super_class/text()',
                                     namespaces=ns)[0]
        except:
            super_class = 'NA'
        try:
            classorg = elem.xpath('hmdb:taxonomy/hmdb:class/text()',
                                  namespaces=ns)[0]
        except:
            classorg = 'NA'
        try:
            sub_class = elem.xpath('hmdb:taxonomy/hmdb:sub_class/text()',
                                   namespaces=ns)[0]
        except:
            sub_class = 'NA'
        try:
            molecular_framework = elem.xpath(
                'hmdb:taxonomy/hmdb:molecular_framework/text()',
                namespaces=ns)[0]
        except:
            molecular_framework = 'NA'
        try:
            vmh_id = elem.xpath('hmdb:vmh_id/text()', namespaces=ns)[0]
        except:
            vmh_id = 'NA'

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
