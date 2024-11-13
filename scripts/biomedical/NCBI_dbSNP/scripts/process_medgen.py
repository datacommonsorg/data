import os
import sys
import copy
import csv
import time
from absl import flags
from absl import logging

MODULE_DIR = os.path.dirname(os.path.dirname(__file__))
_FLAGS = flags.FLAGS

flags.DEFINE_string('output_dir', 'output', 'Output directory for generated files.')
flags.DEFINE_string('input_dir', 'input', 'Input directory where .vcf files downloaded.')

_FLAGS(sys.argv)

MGSTY_file_name = 'MGSTY.txt'
NAMES_file_name = 'NAMES.txt'
MGDEF_file_name = 'MGDEF.txt'
MedGenIDMappings_file_name = 'MedGenIDMappings.txt'
output_file_name = 'medgen.csv'
cui_dcid_mappings_file_name = 'cui_dcid_mappings.csv'

CSV_DICT = {
    'dcid': '',
    'name': '',
    'CUI': '',
    'source': '',
    'DEF': '',
    'source_definition': '',
    'STY': '',
    'GARD': '',
    'HPO': '',
    'MONDO': '',
    'MeSH': '',
    'MedGen': '',
    'OMIM': '',
    'OMIM_Phenotypic_Series': '',
    'OMIM_Allelic_Variant': '',
    'Orphanet': '',
    'SNOMEDCT_US': '',
    'dcid_compound': '',
    'dcid_atc_code': '',
    'dcid_mesh': '',
    'is_drug_response': False
}

CUI_DCID_MAPPING_DICT = {'dcid': '', 'CUI': '', 'name': '', 'is_drug_response': ''}

CUI_ID_SET = set()

SOURCE_DICT = {
    'GTR': 'Genetic Testing Registry',
    'MSH': 'Medical Subject Headings',
    'NCI': 'NCI Thesaurus',
    'OMIM': 'Online Mendelian Inheritance in Man',
    'ORDO': 'Orphanet Rare Disease Ontology (ORDO)',
    'SNOMEDCT_US': 'US Edition of SNOMED CT'
}

SOURCE_DEFINITION_DICT = {
    'AIR':
        'dcs:DiseaseSourceDefinitionAiRheum',
    'AOT':
        'dcs:DiseaseSourceDefinitionAuthorizedOsteopathicThesaurus',
    'CCC':
        'dcs:DiseaseSourceDefinitionClinicalCareClassificationTwoPointFive',
    'CHV':
        'dcs:DiseaseSourceDefinitionConsumerHealthVocabulary',
    'CSP':
        'dcs:DiseaseSourceDefinitionCrispThesaurus',
    'Clinical Pharmacogenetics Implementation Consortium':
        'dcs:DiseaseSourceDefinitionClinicalPharmacogeneticsImplementationConsortium',
    'GO':
        'dcs:DiseaseSourceDefinitionGeneOntology',
    'GeneReviews':
        'dcs:DiseaseSourceDefinitionGeneReviews',
    'HL7V3.0':
        'dcs:DiseaseSourceDefinitionHL7VocabularyVersionThreePointZero',
    'HPO':
        'dcs:DiseaseSourceDefinitionHumanPhenotypeOntology',
    'ICF-CY':
        'dcs:DiseaseSourceDefinitionInternationalClassificationOfFunctioninDisabilityAndHealthForChildrenAndYouth',
    'JABL':
        'dcs:DiseaseSourceDefinitionOnlineCongenitalMultipleAnomalyMentalRetardationSyndromes',
    'LNC':
        'dcs:DiseaseSourceDefinitionLoinc',
    'MEDLINEPLUS':
        'dcs:DiseaseSourceDefinitionMedlinePlus',
    'MONDO':
        'dcs:DiseaseSourceDefinitionMonarchInitiative',
    'MSH':
        'dcs:DiseaseSourceDefinitionMedicalSubjectHeading',
    'Medical Genetics Summaries':
        'dcs:DiseaseSourceDefinitionMedicalGeneticsSummaries',
    'MedlinePlus Genetics':
        'dcs:DiseaseSourceDefinitionMedlinePlusGenetics',
    'NANDA-I':
        'dcs:DiseaseSourceDefinitionNANDAITaxonomyII',
    'NCBI curation':
        'dcs:DiseaseSourceDefinitionNCBI',
    'NCI':
        'dcs:DiseaseSourceDefinitionNCIThesaurus',
    'NOC':
        'dcs:DiseaseSourceDefinitionNursingOutcomesClassificationThirdEdition',
    'OMIM':
        'dcs:DiseaseSourceDefinitionOnlineMendelianInheritanceInMan',
    'OMS':
        'dcs:DiseaseSourceDefinitionOmahaSystem',
    'ORDO':
        'dcs:DiseaseSourceDefinitionOrphanetRareDiseaseOntology',
    'ORPHANET':
        'dcs:DiseaseSourceDefinitionOrphanet',
    'PDQ':
        'dcs:DiseaseSourceDefinitionPhysicianDataQuery',
    'PNDS':
        'dcs:DiseaseSourceDefinitionPerioperativeNursingDataSetSecondEdition',
    'PSY':
        'dcs:DiseaseSourceDefinitionThesaurusOfPsychologicalIndexTerms',
    'PharmGKB':
        'dcs:DiseaseSourceDefinitionPharmGKB',
    'SNOMEDCT_US':
        'dcs:DiseaseSourceDefinitionSnomedCtUs'
}

