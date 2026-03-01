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
'''
Author: Pradeep Kumar Krishnaswamy
Date: 03/06/2024
Name: format_clinvar_and_position.py
Description: converts poorly formatted vcf file into an mcf file, which
includes seperating out data into distinct properties and resolving
incongruent formmatings.
@file_input: input vcf file downloaded from ncbi clinvar
@file_output: formatted cvs files
'''

# Set up environment
import copy
import os
import struct
import sys
import time
import typing
import csv
import re
from absl import logging

MODULE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')

# Setup path for import from data/util
# or set `export PYTHONPATH="./:<repo>/data/util"` in bash
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
_DATA_DIR = _SCRIPT_DIR.split('/data/')[0]
sys.path.append(os.path.join(_DATA_DIR, 'data/util'))

import file_util
from counters import Counters

# Declare Universal Variables
_BASE_32_MAP = [
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'b', 'c', 'd', 'f', 'g',
    'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y',
    'z', 'e'
]

_NUM_BITS_32 = 5
_LONG_ID_LEN = 13

# set species name
SPECIES = 'HomoSapiens'

# declare assembly
ASSEMBLY_HG38 = 'hg38'
ASSEMBLY_HG19 = 'hg19'

OBSERVATION_DATE = ''

# declare fields accounted for in this import
RECORDED_INFO = [
    'RS', 'ALLELEID', 'CLNDISDBINCL', 'CLNDNINCL', 'CLNHGVS', 'CLNREVSTAT',
    'CLNSIGINCL', 'CLNVC', 'CLNVCSO', 'GENEINFO', 'MC', 'ORIGIN', 'AF_ESP',
    'AF_EXAC', 'AF_TGP', 'CLNVI', 'CLNSIGCONF', 'DBVARID', 'CLNDN', 'CLNSIG',
    'CLNDISDB', 'ONC', 'ONCDN', 'ONCDISDB', 'ONCREVSTAT', 'SCI', 'SCIDN',
    'SCIDISDB', 'SCIREVSTAT'
]

DICT_REVIEW_STATUS = {
    'criteria_provided':
        'dcs:ClinVarReviewStatusCriteriaProvided',
    '_single_submitter':
        'dcs:ClinVarReviewStatusSingleSubmitter',
    'single':
        'dcs:ClinVarReviewStatusSingleSubmitter',
    'single_submitter':
        'dcs:ClinVarReviewStatusSingleSubmitter',
    'no_assertion_criteria_provided':
        'dcs:ClinVarReviewStatusNoCriteria',
    'no_assertion':
        'dcs:ClinVarReviewStatusNoCriteria',
    'no_criteria':
        'dcs:ClinVarReviewStatusNoCriteria',
    'no_assertion_provided':
        'dcs:ClinVarReviewStatusNoCriteria',
    'mult':
        'dcs:ClinVarReviewStatusMultipleSubmitter',
    'multiple_submitters':
        'dcs:ClinVarReviewStatusMultipleSubmitter',
    '_multiple_submitters':
        'dcs:ClinVarReviewStatusMultipleSubmitter',
    'reviewed_by_expert_panel':
        'dcs:ClinVarReviewStatusReviewed',
    'conflicting_interpretations':
        'dcs:ClinVarReviewStatusConflictingInterpretations',
    '_conflicting_interpretations':
        'dcs:ClinVarReviewStatusConflictingInterpretations',
    '_conflicting_classifications':
        'dcs:ClinVarReviewStatusConflictingInterpretations',
    'non_interpretation_for_the_single_variant':
        'dcs:ClinVarReviewStatusNoInterpretation',
    'no_interpretation_for_the_single_variant':
        'dcs:ClinVarReviewStatusNoInterpretation',
    'no_classification_provided':
        'dcs:ClinVarReviewStatusNoInterpretation',
    'no_classifications_from_unflagged_records':
        'dcs:ClinVarReviewStatusNoInterpretation',
    'no_classification_for_the_single_variant':
        'dcs:ClinVarReviewStatusNoInterpretation',
    'practice_guideline':
        'dcs:ClinVarReviewStatusPracticeGuideline',
    'no_conflicts':
        'dcs:ClinVarReviewStatusNoConflicts',
    '_no_conflicts':
        'dcs:ClinVarReviewStatusNoConflicts'
}

DICT_CLIN_SIG_CATEGORY = {
    'Tier_I': 'dcs:ClinicalSignificanceTierOne',
    'Tier_II': 'dcs:ClinicalSignificanceTierTwo',
    'Tier_III': 'dcs:ClinicalSignificanceTierThree',
    'Tier_IV': 'dcs:ClinicalSignificanceTierFour',
}

MEASURED_POPULATION_DICT = {
    'AF_ESP': 'Exome Sequencing Project (ESP)',
    'AF_EXAC': 'The Exome Aggregation Consortium (ExAC)',
    'AF_TGP': 'The Genome Project (TGP)'
}

