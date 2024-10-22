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
Date: 22-Aug-2024
Name: format_ncbi_gene
Edited By: Samantha Piekos
Date: 22-Oct-2024
Description: cleaning the NCBI Gene data.
@source data: Download Gene data from FTP location. Refer to download.sh for details
"""

# import the required packages
import sys
import os
from os import listdir
from os.path import dirname, abspath, join
import json
import csv
import re
from copy import deepcopy
from multiprocessing import Process, Manager
from time import time
from absl import app
from absl import logging
from absl import flags
from time import time

_FLAGS = flags.FLAGS

flags.DEFINE_string('root', '.',
                    'root directory where shell script is executed.')
flags.DEFINE_string('output_dir', 'output',
                    'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input',
                    'Input directory where .dmp files downloaded.')
flags.DEFINE_string(
    'mapping_file_path', 'tax_id_dcid_mapping.txt',
    'Please specify the path to the "tax_id_dcid_mapping.txt" file generated in Taxonomy. If not provided, the script will default to the current working directory.'
)

_FLAGS(sys.argv)

SOURCE_FILE_PATH = None
OUTPUT_FILE_PATH = None
TAX_ID_DCID_MAPPING_PATH = None

TAX_ID_DCID_MAPPING = {}
GENE_ID_DCID_MAPPING = {}

GENE_INFO_DICT = {
    'taxID': '',
    'GeneID': '',
    'dcid': '',
    'Symbol': '',
    'synonym': '',
    'chromosome': '',
    'map_location': '',
    'description': '',
    'type_of_gene': '',
    'Full_name_from_nomenclature_authority': '',
    'Nomenclature_status': '',
    'Other_designations': '',
    'Modification_date': '',
    'regulatory': '',
    'misc_feature': '',
    'misc_recomb': ''
}

GENE_INFO_DB_DICT = {
    'GeneID': '',
    'Araport': '',
    'TAIR': '',
    'AllianceGenome': '',
    'AnimalQTLdb': '',
    'APHIDBASE': '',
    'ASAP': '',
    'BEETLEBASE': '',
    'BGD': '',
    'CGNC': '',
    'dictyBase': '',
    'ECOCYC': '',
    'EchinoBase': '',
    'Ensembl': '',
    'FLYBASE': '',
    'HGNC': '',
    'IMGT/GENEDB': '',
    'InterPro': '',
    'miRBase': '',
    'MGI': '',
    'EnsemblRapid': '',
    'MIM': '',
    'Phytozome': '',
    'PFAM': '',
    'PseudoCap': '',
    'RGD': '',
    'SGD': '',
    'AmoebaDB': '',
    'ApiDB_CryptoDB': '',
    'CryptoDB': '',
    'FungiDB': '',
    'GiardiaDB': '',
    'MicrosporidiaDB': '',
    'NASONIABASE': '',
    'PlasmoDB': '',
    'PiroplasmaDB': '',
    'PomBase': '',
    'ToxoDB': '',
    'TrichDB': '',
    'TriTrypDB': '',
    'VectorBase': '',
    'VEuPathDB': '',
    'Xenbase': '',
    'VGNC': '',
    'WormBase': '',
    'ZFIN': '',
}

GENE_PubMedID_DICT = {'GeneID': '', 'PubMed_ID': ''}
GENE_orthology_DICT = {'GeneID': '', 'ortholog': ''}
GENE_group_DICT = {
    'GeneID': '',
    'Other_GeneID': '',
    'PotentialReadthroughSibling': '',
    'ReadthroughChild': '',
    'ReadthroughParent': '',
    'ReadthroughSibling': '',
    'RegionMember': '',
    'RegionParent': '',
    'RelatedFunctionalGene': '',
    'RelatedPseudogene': ''
}

GENE_NEIGHBORS_DICT = {
    'GeneID': '',
    'dcid': '',
    'name': '',
    'genomic_accession.version': '',
    'genomic_gi': '',
    'start_position': '',
    'end_position': '',
    'orientation': '',
    'chromosome': '',
    'assembly': ''
}

GENE_MIM2GENE_DICT = {
    'GeneID': '',
    'MIM_number': '',
    'omim_dcid': '',
    'type': '',
    'Source': '',
    'MedGenCUI': '',
    'Comment': '',
    'dcid': '',
    'MedGenCUI_dcid': ''
}

GENE_GO_DICT = {
    'GeneID': '',
    'dcid': '',
    'GO_ID': '',
    'Evidence': '',
    'Qualifier': '',
    'GO_term': '',
    'PubMed': '',
    'Category': ''
}

GENE_ACCESSION_DICT = {
    'GeneID': '',
    'dcid_rna_coordinates': '',
    'name_rna_coordinates': '',
    'dcid_rna_transcript': '',
    'status': '',
    'RNA_nucleotide_accession.version': '',
    'RNA_nucleotide_gi': '',
    'protein_accession.version': '',
    'protein_gi': '',
    'genomic_nucleotide_accession.version': '',
    'genomic_nucleotide_gi': '',
    'start_position_on_the_genomic_accession': '',
    'end_position_on_the_genomic_accession': '',
    'orientation': '',
    'assembly': '',
    'mature_peptide_accession.version': '',
    'mature_peptide_gi': ''
}

GENE_ACCESSION_RNA_DICT = {
    'GeneID': '',
    'dcid_rna_transcript': '',
    'RNA_nucleotide_accession.version': '',
    'RNA_nucleotide_gi': '',
    'protein_accession.version': '',
    'protein_gi': '',
    'genomic_nucleotide_accession.version': '',
    'genomic_nucleotide_gi': ''
}

GENE_ENSEMBL_DICT = {
    'GeneID': '',
    'Ensembl_gene_identifier': '',
    'RNA_nucleotide_accession.version': '',
    'dcid_rna_transcript': '',
    'Ensembl_rna_identifier': '',
    'protein_accession.version': '',
    'Ensembl_protein_identifier': ''
}

GENE_RIFS_BASIC_DICT = {
    'GeneID': '',
    'dcid': '',
    'name': '',
    'dateModified': '',
    'GeneRifText': '',
    'pubMedId': ''
}

FEATURE_TYPE_ENTRIES = set()
UNIQUE_DBXREFS_LIST = []
UNIQUE_DBXREFS = set()

TYPE_OF_GENE = {
    'biological-region': 'dcs:TypeOfGeneBiologicalRegion',
    'ncRNA': 'dcs:TypeOfGenencRNA',
    'other': 'dcs:TypeOfGeneOther',
    'protein-coding': 'dcs:TypeOfGeneProteinCoding',
    'pseudo': 'dcs:TypeOfGenePseudo',
    'rRNA': 'dcs:TypeOfGenerRNA',
    'scRNA': 'dcs:TypeOfGenescRNA',
    'snRNA': 'dcs:TypeOfGenesnRNA',
    'snoRNA': 'dcs:TypeOfGenesnoRNA',
    'tRNA': 'dcs:TypeOfGenetRNA',
    'Unknown': 'dcs:TypeOfGeneUnknown'
}

NOMENCLATURE_STATUS = {
    'I': 'dcs:NomenclatureStatusInterim',
    'O': 'dcs:NomenclatureStatusOfficial'
}

NCBI_GENE_SCHEMA_EMUN_MCF_FILE_NAME = 'ncbi_gene_schema_enum.mcf'

NCBI_GENE_SCHEMA_EMUN_MCF_ENTRY = """# this is generated by format_ncbi_gene.py
Node: dcid:GeneFeatureTypeEnum
name: "GeneFeatureTypeEnum"
typeOf: schema:Class
subClassOf: dcs:Enumeration
description: "Features are annotated on RefSeq Functional Element NG_ records based on review of the scientific literature. Annotated features are in accord with INSDC Feature Table specifications, where some INSDC feature keys have specific feature classes, e.g., the 'misc_recomb' and 'regulatory' feature keys. In addition, RefSeq-specific controlled vocabulary terms are sometimes used to provide further feature specificity, e.g., for 'misc_feature', or 'misc_recomb' or 'regulatory' features that are not defined by a specific feature class."
descriptionUrl: "https://www.ncbi.nlm.nih.gov/refseq/functionalelements/"