DCID_CUI_ASSOCIATE = {
    'C0568062': {
        'name': 'methotrexate response - Toxicity',
        'dcid_compound': 'dcs:chem/CID126941',
        'dcid_atc_code': 'dcs:chem/L04AX03',
        'dcid_mesh': 'dcs:bio/D008727'
    },
    'CN236531': {
        'name': 'fentanyl response - Dosage',
        'dcid_compound': 'dcs:chem/CID3345',
        'dcid_atc_code': 'dcs:chem/N01AH01',
        'dcid_mesh': 'dcs:bio/D005283'
    },
    'CN236536': {
        'name': 'methadone response - Dosage',
        'dcid_compound': 'dcs:chem/CID4095',
        'dcid_atc_code': 'dcs:chem/N07BC02',
        'dcid_mesh': 'dcs:bio/D008691'
    },
    'CN236588': {
        'name': 'warfarin response - Efficacy',
        'dcid_compound': 'dcs:chem/CID54678486',
        'dcid_atc_code': 'dcs:chem/B01AA03',
        'dcid_mesh': 'dcs:bio/D014859'
    },
    'CN262133': {
        'name': 'vincristine response - Toxicity/ADR',
        'dcid_compound': 'dcs:chem/CID5978',
        'dcid_atc_code': 'dcs:chem/L01CA02',
        'dcid_mesh': 'dcs:bio/D014750'
    },
    'CN322717': {
        'name':
            'interferons, peginterferon alfa-2a, peginterferon alfa-2b, and ribavirin response - Efficacy',
        'dcid_compound':
            'dcs:bio/CHEMBL1201560, dcs:bio/CHEMBL1201561, dcs:chem/CID37542',
        'dcid_atc_code':
            'dcs:chem/L03AB11, dcs:chem/L03AB10, dcs:chem/J05AP01',
        'dcid_mesh':
            'dcs:bio/C100416, dcs:bio/C417083,dcs:bio/D012254'
    },
    'CN322718': {
        'name': 'peginterferon alfa-2a, peginterferon alfa-2b, and ribavirin response - Efficacy',
        'dcid_compound': 'dcs:bio/CHEMBL1201560, dcs:bio/CHEMBL1201561, dcs:chem/CID37542',
        'dcid_atc_code': 'dcs:chem/L03AB11, dcs:chem/L03AB10, dcs:chem/J05AP01',
        'dcid_mesh': 'dcs:bio/C100416, dcs:bio/C417083,dcs:bio/D012254'
    },
    'CN322719': {
        'name':
            'peginterferon alfa-2a, peginterferon alfa-2b, ribavirin, and telaprevir response - Efficacy',
        'dcid_compound':
            'dcs:bio/CHEMBL1201560, dcs:bio/CHEMBL1201561, dcs:chem/CID37542, dcs:chem/CID3010818',
        'dcid_atc_code':
            'dcs:chem/L03AB11, dcs:chem/L03AB10, dcs:chem/J05AP01, dcs:chem/J05AP02',
        'dcid_mesh':
            'dcs:bio/C100416, dcs:bio/C417083,dcs:bio/D012254, dcs:bio/C486464'
    },
    'CN322720': {
        'name': 'Ace Inhibitors, Plain response - Toxicity/ADR',
        'dcid_compound': '',
        'dcid_atc_code': 'dcs:chem/C09A',
        'dcid_mesh': 'dcs:bio/D000806'
    },
    'CN322721': {
        'name': 'acenocoumarol response - Dosage',
        'dcid_compound': 'dcs:chem/CID54676537',
        'dcid_atc_code': 'dcs:chem/B01AA07',
        'dcid_mesh': 'dcs:bio/D000074'
    },
    'CN322722': {
        'name': 'adalimumab response - Efficacy',
        'dcid_compound': 'dcs:bio/CHEMBL1201580',
        'dcid_atc_code': 'dcs:chem/L04AB04',
        'dcid_mesh': 'dcs:bio/D000068879'
    },
    'CN322723': {
        'name': 'alfentanil response - Metabolism/PK',
        'dcid_compound': 'dcs:chem/CID51263',
        'dcid_atc_code': 'dcs:chem/N01AH02',
        'dcid_mesh': 'dcs:bio/D015760'
    },
    'CN322724': {
        'name': 'atorvastatin response - Efficacy',
        'dcid_compound': 'dcs:chem/CID60823',
        'dcid_atc_code': 'dcs:chem/C10AA05',
        'dcid_mesh': 'dcs:bio/D000069059'
    },
    'CN322725': {
        'name': 'captopril response - Efficacy',
        'dcid_compound': 'dcs:chem/CID44093',
        'dcid_atc_code': 'dcs:chem/C09AA01',
        'dcid_mesh': 'dcs:bio/D002216'
    },
    'CN322726': {
        'name': 'carbamazepine response - Dosage',
        'dcid_compound': 'dcs:chem/CID2554',
        'dcid_atc_code': 'dcs:chem/N03AF01',
        'dcid_mesh': 'dcs:bio/D002220'
    },
    'CN322727': {
        'name': 'clopidogrel response - Efficacy',
        'dcid_compound': 'dcs:chem/CID60606',
        'dcid_atc_code': 'dcs:chem/B01AC04',
        'dcid_mesh': 'dcs:bio/D000077144'
    },
    'CN322728': {
        'name': 'phenprocoumon response - Dosage',
        'dcid_compound': 'dcs:chem/CID54680692',
        'dcid_atc_code': 'dcs:chem/B01AA04',
        'dcid_mesh': 'dcs:bio/D010644'
    },
    'CN322729': {
        'name': 'warfarin response - Dosage',
        'dcid_compound': 'dcs:chem/CID54678486',
        'dcid_atc_code': 'dcs:chem/B01AA03',
        'dcid_mesh': 'dcs:bio/D014859'
    },
    'CN322730': {
        'name': 'efavirenz response - Metabolism/PK',
        'dcid_compound': 'dcs:chem/CID64139',
        'dcid_atc_code': 'dcs:chem/J05AG03',
        'dcid_mesh': 'dcs:bio/C098320'
    },
    'CN322731': {
        'name': 'erlotinib response - Efficacy',
        'dcid_compound': 'dcs:chem/CID176870',
        'dcid_atc_code': 'dcs:chem/L01EB02',
        'dcid_mesh': 'dcs:bio/D000069347'
    },
    'CN322732': {
        'name': 'etanercept response - Efficacy',
        'dcid_compound': 'dcs:bio/CHEMBL1201572',
        'dcid_atc_code': 'dcs:chem/L04AB01',
        'dcid_mesh': 'dcs:bio/D000068800'
    },
    'CN322733': {
        'name': 'gefitinib response - Efficacy',
        'dcid_compound': 'dcs:chem/CID123631',
        'dcid_atc_code': 'dcs:chem/L01EB01',
        'dcid_mesh': 'dcs:bio/D000077156'
    },
    'CN322734': {
        'name': 'hydrochlorothiazide response - Efficacy',
        'dcid_compound': 'dcs:chem/CID3639',
        'dcid_atc_code': 'dcs:chem/C03AA03',
        'dcid_mesh': 'dcs:bio/D006852'
    },
    'CN322735': {
        'name': 'ivacaftor response - Efficacy',
        'dcid_compound': 'dcs:chem/CID16220172',
        'dcid_atc_code': 'dcs:chem/R07AX02',
        'dcid_mesh': 'dcs:bio/C545203'
    },
    'CN322736': {
        'name': 'methotrexate response - Efficacy',
        'dcid_compound': 'dcs:chem/CID126941',
        'dcid_atc_code': 'dcs:chem/L04AX03',
        'dcid_mesh': 'dcs:bio/D008727'
    },
    'CN322737': {
        'name': 'pravastatin response - Efficacy',
        'dcid_compound': 'dcs:chem/CID54687',
        'dcid_atc_code': 'dcs:chem/C10AA03',
        'dcid_mesh': 'dcs:bio/D017035'
    },
    'CN322738': {
        'name': 'rosuvastatin response - Efficacy',
        'dcid_compound': 'dcs:chem/CID446157',
        'dcid_atc_code': 'dcs:chem/C10AA07',
        'dcid_mesh': 'dcs:D000068718'
    },
    'CN322739': {
        'name': 'salmeterol response - Efficacy',
        'dcid_compound': 'dcs:chem/CID5152',
        'dcid_atc_code': 'dcs:chem/R03AC12',
        'dcid_mesh': 'dcs:D000068299'
    },
    'CN322746': {
        'name': 'ivacaftor / lumacaftor response',
        'dcid_compound': 'chem/CID71494926',
        'dcid_atc_code': 'chem/R07AX30',
        'dcid_mesh': 'bio/C000599212'
    },
    'CN322747': {
        'name': 'peginterferon alfa-2a response - Efficacy',
        'dcid_compound': 'dcs:bio/CHEMBL1201560',
        'dcid_atc_code': 'dcs:chem/L03AB11',
        'dcid_mesh': 'dcs:bio/C100416'
    },
    'CN322748': {
        'name': 'peginterferon alfa-2b response - Efficacy',
        'dcid_compound': 'dcs:bio/CHEMBL1201561',
        'dcid_atc_code': 'dcs:chem/L03AB10',
        'dcid_mesh': 'dcs:bio/C417083'
    },
    'CN322749': {
        'name': 'ribavirin response - Efficacy',
        'dcid_compound': 'dcs:chem/CID37542',
        'dcid_atc_code': 'dcs:chem/J05AP01',
        'dcid_mesh': 'dcs:bio/D012254'
    }
}