# dict for output csv
CLINVAR_OUTPUT_DICT = {
    'dcid': '',
    'name': '',
    'dcid_pos': '',
    'name_pos': '',
    'chrom': '',
    'position': '',
    'alleleOrigin': '',
    'associatedDiseaseName': '',
    'associatedDrugResponseEfficacy': '',
    'canonicalAlleleID': '',
    'catalogueOfSomaticMutationsInCancerID': '',
    'clinicalSignificanceCategory_onc': '',
    'clinicalSignificanceCategory_sic': '',
    'clinicalSignificance': '',
    'clinVarAlleleID': '',
    'clinVarGermlineReviewStatus': '',
    'clinVarOncogenicityReviewStatus': '',
    'clinVarSomaticReviewStatus': '',
    'dbVarID': '',
    'experimentalFactorOntologyID': '',
    'geneID': '',
    'geneSymbol': '',
    'geneticTestingRegistryID': '',
    'geneticVariantClass': '',
    'geneticVariantFunctionalCategory': '',
    'hbVarID': '',
    'hg19GenomicPosition': '',
    'hgvsNomenclature': '',
    'humanPhenotypeOntologyID': '',
    'inChromosome': '',
    'leidenOpenVariationDatabaseID': '',
    'medicalSubjectHeadingID': '',
    'mitochondrialDiseaseSequenceDataResourceID': '',
    'mondoID': '',
    'ncbiGeneID': '',
    'ncbiGeneID_info': '',
    'observedAllele': '',
    'omimID': '',
    'omimID_gv': '',
    'orphaNumber': '',
    'pharmgkbClinicalAnnotationID': '',
    'referenceAllele': '',
    'rsID': '',
    'sequenceOntologyID': '',
    'sequenceOntologyID_mc': '',
    'snomedCT': '',
    'umlsConceptUniqueID': '',
    'uniProtID': '',
    'uniProtKBSwissProtID': ''
}

CLINVAR_CONFLICTING_OUTPUT_DICT = {
    'dcid': '',
    'dcid_conflicting': '',
    'name_conflicting': '',
    'alternativeAllele': '',
    'clinicalSignificance': '',
    'count': ''
}

CLINVAR_OBS_OUTPUT_DICT = {
    'dcid': '',
    'dcid_freq': '',
    'name_freq': '',
    'alleleFrequency': '',
    'measuredPopulation': '',
    'rsID': ''
}

CLINVAR_POS_OUTPUT_DICT = {
    'dcid': '',
    'name': '',
    'dcid_pos': '',
    'name_pos': '',
    'chrom': '',
    'position': '',
    'rsID': ''
}

OUTPUT_CLINVAR_FILE_NAME = 'clinvar.csv'
OUTPUT_CLINVAR_CONFLICTING_FILE_NAME = 'clinvar_conflicting.csv'
OUTPUT_CLINVAR_OBS_FILE_NAME = 'clinvar_obs.csv'
OUTPUT_CLINVAR_POS_FILE_NAME = 'clinvar_pos_only.csv'

CLINVAR_FILE_WRITER = None
CLINVAR_CONFLICTING_FILE_WRITER = None
CLINVAR_OBS_FILE_WRITER = None
CLINVAR_POS_FILE_WRITER = None

CURRENT_ROW = None

# default input files
HG19_INPUT_FILES = ['input/hg19_clinvar.vcf', 'input/hg19_clinvar_papu.vcf']
HG38_INPUT_FILES = ['input/hg38_clinvar.vcf', 'input/hg38_clinvar_papu.vcf']


class WriteToCsv:

    def write(self, prop: str, value: str) -> None:
        global CURRENT_ROW
        try:
            CURRENT_ROW[prop] = value
        except:
            logging.error(f"Prop type '{prop}' is not available")

    def write_to_file(self, files):
        global CURRENT_ROW
        global CLINVAR_FILE_WRITER, CLINVAR_CONFLICTING_FILE_WRITER, CLINVAR_OBS_FILE_WRITER, CLINVAR_POS_FILE_WRITER

        for ft in files:
            if ft == 'clinvar_obs':
                curr_row = {
                    v: CURRENT_ROW[v] for v in CLINVAR_OBS_OUTPUT_DICT.keys()
                }

                CLINVAR_OBS_FILE_WRITER.writerow(curr_row)

            elif ft == 'clinvar_conflicting':
                curr_row = {
                    v: CURRENT_ROW[v]
                    for v in CLINVAR_CONFLICTING_OUTPUT_DICT.keys()
                }
                CLINVAR_CONFLICTING_FILE_WRITER.writerow(curr_row)

            elif ft == 'clinvar':
                curr_row = {
                    v: CURRENT_ROW[v] for v in CLINVAR_OUTPUT_DICT.keys()
                }
                CLINVAR_FILE_WRITER.writerow(curr_row)

            elif ft == 'clinvar_pos_only':
                curr_row = {
                    v: CURRENT_ROW[v] for v in CLINVAR_POS_OUTPUT_DICT.keys()
                }
                CLINVAR_POS_FILE_WRITER.writerow(curr_row)

    def close(self) -> None:
        global CURRENT_ROW
        CURRENT_ROW = None


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


def addToDict(dictionary, key, value):
    '''
    Add value to a dictionary if the value is not empty.
    @dictionary dict to which to add the key, value pair
    @key        key to which to associate the value
    @value      value to be associated with the key
    @return     updated dictionary
    '''
    if len(value) > 0:
        dictionary[key] = value
    return (dictionary)


def writeEntry(prop, value, f, quotes):
    '''
    If the data is not missing write the property to the provided file.

    @prop     string of the property to write to the file
    @value    string of the value to write to the file
    @f        file to which to write the property in .mcf format
    @quotes   boolean specifying if quotes need to be added around the data
              entry for a string
  '''
    if value is None:
        return ()
    if len(value) > 0 and quotes:
        # f.write(prop, f'"{value}"')
        f.write(prop, value)
    elif len(value) > 0:
        f.write(prop, value)
    return


