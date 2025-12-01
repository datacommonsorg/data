# Copyright 2024 Google LLC
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
Author: Samantha Piekos
Date: 02/21/2024
Name: format_virus_master_species_list.py
Description: Formats ICTV Master Species List into a csv format for import
into Data Commons. This includes converting genome composition and last
change made to corresponding enums. Dcids were formatted by converting the
viral species name to pascalcase and adding the prefix 'bio/'. The viral
taxonomy is encoded in enum format.
@file_input: ICTV Master Speices List .xslx file
@file_output: formatted csv format of Virus nodes
"""

# load environment
import pandas as pd
import sys

# declare universal variables
DICT_CHANGE_ENUM = {
    'abolished': 'dcs:VirusLastTaxonomicChangeAbolished',
    'demoted': 'dcs:VirusLastTaxonomicChangeDemoted',
    'merged': 'dcs:VirusLastTaxonomicChangeMerged',
    'moved': 'dcs:VirusLastTaxonomicChangeMoved',
    'new': 'dcs:VirusLastTaxonomicChangeNew',
    'promoted': 'dcs:VirusLastTaxonomicChangePromoted',
    'removed as type species': 'dcs:VirusLastTaxonomicChangeRemoved',
    'renamed': 'dcs:VirusLastTaxonomicChangeRenamed',
    'split': 'dcs:VirusLastTaxonomicChangeSplit'
}

DICT_GC = {
    'dsDNA':
        'dcs:VirusGenomeCompositionDoubleStrandedDNA',
    'ssDNA':
        'dcs:VirusGenomeCompositionSingleStrandedDNA',
    'ssDNA(-)':
        'dcs:VirusGenomeCompositionSingleStrandedDNANegative',
    'ssDNA(+)':
        'dcs:VirusGenomeCompositionSingleStrandedDNAPositive',
    'ssDNA(+/-)':
        'dcs:VirusGenomeCompositionSingleStrandedDNA',
    'dsDNA-RT':
        'dcs:VirusGenomeCompositionDoubleStrandedDNAReverseTranscription',
    'ssRNA-RT':
        'dcs:VirusGenomeCompositionSingleStrandedRNAReverseTranscription',
    'dsRNA':
        'dcs:VirusGenomeCompositionDoubleStrandedRNA',
    'ssRNA':
        'dcs:VirusGenomeCompositionSingleStrandedRNA',
    'ssRNA(-)':
        'dcs:VirusGenomeCompositionSingleStrandedRNANegative',
    'ssRNA(+)':
        'dcs:VirusGenomeCompositionSingleStrandedRNAPositive',
    'ssRNA(+/-)':
        'dcs:VirusGenomeCompositionSingleStrandedRNA'
}

HEADER = [
    'sort', 'realm', 'subrealm', 'kingdom', 'subkingdom', 'phylum', 'subphylum',
    'class', 'subclass', 'order', 'suborder', 'family', 'subfamily', 'genus',
    'subgenus', 'species', 'genomeComposition', 'lastChange',
    'lastChangeVersion', 'proposalForLastChange', 'taxonHistoryURL', 'dcid'
]

LIST_TAXONOMIC_LEVELS = [
    'realm', 'subrealm', 'kingdom', 'subkingdom', 'phylum', 'subphylum',
    'class', 'subclass', 'order', 'suborder', 'family', 'subfamily', 'genus',
    'subgenus'
]


# declare functions
def pascalcase(s):
    list_words = s.split()
    converted = "".join(
        word[0].upper() + word[1:].lower() for word in list_words)
    return converted


def check_for_illegal_charc(s):
    list_illegal = ["'", "–", "*"
                    ">", "<", "@", "]", "[", "|", ":", ";"
                    " "]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)


def format_taxonomic_rank_properties(df, index, row):
    for rank in LIST_TAXONOMIC_LEVELS:
        if row[rank] == row[rank]:
            enum = 'dcs:Virus' + rank.upper()[0] + rank.lower(
            )[1:] + pascalcase(row[rank])
            df.loc[index, rank] = enum
    return df


def convert_gc_to_enum(gc):
    list_enum = []
    list_gc = gc.split(';')
    for item in list_gc:
        item = item.strip()
        enum = DICT_GC[item]
        list_enum.append(enum)
    return (',').join(list_enum)


def convert_change_to_enum(change):
    list_enum = []
    change = change.lower()
    list_changes = change.split(',')[:-1]
    for item in list_changes:
        enum = DICT_CHANGE_ENUM[item]
        list_enum.append(enum)
    return (',').join(list_enum)


def clean_df(df):
    for index, row in df.iterrows():
        dcid = 'bio/' + pascalcase(row['species'])
        check_for_illegal_charc(dcid)
        df = format_taxonomic_rank_properties(df, index, row)
        df.loc[index, 'dcid'] = dcid
        df.loc[index, 'genomeComposition'] = convert_gc_to_enum(
            row['genomeComposition'])
        df.loc[index, 'lastChange'] = convert_change_to_enum(row['lastChange'])
        df.loc[index,
               'taxonHistoryURL'] = row['taxonHistoryURL'].strip('ICTVonline=')
    return df


def clean_file(f, w):
    df = pd.read_excel(f, names=HEADER, header=None, sheet_name=1)
    df = df.drop('sort', axis=1).drop(0, axis=0)
    df = clean_df(df)
    df.to_csv(w, index=False)


def main():
    file_input = sys.argv[1]
    file_output = sys.argv[2]

    clean_file(file_input, file_output)


if __name__ == '__main__':
    main()
