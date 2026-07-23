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
Date: 09-Oct-2024
"""

import os
import unittest
from pathlib import Path
from absl import flags
from format_clinvar_and_position import *

CURRENT_ROW = None


class TestNCBIClinVar(unittest.TestCase):

    def test_check_clinvar_parser(self):
        """ Unit test to parse clinvar row
        """
        global CURRENT_ROW

        line = [
            'Y', '641068', '1224466', 'T', 'TAA', '.', '.',
            'ALLELEID=1214433;CLNDISDB=MedGen:C3661900;CLNDN=not_provided;CLNHGVS=NC_000024.10:g.641069_641070insAA;CLNREVSTAT=criteria_provided,_single_submitter;CLNSIG=Likely_pathogenic;CLNVC=Insertion;CLNVCSO=SO:0000667;GENEINFO=SHOX:6473;MC=SO:0001589|frameshift_variant;ORIGIN=1;RS=2124183611'
        ]
        expected_result = {
            'dcid':
                'bio/rs2124183611',
            'name':
                'rs2124183611',
            'dcid_pos':
                'bio/hg38_chrY_641068',
            'name_pos':
                'hg38 chrY 641068',
            'chrom':
                'chrY',
            'position':
                '641068',
            'alleleOrigin':
                'dcs:VariantAlleleOriginGermline',
            'associatedDiseaseName':
                '',
            'associatedDrugResponseEfficacy':
                '',
            'canonicalAlleleID':
                '',
            'catalogueOfSomaticMutationsInCancerID':
                '',
            'clinicalSignificanceCategory_onc':
                '',
            'clinicalSignificanceCategory_sic':
                '',
            'clinicalSignificance':
                'dcs:ClinSigConflictingPathogenicity',
            'clinVarAlleleID':
                '1214433',
            'clinVarGermlineReviewStatus':
                'dcs:ClinVarReviewStatusSingleSubmitter',
            'clinVarOncogenicityReviewStatus':
                '',
            'clinVarSomaticReviewStatus':
                '',
            'dbVarID':
                '',
            'experimentalFactorOntologyID':
                '',
            'geneID':
                'dcid:bio/SHOX',
            'geneSymbol':
                'SHOX',
            'geneticTestingRegistryID':
                '',
            'geneticVariantClass':
                'dcs:GeneticVariantClassInsertion',
            'geneticVariantFunctionalCategory':
                'dcs:GeneticVariantFunctionalCategorySplice5',
            'hbVarID':
                '',
            'hg19GenomicPosition':
                '641068',
            'hgvsNomenclature':
                'NC_000024.10:g.641069_641070insAA',
            'humanPhenotypeOntologyID':
                '',
            'inChromosome':
                '',
            'leidenOpenVariationDatabaseID':
                '',
            'medicalSubjectHeadingID':
                '',
            'mitochondrialDiseaseSequenceDataResourceID':
                '',
            'mondoID':
                '',
            'ncbiGeneID':
                '6473',
            'ncbiGeneID_info':
                '',
            'observedAllele':
                '',
            'omimID':
                '',
            'omimID_gv':
                '',
            'orphaNumber':
                '',
            'pharmgkbClinicalAnnotationID':
                '',
            'referenceAllele':
                'T',
            'rsID':
                'rs2124183611',
            'sequenceOntologyID':
                'dcid:bio/SO_0000667',
            'sequenceOntologyID_mc':
                'dcid:bio/SO_0001589',
            'snomedCT':
                '',
            'umlsConceptUniqueID':
                'C3661900',
            'uniProtID':
                '',
            'uniProtKBSwissProtID':
                '',
            'dcid_conflicting':
                '',
            'name_conflicting':
                '',
            'alternativeAllele':
                'TAA',
            'count':
                '',
            'dcid_freq':
                '',
            'name_freq':
                '',
            'alleleFrequency':
                '',
            'measuredPopulation':
                ''
        }

        CURRENT_ROW = copy.deepcopy(CLINVAR_OUTPUT_DICT)
        CURRENT_ROW.update(copy.deepcopy(CLINVAR_CONFLICTING_OUTPUT_DICT))
        CURRENT_ROW.update(copy.deepcopy(CLINVAR_OBS_OUTPUT_DICT))
        w = WriteToCsv()
        _, _, _, _, curr_row = parse_clinvar_row(line, w, curr_row=CURRENT_ROW)
        self.assertDictEqual(curr_row, expected_result)

    def test_check_clinvar_pos_parser(self):
        """ Unit test to parse clinvar pos row
        """
        global CURRENT_ROW
        line = [
            'Y', '551575', '929168', 'G', 'A', '.', '.',
            'ALLELEID=917376;CLNDISDB=MedGen:CN169374;CLNDN=not_specified;CLNHGVS=NC_000024.9:g.551575G>A;CLNREVSTAT=criteria_provided,_single_submitter;CLNSIG=Uncertain_significance;CLNVC=single_nucleotide_variant;CLNVCSO=SO:0001483;GENEINFO=SHOX:6473;MC=SO:0001583|missense_variant;ORIGIN=1;RS=2052840553'
        ]

        expected_result = {
            'dcid': 'bio/rs2052840553',
            'name': '2052840553',
            'dcid_pos': 'bio/hg19_chrY_551575',
            'name_pos': '"hg19 chrY 551575"',
            'chrom': 'chrY',
            'position': '551575',
            'rsID': '2052840553'
        }

        CURRENT_ROW = copy.deepcopy(CLINVAR_POS_OUTPUT_DICT)
        w = WriteToCsv()
        row = parse_clinvar_pos_row(line, w, CURRENT_ROW)
        self.assertDictEqual(row, expected_result)


if __name__ == '__main__':
    unittest.main()