def writeEntry2(prop, dictionary, key, f, quotes):
    '''
    If the data is not missing write the property to the provided file.

    @prop          string of the property to write to the file
    @dictionary    dictionary potentially containing the value of interest
    @key           string that's the key to the value of interest
    @f             file to which to write the property in .mcf format
    @quotes        boolean specifying if quotes need to be added around the data
                   entry for a string
    '''
    if key not in dictionary:
        return
    if len(dictionary[key]) > 0 and quotes:
        #f.write(prop + ': "' + dictionary[key] + '"\n')
        # f.write(prop, f'"{dictionary[key]}"')
        f.write(prop, dictionary[key])
    elif len(dictionary[key]) > 0:
        # f.write(prop + ': ' + dictionary[key] + '\n')
        f.write(prop, dictionary[key])
    return


def write_sequence_ontology(prop, dictionary, key, f):
    '''
    If the data is not missing, convert the provided data to a dcid link
    and write it to the provided file.

    @prop          string of the property to write to the file
    @dictionary    dictionary potentially containing the value of interest
    @key           string that's the key to the value of interest
    @f             file to which to write the property in .mcf format
    '''
    if key not in dictionary:
        return
    value = dictionary[key]
    if len(value) > 0:
        value = value.replace(':', '_')
        value = 'bio/' + value
        #f.write(prop + ': ' + value + '\n')
        f.write(prop, value)
    return


def writeClinicalDiseases(dictionary, key, w):
    df_property_names = {
        'MedGen': 'umlsConceptUniqueID',
        'Orphanet': 'orphaNumber',
        'OMIM': 'omimID',
        'SNOMED_CT': 'snomedCT',
        'MeSH': 'medicalSubjectHeadingID',
        'Gene': 'ncbiGeneID',
        'EFO': 'experimentalFactorOntologyID',
        'MONDO': 'mondoID'
    }
    if key not in dictionary:
        return ()
    entries = dictionary[key].replace('|', ',').split(',')
    for e in entries:
        if e.startswith('Human_Phenotype_Ontology'):
            writeEntry('humanPhenotypeOntologyID', e[25:], w, True)
        else:
            if e == '.':
                continue
            if e.startswith('MONDO:'):
                items = e.split(':')
                db_prop = df_property_names[items[0]]
                value = (':').join(items[1:])
                writeEntry(db_prop, value, w, True)

            else:
                try:
                    db, value = e.split(':')
                    db_prop = df_property_names[db]
                    if db_prop == 'medicalSubjectHeadingID':
                        value = 'bio/' + value
                        writeEntry(db_prop, value, w, False)
                    else:
                        writeEntry(db_prop, value, w, True)
                except:
                    logging.error(f"Error in {e}")
        return


def write_clin_sig_category(dictionary, key, prop, file):
    if key not in dictionary:
        return
    value = dictionary[key]
    enum = None
    if value == 'no_classification_for_the_single_variant' or value == 'Uncertain_significance':
        enum = 'dcs:ClinicalSignificanceTierThree'
    elif value == 'Oncogenic':
        enum = 'dcs:ClinicalSignificanceTierOne'
    else:
        try:
            if '_-_' in value:
                category = value.split('_-_')[0]
                enum = DICT_CLIN_SIG_CATEGORY[category]
        except:
            logging.error(
                f"{category} not available in Clinical Significance Tier")
            return
    if enum:
        writeEntry(prop, enum, file, False)
    return


def write_review_status(dictionary, key, prop, file):
    if key not in dictionary:
        return
    values = dictionary[key].split(',')
    for value in values:
        if value in DICT_REVIEW_STATUS.keys():
            enum = DICT_REVIEW_STATUS[value]
            writeEntry(prop, enum, file, False)
        else:
            logging.info(f'Review Status Error: {value}')
    return


def writeClinSig(dictionary, key, file):
    # assign the clin significance to a
    if key not in dictionary:
        return ()
    value = dictionary[key]
    if value == 'Other' or value == 'other':
        writeEntry('clinicalSignificance', 'dcs:ClinSigOther', file, False)
        return ()
    if value == 'Affects':
        writeEntry('clinicalSignificance', 'dcs:ClinSigAffects', file, False)
        return ()
    if value == 'Uncertain_significance':
        writeEntry('clinicalSignificance', 'dcs:ClinSigUncertain', file, False)
        return ()
    if value == 'Pathogenic':
        writeEntry('clinicalSignificance', 'dcs:ClinSigPathogenic', file, False)
        return ()
    if value == 'Risk_factor' or value == 'Pathogenic,_risk_factor' or value == 'risk_factor':
        writeEntry('clinicalSignificance', 'dcs:ClinSigRiskFactor', file, False)
        return ()
    if value == 'Benign':
        writeEntry('clinicalSignificance', 'dcs:ClinSigBenign', file, False)
        return ()
    if value == 'Conflicting_interpretations_of_pathogenicity' or 'Conflicting_interpretations_of_pathogenicity,_risk_factor':
        writeEntry('clinicalSignificance',
                   'dcs:ClinSigConflictingPathogenicity', file, False)
        return ()
    if value == 'Association':
        writeEntry('clinicalSignificance', 'dcs:ClinSigAssociation', file,
                   False)
        return ()
    if value == 'Likely_pathogenic':
        writeEntry('clinicalSignificance', 'dcs:ClinSigLikelyPathogenic', file,
                   False)
        return ()
    if value == 'Protective' or value == 'protective':
        writeEntry('clinicalSignificance', 'dcs:ClinSigProtective', file, False)
        return ()
    if value == 'Likely_benign':
        writeEntry('clinicalSignificance', 'dcs:ClinSigLikelyBenign', file,
                   False)
        return ()
    if value == 'Not_provided' or value == 'not_provided':
        writeEntry('clinicalSignificance', 'dcs:ClinSigNotProvided', file,
                   False)
        return ()
    if value == 'Association_not_found':
        writeEntry('clinicalSignificance', 'dcs:ClinSigAssociationNotFound',
                   file, False)
        return ()
    if value == 'Drug_response':
        writeEntry('clinicalSignificance', 'dcs:ClinSigDrugResponse', file,
                   False)
        return ()
    if value == 'Pathogenic/Likely_pathogenic':
        writeEntry('clinicalSignificance',
                   'dcs:ClinSigPathogenicLikelyPathogenic', file, False)
        return ()
    if value == 'Benign/Likely_benign' or value == 'Benign/Likely_benign,_other':
        writeEntry('clinicalSignificance', 'dcs:ClinSigBenignLikelyBenign',
                   file, False)
        return ()
    logging.info(f'Clinical Significance Error: {value}')
    return


