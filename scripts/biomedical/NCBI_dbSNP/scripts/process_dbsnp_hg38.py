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
Author: Pradeep Kumar Krishnaswamy
Date: 13-Oct-2024
Name: process_dbsnp_hg38
Description: cleaning the NCBI dbSNP HG38 input file.
@source data: Download NCBI dbSNP data from FTP location. Refer to download.sh for details
"""

import csv
import os
import sys
import re
import json
import struct
import typing
import time
from copy import deepcopy
from absl import flags
from absl import logging
from datetime import datetime as dt

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))

# Setup path for import from data/util
# or set `export PYTHONPATH="./:<repo>/data/util"` in bash
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
_DATA_DIR = _SCRIPT_DIR.split('/data/')[0]
sys.path.append(os.path.join(_DATA_DIR, 'data/util'))

import file_util
from counters import Counters

# for local testing purpose only
# from Utils.counters import Counters
# import Utils.file_util as file_util

_FLAGS = flags.FLAGS
# flag dict
flags.DEFINE_string('input_file', 'gcf40_shard_aa.vcf',
                    'Input file to process. Mandatory to pass this argument')
flags.DEFINE_string('output_dir', 'output/GCF40', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input/GCF40', 'Input directory where .vcf files downloaded.')
flags.DEFINE_string('mapping_file_dir', 'output', 'path of the cui_dcid_mapping.csv file.')
flags.DEFINE_string('json_dir', 'output', 'Directory of json file generated from genome_assembly')
flags.DEFINE_string(
    'gene_id_dcid_mapping', 'ncbi_gene_id_dcid_mapping.csv',
    'Please specify the path to the "ncbi_gene_id_dcid_mapping.csv" file generated in Gene import. If not provided, the script will default to the current working directory.'
)

_FLAGS(sys.argv)

# Declare Universal Variables
_BASE_32_MAP = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l',
    'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z', 'e'
]
_NUM_BITS_32 = 5
_LONG_ID_LEN = 13

HG38_DICT = {
    'dcid': '',
    'name': '',
    'dcid_pos': '',
    'name_pos': '',
    'chrom': '',
    'position': '',
    'alleleOrigin': '',
    'alternativeAllele': '',
    'dbSNPBuildID': '',
    'geneID': '',
    'geneID_2': '',
    'referenceAllele': '',
    'rsID': '',
    'suspectReasonCode': '',
    'variantClass': '',
    'genotypesAvailable': False,
    'hasNonSynonymousFrameShift': False,
    'hasNonSynonymousMissenseMutation': False,
    'hasNonSynonymousNonsenseMutation': False,
    'hasSynonymousMutation': False,
    'isCommonVariant': False,
    'isInAcceptorSpliceSite': False,
    'isInDonorSpliceSite': False,
    'isInIntron': False,
    'isInFivePrimeGeneRegion': False,
    'isInFivePrimeUTR': False,
    'isInThreePrimeGeneRegion': False,
    'isInThreePrimeUTR': False,
    'isPublished': False
}
HG38_ALLELES_DICT = {
    'dcid': '',
    'dcid_allele': '',
    'name_allele': '',
    'CLNHGVS': '',
    'variant': '',
    'ARUP_Laboratories\x2c_Molecular_Genetics_and_Genomics\x2cARUP_Laboratories': '',
    'arupLaboratoriesMolecularGeneticsAndGenomicsArupLaboratoriesID': '',
    'HGMD': '',
    'OMIM': '',
    'PharmGKB': '',
    'PharmGKB_Clinical_Annotation': '',
    'UniProtKB': ''
}
HG38_ALLELES_DISEASE_DICT = {
    'dcid': '',
    'dcid_allele': '',
    'arupLaboratoriesMolecularGeneticsAndGenomicsArupLaboratoriesID': '',
    'geneticTestingRegistryID': '',
    'humanGeneMutationDatabaseID': '',
    'omimID': '',
    'pharmGKBID': '',
    'uniProtID': '',
    'dcid_disease': '',
    'name_disease': '',
    'experimentalFactorOntologyID': '',
    'geneReviewsID': '',
    'humanPhenotypeOntologyID': '',
    'medicalGeneticsSummariesID': '',
    'medicalSubjectHeadingID': '',
    'officeOfRareDiseasesId': '',
    'orphaNumber': '',
    'snomedCT': '',
    'medGenID': '',
    'dcid_disease_allele_association': '',
    'name_disease_allele_association': '',
    'CLNORIGIN': '',
    'CLNSIG': '',
    'CLNREVSTAT': '',
    'geneID': '',
    'geneticTestingRegistryID': '',
    'pharmGKBID': '',
    'CLNACC': ''
}
HG38_ALLELES_DRUG_DICT = {
    'dcid': '',
    'dcid_allele': '',
    'arupLaboratoriesMolecularGeneticsAndGenomicsArupLaboratoriesID': '',
    'geneticTestingRegistryID': '',
    'humanGeneMutationDatabaseID': '',
    'omimID': '',
    'pharmGKBID': '',
    'uniProtID': '',
    'dcid_disease': '',
    'name_disease': '',
    'compound_dcid': '',
    'experimentalFactorOntologyID': '',
    'geneReviewsID': '',
    'humanPhenotypeOntologyID': '',
    'medicalGeneticsSummariesID': '',
    'medicalSubjectHeadingID': '',
    'officeOfRareDiseasesId': '',
    'orphaNumber': '',
    'snomedCT': '',
    'medGenID': '',
    'dcid_disease_allele_association': '',
    'name_disease_allele_association': '',
    'CLNORIGIN': '',
    'CLNSIG': '',
    'CLNREVSTAT': '',
    'geneID': '',
    'geneticTestingRegistryID': '',
    'pharmGKBID': '',
    'CLNACC': ''
}
HG38_FREQ_DICT = {
    'dcid': '',
    'dcid_freq': '',
    'name_freq': '',
    'alleleFrequency': '',
    'measuredPopulation': '',
    'rsID': ''
}

CUI_DCID_MAPPING_DICT = {}

dbsnp_hg38_file_name = 'hg38/{0}'
dbsnp_hg38_alleles_file_name = 'hg38alleles/{0}'
dbsnp_hg38_allele_disease_file_name = 'hg38alleledisease/{0}'
dbsnp_hg38_allele_drug_file_name = 'hg38alleledrug/{0}'
dbsnp_hg38_freq_file_name = 'hg38freq/{0}'
cui_dict_mapping_file_name = 'cui_dcid_mappings.csv'
writer_hg38 = None
writer_hg38_alleles = None
writer_hg38_allele_disease = None
writer_hg38_allele_drug = None
writer_hg38_freq = None
hg19_genome_assembly_file_name = 'hg19_genome_assembly_report.json'
hg38_genome_assembly_file_name = 'hg38_genome_assembly_report.json'
gene_id_dcid_mapping_file_name = 'ncbi_gene_id_dcid_mapping.csv'
HG19_REFSEQ_DICT = {}
HG38_DCID_DICT = {}
GENE_ID_DCID_MAPPING = {}
DB_NOT_AVAILABLE = set()

HG38_FLAG_PROPS = {
    'NSF': 'hasNonSynonymousFrameShift',
    'NSM': 'hasNonSynonymousMissenseMutation',
    'NSN': 'hasNonSynonymousNonsenseMutation',
    'SYN': 'hasSynonymousMutation',
    'U3': 'isInThreePrimeUTR',
    'U5': 'isInFivePrimeUTR',
    'ASS': 'isInAcceptorSpliceSite',
    'DSS': 'isInDonorSpliceSite',
    'INT': 'isInIntron',
    'R3': 'isInThreePrimeGeneRegion',
    'R5': 'isInFivePrimeGeneRegion',
    'GNO': 'genotypesAvailable',
    'PUB': 'isPublished',
    'COMMON': 'isCommonVariant',
    'PM': 'isPublished'
}

# database dict
HG38_DB_DICT = {
    'ARUP_Laboratories\x2c_Molecular_Genetics_and_Genomics\x2cARUP_Laboratories':
        'arupLaboratoriesMolecularGeneticsAndGenomicsArupLaboratoriesID',
    'Genetic_Testing_Registry_(GTR)':
        'geneticTestingRegistryID',
    'HGMD':
        'humanGeneMutationDatabaseID',
    'OMIM':
        'omimID',
    'PharmGKB':
        'pharmGKBID',
    'PharmGKB_Clinical_Annotation':
        'pharmGKBID',
    'UniProtKB':
        'uniProtID'
}

# database to column mapping

HG38_DB_COL_MAPPING = {
    'MedGen': 'medGenID',
    'Orphanet': 'orphaNumber',
    'OMIM': 'omimID',
    'SNOMED_CT': 'snomedCT',
    'MeSH': 'medicalSubjectHeadingID',
    'Gene': 'geneID',
    'EFO': 'experimentalFactorOntologyID',
    'GeneReviews': 'geneReviewsID',
    'GeneReviews\\x2c': 'geneReviewsID',
    'Genetics_Home_Reference': 'geneticsHomeReferenceID',
    'Genetic_Testing_Registry_(GTR)': 'geneticTestingRegistryID',
    'Medical_Genetics_Summaries': 'medicalGeneticsSummariesID',
    'Office_of_Rare_Diseases': 'officeOfRareDiseasesId',
    'PharmGKB': 'pharmGKBID',
    'PharmGKB_Clinical_Annotation': 'pharmGKBID'
}

# clinicalSignificance dict
HG38_SIG_DICT = {
    '0': 'dcs:ClinSigUncertain',  # Uncertain significance
    '1': 'dcs:ClinSigNotProvided',  # not provided
    '2': 'dcs:ClinSigBenign',  # Benign
    '3': 'dcs:ClinSigLikelyBenign',  # Likely benign
    '4': 'dcs:ClinSigLikelyPathogenic',  # Likely pathogenic
    '5': 'dcs:ClinSigPathogenic',  # Pathogenic
    '6': 'dcs:ClinSigDrugResponse',  # Drug response
    '8': 'dcs:ClinSigConfersSensitivity',  # Confers sensitivity
    '9': 'dcs:ClinSigRiskFactor',  # Risk factor
    '10': 'dcs:ClinSigAssociation',  # Association
    '11': 'dcs:ClinSigProtective',  # Protective
    '12': 'dcs:ClinSigConflictingPathogenicity',  # Conflicting interpretations of pathogenicity
    '13': 'dcs:ClinSigAffects',  # Affects
    '14': 'dcs:ClinSigAssociationNotFound',  # Association not found
    '15': 'dcs:ClinSigBenign, dcs:ClinSigLikelyBenign',  # Benign/Likely bengin
    '16': 'dcs:ClinSigPathogenic, dcs:ClinSigLikelyPathogenic',  # Pathogenic/Likely pathogenic
    '17': 'dcs:ClinSigConflicting',  # Conflicting data from submitters
    '18': 'dcs:ClinSigPathogenic, dcs:ClinSigLowPenetrance',  # Pathogenic, low penetrance
    '19': 'dcs:ClinSigPathogenic, dcs:ClinSigLowPenetrance',  # Pathogenic, low penetrance
    '20': 'dcs:ClinSigEstablishedRiskAllele',  # Established risk allele
    '21': 'dcs:ClinSigLikelyRiskAllele',  # Likely risk allele
    '22': 'dcs:ClinSigUncertainRiskAllele',  # Uncertain risk allele
    '255': 'dcs:ClinSigOther'  # other
}

# enums

SAO_ENUM = {
    '0': 'dcs:VariantAlleleOriginUnspecified',
    '1': 'dcs:VariantAlleleOriginGermline',
    '2': 'dcs:VariantAlleleOriginSomatic',
    '3': 'dcs:VariantAlleleOriginGermline, dcs:VariantAlleleOriginSomatic'
}

VC_ENUM = {
    '1': 'dcs:VariationTypeSNV',
    'SNV': 'dcs:VariationTypeSNV',
    '2': 'dcs:VariationTypeDIV',
    'DIV': 'dcs:VariationTypeDIV',
    '3': 'dcs:VariationTypeHeterozygous',
    'HETEROZYGOUS': 'dcs:VariationTypeHeterozygous',
    '4': 'dcs:VariationTypeSTR',
    'STR': 'dcs:VariationTypeSTR',
    '5': 'dcs:VariationTypeNamed',
    'NAMED': 'dcs:VariationTypeNamed',
    '6': 'dcs:VariationTypeNoVariation',
    'NO VARIATION': 'dcs:VariationTypeNoVariation',
    '7': 'dcs:VariationTypeMixed',
    'MIXED': 'dcs:VariationTypeMixed',
    '8': 'dcs:VariationTypeMNV',
    'MNV': 'dcs:VariationTypeMNV',
    '9': 'dcs:VariationTypeException',
    'Exception': 'dcs:VariationTypeException',
    'INS': 'dcs:VariationTypeINS',
    'DEL': 'dcs:VariationTypeDEL',
    'INDEL': 'dcs:VariationTypeINDEL'
}

REVIEW_STATUS_ENUM = {
    'no_assertion': 'dcs:ClinVarReviewStatusNoAssertion',  # No asserition provided by submitter
    'no_assertion_criteria_provided': 'dcs:ClinVarReviewStatusNoAssertion',
    'no_criteria':
        'dcs:ClinVarReviewStatusNoCriteria',  # No assertion criteria provided by submitter
    'no_assertion_criteria_provided': 'dcs:ClinVarReviewStatusNoCriteria',
    'no_assertion': 'dcs:ClinVarReviewStatusNoCriteria',
    'no_assertion_provided': 'dcs:ClinVarReviewStatusNoCriteria',
    'Single': 'dcs:ClinVarReviewStatusSingleSubmitter',  # Classified by single submitter
    '_single_submitter': 'dcs:ClinVarReviewStatusSingleSubmitter',
    'single_submitter': 'dcs:ClinVarReviewStatusSingleSubmitter',
    'mult': 'dcs:ClinVarReviewStatusMultipleSubmitters',  # Classified by multiple submitters
    '_multiple_submitters': 'dcs:ClinVarReviewStatusMultipleSubmitters',
    'multiple_submitters': 'dcs:ClinVarReviewStatusMultipleSubmitters',
    'conf':
        'dcs:ClinVarReviewStatusConflictingInterpretations',  # Criteria provided conflicting interpretations
    'conflicting_interpretations': 'dcs:ClinVarReviewStatusConflictingInterpretations',
    '_conflicting_interpretations': 'dcs:ClinVarReviewStatusConflictingInterpretations',
    'exp': 'dcs:ClinVarReviewStatusReviewed',  # Reviewed by expert panel
    'reviewed_by_expert_panel': 'dcs:ClinVarReviewStatusReviewed',
    'guideline': 'dcs:ClinVarReviewStatusPracticeGuideline',  # Practice guideline
    'practice_guideline': 'dcs:ClinVarReviewStatusPracticeGuideline',
    'criteria_provided': 'dcs:ClinVarReviewStatusCriteriaProvided',
    'no_conflicts': 'dcs:ClinVarReviewStatusNoConflicts',
    '_no_conflicts': 'dcs:ClinVarReviewStatusNoConflicts',
    'non_interpretation_for_the_single_variant': 'dcs:ClinVarReviewStatusNoInterpretation',
    'no_interpretation_for_the_single_varian': 'dcs:ClinVarReviewStatusNoInterpretation'
}


def load_json(hg38_file_path: str, hg19_file_path: str, gene_id_dcid_mapping_path) -> None:
    global HG19_REFSEQ_DICT, HG38_DCID_DICT, GENE_ID_DCID_MAPPING
    start_time = time.time()
    hg19_dict = None
    with open(hg19_file_path, 'r') as f:
        hg19_dict = json.load(f)
    for hg in hg19_dict:
        HG19_REFSEQ_DICT[hg['refSeqAccession']] = hg['dcid']

    hg38_dict = None
    with open(hg38_file_path, 'r') as f:
        hg38_dict = json.load(f)
    for hg in hg38_dict:
        HG38_DCID_DICT[hg['refSeqAccession']] = [hg['dcid'], hg['name']]

    with open(gene_id_dcid_mapping_path) as f:
        next(f)  # Skip the header
        reader = csv.reader(f, skipinitialspace=True)
        GENE_ID_DCID_MAPPING = dict(reader)

    logging.info(f"Count of GENE_ID_DCID_MAPPING loaded {len(GENE_ID_DCID_MAPPING)}")
    logging.info(f"Time take to load mapping files {int((time.time() - start_time))} sec")


def load_mapping_data(file_path: str) -> None:
    global CUI_DCID_MAPPING_DICT
    with open(file_path, 'r') as csv_file:
        next(csv_file)
        for input_row in csv_file:
            line = input_row.split(',')
            CUI_DCID_MAPPING_DICT[line[1]] = {
                "dcid": line[0],
                'name': line[2],
                'is_drug_response': line[3]
            }
    logging.info(f"CUI DCID MAPPING records {len(CUI_DCID_MAPPING_DICT)}")


def process_input_csv(input_file: str, dbsnp_hg38_file_path: str, dbsnp_hg38_alleles_file_path: str,
                      dbsnp_hg38_allele_disease_file_path: str,
                      dbsnp_hg38_allele_drug_file_path: str,
                      dbsnp_hg38_freq_file_path: str) -> None:

    global CUI_DCID_MAPPING_DICT, writer_hg38, writer_hg38_alleles, writer_hg38_allele_disease, writer_hg38_allele_drug, writer_hg38_freq

    # open all output file and write header
    with open(dbsnp_hg38_file_path, 'w') as output_hg38, open(
            dbsnp_hg38_alleles_file_path, 'w') as output_hg38_alleles, open(
                dbsnp_hg38_allele_disease_file_path, 'w') as output_hg38_allele_disease, open(
                    dbsnp_hg38_allele_drug_file_path,
                    'w') as output_hg38_allele_drug, open(dbsnp_hg38_freq_file_path,
                                                          'w') as output_hg38_freq:
        writer_hg38 = csv.DictWriter(output_hg38, HG38_DICT, extrasaction='ignore')
        writer_hg38.writeheader()

        writer_hg38_alleles = csv.DictWriter(output_hg38_alleles,
                                             HG38_ALLELES_DICT,
                                             extrasaction='ignore')
        writer_hg38_alleles.writeheader()

        writer_hg38_allele_disease = csv.DictWriter(output_hg38_allele_disease,
                                                    HG38_ALLELES_DISEASE_DICT,
                                                    extrasaction='ignore')
        writer_hg38_allele_disease.writeheader()

        writer_hg38_allele_drug = csv.DictWriter(output_hg38_allele_drug,
                                                 HG38_ALLELES_DRUG_DICT,
                                                 extrasaction='ignore')
        writer_hg38_allele_drug.writeheader()

        writer_hg38_freq = csv.DictWriter(output_hg38_freq, HG38_FREQ_DICT, extrasaction='ignore')
        writer_hg38_freq.writeheader()

        counters = Counters()
        counters.add_counter('total', file_util.file_estimate_num_rows(input_file))

        with open(input_file, 'r') as input_file_csv:
            for line in input_file_csv:
                # skip row
                if line[0] == '#':
                    continue

                # core process starts here
                else:
                    input_row = line.replace('\n', '').split('\t')

                    # dcid
                    dcid = f'bio/{input_row[2]}'
                    rsID = input_row[2]
                    hg38_dcid = None
                    if input_row[0] in HG38_DCID_DICT:
                        hg38_dcid = HG38_DCID_DICT[input_row[0]]

                    hg38_row, dict_info = parse_hg38_row(input_row, dcid, rsID, hg38_dcid)

                    # process hg38_freq
                    process_hg38_freq(dcid, input_row[3], input_row[4], dict_info, rsID,
                                      writer_hg38_freq)

                    # Process hg38_alleles
                    process_hg38_alleles(dcid, input_row[3], input_row[4], dict_info,
                                         writer_hg38_alleles)

                    # Process hg38_alleles_disease_association & hg38_allele_drug_response_associations
                    process_hg38_alleles_disease_drug(dcid, dict_info, writer_hg38_allele_disease,
                                                      writer_hg38_allele_drug)

                    writer_hg38.writerow(hg38_row)
                counters.add_counter('processed', 1)


def parse_hg38_row(input_row, dcid, rsID, hg38_dcid):
    hg38_row = deepcopy(HG38_DICT)
    hg38_row['dcid'] = dcid
    hg38_row['rsID'] = rsID
    # name
    hg38_row['name'] = input_row[2]

    if hg38_dcid:
        hg38_row['dcid_pos'] = f'hg38_{dcid}_{input_row[1]}'
        hg38_row['name_pos'] = f'"hg38 {hg38_dcid[1]} {input_row[1]}"'
        hg38_row['chrom'] = hg38_dcid[1]
        hg38_row['inChromosome'] = hg38_dcid[1]

    hg38_row['position'] = input_row[1]
    hg38_row['alternativeAllele'] = input_row[4]
    hg38_row['referenceAllele'] = input_row[3]

    dict_info = {}
    l = input_row[7].split(';')
    for item in l:
        entry = item.split('=', maxsplit=1)
        if len(entry) == 2:
            dict_info[entry[0]] = entry[1]
        else:
            dict_info[entry[0]] = ''

    if 'GENEINFO' in dict_info:
        writeGeneInfo(dict_info['GENEINFO'], 'geneID', hg38_row)

    if 'PSEUDOGENEINFO' in dict_info:
        writeGeneInfo(dict_info['PSEUDOGENEINFO'], 'geneID_2', hg38_row)

    if 'dbSNPBuildID' in dict_info:
        hg38_row['dbSNPBuildID'] = dict_info['dbSNPBuildID']

    if 'SAO' in dict_info:
        hg38_row['alleleOrigin'] = SAO_ENUM[dict_info['SAO']]

    if 'SSR' in dict_info:
        hg38_row['suspectReasonCode'] = ','.join(write_reason_code(int(dict_info['SSR'])))

    if 'VC' in dict_info:
        hg38_row['variantClass'] = VC_ENUM[dict_info['VC']]

        # update flags
    for k, v in HG38_FLAG_PROPS.items():
        if k in dict_info:
            hg38_row[v] = True
    return hg38_row, dict_info


def writeGeneInfo(value, prop, row):
    genes = value.split('|')
    geneIDs = []
    for g in genes:
        geneIDs.append(f'dcid:bio/{g.split(":", maxsplit=1)[0]}')

    row[prop] = ','.join(geneIDs)
    return


def write_reason_code(value):
    global DB_NOT_AVAILABLE
    original = deepcopy(value)
    line = []
    try:
        if value == 0:
            line.append(f'dcs:VariantSuspectReasonCodesUnspecified')
            return (line)
        if value >= 1024:
            line.append(f'dcs:VariantSuspectReasonCodesOther')
            value -= 1024
        if value >= 512:
            value -= 512
        if value >= 256:
            value -= 256
        if value >= 128:
            value -= 128
        if value >= 64:
            value -= 64
        if value >= 32:
            value -= 32
        if value >= 16:
            line.append(f'dcs:VariantSuspectReasonCodes1kgFailed')
            value -= 16
        if value >= 8:
            line.append(f'dcs:VariantSuspectReasonCodesParaEST')
            value -= 8
        if value >= 4:
            line.append(f'dcs:VariantSuspectReasonCodesOldAlign')
            value -= 4
        if value >= 2:
            line.append(f'dcs:VariantSuspectReasonCodesByEST')
            value -= 2
        if value >= 1:
            line.append(f'dcs:VariantSuspectReasonCodesParalog')
            value -= 1
        if value > 0:
            logging.info(f'Suspect Reason Code Error: value = {value}, original = {original}')
    except:
        logging.info(f"Error parsing Reason Code {value}")
    return (line)


def process_hg38_alleles(dcid, ref, alt, dict_info, file) -> None:
    alleles = str(ref + ',' + alt).split(',')
    hgvs = []
    db_lst = []
    db_set = {}
    if 'CLNHGVS' in dict_info and len(dict_info['CLNHGVS']) > 0:
        hgvs = dict_info['CLNHGVS'].split(",")

    if 'CLNVI' in dict_info:
        db_entries = [x for x in dict_info['CLNVI'].split(',') if len(x) > 1]

        for dbs in db_entries:
            for dbs_level1 in dbs.split('|'):
                for dbs_level2 in dbs_level1.split('/'):
                    if ':' in dbs_level2:
                        dbs = dbs_level2.split(':', maxsplit=1)
                        if dbs[0] in HG38_DB_DICT.keys():
                            db_set[dbs[0]] = HG38_DB_DICT[dbs[0]]

    for idx, alle in enumerate(alleles):
        # bio/rs199509194_Allele_<hashed ‘G'>)
        row = deepcopy(HG38_ALLELES_DICT)
        dcid_allele = f'{dcid}_Allele_{generate_short_id(alle)}'
        name_allele = f'"{dcid} Allele {alle}"'
        row['dcid'] = dcid
        row['dcid_allele'] = dcid_allele
        row['name_allele'] = name_allele
        row['variant'] = alle
        if len(hgvs) > idx:
            row['CLNHGVS'] = hgvs[idx]
        if db_set:
            for db in db_set:
                row[db] = db_set[db]
        file.writerow(row)


def process_hg38_alleles_disease_drug(dcid, dict_info, disease_file, drug_file) -> None:
    dcid_disease = None
    name_disease = None
    is_drug_response = False
    dcid_compound = []
    global CUI_DCID_MAPPING_DICT
    if 'CLNDISDB' in dict_info:
        values = [x for x in dict_info['CLNDISDB'].split(',') if len(x) > 1]
        for val in values:
            if 'MedGen' in val:
                cui = val.split(':')[1]
                dcid_disease = f'bio/{cui}'
                try:
                    name_disease = CUI_DCID_MAPPING_DICT[cui]['name']
                    is_drug_response = CUI_DCID_MAPPING_DICT[cui]['is_drug_response']
                    dcid_compound.append(CUI_DCID_MAPPING_DICT[cui]['dcid'])
                except:
                    pass

    if not dcid_disease or not name_disease:
        if 'CLNDN' in dict_info:
            if not dcid_disease:
                dcid_disease = f'bio/{get_disease_pascal_case(dict_info["CLNDN"])}'
            if not name_disease:
                name_disease = dict_info['CLNDN']
                name_disease = name_disease.replace('_', ' ').replace('x2c_', '').replace(
                    '-', '').replace(',', ' ').replace('\\', ' ')

    row = deepcopy(HG38_ALLELES_DISEASE_DICT)
    row['dcid'] = dcid
    row['dcid_disease'] = dcid_disease
    row['name_disease'] = name_disease

    if 'CLNACC' in dict_info:
        acc = [d for d in dict_info['CLNACC'].split(",") if len(d) > 1]
        row['dcid_allele_disease_association'] = f'bio/{acc[0]}'
        row['name_allele_disease_association'] = acc[0]
        row['CLNACC'] = ",".join(acc)

    if 'CLNORIGIN' in dict_info:
        row['alleleOrigin'] = writeOrigin(dict_info['CLNORIGIN'])

    if 'CLNSIG' in dict_info:
        sigs_lst = set()
        for sigs in dict_info['CLNSIG'].split(","):
            for sig in sigs.split('|'):
                for s in sig.split('/'):
                    if len(s) > 0 and s != '.':
                        sigs_lst.add(HG38_SIG_DICT[s])

        row['clinicalSignificance'] = ','.join(sigs_lst)

    if 'CLNDISDB' in dict_info:
        db_dict = getDatabasetoColMapping(dict_info['CLNDISDB'])
        for db in db_dict:
            row[db] = ",".join(db_dict[db])

    if 'CLNREVSTAT' in dict_info:
        stats = set(dict_info['CLNREVSTAT'].replace('.,', '').split(','))
        row['clinVarReviewStatus'] = ",".join(stats)

    if is_drug_response:
        row['dcid_compound'] = ','.join(dcid_compound)
        drug_file.writerow(row)
    else:
        disease_file.writerow(row)


def process_hg38_freq(dcid, ref, alt, dict_info, rsID, file):
    freq_lst = []
    if 'FREQ' in dict_info:
        freq_lst = dict_info['FREQ'].split('|')
        for freq in freq_lst:
            row = parse_hg38_freq_row(dcid, ref, alt, rsID, freq)
            if row:
                file.writerow(row)


def parse_hg38_freq_row(dcid, ref, alt, rsID, freq):
    """ parse freq entry to row dict

    Args:
        dcid (_type_): dcid
        ref (_type_): referenceAllele
        alt (_type_): alternativeAllele
        rsID (_type_): rsID
        freq (_type_): freq entry

    Returns:
        _type_: row dict
    """
    row = deepcopy(HG38_FREQ_DICT)
    row['dcid'] = dcid
    row['rsID'] = rsID
    key, val = freq.split(':')
    row['dcid_freq'] = f'{dcid}_{key}'
    row['name_freq'] = f'"{rsID} {key} Population Frequency"'
    freq_val = val.split(',')
    ref_freq = f'{ref}:{freq_val[0]}'
    alt_freq_lst = []
    for idx, a in enumerate(alt.split(',')):
        if idx == 0:
            alt_freq_lst.append(f'{a}:{freq_val[1]}')
        else:
            alt_freq_lst.append(f'{a}:0.0')

    row['alleleFrequency'] = f'{ref_freq},{",".join(alt_freq_lst)}'
    row['measuredPopulation'] = key
    return row


def get_disease_pascal_case(s: str, sep=None) -> str:
    s = s.replace('x2c_', '').replace('-', '').replace(',', '')

    if sep and sep in s:
        if '\\' in s:
            s = s.replace('\\', sep)
        return "".join(map(lambda x: x[:1].upper() + x[1:], s.split(sep)))
    else:
        return s[:1].upper() + s[1:]


def getDatabasetoColMapping(value):
    global GENE_ID_DCID_MAPPING
    values = [i for i in value.split(',') if i != "." and len(i) > 0]  # split into entries
    result_dict = {}
    for v in values:
        db_lst = []
        if '\\' in v:
            db_lst.extend(v.split('\\'))
        elif '/' in v:
            db_lst.extend(v.split('/'))
        else:
            db_lst.append(v)

        for dbs in db_lst:
            if ':' in dbs:
                db, val = dbs.split(':', maxsplit=1)
                if db == 'Human_Phenotype_Ontology':
                    if 'humanPhenotypeOntologyID' in result_dict:
                        result_dict['humanPhenotypeOntologyID'].append(val)
                    else:
                        result_dict['humanPhenotypeOntologyID'] = [val]
                elif db == 'MeSH':
                    if 'medicalSubjectHeadingID' in result_dict:
                        result_dict['medicalSubjectHeadingID'].append(f'bio/{val}')
                    else:
                        result_dict['medicalSubjectHeadingID'] = [f'bio/{val}']
                elif db == 'Gene':
                    try:
                        if 'Gene' in result_dict:
                            result_dict['geneID'].append(GENE_ID_DCID_MAPPING[val])
                        else:
                            result_dict['geneID'] = [GENE_ID_DCID_MAPPING[val]]
                    except:
                        logging.info(f"Gene {val} not available in  GENE_ID_DCID_MAPPING")

                else:
                    try:
                        if HG38_DB_COL_MAPPING[db] in result_dict:
                            result_dict[HG38_DB_COL_MAPPING[db]].append(val)
                        else:
                            result_dict[HG38_DB_COL_MAPPING[db]] = [val]
                    except:
                        if db in result_dict:
                            result_dict[db].append(val)
                        else:
                            result_dict[db] = [val]

    return result_dict


def write_review_status(value):
    # extract entries
    values = re.findall(r"[\w']+", value)
    # remove duplicates
    values = set(list(values))
    line = []
    for value in values:
        if value in REVIEW_STATUS_ENUM:
            line.append(REVIEW_STATUS_ENUM[value])
        else:
            logging.info(f'Review Status Error: {value}')
    return line


def writeOrigin(value):
    # name = 'alleleOrigin'
    original = deepcopy(value)  # save copy of original value
    values = [i for i in re.split('\||,', value) if i != "." and len(i) > 0]  # split into entries
    line = []
    for v in values:
        v = int(v)  # convert to integer
        if v >= 1073741824:
            line.append('dcs:VariantAlleleOriginOther')
            v -= 1073741824
        if v == 0:
            line.append('dcs:VariantAlleleOriginUnspecified')
            next
        if v >= 1024:
            line.append('dcs:VariantAlleleOriginOther')
            v -= 1024
        if v >= 512:
            line.append('dcs:VariantAlleleOriginTestedInconclusive')
            v -= 512
        if v >= 256:
            line.append('dcs:VariantAlleleOriginNotTested')
            v -= 256
        if v >= 128:
            line.append('dcs:VariantAlleleOriginUniParental')
            v -= 128
        if v >= 64:
            line.append('dcs:VariantAlleleOriginBiParenal')
            v -= 64
        if v >= 32:
            line.append('dcs:VariantAlleleOriginDeNovo')
            v -= 32
        if v >= 16:
            line.append('dcs:VariantAlleleOriginMaternal')
            v -= 16
        if v >= 8:
            line.append('dcs:VariantAlleleOriginPaternal')
            v -= 8
        if v >= 4:
            line.append('dcs:VariantAlleleOriginInherited')
            v -= 4
        if v >= 2:
            line.append('dcs:VariantAlleleOriginSomatic')
            v -= 2
        if v >= 1:
            line.append('dcs:VariantAlleleOriginGermline')
            v -= 1
        if v > 0:
            logging.info(f'Allele Origin Error: value = {value}, original = {original}')
    return ','.join(line)


def generate_short_id(input_str):
    fp = robust_farm_fingerprint_64(input_str)
    res = []
    for i in range(0, _LONG_ID_LEN):
        idx = fp & 0x1f
        res.append(_BASE_32_MAP[idx])
        fp = fp >> _NUM_BITS_32
        if fp == 0:
            break
    return u''.join(res)


# define functions
def robust_farm_fingerprint_64(data: typing.Union[str, bytes]) -> int:
    """Calculates a 64-bit FarmHash fingerprint, robust against different input types.

    Args:
        data: The data to fingerprint (either a string or bytes).

    Returns:
        The 64-bit fingerprint as an integer.
    """

    if isinstance(data, str):
        data = data.encode("utf-8")  # Ensure bytes for hashing consistency

    # Modified from FarmHash (reference: https://github.com/google/farmhash)
    size = len(data)
    h = size * 0x811c9dc5

    if size >= 8:
        h = (h ^ struct.unpack("<Q", data[:8])[0]) * 0x811c9dc5
        data = data[8:]
        size -= 8

    if size >= 4:
        h = (h ^ struct.unpack("<I", data[:4])[0]) * 0x811c9dc5
        data = data[4:]
        size -= 4

    if size >= 2:
        h = (h ^ struct.unpack("<H", data[:2])[0]) * 0x811c9dc5
        data = data[2:]
        size -= 2

    if size == 1:
        h = (h ^ data[0]) * 0x811c9dc5

    h = (h ^ h >> 33) * 0xc2b2ae35
    h = h ^ h >> 29
    return h


def main(input_file_name: str) -> None:
    """ Main method

    Args:
        input_file (str): file path to process
    """
    logging.set_verbosity('info')
    logging.info(f"HG38 processing input file {input_file_name}  - {dt.now()}")
    start_time = time.time()

    input_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, input_file_name)

    output_file_name = input_file_name.split('.')[0] + '.csv'
    dbsnp_hg38_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir,
                                        dbsnp_hg38_file_name.format(output_file_name))
    dbsnp_hg38_alleles_file_path = os.path.join(
        MODULE_DIR + '/' + _FLAGS.output_dir, dbsnp_hg38_alleles_file_name.format(output_file_name))
    dbsnp_hg38_allele_disease_file_path = os.path.join(
        MODULE_DIR + '/' + _FLAGS.output_dir,
        dbsnp_hg38_allele_disease_file_name.format(output_file_name))
    dbsnp_hg38_allele_drug_file_path = os.path.join(
        MODULE_DIR + '/' + _FLAGS.output_dir,
        dbsnp_hg38_allele_drug_file_name.format(output_file_name))
    dbsnp_hg38_freq_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir,
                                             dbsnp_hg38_freq_file_name.format(output_file_name))
    logging.info("load mapping data")
    load_mapping_data(
        os.path.join(MODULE_DIR + '/' + _FLAGS.mapping_file_dir, cui_dict_mapping_file_name))
    logging.info("load JSON data")
    load_json(os.path.join(MODULE_DIR + '/' + _FLAGS.json_dir, hg19_genome_assembly_file_name),
              os.path.join(MODULE_DIR + '/' + _FLAGS.json_dir, hg38_genome_assembly_file_name),
              os.path.join(MODULE_DIR, _FLAGS.gene_id_dcid_mapping))

    process_input_csv(input_file_path, dbsnp_hg38_file_path, dbsnp_hg38_alleles_file_path,
                      dbsnp_hg38_allele_disease_file_path, dbsnp_hg38_allele_drug_file_path,
                      dbsnp_hg38_freq_file_path)

    global DB_NOT_AVAILABLE
    if len(DB_NOT_AVAILABLE) > 0:
        logging.info("Database not available in the DB DICT..")
        for db in DB_NOT_AVAILABLE:
            logging.info(db)

    logging.info(f"Time taken to process {((time.time() - start_time)/60):.2f} - {dt.now()}")


if __name__ == '__main__':
    main(_FLAGS.input_file)
