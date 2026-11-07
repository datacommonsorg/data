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
import pandas as pd
import numpy as np
import sys
import os
import csv
from SPARQLWrapper import SPARQLWrapper, JSON
from io import StringIO
from lxml import etree


def hmdbextract(name, file):
    ns = {'hmdb': 'http://www.hmdb.ca'}
    context = etree.iterparse(name, tag='{http://www.hmdb.ca}protein')
    csvfile = open(file, 'w')
    fieldnames = [
        'accession', 'protein_type', 'gene_name', 'general_function',
        'specific_function', 'subcellular_location', 'gene_loc',
        'residue_number', 'genbank_protein_id', 'uniprot_id', 'genbank_gene_id',
        'genecard_id', 'hgnc_id'
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for event, elem in context:

        def hmdbproperty(path):
            try:
                var = elem.xpath(path, namespaces=ns)[0]
            except:
                var = 'NA'
            return var

        accession = elem.xpath('hmdb:accession/text()', namespaces=ns)[0]
        protein_type = hmdbproperty('hmdb:protein_type/text()')
        gene_name = hmdbproperty('hmdb:gene_name/text()')
        general_function = hmdbproperty('hmdb:general_function/text()')
        specific_function = hmdbproperty('hmdb:specific_function/text()')
        subcellular_location = hmdbproperty(
            'hmdb:subcellular_locations/hmdb:subcellular_location/text()')
        gene_loc = hmdbproperty(
            'hmdb:gene_properties/hmdb:chromosome_location/text()')
        residue_number = hmdbproperty(
            'hmdb:protein_properties/hmdb:residue_number/text()')
        genbank_protein_id = hmdbproperty('hmdb:genbank_protein_id/text()')
        uniprot_id = hmdbproperty('hmdb:uniprot_id/text()')
        genbank_gene_id = hmdbproperty('hmdb:genbank_gene_id/text()')
        genecard_id = hmdbproperty('hmdb:genecard_id/text()')
        hgnc_id = hmdbproperty('hmdb:hgnc_id/text()')

        writer.writerow({
            'accession': accession,
            'protein_type': protein_type,
            'gene_name': gene_name,
            'general_function': general_function,
            'specific_function': specific_function,
            'subcellular_location': subcellular_location,
            'gene_loc': gene_loc,
            'residue_number': residue_number,
            'genbank_protein_id': genbank_protein_id,
            'uniprot_id': uniprot_id,
            'genbank_gene_id': genbank_gene_id,
            'genecard_id': genecard_id,
            'hgnc_id': hgnc_id
        })
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
    hmdbextract(file_input, 'hmdb_p.csv')


if __name__ == '__main__':
    main()