def convertToClassEnum(dictionary, key):
    if key not in dictionary:
        return ()
    c = dictionary[key]
    if c == 'single' or c == 'single_nucleotide_variant':
        return ('dcs:GeneticVariantClassSingle')
    if c == 'deletion' or c == 'Deletion':
        return ('dcs:GeneticVariantClassDeletion')
    if c == 'insertion' or c == 'Insertion':
        return ('dcs:GeneticVariantClassInsertion')
    if c == 'in-del' or c == 'Indel':
        return ('dcs:GeneticVariantClassIn-del')
    if c == 'named':
        return ('dcs:GeneticVariantClassNamed')
    if c == 'mixed':
        return ('dcs:GeneticVariantClassMixed')
    if c == 'mnp':
        return ('dcs:GeneticVariantClassMNP')
    if c == 'microsatellite' or c == 'Microsatellite':
        return ('dcs:GeneticVariantClassMicrosatellite')
    if c == 'het':
        return ('dcs:SNPClassHet')
    if c == 'Duplication':
        return ('dcs:GeneticVariantClassDuplication')
    if c == 'Inversion':
        return ('dcs:GeneticVariantClassInversion')
    if c == 'Variation':
        return ('dcs:GeneticVariantClassVariation')
    if c == 'copy_number_loss':
        return ('dcs:GeneticVariantCopyNumberLoss')
    if c == 'copy_number_gain':
        return ('dcs:GeneticVariantCopyNumberGain')
    logging.error(f'Class Error: {c}')
    return


def writeGeneInfo(dictionary, key, file):
    if key not in dictionary:
        return ()
    genes = dictionary[key].split('|')
    geneIDs = []
    geneSymbols = []
    ncbiGeneIDs = []
    for g in genes:
        try:
            geneSymbol, ncbiGeneID = g.split(':', maxsplit=1)
            geneIDs.append('bio/' + geneSymbol.replace("@", "_Cluster"))
            geneSymbols.append(geneSymbol)
            ncbiGeneIDs.append(ncbiGeneID)
        except:
            logging.error(f"Error in writeGeneInfo {g}")

    writeEntry('geneID', ','.join(geneIDs), file, False)
    writeEntry('geneSymbol', ','.join(geneSymbols), file, False)
    writeEntry('ncbiGeneID', ','.join(ncbiGeneIDs), file, False)
    return


def convertToFunctionalCategoryEnum(category):
    if category == None or len(category) <= 0:
        return ()
    if category == 'coding-synon' or category == 'synonymous_variant':
        return ('dcs:GeneticVariantFunctionalCategoryCodingSynon')
    if category == 'splice-5' or 'splice_donor_variant':
        return ('dcs:GeneticVariantFunctionalCategorySplice5')
    if category == 'missense' or category == 'missense_variant':
        return ('dcs:GeneticVariantFunctionalCategoryMissense')
    if category == 'frameshift' or category == 'frameshift_variant':
        return ('dcs:GeneticVariantFunctionalCategoryFrameshift')
    if category == 'near-gene-5':
        return ('dcs:GeneticVariantFunctionalCategoryNearGene5')
    if category == 'untranslated-3':
        return ('dcs:GeneticVariantFunctionalCategoryUTR3')
    if category == 'near-gene-3':
        return ('dcs:GeneticVariantFunctionalCategoryNearGene3')
    if category == 'nonsense':
        return ('dcs:GeneticVariantFunctionalCategoryNonsense')
    if category == 'splice-3':
        return ('dcs:GeneticVariantFunctionalCategorySplice3')
    if category == 'intron' or category == 'intron_variant':
        return ('dcs:GeneticVariantFunctionalCategoryIntron')
    if category == 'cds-reference':
        return ('dcs:GeneticVariantFunctionalCategoryCDSReference')
    if category == 'untranslated-5' or category == '5_prime_UTR_variant':
        return ('dcs:GeneticVariantFunctionalCategoryUTR5')
    if category == 'unknown':
        return ('dcs:GeneticVariantFunctionalCategoryUnknown')
    if category == 'stop-loss':
        return ('dcs:GeneticVariantFunctionalCategoryStopLoss')
    if category == 'cds-indel':
        return ('dcs:GeneticVariantFunctionalCategoryCDSIndel')
    if category == 'ncRNA':
        return ('dcs:GeneticVariantFunctionalCategoryncRNA')
    logging.error(f"Category Error: {category}")
    return


