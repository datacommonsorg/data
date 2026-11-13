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
Date: 20-Sep-2024
"""
import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

#import format_ncbi_gene as gene

from .format_ncbi_gene import GeneInfo, Gene2Accession, Gene2Go, GeneNeighbors, GeneMim2gene, GeneRifs_Basic, Gene2Ensembl


class NcbiGeneTest(unittest.TestCase):

    def test_check_gene_info_parser(self):
        """ Unit test to parse gene_info row
        """
        gene_id_dcid_mapping = {}
        feature_type_entries = set()
        unique_dbXrefs_list = []
        unique_dbXrefs = set()
        input_row = [
            '2010893', '33370007', 'rbcL', 'CGW41_pgp092', 'Lo_mil1Pt0025', '-',
            '-', '-',
            'ribulose-1,5-bisphosphate carboxylase/oxygenase large subunit',
            'protein-coding', '-', '-', '-', '-', '20230531', '-'
        ]
        expected_result = {
            'taxID':
                '2010893',
            'dcid_taxon':
                'dcid:bio/LobeliaMildbraedii',
            'GeneID':
                '33370007',
            'dcid':
                'bio/33370007',
            'Symbol':
                '"rbcL"',
            'synonym':
                'Lo_mil1Pt0025',
            'chromosome':
                '',
            'map_location':
                '',
            'description':
                '"ribulose-15-bisphosphate carboxylaseoxygenase large subunit"',
            'type_of_gene':
                '',
            'Full_name_from_nomenclature_authority':
                '',
            'Nomenclature_status':
                '',
            'Other_designations':
                '',
            'Modification_date':
                '2023-05-31',
            'regulatory':
                '',
            'misc_feature':
                '',
            'misc_recomb':
                ''
        }

        row = GeneInfo().parse_gene_info_row('dcid:bio/LobeliaMildbraedii',
                                             gene_id_dcid_mapping,
                                             feature_type_entries,
                                             unique_dbXrefs_list,
                                             unique_dbXrefs, input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_neighbors_parser(self):
        """ Unit test to parse gene_neighbors row
        """
        input_row = [
            '7888', '122811710', 'NC_056743.1', '2089853587', '978179254',
            '978360469', '+', '9.part0', '122811707|122811709', '26167',
            '122810615|122812657', '258305', '-',
            'Reference PAN1.0 Primary Assembly'
        ]
        expected_result = {
            'GeneID': 'bio/122811710',
            'dcid': 'bio/NC_056743.1_978179254_978360469',
            'name': '"NC_056743.1 978179254 978360469"',
            'genomic_accession.version': 'NC_056743.1',
            'genomic_gi': '2089853587',
            'start_position': '978179254',
            'end_position': '978360469',
            'orientation': 'dcs:StrandOrientationPositive',
            'chromosome': 'chr9.part0',
            'assembly': '"Reference PAN1.0 Primary Assembly"'
        }
        row = GeneNeighbors().parse_gene_neighbors_row('bio/122811710',
                                                       input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_mim2gene_parser(self):
        """  Unit test to parse gene_mim2gene row
        """
        input_row = ['620758', '100652748', 'gene', '-', '-', '-']
        expected_result = {
            'GeneID': 'bio/ncbi_100652748',
            'MIM_number': '620758',
            'omim_dcid': 'bio/omim_620758',
            'type': 'dcs:GeneOmimRelationshipTypeGene',
            'Source': '',
            'MedGenCUI': '',
            'Comment': '',
            'dcid': 'bio/ncbi_100652748_omim_620758',
            'MedGenCUI_dcid': ''
        }
        row = GeneMim2gene().parse_gene_mim2gene_row('bio/ncbi_100652748',
                                                     input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_gene2go_parser(self):
        """  Unit test to parse gene_gene3go row
        """
        input_row = [
            '75485', '128904962', 'GO:0048025', 'IEA', 'involved_in',
            'negative regulation of mRNA splicing, via spliceosome', '30032202',
            'Process'
        ]
        expected_result = {
            'GeneID':
                'bio/128904962',
            'dcid':
                'bio/GO_0048025',
            'GO_ID':
                'GO:0048025',
            'Evidence':
                'dcs:GOTermEvidenceCodeElectronicAnnotation',
            'Qualifier':
                'dcs:GOTermQualifierInvolvedIn',
            'GO_term':
                '"negative regulation of mRNA splicing, via spliceosome"',
            'PubMed':
                '"30032202"',
            'Category':
                'dcs:GeneOntologyCategoryBiologicalProcess'
        }
        row = Gene2Go().parse_gene_gene2go_row('bio/128904962', input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_gene2ensembl_parser(self):
        """ Unit test to parse gene_gene2ensembl row
        """
        input_row = [
            '9606', '113218477', 'ENSG00000178440', 'NR_158657.1',
            'ENST00000651208.1', '-', '-'
        ]
        expected_result = {
            'GeneID': 'bio/ncbi_113218477',
            'Ensembl_gene_identifier': 'ENSG00000178440',
            'RNA_nucleotide_accession.version': 'NR_158657.1',
            'dcid_rna_transcript': 'bio/NR_158657.1',
            'Ensembl_rna_identifier': 'ENST00000651208.1',
            'protein_accession.version': '',
            'Ensembl_protein_identifier': ''
        }

        row = Gene2Ensembl().parse_gene_gene2ensembl_row(
            'bio/ncbi_113218477', input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_rifs_basic_parser(self):
        """ Unit test to parse gene_rifs_basic row
        """
        input_row = [
            '9606', '3188', '16171461', '2010-01-21 00:00',
            'the relative levels of hnRNP F and H2 in cells, as well as the target sequences in the downstream GRS on pre-mRNA, influence gene expression'
        ]
        expected_result = {
            'GeneID':
                'bio/ncbi_3188',
            'dcid':
                'bio/ncbi_3188_16171461',
            'name':
                '"ncbi 3188 PubMed 16171461 Reference Into Function"',
            'dateModified':
                '2010-01-21',
            'pubMedId':
                '16171461',
            'GeneRifText':
                '"the relative levels of hnRNP F and H2 in cells, as well as the target sequences in the downstream GRS on pre-mRNA, influence gene expression"'
        }

        row = GeneRifs_Basic().parse_gene_generifs_row('bio/ncbi_3188',
                                                       input_row)
        self.assertDictEqual(row, expected_result)

    def test_check_gene_gene2accession_parser(self):
        """ Unit test to parse gene_gene2accession row
        """
        input_row = [
            '9606', '113218477', 'VALIDATED', 'NR_158661.1', '1476411838', '',
            '', 'NC_060934.1', '2194973501', '50791694', '50860158', '+',
            'Alternate T2TCHM13v2.0', '', '', 'TIMM23BAGAP6'
        ]
        expected_result = {
            'GeneID': 'bio/ncbi_113218477',
            'dcid_dna_coordinates': 'bio/NR_158661.1_50791694_50860158',
            'name_dna_coordinates': '"NR_158661.1 50791694 50860158"',
            'dcid_genomic_nucleotide': 'bio/NC_060934.1',
            'dcid_protein': '',
            'dcid_peptide': '',
            'dcid_rna_transcript': 'bio/NR_158661.1',
            'status': 'dcs:RefSeqStatusValidated',
            'RNA_nucleotide_accession.version': 'NR_158661.1',
            'RNA_nucleotide_gi': '1476411838',
            'protein_accession.version': '',
            'protein_gi': '',
            'genomic_nucleotide_accession.version': 'NC_060934.1',
            'genomic_nucleotide_gi': '2194973501',
            'start_position_on_the_genomic_accession': '50791694',
            'end_position_on_the_genomic_accession': '50860158',
            'orientation': 'dcs:StrandOrientationPositive',
            'assembly': 'Alternate T2TCHM13v2.0',
            'mature_peptide_accession.version': '',
            'mature_peptide_gi': ''
        }

        row = Gene2Accession().parse_gene_gene2accession_row(
            'bio/ncbi_113218477', input_row)
        self.assertDictEqual(row, expected_result)


if __name__ == '__main__':
    unittest.main()