def get_pascal_case(s: str, sep=None):
    if sep and sep in s:
        return "".join(map(lambda x: x[:1].upper() + x[1:], s.split(sep)))
    else:
        return s[:1].upper() + s[1:]


def main_process_csv(MGSTY_file_path: str, NAMES_file_path: str, MGDEF_file_path,
                     MedGenIDMappings_file_path: str, output_file_path: str,
                     cui_dcid_mapping_file_path: str) -> None:
    # get unique CUI id from all four files:
    # Clean-up the MGDEF file which is having '\n' newline character in column 2
    MGDEF_records = []
    with open(MGDEF_file_path, mode='r') as f:
        next(f)
        curr_line = ''
        for line in f:
            if line[-2:-1] == '|':
                if curr_line == '':
                    MGDEF_records.append(line)
                    curr_line = ''
                else:
                    MGDEF_records.append(curr_line + line)
                    curr_line = ''
            else:
                curr_line = curr_line + line

    with open(MGSTY_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            add_to_cui_set(val[0])

    with open(NAMES_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            if val[3] == 'N':
                add_to_cui_set(val[0])

    for line in MGDEF_records:
        val = line.split('|')
        if val[3] == 'N':
            add_to_cui_set(val[0])

    with open(MedGenIDMappings_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            add_to_cui_set(val[0])

    # final output dict
    CSV_OUTPUT_DICT = {}
    global CUI_ID_SET
    for id in CUI_ID_SET:
        obj = copy.deepcopy(CSV_DICT)
        obj['CUI'] = id
        obj['dcid'] = f"bio/{id}"
        if id in DCID_CUI_ASSOCIATE:
            obj['dcid_compound'] = DCID_CUI_ASSOCIATE[id]['dcid_compound']
            obj['dcid_atc_code'] = DCID_CUI_ASSOCIATE[id]['dcid_atc_code']
            obj['dcid_mesh'] = DCID_CUI_ASSOCIATE[id]['dcid_mesh']
            obj['is_drug_response'] = True
        CSV_OUTPUT_DICT[id] = obj

    # process individual files and update the respective properties to final output dict
    with open(MGSTY_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            try:
                # Convert to MedGenSemanticTypeEnum
                if val[0] in CUI_ID_SET:
                    CSV_OUTPUT_DICT[
                        val[0]]['STY'] = f"dcs:MedGeneSemanticType{get_pascal_case(val[3], ' ')}"
            except:
                print(f"Error at {val[0]} in MGSTY file")

    with open(NAMES_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            if val[3] == 'N':
                if val[0] in CUI_ID_SET:
                    try:
                        curr_record = CSV_OUTPUT_DICT[val[0]]
                        name = val[1].replace('"', "'")
                        curr_record['name'] = f'"{name}"'
                        curr_record['source'] = f'"{SOURCE_DICT[val[2]]}"'
                    except:
                        print(f"source {val[2]} not in SOURCE_DICT")

    for line in MGDEF_records:
        val = line.split('|')
        if val[3] == 'N':
            if val[0] in CUI_ID_SET:
                try:
                    curr_record = CSV_OUTPUT_DICT[val[0]]
                    curr_record[
                        'source_definition'] = f'"{SOURCE_DEFINITION_DICT[val[2]].replace("[", "(").replace("]", ")")}"'
                    if "\n" in val[1]:
                        pass

                    def_str = str(val[1]).replace("\\n", "").replace("\n", "").replace('"', "'")
                    curr_record['DEF'] = f'"{def_str}"'
                except:
                    print(f"source_definition {val[2]} not in SOURCE_DEFINITION_DICT")

    with open(MedGenIDMappings_file_path, mode='r') as f:
        next(f)
        for line in f:
            val = line.split('|')
            if val[0] in CUI_ID_SET:
                curr_record = CSV_OUTPUT_DICT[val[0]]
                source_id = val[2]
                match val[3]:
                    case 'GARD':
                        curr_record['GARD'] = source_id
                    case 'HPO':
                        curr_record['HPO'] = source_id
                    case 'MONDO':
                        curr_record['MONDO'] = source_id
                    case 'MeSH':
                        curr_record['MeSH'] = f"bio/{source_id}"
                    case 'MedGen':
                        curr_record['MedGen'] = source_id
                    case 'OMIM':
                        curr_record['OMIM'] = source_id
                    case 'OMIM included':
                        curr_record['OMIM'] = source_id
                    case 'OMIM Phenotypic Series':
                        curr_record['OMIM_Phenotypic_Series'] = source_id
                    case 'OMIM Allelic Variant':
                        curr_record['OMIM_Allelic_Variant'] = source_id
                    case 'Orphanet':
                        curr_record['Orphanet'] = source_id
                    case 'SNOMEDCT_US':
                        curr_record['SNOMEDCT_US'] = source_id

    with open(output_file_path, 'w') as output_file_csv, open(cui_dcid_mapping_file_path,
                                                              'w') as cui_dcid_csv:
        writer = csv.DictWriter(output_file_csv, CSV_DICT)
        writer.writeheader()
        cui_writer = csv.DictWriter(cui_dcid_csv, CUI_DCID_MAPPING_DICT, extrasaction="ignore")
        cui_writer.writeheader()
        for _, row in CSV_OUTPUT_DICT.items():
            writer.writerow(row)
            cui_writer.writerow(row)


def add_to_cui_set(val: str) -> None:
    global CUI_ID_SET
    if ' ' in val:
        cui = val.split(' ')
        CUI_ID_SET.add(cui[0])
    else:
        CUI_ID_SET.add(val)


def main():
    # set start time
    logging.set_verbosity('info')
    logging.info("Started medgen process")
    start = time.time()

    MGSTY_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, MGSTY_file_name)
    NAMES_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, NAMES_file_name)
    MGDEF_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir, MGDEF_file_name)
    MedGenIDMappings_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.input_dir,
                                              MedGenIDMappings_file_name)
    output_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir, output_file_name)
    cui_dcid_mapping_file_path = os.path.join(MODULE_DIR + '/' + _FLAGS.output_dir,
                                              cui_dcid_mappings_file_name)

    main_process_csv(MGSTY_file_path, NAMES_file_path, MGDEF_file_path, MedGenIDMappings_file_path,
                     output_file_path, cui_dcid_mapping_file_path)

    print(f'Process completed in {round((time.time() - start)/60,2)} mins')


if __name__ == '__main__':
    main()