def writeSeqOntologyFunctionalType(dictionary, key, file):
    if key not in dictionary:
        return ()
    pairs = dictionary[key].split(',')
    sequenceOntologyID_mcs = []
    geneticVariantFunctionalCategories = set()
    for entry in pairs:
        try:
            seqOntology, funcType = entry.split('|')
            seqOntology = 'bio/' + seqOntology.replace(':', '_')
            # writeEntry('sequenceOntologyID', seqOntology, file, False)
            sequenceOntologyID_mcs.append(seqOntology)
            geneticVariantFunctionalCategories.add(
                convertToFunctionalCategoryEnum(funcType))
        except:
            logging.error(f"Error in writeSeqOntologyFunctionalType {entry}")

    # file.write('sequenceOntologyID_mc', f'"{seqOntology}"')
    file.write('sequenceOntologyID_mc', seqOntology)

    file.write('geneticVariantFunctionalCategory',
               ",".join(geneticVariantFunctionalCategories))
    return


def writeOrigin(dictionary, key, file):
    if key not in dictionary:
        return ()
    value = int(dictionary[key])
    original = copy.deepcopy(value)
    if value == 1073741824:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginOther', file, False)
        return ()
    if value == 0:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginUnspecified', file,
                   False)
        return ()
    if value >= 1024:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginOther', file, False)
        value -= 1024
    if value >= 512:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginTestedInconclusive',
                   file, False)
        value -= 512
    if value >= 256:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginNotTested', file,
                   False)
        value -= 256
    if value >= 128:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginUniParental', file,
                   False)
        value -= 128
    if value >= 64:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginBiParental', file,
                   False)
        value -= 64
    if value >= 32:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginDeNovo', file, False)
        value -= 32
    if value >= 16:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginMaternal', file,
                   False)
        value -= 16
    if value >= 8:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginPaternal', file,
                   False)
        value -= 8
    if value >= 4:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginInherited', file,
                   False)
        value -= 4
    if value >= 2:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginSomatic', file,
                   False)
        value -= 2
    if value >= 1:
        writeEntry('alleleOrigin', 'dcs:VariantAlleleOriginGermline', file,
                   False)
        value -= 1
    if value > 0:
        logging.error(
            f'Allele Origin Error: - value {value} - original {original}')
    return


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


def writeSubPopNode(dcid, allele, w, prop_type, files, rsID):

    dc = dcid + '_Allele_' + generate_short_id(allele)
    # “Population Frequency: <rsID> Allele <allele>”.
    name = f'Population Frequency: {rsID} Allele {allele}'
    w.write('dcid', dc)
    if prop_type == 'ref':
        w.write('ref_allele_sv_dcid', dc)
        w.write('referenceAllele', allele)
        w.write('ref_allele_sv_name', name)
    elif prop_type == 'alt':
        w.write('alt_allele_sv_dcid', dc)
        w.write('alternativeAllele', allele)
        w.write('alt_allele_sv_name', name)
    else:
        return None
    w.write_to_file(files, prop_type)

    return (dc)


def writeAlleleFreq(dictionary, alleles, w, dcid, rsID):
    # Columns to add
    # dcid_freq, name_freq, alleleFrequency, measuredPopulation, rsID
    freq_entries = [
        key for key in dictionary if key in ['AF_ESP', 'AF_EXAC', 'AF_TGP']
    ]
    if freq_entries:
        ref, alt = alleles
        for key1 in freq_entries:
            freq = dictionary[key1]
            w.write('dcid_freq', f"{dcid}_{key1}")
            w.write('name_freq', f"{rsID} {key1}")
            w.write('alleleFrequency',
                    f"{ref}: {str(1 - float(freq))}, {alt}: {freq}")
            w.write('measuredPopulation', MEASURED_POPULATION_DICT[key1])
            w.write_to_file(['clinvar_obs'])

    return


def write_id_to_file(db, identifier, w):
    # do not include id before ':'
    dict_value_only = {
        'ClinGen': 'canonicalAlleleID',
        'COSMIC':
            'catalogueOfSomaticMutationsInCancerID',  # need to add prefix COSM to vale
        'Genetic_Testing_Registry_(GTR)': 'geneticTestingRegistryID',
        'MSeqDR': 'mitochondrialDiseaseSequenceDataResourceID',
        'PharmGKB_Clinical_Annotation': 'pharmgkbClinicalAnnotationID'
    }
    # include full value as is including db before ':'
    dict_db_value = {
        'HBVAR': 'hbVarID',
        'OMIM': 'omimID',
        'UniProtKB': 'uniProtID',
        'UniProtKB/Swiss-Prot': 'uniProtKBSwissProtID'
    }
    # databases no longer maintained - ignore
    list_ignore = ['dbRBC', 'RettBASE_(CDKL5)']
    # map to property leidenOpenVariationDatabaseID
    # do not include id before ':'
    list_lovd = [
        'LOVD', 'Leiden_Muscular_Dystrophy', 'Tuberous_sclerosis_database',
        'BRCA1-HCI', 'Breast_Cancer_Information_Core_(BIC)', 'COL7A1_database',
        'GUCY2C_database'
    ]
    key = db
    if key in list_ignore:
        pass
    elif any(name in db for name in list_lovd):
        db = 'leidenOpenVariationDatabaseID'
    elif key in dict_db_value.keys():
        db = dict_db_value[key]
        identifier = db + ':' + identifier
    elif key in dict_value_only.keys():
        db = dict_value_only[key]
        if key == 'COSMIC':
            identifier = 'COSM' + identifier
    else:
        logging.error(
            'Clinical Identifier Error! Missing mapping of database to property:',
            db)
    writeEntry(key, identifier, w, True)
    return