Node: dcid:GeneFeatureTypeMiscellaneousEnum
name: "GeneFeatureTypeMiscellaneousEnum"
typeOf: schema:Class
subClassOf: dcs:GeneFeatureTypeEnum
description: "Used for functionally significant features that currently lack a more specific INSDC feature key. Controlled vocabularies are provided for additional feature specificity and to facilitate bulk search and retrieval."
descriptionUrl: "https://www.ncbi.nlm.nih.gov/refseq/functionalelements/"

Node: dcid:GeneFeatureTypeMiscellaneousRecombinationEnum
name: "GeneFeatureTypeMiscellaneousRecombinationEnum"
typeOf: schema:Class
subClassOf: dcs:GeneFeatureTypeEnum
description: "Used for genomic regions known to undergo recombination events."
descriptionUrl: "https://www.ncbi.nlm.nih.gov/refseq/functionalelements/"

Node: dcid:GeneFeatureTypeRegulatoryEnum
name: "GeneFeatureTypeRegulatoryEnum"
typeOf: dcs:GeneFeatureTypeEnum
subClassOf: schema:Enumeration
description: "A structured description of the classification of transcriptional, translational, replicational and chromatin structure related regulatory elements in a sequence."
descriptionUrl: "https://www.insdc.org/submitting-standards/controlled-vocabulary-regulatoryclass/"\n
"""

NCBI_GENE_SCHEMA_EMUN_MCF = 'Node: dcid:GeneFeatureType{type}{item}\nname: "{name}"\ntypeOf: dcs:GeneFeatureType{type}Enum\n\n'

GENE_EVIDENCE_DICT = {
    'EXP': 'dcs:GOTermEvidenceCodeExperimental',
    'HDA': 'dcs:GOTermEvidenceCodeHighThroughputDirectAssay',
    'HEP': 'dcs:GOTermEvidenceCodeHighThroughputExpressionAssay',
    'HGI': 'dcs:GOTermEvidenceCodeHighThroughputGeneticInteraction',
    'HMP': 'dcs:GOTermEvidenceCodeHighThroughputMutantPhenotype',
    'HTP': 'dcs:GOTermEvidenceCodeHighThroughputExperiment',
    'IBA': 'dcs:GOTermEvidenceCodeBiologicalAspectOfAncestor',
    'IC': 'dcs:GOTermEvidenceCodeInferredByCurator',
    'IDA': 'dcs:GOTermEvidenceCodeDirectAssay',
    'IEA': 'dcs:GOTermEvidenceCodeElectronicAnnotation',
    'IEP': 'dcs:GOTermEvidenceCodeExpressionPattern',
    'IGC': 'dcs:GOTermEvidenceCodeGenomicContext',
    'IGI': 'dcs:GOTermEvidenceCodeGeneticInteraction',
    'IKR': 'dcs:GOTermEvidenceCodeKeyResidues',
    'IMP': 'dcs:GOTermEvidenceCodeMutantPhenotype',
    'IPI': 'dcs:GOTermEvidenceCodePhysicalInteraction',
    'ISA': 'dcs:GOTermEvidenceCodeSequenceAlignment',
    'ISM': 'dcs:GOTermEvidenceCodeSequenceModel',
    'ISO': 'dcs:GOTermEvidenceCodeSequenceOrthology',
    'ISS': 'dcs:GOTermEvidenceCodeSequenceOrStructuralSimilarity',
    'NAS': 'dcs:GOTermEvidenceCodeNonTraceableAuthorStatement',
    'ND': 'dcs:GOTermEvidenceCodeNoBiologicalDataAvailable',
    'RCA': 'dcs:GOTermEvidenceCodeReviewedComputationalAnalysis',
    'TAS': 'dcs:GOTermEvidenceCodeTraceableAuthorStatement'
}

GENE_QUALIFIER_DICT = {
    'NOT acts_upstream_of': 'dcs:GOTermQualifierNotActsUpstreamOf',
    'NOT acts_upstream_of_or_within':
    'dcs:GOTermQualifierNotActsUpstreamOfOrWithin',
    'NOT acts_upstream_of_or_within_negative_effect':
    'dcs:GOTermQualifierNotActsUpstreamOfOrWithinNegativeEffect',
    'NOT acts_upstream_of_or_within_positive_effect':
    'dcs:GOTermQualifierNotActsUpstreamOfOrWithinPositiveEffect',
    'NOT colocalizes_with': 'dcs:GOTermQualifierNotColocalizesWith',
    'NOT contributes_to': 'dcs:GOTermQualifierNotContributesTo',
    'NOT enables': 'dcs:GOTermQualifierNotEnables',
    'NOT involved_in': 'dcs:GOTermQualifierNotInvolvedIn',
    'NOT is_active_in': 'dcs:GOTermQualifierNotIsActiveIn',
    'NOT located_in': 'dcs:GOTermQualifierNotLocatedIn',
    'NOT part_of': 'dcs:GOTermQualifierNotPartOf',
    'acts_upstream_of': 'dcs:GOTermQualifierActsUpstreamOf',
    'acts_upstream_of_negative_effect':
    'dcs:GOTermQualifierActsUpstreamOfNegativeEffect',
    'acts_upstream_of_or_within': 'dcs:GOTermQualifierActsUpstreamOfOrWithin',
    'acts_upstream_of_or_within_negative_effect':
    'dcs:GOTermQualifierActsUpstreamOfOrWithinNegativeEffect',
    'acts_upstream_of_or_within_positive_effect':
    'dcs:GOTermQualifierActsUpstreamOfOrWithinPositiveEffect',
    'acts_upstream_of_positive_effect':
    'dcs:GOTermQualifierActsUpstreamOfPositiveEffect',
    'colocalizes_with': 'dcs:GOTermQualifierColocalizesWith',
    'contributes_to': 'dcs:GOTermQualifierContributesTo',
    'enables': 'dcs:GOTermQualifierEnables',
    'involved_in': 'dcs:GOTermQualifierInvolvedIn',
    'is_active_in': 'dcs:GOTermQualifierIsActiveIn',
    'located_in': 'dcs:GOTermQualifierLocatedIn',
    'part_of': 'dcs:GOTermQualifierPartOf'
}

GENE_CATEGORY_DICT = {
    'Component': 'dcs:GeneOntologyCategoryCellularComponent',
    'Function': 'dcs:GeneOntologyCategoryMolecularFunction',
    'Process': 'dcs:GeneOntologyCategoryBiologicalProcess'
}

GENE_OMIM_SOURCE_DICT = {
    'GeneMap': 'dcs:GeneOmimRelationshipSourceGeneMap',
    'GeneReviews': 'dcs:GeneOmimRelationshipSourceGeneReviews',
    'GeneTests': 'dcs:GeneOmimRelationshipSourceGeneTests',
    'NCBI curation': 'dcs:GeneOmimRelationshipSourceNcbiCuration',
    'OMIM': 'dcs:GeneOmimRelationshipSourceOmim',
    '_': ''
}

GENE_COMMENT_DICT = {
    'nondisease': 'dcs:GeneOmimRelationshipCommentNondisease',
    'QTL 2': 'dcs:GeneOmimRelationshipCommentQtl2',
    'susceptibility': 'dcs:GeneOmimRelationshipCommentSusceptibility',
    'question': 'dcs:GeneOmimRelationshipCommentQuestion',
    'QTL 1': 'dcs:GeneOmimRelationshipCommentQTL1',
    'modifier': 'dcs:GeneOmimRelationshipCommentModifier',
    'somatic': 'dcs:GeneOmimRelationshipCommentSomatic'
}

REF_SEQ_STATUS_ENUM_DICT = {
    'INFERRED': 'dcs:RefSeqStatusInferred',
    'MODEL': 'dcs:RefSeqStatusModel',
    'NA': '',
    'PREDICTED': 'dcs:RefSeqStatusPredicted',
    'PROVISIONAL': 'dcs:RefSeqStatusProvisional',
    'REVIEWED': 'dcs:RefSeqStatusReviewed',
    'SUPPRESSED': 'dcs:RefSeqStatusSuppressed',
    'VALIDATED': 'dcs:RefSeqStatusValidated',
    'PIPELINE': 'dcs:RefSeqStatusPipeline',
    '-': '',
    '': ''
}

GENE_MIM_TYPE_DIC = {
    'gene': 'dcs:GeneOmimRelationshipTypeGene',
    'phenotype': 'dcs:GeneOmimRelationshipTypePhenotype'
}

GENE_ORIENTATION_DICT = {
    '+': 'dcs:StrandOrientationPositive',
    '-': 'dcs:StrandOrientationNegative',
    '?': '',
    '': 'dcs:StrandOrientationNegative'
}

MODULE_DIR = dirname(dirname(abspath(__file__)))

DATE_MODIFY = lambda x: str(x)[:4] + "-" + str(x)[4:6] + "-" + str(x)[-2:]
DATETIME_MODIFY = lambda x: str(x)[:4] + "-" + str(x)[5:7] + "-" + str(x)[8:10]
RE_PATTERN = r"[^a-zA-Z0-9_\- ]"


def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        #logging.info(f'Started {func.__qualname__!r}')
        t1 = time()
        #logging.info(f'Executing {func.__qualname__!r} function')
        result = func(*args, **kwargs)
        t2 = time()
        logging.info(
            f'Function {func.__qualname__!r} executed in {((t2-t1)):.2f} seconds'
        )
        return result

    return wrap_func


@timer_func
def load_tax_id_dcid_mapping() -> None:
    global TAX_ID_DCID_MAPPING, TAX_ID_DCID_MAPPING_PATH
    with open(TAX_ID_DCID_MAPPING_PATH, 'r') as csv_file:
        reader = csv.reader(csv_file)
        TAX_ID_DCID_MAPPING = {rows[0]: rows[1] for rows in reader}

    logging.info(f"No of TAX_ID loaded {len(TAX_ID_DCID_MAPPING)}")


def get_pascal_case(s: str, sep=None):
    if sep and sep in s:
        return "".join(map(lambda x: x[:1].upper() + x[1:], s.split(sep)))
    else:
        return s[:1].upper() + s[1:]


def set_flags(_FLAGS) -> None:
    global MODULE_DIR

    if _FLAGS.root != ".":
        MODULE_DIR = _FLAGS.root

    _OUTPUT_FILE_PATH = path_join(MODULE_DIR, _FLAGS.output_dir)
    if not os.path.exists(os.path.join(MODULE_DIR, _FLAGS.output_dir)):
        os.mkdir(_OUTPUT_FILE_PATH)
    _SOURCE_FILE_PATH = path_join(MODULE_DIR, _FLAGS.input_dir)
    _TAX_ID_DCID_MAPPING_PATH = path_join(MODULE_DIR, _FLAGS.mapping_file_path)
    return _OUTPUT_FILE_PATH, _SOURCE_FILE_PATH, _TAX_ID_DCID_MAPPING_PATH


def path_join(path: str, filename: str) -> str:
    """path join

    Args:
        path (str): path
        filename (str): filename

    Returns:
        str: full filename
    """
    return os.path.join(path, filename)


class GeneInfo:
    """
        Class to process gene_info.txt file
    """

    @timer_func
    def process_gene_info(self, file_to_process: str, return_dict) -> None:
        """Creates and clean GeneInfo DataFrame
        """
        logging.info(f"Processing GeneInfo file {file_to_process}")
        global TAX_ID_DCID_MAPPING  # GENE_ID_DCID_MAPPING  #,
        gene_id_dcid_mapping = {}
        feature_type_entries = set()
        unique_dbXrefs_list = []
        unique_dbXrefs = set()

        with open(
                path_join(OUTPUT_FILE_PATH + '/gene_info',
                          file_to_process.replace('txt', 'csv')),
                'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_INFO_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(
                    path_join(SOURCE_FILE_PATH + '/gene_info',
                              file_to_process), 'r') as source_file:

                # reader = csv.reader(source_file)
                for line in source_file:
                    line = line.replace('\\\\',
                                        ' ').replace('-',
                                                     '').replace('\\', ' ')
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        input_row = [
                            x for x in line.replace('\n', '').split('\t')
                        ]
                        if input_row[0] in TAX_ID_DCID_MAPPING:
                            # continue only tax_id matches with
                            row = deepcopy(GENE_INFO_DICT)
                            print(f"{file_to_process} {input_row[1]}",
                                  end='\r')
                            row['taxID'] = input_row[0]
                            row['GeneID'] = input_row[1]
                            dcid = f"bio/ncbi_{input_row[1]}" if input_row[
                                0] != '9606' else f"bio/{input_row[2]}"
                            dcid = dcid.replace("@", "_Cluster")
                            row['dcid'] = dcid
                            gene_id_dcid_mapping[input_row[1]] = dcid
                            row['Symbol'] = f'"{input_row[2]}"'
                            row['synonym'] = ','.join(
                                [f'"{x}"' for x in input_row[4].split('|')])
                            if len(input_row[5]) > 1:
                                dbs_lst = [x for x in input_row[5].split('|')]
                                db_obj = {'GeneID': f"{dcid}"}
                                for dbs in dbs_lst:
                                    db = dbs.split(':')
                                    unique_dbXrefs.add(db[0])
                                    db_obj[db[0]] = db[1]
                                unique_dbXrefs_list.append(db_obj)

                            if len(input_row[6]) > 1:
                                row['chromosome'] = ",".join([
                                    f'"chr{x}"'
                                    for x in input_row[6].split('|')
                                ])
                            row['map_location'] = ','.join(
                                [f'"{x}"' for x in input_row[7].split('|')])
                            row['description'] = f'"{re.sub(RE_PATTERN, "", input_row[8])}"'
                            try:
                                if len(input_row[11]) > 1:
                                    row['type_of_gene'] = TYPE_OF_GENE[
                                        input_row[9]]
                            except:
                                row['type_of_gene'] = 'dcs:TypeOfGeneUnknown'
                            row['Full_name_from_nomenclature_authority'] = f'"{re.sub(RE_PATTERN, "", input_row[11])}"'
                            try:
                                if len(input_row[12]) > 1:
                                    row['Nomenclature_status'] = NOMENCLATURE_STATUS[
                                        input_row[12]]
                            except:
                                logging.info(f"No match for {input_row[12]}")
                            row['Other_designations'] = ','.join(
                                [f'"{x}"' for x in input_row[13].split('|')])
                            row['Modification_date'] = DATE_MODIFY(
                                input_row[14])
                            if len(input_row[15]) > 1:
                                row['regulatory'], row['misc_feature'], row[
                                    'misc_recomb'], feature_entries = self._get_feature_type_list(
                                        input_row[15])
                                feature_type_entries.update(feature_entries)

                            writer_gene.writerow(row)

        logging.info(
            f"{file_to_process} - gene_id {len(gene_id_dcid_mapping)}  feature_type {len(feature_type_entries)} unique_dbXrefs_list {len(unique_dbXrefs_list)} unique_dbXrefs {len(unique_dbXrefs)} "
        )
        return_dict[file_to_process] = {
            'gene_id_dcid_mapping': gene_id_dcid_mapping,
            'feature_type_entries': feature_type_entries,
            'unique_dbXrefs_list': unique_dbXrefs_list,
            'unique_dbXrefs': unique_dbXrefs
        }

    @timer_func
    def save_gene_info_files(self, mcf_file_path: str):
        global FEATURE_TYPE_ENTRIES, UNIQUE_DBXREFS_LIST, UNIQUE_DBXREFS
        db_values = ['GeneID']
        db_values.extend(list(UNIQUE_DBXREFS))
        for db in db_values:
            if db not in GENE_INFO_DB_DICT.keys():
                logging.info(f"Database {db} not in gene db tmcf")

        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_gene_db.csv'),
                  'w') as file:
            writer_db = csv.DictWriter(file,
                                       GENE_INFO_DB_DICT,
                                       extrasaction='ignore',
                                       delimiter=',',
                                       doublequote=False,
                                       escapechar='\\',
                                       lineterminator='\n')
            writer_db.writeheader()
            for l in UNIQUE_DBXREFS_LIST:
                writer_db.writerow(l)

        # add feature_type emun in ncbi_gene_schema_enum.mcf
        with open(mcf_file_path, 'w') as file:
            file.write(NCBI_GENE_SCHEMA_EMUN_MCF_ENTRY)

        with open(mcf_file_path, 'a') as file:
            for feature_type in FEATURE_TYPE_ENTRIES:
                ftype = json.loads(feature_type)
                mfc_entry = NCBI_GENE_SCHEMA_EMUN_MCF.format(
                    type=ftype['type'],
                    item=ftype['entry'],
                    name=ftype['name'])
                file.write(mfc_entry)

    def _get_feature_type_list(self, value):
        feature_type_entries = set()
        first_split_val = value.split("|")
        #logging.info("first_split_val", first_split_val)
        misc_str = []
        req_str = []
        recomb_str = []
        if len(first_split_val) > 0:
            for sval in first_split_val:
                second_split_val = sval.split(":")
                str_pascal_case = get_pascal_case(second_split_val[1], '_')
                name = second_split_val[1].replace('_', ' ').title()

                if second_split_val[0] == 'regulatory':
                    req_str.append('dcs:GeneFeatureTypeRegulatory' +
                                   str_pascal_case)
                    feature_type_entries.add(
                        json.dumps(
                            {
                                "type": "Regulatory",
                                "entry": str_pascal_case,
                                "name": name
                            },
                            sort_keys=True))
                elif second_split_val[0] == 'misc_recomb':
                    recomb_str.append(
                        'dcs:GeneFeatureTypeMiscellaneousRecombination' +
                        str_pascal_case)
                    feature_type_entries.add(
                        json.dumps(
                            {
                                "type": "Miscellaneous",
                                "entry": str_pascal_case,
                                "name": name
                            },
                            sort_keys=True))
                elif second_split_val[0] == 'misc_feature':
                    req_str.append('dcs:MiscellaneousGeneFeature' +
                                   str_pascal_case)
                    feature_type_entries.add(
                        json.dumps(
                            {
                                "type": "Miscellaneous",
                                "entry": str_pascal_case,
                                "name": name
                            },
                            sort_keys=True))
                else:
                    pass

        return ",".join(misc_str), ",".join(req_str), ",".join(
            recomb_str), feature_type_entries


class GenePubmed:
    """
        Class to process gene2pubmed.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        """Creates and clean Gene2pubmed DataFrame
        """
        logging.info("Processing GenePubmed")
        global GENE_ID_DCID_MAPPING
        Gene_PubMedID = {}

        with open(path_join(SOURCE_FILE_PATH, "gene2pubmed.txt"),
                  'r') as source_file:

            for line in source_file:
                # skip row
                if line[0] == '#':
                    continue
                else:
                    input_row = line.replace('\n', '').split('\t')
                    if input_row[1] in GENE_ID_DCID_MAPPING:
                        print(f"gene2pubmed {input_row[1]}", end='\r')
                        if input_row[1] in Gene_PubMedID:
                            Gene_PubMedID[input_row[1]]['PubMedID'].append(
                                input_row[2])
                        else:
                            Gene_PubMedID[input_row[1]] = {
                                'dcid':
                                f"{GENE_ID_DCID_MAPPING[input_row[1]]}",
                                'PubMedID': [input_row[2]]
                            }
                            #Gene_PubMedID[input_row[1]].append()

        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_gene_pubmed.csv'),
                  'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_PubMedID_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()
            for l in Gene_PubMedID:
                writer_gene.writerow({
                    'GeneID':
                    Gene_PubMedID[l]['dcid'],
                    'PubMed_ID':
                    f'"{",".join(Gene_PubMedID[l]["PubMedID"])}"'
                })


