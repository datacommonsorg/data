# Copyright 2021 Google LLC
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
'''
Author: Padma Gundapaneni @padma-g
Date: 7/28/21
Description: This script will generate a csv of gene symbols for a given species.
@input_file   filepath to the original gaf file with gene symbols
@species      species of gene annotations contained in original gaf file
@output_file  filepath to the csv to which the gene symbols are written
python3 generate_gene_symbols.py input_file species output_file
'''

import sys
import pandas as pd


def main():
    """Main function to generate the gene symbols."""
    file_path = sys.argv[1]
    species = sys.argv[2]
    output_file = sys.argv[3]
    data = add_headers_remove_rows(file_path, species)
    return_gene_symbols(data, output_file)


def add_headers_remove_rows(file_path, species):
    """
    Args:
        file: a tab-separated gene ontology annotation file
        species: a species name
    Returns:
        a file with a correctly-formatted header
    """
    data = pd.read_csv(file_path,
                       sep="\t",
                       names=[
                           "DB", "DBObjectID", "DBObjectSymbol", "Qualifier",
                           "GOID", "DBReference", "EvidenceCode", "With/From",
                           "Aspect", "DBObjectName", "DBObjectSynonym",
                           "DBObjectType", "Taxon", "Date", "AssignedBy"
                       ])
    if species == "mouse":
        data = data[31:]
    elif species in ("chicken", "human"):
        data = data[41:]
    elif species in ("chicken_isoform", "human_isoform"):
        data = data[27:]
    elif species in ("fly", "zebrafish"):
        data = data[33:]
    elif species == "yeast":
        data = data[35:]
    elif species == "worm":
        data = data[127909:]
    return data


def return_gene_symbols(data, output_file):
    """
    Args:
        data: a tab-separated gene ontology annotation file
        output_file: an output file path
    Returns:
        a csv file with gene symbols
    """
    print("Returning gene symbols...")
    data = pd.DataFrame(data.DBObjectSymbol.unique().tolist())
    data.columns = ['GeneSymbol']
    data.to_csv(output_file)
    print("Returned gene symbols!")


if __name__ == "__main__":
    main()