def write_variant_database_ids(dictionary, key, w):
    # split list of db:id pairs on '|'
    # write each identifier to the appropriate propery based on database source
    if key not in dictionary:
        return ()
    items = dictionary[key].split('|')
    for item in items:
        i = item.split(':')
        db = i[0]
        value = i[-1]
        write_id_to_file(db, value, w)
    return


def convertToSigObsEnum(value):
    if value == 'Benign':
        return ('GenVarClinSigReportsBenign')
    if value == 'Uncertain_significance':
        return ('GenVarClinSigReportsUncertainSignificance')
    if value == 'Likely_benign':
        return ('GenVarClinSigReportsLikelyBenign')
    if value == 'Likely_pathogenic':
        return ('GenVarClinSigReportsLikelyPathogenic')
    if value == 'Pathogenic':
        return ('GenVarClinSigReportsPathogenic')
    if 'low_penetrance' in value:
        return ('GenVarClinSigReportsLowPenetrance')
    if 'risk_allele' in value or 'risk_factor' in value:
        return ('GenVarClinSigReportsRiskFactor')
    logging.error('Clinical Significance Observation Error:' + value)
    return


def writeSigObsNode(obsDCID, sigPopDCID, name, count, w):
    global OBSERVATION_DATE

    w.write('dcid', obsDCID)
    w.write('obs_dcid', obsDCID)
    w.write('count', count)
    w.write('measurementMethod', convertToSigObsEnum(name))
    w.write('date', OBSERVATION_DATE)
    w.write_to_file(['clinvar_conflicting'])
    return


def handle_missing_count(item, ref, alt, dcid, sigPopDCID, w):
    try:
        if ' ' in item:
            list_item = item.split(' ')
            name, count = list_item[0], list_item[1]
        else:
            name = item
            count = '1'
        obsDCID = dcid + '_' + generate_short_id(
            ref + '/' + alt) + '_SigObs_' + name + '_ClinVar'
        writeSigObsNode(obsDCID, sigPopDCID, name, count, w)
    except:
        logging.error(f"Error in handle_missing_count {item}")
    return


def parse_clinical_obs(item, ref, alt, dcid, sigPopDCID, w):
    if '|' in item:
        list_item = item.split('|')
        for i in list_item:
            if ('(') in i:
                try:
                    name, count = i.split('(')
                    count = count.strip(')')
                    obsDCID = dcid + '_' + generate_short_id(
                        ref + '/' + alt) + '_SigObs_' + name + '_ClinVar'
                    writeSigObsNode(obsDCID, sigPopDCID, name, count, w)
                except:
                    logging.error(f"Error in parse_clinical_obs {i}")
            else:
                handle_missing_count(i, ref, alt, dcid, sigPopDCID, w)
    else:
        handle_missing_count(item, ref, alt, dcid, sigPopDCID, w)
    return


def writeClincalConflicting(dcid, ref, alt, dictionary, key, w, rsID):
    if key not in dictionary:
        return ()
    sigTypes = dictionary[key].split('|')
    # Columns to add
    # dcid_conflicting, name_conflicting, alternativeAllele, clinicalSignificance, count

    # sigPopDCID = writeSubPopNode(dcid, alt, w, 'alt', ['clinvar_conflicting'],
    #                              rsID)
    for value in sigTypes:
        if ('(') in value:
            clinicalSignificance, count = value.split('(')
            count = count.strip(')')
            w.write('dcid', dcid)
            clinical_dcid = re.sub('\W+', '', clinicalSignificance).title()
            w.write('dcid_conflicting', f"{dcid}_{clinical_dcid}")
            w.write('name_conflicting',
                    f"{str(dcid).replace('bio/', '')} {clinical_dcid}")
            w.write('alternativeAllele', alt)
            w.write('clinicalSignificance', clinical_dcid)
            w.write('count', count)
            w.write_to_file(['clinvar_conflicting'])
    return


def write_disease_name(dictionary, key, f):
    if key not in dictionary:
        return
    if len(dictionary[key]) > 0:
        things = dictionary[key].split('|')
        for item in things:
            if item == 'not_specified' or item == 'not_provided':
                continue
            item = item.replace("_", " ").strip()
            if item.endswith('Efficacy'):
                item = item.split(' response')[0]
                if ',' not in item:
                    item = f'"{item}"'
                f.write('associatedDrugResponseEfficacy', item)

            else:
                if ',' not in item:
                    item = f'"{item}"'
                f.write('associatedDrugResponseEfficacy', item)

    return