class GeneNeighbors:
    """
        Class to process gene_neighbors.txt file
    """

    @timer_func
    def process_csv_file(self, file_to_process: str) -> None:
        """Creates and clean gene_neighbors DataFrame
        """
        logging.info(f"Processing GeneNeighbors {file_to_process}")
        global GENE_ID_DCID_MAPPING, GENE_ORIENTATION_DICT
        with open(
                path_join(OUTPUT_FILE_PATH + '/gene_neighbors',
                          file_to_process.replace('txt', 'csv')),
                'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_NEIGHBORS_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(
                    path_join(SOURCE_FILE_PATH + '/gene_neighbors',
                              file_to_process), 'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        input_row = line.replace('\n', '').split('\t')
                        if input_row[1] in GENE_ID_DCID_MAPPING:
                            # continue only GeneID matches with input row
                            print(f"{file_to_process} {input_row[1]}",
                                  end='\r')
                            row = deepcopy(GENE_NEIGHBORS_DICT)
                            row['GeneID'] = f"{GENE_ID_DCID_MAPPING[input_row[1]]}"
                            row['genomic_accession.version'] = input_row[2]
                            row['genomic_gi'] = input_row[3]
                            row['start_position'] = input_row[4]
                            row['end_position'] = input_row[5]
                            row['orientation'] = GENE_ORIENTATION_DICT[
                                input_row[6]]
                            row['assembly'] = f'"{input_row[13]}"'
                            # 'bio/<genomic accession.version>_<start position>_<end position>
                            row['dcid'] = f"bio/{input_row[2]}_{input_row[4]}_{input_row[5]}"
                            row['name'] = f'"{input_row[2]} {input_row[4]} {input_row[5]}"'
                            writer_gene.writerow(row)


class GeneOrthology:
    """
        Class to process gene_orthology.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        """Creates and clean gene_orthology DataFrame
        """
        logging.info("Processing GeneOrthology")
        global GENE_ID_DCID_MAPPING
        Gene_orthologs = {}

        with open(path_join(SOURCE_FILE_PATH, "gene_orthologs.txt"),
                  'r') as source_file:

            for line in source_file:
                # skip row
                if line[0] == '#':
                    continue
                else:
                    input_row = line.replace('\n', '').split('\t')
                    if input_row[1] in GENE_ID_DCID_MAPPING:
                        print(f"gene_orthologs {input_row[1]}", end='\r')
                        if input_row[1] in Gene_orthologs:
                            if input_row[4] in GENE_ID_DCID_MAPPING:
                                Gene_orthologs[input_row[1]]['ortholog'].append(
                                    f'{GENE_ID_DCID_MAPPING[input_row[4]]}'
                                )
                        else:
                            if input_row[4] in GENE_ID_DCID_MAPPING:
                                Gene_orthologs[input_row[1]] = {
                                    'dcid':
                                    f'{GENE_ID_DCID_MAPPING[input_row[1]]}',
                                    'ortholog': [
                                        f'{GENE_ID_DCID_MAPPING[input_row[4]]}'
                                    ]
                                }

        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_gene_ortholog.csv'),
                  'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_orthology_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()
            for l in Gene_orthologs:
                writer_gene.writerow({
                    'GeneID':
                    Gene_orthologs[l]['dcid'],
                    'ortholog':
                    ','.join(Gene_orthologs[l]['ortholog'])
                })


class GeneGroup:
    """
        Class to process gene_group.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        # gene_group.txt, ncbi_gene_gene_group.csv
        """Creates and clean gene_group DataFrame
        """
        logging.info("Processing GeneGroup")
        global GENE_ID_DCID_MAPPING
        Gene_group = {}

        with open(path_join(SOURCE_FILE_PATH, "gene_group.txt"),
                  'r') as source_file:

            for line in source_file:
                # skip row
                if line[0] == '#':
                    continue
                else:
                    input_row = line.replace('\n', '').split('\t')
                    column_name = get_pascal_case(input_row[2], sep=' ')
                    if input_row[1] in GENE_ID_DCID_MAPPING:
                        print(f"gene_group {input_row[1]}", end='\r')
                        if input_row[1] in Gene_group:
                            if column_name in Gene_group[input_row[1]]:
                                try:
                                    Gene_group[input_row[1]][column_name].append(
                                        f'dcid:{GENE_ID_DCID_MAPPING[input_row[4]]}'
                                    )
                                except:
                                    logging.info(
                                        f"GeneID not available {input_row[4]}")
                            else:
                                try:
                                    Gene_group[input_row[1]][column_name] = []
                                    Gene_group[input_row[1]][column_name].append(
                                        f'dcid:{GENE_ID_DCID_MAPPING[input_row[4]]}'
                                    )
                                except:
                                    logging.info(
                                        f"GeneID not available {input_row[4]}")

                        else:
                            try:
                                Gene_group[input_row[1]] = {
                                    'GeneID':
                                    f"{GENE_ID_DCID_MAPPING[input_row[1]]}",
                                    column_name: [
                                        f'dcid:{GENE_ID_DCID_MAPPING[input_row[4]]}'
                                    ]
                                }
                            except:
                                logging.info(
                                    f"GeneID not available {input_row[4]}")

        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_gene_group.csv'),
                  'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_group_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()
            for l in Gene_group:
                grp_obj = {}
                for g in Gene_group[l]:
                    if g == 'GeneID':
                        grp_obj[g] = Gene_group[l][g]
                    else:
                        grp_obj[g] = ",".join(Gene_group[l][g])
                writer_gene.writerow(grp_obj)


class GeneMim2gene:
    """
        Class to process mim2gene_medgen.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        # mim2gene_medgen.txt, ncbi_gene_gene_phenotype_association.csv
        """Creates and clean mim2gene DataFrame
        """
        logging.info("Processing GeneMim2gene")
        global GENE_ID_DCID_MAPPING, GENE_COMMENT_DICT
        with open(
                path_join(OUTPUT_FILE_PATH,
                          'ncbi_gene_gene_phenotype_association.csv'),
                'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_MIM2GENE_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(path_join(SOURCE_FILE_PATH, "mim2gene_medgen.txt"),
                      'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        input_row = line.replace('\n', '').split('\t')
                        if input_row[1] in GENE_ID_DCID_MAPPING:
                            # continue only GeneID matches with input row
                            print(f"mim2gene_medgen {input_row[1]}", end='\r')
                            row = deepcopy(GENE_MIM2GENE_DICT)
                            dcid = GENE_ID_DCID_MAPPING[input_row[1]]
                            row['GeneID'] = f"{dcid}"
                            row['MIM_number'] = input_row[0]
                            row['omim_dcid'] = f"bio/omim_{input_row[0]}"
                            row['type'] = GENE_MIM_TYPE_DIC[input_row[2]]
                            row['Source'] = ','.join([
                                f'{GENE_OMIM_SOURCE_DICT.get(x.strip(), x.strip())}'
                                for x in input_row[3].strip().split(';')
                            ])
                            if row['MedGenCUI'].startswith('C'):
                                row['MedGenCUI'] = input_row[4]
                                row['MedGenCUI_dcid'] = f"bio/{input_row[4]}"
                            cmt = []
                            for c in input_row[5].split(':'):
                                if c.strip() in GENE_COMMENT_DICT:
                                    cmt.append(
                                        f'{GENE_COMMENT_DICT[c.strip()]}')
                            if len(cmt) > 0:
                                row['Comment'] = ','.join(cmt)
                            row['dcid'] = f"{dcid}_omim_{input_row[0]}"
                            writer_gene.writerow(row)


class Gene2Go:
    """
        Class to process gene2go.txt file
    """

    @timer_func
    def process_csv_file(self, file_to_process: str) -> None:
        """Creates and clean gene2go DataFrame
        """
        # gene2go.txt, ncbi_gene_go_terms.csv ,
        logging.info(f"Processing Gene2Go {file_to_process}")
        global GENE_ID_DCID_MAPPING
        with open(
                path_join(OUTPUT_FILE_PATH + '/gene2go',
                          file_to_process.replace('txt', 'csv')),
                'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_GO_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(
                    path_join(SOURCE_FILE_PATH + '/gene2go', file_to_process),
                    'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        input_row = line.replace('\n', '').split('\t')
                        if input_row[1] in GENE_ID_DCID_MAPPING:
                            # continue only GeneID matches with input row
                            print(f"{file_to_process} {input_row[1]}",
                                  end='\r')
                            row = deepcopy(GENE_GO_DICT)
                            dcid = GENE_ID_DCID_MAPPING[input_row[1]]
                            row['GeneID'] = f"{dcid}"
                            row['GO_ID'] = input_row[2]
                            row['dcid'] = f"bio/{input_row[2].replace(':','_')}"
                            row['Evidence'] = GENE_EVIDENCE_DICT[input_row[3]]
                            row['Qualifier'] = GENE_QUALIFIER_DICT[
                                input_row[4]]
                            row['GO_term'] = f'"{input_row[5]}"'
                            row['PubMed'] = ','.join(
                                [f'"{x}"' for x in input_row[6].split('|')])
                            row['Category'] = GENE_CATEGORY_DICT[input_row[7]]
                            writer_gene.writerow(row)


class Gene2Accession:
    """
        Class to process gene2accession.txt file
    """

    @timer_func
    def process_csv_file(self, file_to_process: str) -> None:
        """Creates and clean gene2accession DataFrame
        """
        # gene2accession.txt ncbi_gene_rna_transcript.csv

        logging.info(f"Processing Gene2Accession {file_to_process}")
        global GENE_ID_DCID_MAPPING, REF_SEQ_STATUS_ENUM_DICT, GENE_ORIENTATION_DICT
        with open(path_join(OUTPUT_FILE_PATH + '/gene2accession', \
                            file_to_process.replace('txt', 'csv')), 'w') as output_gene, \
            open(path_join(OUTPUT_FILE_PATH + '/gene2accession', \
                            'rna_' + file_to_process.replace('txt', 'csv')), 'w') as output_gene_rna:

            writer_gene = csv.DictWriter(output_gene,
                                         GENE_ACCESSION_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            writer_gene_rna = csv.DictWriter(output_gene_rna,
                                             GENE_ACCESSION_RNA_DICT,
                                             extrasaction='ignore',
                                             delimiter=',',
                                             doublequote=False,
                                             escapechar='\\',
                                             lineterminator='\n')
            writer_gene_rna.writeheader()

            with open(
                    path_join(SOURCE_FILE_PATH + '/gene2accession',
                              file_to_process), 'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        # input_row = line.replace('\n', '').split('\t')
                        input_row = [
                            x.replace('-', '')
                            for x in line.replace('\n', '').split('\t')
                        ]
                        if input_row[1] in GENE_ID_DCID_MAPPING:
                            # continue only GeneID matches with input row
                            print(f"{file_to_process} {input_row[1]}",
                                  end='\r')
                            row = deepcopy(GENE_ACCESSION_DICT)

                            dcid = GENE_ID_DCID_MAPPING[input_row[1]]
                            row['GeneID'] = f"{dcid}"
                            row['dcid_rna_coordinates'] = f"bio/{input_row[3]}_{input_row[9]}_{input_row[10]}"
                            row['name_rna_coordinates'] = f"{input_row[3]} {input_row[9]} {input_row[10]}"
                            row['dcid_rna_transcript'] = f"bio/{input_row[3]}"
                            row['status'] = REF_SEQ_STATUS_ENUM_DICT[
                                input_row[2]]
                            row['RNA_nucleotide_accession.version'] = input_row[
                                3]
                            row['RNA_nucleotide_gi'] = input_row[4]
                            row['protein_accession.version'] = input_row[5]
                            row['protein_gi'] = input_row[6]
                            row['genomic_nucleotide_accession.version'] = input_row[
                                7]
                            row['genomic_nucleotide_gi'] = input_row[8]
                            row['start_position_on_the_genomic_accession'] = input_row[
                                9]
                            row['end_position_on_the_genomic_accession'] = input_row[
                                10]
                            row['orientation'] = GENE_ORIENTATION_DICT[
                                input_row[11]]
                            row['assembly'] = input_row[12]
                            row['mature_peptide_accession.version'] = input_row[
                                13]
                            row['mature_peptide_gi'] = input_row[13]

                            writer_gene.writerow(row)

                            if len(input_row[3]) > 1:
                                row_rna = deepcopy(GENE_ACCESSION_RNA_DICT)
                                row_rna[
                                    'RNA_nucleotide_accession.version'] = input_row[
                                        3]
                                row_rna[
                                    'dcid_rna_transcript'] = f"bio/{input_row[3]}"
                                row_rna['RNA_nucleotide_gi'] = input_row[4]
                                row_rna[
                                    'protein_accession.version'] = input_row[5]
                                row_rna['protein_gi'] = input_row[6]
                                row_rna[
                                    'genomic_nucleotide_accession.version'] = input_row[
                                        7]
                                row_rna['genomic_nucleotide_gi'] = input_row[8]
                                writer_gene_rna.writerow(row_rna)


class Gene2Ensembl:
    """
        Class to process gene2ensembl.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        """Creates and clean gene2go DataFrame
        """
        # gene2ensembl.txt, ncbi_gene_ensembl.csv

        logging.info("Processing Gene2Ensembl")

        global GENE_ID_DCID_MAPPING
        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_ensembl.csv'),
                  'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_ENSEMBL_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(path_join(SOURCE_FILE_PATH, "gene2ensembl.txt"),
                      'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:
                        input_row = line.replace('\n', '').split('\t')
                        if input_row[1] in GENE_ID_DCID_MAPPING and len(
                                input_row[3]) > 1:
                            # continue only GeneID matches with input row
                            print(f"gene2ensembl {input_row[1]}", end='\r')
                            row = deepcopy(GENE_ENSEMBL_DICT)
                            dcid = GENE_ID_DCID_MAPPING[input_row[1]]
                            row['GeneID'] = f"{dcid}"
                            row['Ensembl_gene_identifier'] = input_row[2]
                            if len(input_row[3]) > 0:
                                row['RNA_nucleotide_accession.version'] = input_row[
                                    3]
                                row['dcid_rna_transcript'] = f"bio/{input_row[3]}"

                            row['Ensembl_rna_identifier'] = input_row[4]
                            if input_row[5] != "-":
                                row['protein_accession.version'] = input_row[5]
                            row['Ensembl_protein_identifier'] = input_row[6]
                            writer_gene.writerow(row)


class GeneRifs_Basic:
    """
        Class to process generifs_basic.txt file
    """

    @timer_func
    def process_csv_file(self) -> None:
        """Creates and clean generifs_basic DataFrame
        """
        # generifs_basic.txt, ncbi_gene_gene_rif.csv
        logging.info("Processing GeneRifs_Basic")
        global GENE_ID_DCID_MAPPING
        with open(path_join(OUTPUT_FILE_PATH, 'ncbi_gene_gene_rif.csv'),
                  'w') as output_gene:
            writer_gene = csv.DictWriter(output_gene,
                                         GENE_RIFS_BASIC_DICT,
                                         extrasaction='ignore',
                                         delimiter=',',
                                         doublequote=False,
                                         escapechar='\\',
                                         lineterminator='\n')
            writer_gene.writeheader()

            with open(path_join(SOURCE_FILE_PATH, "generifs_basic.txt"),
                      'r') as source_file:

                for line in source_file:
                    # skip row
                    if line[0] == '#':
                        continue
                    else:

                        input_row = line.replace('\n', '').split('\t')
                        if input_row[1] in GENE_ID_DCID_MAPPING:
                            # continue only GeneID matches with input row
                            print(f"generifs_basic {input_row[1]}", end='\r')

                            # Explode the comma-separated list in index position 2
                            pub_med_ids = input_row[2].split(',')
                            for pub_med_id in pub_med_ids:
                                row = deepcopy(GENE_RIFS_BASIC_DICT)
                                dcid = GENE_ID_DCID_MAPPING[input_row[1]]
                                row['GeneID'] = f"{dcid}"
                                # Use the individual pub_med_id here
                                row['dcid'] = f"{dcid}_{pub_med_id}"
                                row['name'] = f'"{dcid.replace("bio/", "").replace("_", " ")} PubMed {pub_med_id} Reference Into Function"'
                                row['dateModified'] = DATETIME_MODIFY(input_row[3])
                                # Escape quotes in GeneRifText
                                rif_text = input_row[4].replace('"', '""')
                                row['GeneRifText'] = f'"{rif_text}"'
                                row['pubMedId'] = pub_med_id  # Use the individual pub_med_id here
                                writer_gene.writerow(row)


def main(_):
    """Main method
    """
    start_time = time()
    logging.info("Start format gene first script")
    global OUTPUT_FILE_PATH, SOURCE_FILE_PATH, TAX_ID_DCID_MAPPING_PATH, GENE_ID_DCID_MAPPING
    global FEATURE_TYPE_ENTRIES, UNIQUE_DBXREFS_LIST, UNIQUE_DBXREFS
    OUTPUT_FILE_PATH, SOURCE_FILE_PATH, TAX_ID_DCID_MAPPING_PATH = set_flags(
        _FLAGS)
    load_tax_id_dcid_mapping()
    manager = Manager()
    return_dict = manager.dict()
    procs_info = []
    gene_info_shard_files = [
        f for f in listdir(join(SOURCE_FILE_PATH, 'gene_info'))
    ]
    for info_file in gene_info_shard_files:
        info_proc = Process(target=GeneInfo().process_gene_info,
                            args=(
                                info_file,
                                return_dict,
                            ))
        procs_info.append(info_proc)
        info_proc.start()

    for p in procs_info:
        p.join()
    logging.info("All gene info files processed")
    for res in return_dict:
        logging.info(f"Saving {res} result to global variable")
        GENE_ID_DCID_MAPPING.update(return_dict[res]['gene_id_dcid_mapping'])
        FEATURE_TYPE_ENTRIES.update(return_dict[res]['feature_type_entries'])
        UNIQUE_DBXREFS_LIST.extend(return_dict[res]['unique_dbXrefs_list'])
        UNIQUE_DBXREFS.update(return_dict[res]['unique_dbXrefs'])

    # Save Gene Info database & MCF files
    GeneInfo().save_gene_info_files(
        path_join(OUTPUT_FILE_PATH, NCBI_GENE_SCHEMA_EMUN_MCF_FILE_NAME))

    procs = []
    procPub = Process(target=GenePubmed().process_csv_file)
    procs.append(procPub)
    procOrth = Process(target=GeneOrthology().process_csv_file)
    procs.append(procOrth)
    procGrp = Process(target=GeneGroup().process_csv_file)
    procs.append(procGrp)
    procMim = Process(target=GeneMim2gene().process_csv_file)
    procs.append(procMim)
    procEns = Process(target=Gene2Ensembl().process_csv_file)
    procs.append(procEns)
    procRif = Process(target=GeneRifs_Basic().process_csv_file)
    procs.append(procRif)
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()

    procs_Neighbors = []
    gene_Neighbors_shard_files = [
        f for f in listdir(join(SOURCE_FILE_PATH, 'gene_neighbors'))
    ]
    for neighbors_file in gene_Neighbors_shard_files:
        neighbors_proc = Process(target=GeneNeighbors().process_csv_file,
                                 args=(neighbors_file, ))
        procs_Neighbors.append(neighbors_proc)
        neighbors_proc.start()

    for p in procs_Neighbors:
        p.join()
    logging.info("All gene neighbors files processed")

    procs_Go = []
    gene_Go_shard_files = [
        f for f in listdir(join(SOURCE_FILE_PATH, 'gene2go'))
    ]
    for go_file in gene_Go_shard_files:
        go_proc = Process(target=Gene2Go().process_csv_file, args=(go_file, ))
        procs_Go.append(go_proc)
        go_proc.start()

    for p in procs_Go:
        p.join()
    logging.info("All gene2go files processed")

    procs_Accession = []
    gene_Accession_shard_files = [
        f for f in listdir(join(SOURCE_FILE_PATH, 'gene2accession'))
    ]
    for accession_file in gene_Accession_shard_files:
        accession_proc = Process(target=Gene2Accession().process_csv_file,
                                 args=(accession_file, ))
        procs_Accession.append(accession_proc)
        accession_proc.start()

    for p in procs_Accession:
        p.join()

    logging.info("All gene2accession files processed")

    # GenePubmed().process_csv_file()
    # GeneNeighbors().process_csv_file()
    # GeneOrthology().process_csv_file()
    # GeneGroup().process_csv_file()
    # GeneMim2gene().process_csv_file()
    # Gene2Go().process_csv_file()
    # Gene2Accession().process_csv_file()
    # Gene2Ensembl().process_csv_file()
    # GeneRifs_Basic().process_csv_file()

    logging.info(f"Script completed in {((time() - start_time)/60):.2f} mins")


if __name__ == "__main__":
    app.run(main)
