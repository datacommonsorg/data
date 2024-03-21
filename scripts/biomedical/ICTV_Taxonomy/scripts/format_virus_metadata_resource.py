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
Description: Formats ICTV Virus Metadata Resource into two csv files - 
one specific to VirusIsolates and the other VirusGenomeSegment for import
into Data Commons. This includes converting genome composition, genome
coverage, viral host, and viral source to corresponding enums. Virus,
VirusIsolate and VirusGenomeSegment dcids were formatted by converting
the names into pascal case and adding the prefix 'bio/'. The viral taxonomy
is encoded in enum format and found within Virus nodes. Whether an isolate
is an exemplar isolate or not was encoded into a boolean as a value for the
property 'isExemplar'.
@file_input: 	ICTV Virus Metadata Resource .xslx file
@file_output:	formatted csv format of VirusIsolate and VirusGenomeSegment
			 	nodes
"""

# set up environment
import pandas as pd
import sys
import unidecode

# declare universal variables
DICT_COVERAGE = {
    'coding-complete genome': 'dcs:GenomeCoverageCompleteGenome',
    'complete genome': 'dcs:GenomeCoverageCompleteGenome',
    'complete coding genome': 'dcs:GenomeCoverageCompleteCodingGenome',
    'no entry in genbank': 'dcs:GenomeCoverageNoEntryInGenBank',
    'partial genome': 'dcs:GenomeCoveragePartialGenome'
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

DICT_HOST = {
    'algae': 'dcs:VirusHostAlgae',
    'archaea': 'dcs:VirusHostArchaea',
    'bacteria': 'dcs:VirusHostBacteria',
    'fungi': 'dcs:VirusHostFungi',
    'invertebrates': 'dcs:VirusHostInvertebrates',
    'plants': 'dcs:VirusHostPlants',
    'protists': 'dcs:VirusHostProtists',
    'vertebrates': 'dcs:VirusHostVertebrates'
}

DICT_SOURCE = {
    'freshwater': 'dcs:VirusSourceFreshwater',
    'invertebrates': 'dcs:VirusSourceInvertebrates',
    'marine': 'dcs:VirusSourceMarine',
    'phytobiome': 'dcs:VirusSourcePhytobiome',
    'plants': 'dcs:VirusSourcePlants',
    'protists': 'dcs:VirusSourceProtists',
    'sewage': 'dcs:VirusSourceSewage',
    'soil': 'dcs:VirusSourceSoil'
}

HEADER = [
    'sort', 'isolateSort', 'realm', 'subrealm', 'kingdom', 'subkingdom',
    'phylum', 'subphylum', 'class', 'subclass', 'order', 'suborder', 'family',
    'subfamily', 'genus', 'subgenus', 'species', 'isExemplar', 'name',
    'abbreviation', 'isolateDesignation', 'genBankAccession', 'refSeqAccession',
    'genomeCoverage', 'genomeComposition', 'hostSource', 'host', 'source',
    'dcid', 'isolate_dcid', 'isolate_name'
]

HEADER_2 = [
    'dcid', 'name', 'genBankAccession', 'genomeSegmentOf', 'refSeqAccession'
]

LIST_TAXONOMIC_LEVELS = [
    'realm', 'subrealm', 'kingdom', 'subkingdom', 'phylum', 'subphylum',
    'class', 'subclass', 'order', 'suborder', 'family', 'subfamily', 'genus',
    'subgenus'
]


# declare functions
# declare functions
def pascalcase(s):
    list_words = s.split()
    converted = "".join(word[0].upper() + word[1:] for word in list_words)
    return converted


def check_for_illegal_charc(s):
    list_illegal = [
        "'", "#", "–", "*"
        ">", "<", "@", "]", "[", "|", ":", ";", " "
    ]
    if any([x in s for x in list_illegal]):
        print('Error! dcid contains illegal characters!', s)


def format_list(s):
    if s != s:
        return s
    list_items = []
    s = str(s)
    list_s = s.split(';')
    for item in list_s:
        list_items.append(item.strip())
    return (',').join(list_items)


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


def convert_coverage_to_enum(cov):
    return DICT_COVERAGE[cov.lower()]


def convert_type_to_boolean(t):
    if t == 'E':
        return True
    if t == 'A':
        return False
    print('Error! Not an expected isolate type! Expected E or A, but got', t,
          '.')


def convert_source_to_enum(source):
    source = source[:-4]
    return DICT_SOURCE[source]


def convert_host_to_enum(host):
    list_enum = []
    list_host = host.split(',')
    for item in list_host:
        item = item.strip()
        enum = DICT_HOST[item]
        list_enum.append(enum)
    return (',').join(list_enum)


def handle_genBank_missing_exception(n, virus_dcid, virus_name):
    if n != n:
        dcid = virus_dcid + 'Isolate'
        name = virus_name + ' Isolate'
        return dcid, name
    n = str(n)
    if ';' in n:
        n = n.split(';')[0]
    dcid = virus_dcid + pascalcase(n)
    dcid = dcid.replace("'", "")
    dcid = dcid.replace('–', '-')
    name = virus_name + n
    return dcid, name


def handle_genBank_components_exception(genBank, virus_dcid, virus_name):
    dcid = virus_dcid
    name = virus_name
    list_genBank = genBank.split(';')
    for item in list_genBank:
        if ':' in item:
            n, gb = item.split(':')
            dcid = virus_dcid + '_' + gb.strip()
            name = virus_name + gb
        else:
            dcid = virus_dcid + '_' + item.strip()
            name = virus_name + item
    return dcid, name


def format_isolate_designation_for_dcid(des):
    des = str(des)
    des = des.replace(':', '_')
    des = des.replace(';', '_')
    des = des.replace('[', '(')
    des = des.replace(']', ')')
    des = des.replace('-', '_')
    des = des.replace('–', '_')
    des = des.replace("'", '')
    des = des.replace('#', '')
    return des


def verify_isolate_dcid_uniqueness(dcid, list_isolate_dcids, genBank,
                                   virus_abrv):
    if dcid in list_isolate_dcids:
        if ';' in genBank:
            dcid = dcid + '_' + virus_abrv
        else:
            dcid = dcid + '_' + genBank
        print(
            'Non-unique VirusIsolate dcid generated! Added additional info to differentiate:',
            dcid)
    list_isolate_dcids.append(dcid)
    return dcid, list_isolate_dcids


def declare_isolate_dcid(n, genBank, virus_dcid, virus_name, virus_abrv,
                         isolate_designation, list_isolate_dcids):
    if isolate_designation == isolate_designation:
        des = format_isolate_designation_for_dcid(isolate_designation)
        dcid = virus_dcid + '_' + pascalcase(des)
        name = virus_name + ' strain ' + str(isolate_designation)
    elif genBank != genBank:
        dcid, name = handle_genBank_missing_exception(n, virus_dcid, virus_name)
    elif ':' in genBank or ';' in genBank:
        dcid, name = handle_genBank_components_exception(
            genBank, virus_dcid, virus_name)
    else:
        dcid = virus_dcid + '_' + genBank
        name = virus_name + ' ' + genBank
    dcid = dcid.replace(' ', '')
    dcid = unidecode.unidecode(dcid)
    dcid, list_isolate_dcids = verify_isolate_dcid_uniqueness(
        dcid, list_isolate_dcids, genBank, virus_abrv)
    return dcid, name, list_isolate_dcids


def make_refSeq_dict(refSeq):
    d = {}
    list_refSeq = refSeq.split(';')
    for item in list_refSeq:
        if ':' in item:
            name, rs = item.split(':')
            d[name.strip()] = rs.strip()
    return d


def handle_genome_segments(df_segment, virus_dcid, virus_name, isolate_dcid,
                           genBank, refSeq):
    dict_refSeq = {}
    list_genBank = genBank.split(';')
    if refSeq == refSeq:
        dict_refSeq = make_refSeq_dict(refSeq)
    for item in list_genBank:
        d = {
            'dcid': [],
            'name': [],
            'genBankAccession': [],
            'genomeSegmentOf': [],
            'refSeqAccession': []
        }
        if ':' not in item:
            continue
        name, gb = item.split(':')
        name = name.strip()
        gb = gb.strip()
        d['dcid'].append(virus_dcid + gb)
        check_for_illegal_charc(virus_dcid + gb)
        d['name'].append(virus_name + ' Segment ' + name)
        d['genBankAccession'].append(gb)
        d['genomeSegmentOf'].append('dcid:' + isolate_dcid)
        if name in dict_refSeq:
            d['refSeqAccession'].append(dict_refSeq[name])
        else:
            d['refSeqAccession'].append('')
        df_new_row = pd.DataFrame.from_dict(d, orient='columns')
        df_segment = pd.concat([df_segment, df_new_row], ignore_index=True)
    return df_segment


def clean_df(df, df_segment):
    list_isolate_dcids = []
    for index, row in df.iterrows():
        dcid = 'bio/' + pascalcase(row['species'])
        check_for_illegal_charc(dcid)
        df.loc[index, 'dcid'] = dcid
        df = format_taxonomic_rank_properties(df, index, row)
        isolate_dcid, isolate_name, list_isolate_dcids = declare_isolate_dcid(
            row['name'], row['genBankAccession'], dcid, row['species'],
            row['abbreviation'], row['isolateDesignation'], list_isolate_dcids)
        check_for_illegal_charc(isolate_dcid)
        df.loc[index, 'isolate_dcid'] = isolate_dcid
        df.loc[index, 'isolate_name'] = isolate_name
        df.loc[index, 'genomeComposition'] = convert_gc_to_enum(
            row['genomeComposition'])
        df.loc[index, 'genomeCoverage'] = convert_coverage_to_enum(
            row['genomeCoverage'])
        df.loc[index, 'isExemplar'] = convert_type_to_boolean(row['isExemplar'])
        df.loc[index, 'name'] = format_list(row['name'])
        df.loc[index, 'abbreviation'] = format_list(row['abbreviation'])
        df.loc[index,
               'isolateDesignation'] = format_list(row['isolateDesignation'])
        genBank = row['genBankAccession']
        if genBank == genBank and ':' in genBank:
            df_segment = handle_genome_segments(df_segment, dcid, row['name'],
                                                isolate_dcid, genBank,
                                                row['refSeqAccession'])
            df.loc[index, 'genBankAccession'] = ''
            df.loc[index, 'refSeqAccession'] = ''
        elif genBank == genBank and ';' in genBank:
            df.loc[index, 'genBankAccession'] = format_list(genBank)
            df.loc[index,
                   'refSeqAccession'] = format_list(row['refSeqAccession'])
        if '(S)' in row['hostSource']:
            df.loc[index, 'source'] = convert_source_to_enum(row['hostSource'])
        else:
            df.loc[index, 'host'] = convert_host_to_enum(row['hostSource'])
    return df, df_segment


def clean_file(f, w, w_2):
    df = pd.read_excel(f, names=HEADER, header=None, sheet_name=0)
    df = df.drop(0, axis=0)
    df_segment = pd.DataFrame([], columns=HEADER_2)
    df, df_segment = clean_df(df, df_segment)
    df = df.drop(['sort', 'isolateSort', 'hostSource'], axis=1)
    df.to_csv(w, index=False)
    df_segment.to_csv(w_2, index=False)


def main():
    file_input = sys.argv[1]
    file_output_1 = sys.argv[2]
    file_output_2 = sys.argv[3]

    clean_file(file_input, file_output_1, file_output_2)


if __name__ == '__main__':
    main()