def writeNode(line, w):
    try:
        w, dict_info, dcid, rsID, _ = parse_clinvar_row(line, w, None)

        # clinvar_obs
        writeAlleleFreq(dict_info, [line[3], line[4]], w, dcid, rsID)
        # clinvar_conflicting
        writeClincalConflicting(dcid, line[3], line[4], dict_info, 'CLNSIGCONF',
                                w, rsID)

        w.write_to_file(['clinvar'])
        w.close()

    except Exception as e:
        logging.error(f"Error in line {line} - with exception {e}")
        sys.exit(0)


def parse_clinvar_row(line, w, curr_row=None):
    global CURRENT_ROW
    if curr_row:
        CURRENT_ROW = copy.deepcopy(curr_row)

    l = line[7].split(';')
    rsID = None
    dict_info = {}

    dcid = 'bio/VariationID_' + line[2]
    for item in l:
        entry = item.split('=')
        dict_info[entry[0]] = entry[1]
    if 'RS' in dict_info:
        rsID = dict_info['RS']
        dcid = f"bio/rs{rsID}"
        w.write('dcid', dcid)
        w.write('name', f'rs{rsID}')
        w.write('rsID', f'rs{rsID}')

    elif line[2].isdigit():
        w.write('dcid', dcid)
        w.write('name', line[2])
    else:
        logging.info(line)
        return None
    w.write('dcid_pos', f"bio/{ASSEMBLY_HG38}_chr{line[0]}_{line[1]}")
    w.write('name_pos', f"{ASSEMBLY_HG38} chr{line[0]} {line[1]}")
    w.write('chrom', f'chr{line[0]}')
    w.write('position', line[1])
    w.write('referenceAllele', line[3])
    w.write('alternativeAllele', line[4])
    w.write('hg19GenomicPosition', line[1])

    writeEntry2('clinVarAlleleID', dict_info, 'ALLELEID', w, True)

    writeClinicalDiseases(dict_info, 'CLNDISDB', w)
    writeClinicalDiseases(dict_info, 'CLNDISDBINCL', w)
    writeClinicalDiseases(dict_info, 'ONCDISDB', w)
    writeClinicalDiseases(dict_info, 'SCIDISDB', w)

    write_disease_name(dict_info, 'CLNDN', w)
    write_disease_name(dict_info, 'CLNDNINCL', w)
    write_disease_name(dict_info, 'ONCDN', w)
    write_disease_name(dict_info, 'SCIDN', w)
    writeEntry2('hgvsNomenclature', dict_info, 'CLNHGVS', w, True)

    write_review_status(dict_info, 'CLNREVSTAT', 'clinVarGermlineReviewStatus',
                        w)
    writeClinSig(dict_info, 'CLNSIG', w)
    writeClinSig(dict_info, 'CLNSIGINCL', w)

    writeEntry('geneticVariantClass', convertToClassEnum(dict_info, 'CLNVC'), w,
               False)
    write_variant_database_ids(dict_info, 'CLNVI', w)
    write_sequence_ontology('sequenceOntologyID', dict_info, 'CLNVCSO', w)
    writeGeneInfo(dict_info, 'GENEINFO', w)
    writeSeqOntologyFunctionalType(dict_info, 'MC', w)

    writeOrigin(dict_info, 'ORIGIN', w)

    writeEntry2('dbVarID', dict_info, 'DBVARID', w, True)

    write_clin_sig_category(dict_info, 'ONC',
                            'clinicalSignificanceCategory_onc', w)

    write_review_status(dict_info, 'ONCREVSTAT',
                        'clinVarOncogenicityReviewStatus', w)

    write_clin_sig_category(dict_info, 'SCI',
                            'clinicalSignificanceCategory_sic', w)

    write_review_status(dict_info, 'SCIREVSTAT', 'clinVarSomaticReviewStatus',
                        w)
    #print("line", '\n', line, '\n', "CURRENT_ROW", CURRENT_ROW)

    return w, dict_info, dcid, rsID, CURRENT_ROW


def writeNode_POS(line, count, ASSEMBLY_HG19, start_time):
    w = WriteToCsv()
    parse_clinvar_pos_row(line, w, None)
    # print("POSline", line, '\n', CURRENT_ROW)
    #w.write('\n')
    w.write_to_file(['clinvar_pos_only'])
    w.close()
    count += 1
    if count % 100000 == 0:  # start writing to new output file
        time_running = time.time() - start_time
        logging.info(f"{count} lines processed: {time_running:.2f} second")
    return (count)


def parse_clinvar_pos_row(line, w, curr_row=None):
    global CURRENT_ROW
    if curr_row:
        CURRENT_ROW = copy.deepcopy(curr_row)

    l = line[7].split(';')
    dict_info = {}
    dcid = 'bio/VariationID_' + line[2]
    for item in l:
        entry = item.split('=')
        dict_info[entry[0]] = entry[1]
    if 'RS' in dict_info:
        dcid = 'bio/rs' + dict_info['RS']
        rsID = dict_info['RS']
        w.write('dcid', dcid)
        w.write('name', f'rs{rsID}')
        w.write('rsID', f'rs{rsID}')
    elif line[2].isdigit():
        w.write('dcid', dcid)
        w.write('name', f'{line[2]}')
    else:
        logging.info(line)

    w.write('dcid_pos', f'bio/{ASSEMBLY_HG19}_chr{line[0]}_{line[1]}')
    w.write('name_pos', f'"{ASSEMBLY_HG19} chr{line[0]} {line[1]}"')
    w.write('chrom', f'chr{line[0]}')
    w.write('position', line[1])
    return CURRENT_ROW


def process_clinvar_files():
    global CURRENT_ROW, OUTPUT_CLINVAR_FILE_NAME, OUTPUT_CLINVAR_CONFLICTING_FILE_NAME, OUTPUT_CLINVAR_OBS_FILE_NAME
    global CLINVAR_FILE_WRITER, CLINVAR_CONFLICTING_FILE_WRITER, CLINVAR_OBS_FILE_WRITER
    OUTPUT_CLINVAR_FILE_NAME = os.path.join(MODULE_DIR,
                                            OUTPUT_CLINVAR_FILE_NAME)
    OUTPUT_CLINVAR_CONFLICTING_FILE_NAME = os.path.join(
        MODULE_DIR, OUTPUT_CLINVAR_CONFLICTING_FILE_NAME)
    OUTPUT_CLINVAR_OBS_FILE_NAME = os.path.join(MODULE_DIR,
                                                OUTPUT_CLINVAR_OBS_FILE_NAME)
    # set start time
    start_time = time.time()
    # open all output files and save in global scope
    clinvar_file, conflicting_file, obs_file = None, None, None
    try:
        clinvar_file = open(OUTPUT_CLINVAR_FILE_NAME, 'w')
        CLINVAR_FILE_WRITER = csv.DictWriter(clinvar_file,
                                             CLINVAR_OUTPUT_DICT,
                                             quotechar='"',
                                             quoting=csv.QUOTE_MINIMAL)
        CLINVAR_FILE_WRITER.writeheader()

        conflicting_file = open(OUTPUT_CLINVAR_CONFLICTING_FILE_NAME, 'w')
        CLINVAR_CONFLICTING_FILE_WRITER = csv.DictWriter(
            conflicting_file,
            CLINVAR_CONFLICTING_OUTPUT_DICT,
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL)
        CLINVAR_CONFLICTING_FILE_WRITER.writeheader()

        obs_file = open(OUTPUT_CLINVAR_OBS_FILE_NAME, 'w')
        CLINVAR_OBS_FILE_WRITER = csv.DictWriter(obs_file,
                                                 CLINVAR_OBS_OUTPUT_DICT,
                                                 quotechar='"',
                                                 quoting=csv.QUOTE_MINIMAL)
        CLINVAR_OBS_FILE_WRITER.writeheader()

        counters = Counters()

        for file_input in HG38_INPUT_FILES:
            # write the ClinVar file into csv
            counters.add_counter('total',
                                 file_util.file_estimate_num_rows(file_input))
            with open(file_input, 'r') as r:
                logging.info(f"processing file {r.name}")
                for line in r:
                    if 'fileDate' in line:
                        date = line.split('=')
                        global OBSERVATION_DATE
                        OBSERVATION_DATE = date[1].replace('\n', '')

                    if line.startswith("#"):  # skip header lines
                        continue  # go to next header line

                    line = line.strip('\r\n').split('\t')
                    CURRENT_ROW = copy.deepcopy(CLINVAR_OUTPUT_DICT)
                    CURRENT_ROW.update(
                        copy.deepcopy(CLINVAR_CONFLICTING_OUTPUT_DICT))
                    CURRENT_ROW.update(copy.deepcopy(CLINVAR_OBS_OUTPUT_DICT))
                    w = WriteToCsv()
                    writeNode(line, w)
                    counters.add_counter('processed', 1)

    except Exception as e:
        logging.error(f"Error processing files {e}")
    finally:
        clinvar_file.close()
        conflicting_file.close()
        obs_file.close()
        logging.info(
            f'Process completed in {round((time.time() - start_time)/60,2)} mins'
        )


def process_clinvar_pos_files():
    global CURRENT_ROW, OUTPUT_CLINVAR_POS_FILE_NAME, CLINVAR_POS_FILE_WRITER
    # set start time for POS only files
    start_time = time.time()

    try:
        OUTPUT_CLINVAR_POS_FILE_NAME = os.path.join(
            MODULE_DIR, OUTPUT_CLINVAR_POS_FILE_NAME)
        pos_file = open(OUTPUT_CLINVAR_POS_FILE_NAME, 'w')
        CLINVAR_POS_FILE_WRITER = csv.DictWriter(pos_file,
                                                 CLINVAR_POS_OUTPUT_DICT,
                                                 quotechar='"',
                                                 quoting=csv.QUOTE_MINIMAL)
        CLINVAR_POS_FILE_WRITER.writeheader()

        count = 0
        for file_input in HG19_INPUT_FILES:
            with open(file_input, 'r') as r:
                logging.info(f"processing file {r.name}")

                for line in r:
                    if line.startswith("#"):  # skip header lines
                        continue  # go to next header line
                    line = line.strip('\r\n').split('\t')
                    CURRENT_ROW = copy.deepcopy(CLINVAR_POS_OUTPUT_DICT)
                    count = writeNode_POS(line, count, ASSEMBLY_HG19,
                                          start_time)
    except Exception as e:
        logging.error(f"Error processing files {e}")

    finally:
        pos_file.close()
        logging.info(
            f'Number of GeneticVariant instances: {count} in {round((time.time() - start_time)/60,2)} mins'
        )


def main():
    # global variable for current row
    logging.info("ClinVar process started")
    process_clinvar_files()
    process_clinvar_pos_files()
    logging.info("Processing ClinVar completed")


if __name__ == "__main__":
    main()
