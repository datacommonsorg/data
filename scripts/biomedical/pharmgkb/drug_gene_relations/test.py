# Copyright 2020 Google LLC
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
"""Tests for pharm.py."""
import unittest
import numpy as np

import pharm
import config


class TestSuite(unittest.TestCase):

    def test_format_text_list(self):
        test_str = 'test1, "Aftate for jock itch sprinkle powder","Carbanilic acid, M,N-dimethylthio-, O-2-naphthyl ester","Carbanilic acid, N,M-dimethylthio-, O-2-naphthyl ester","Chinofungin","Dermoxin","Dr. Scholl\'s athlete\'s foot spray","Dungistop"'
        ref_str = '"test1","Aftate for jock itch sprinkle powder","Carbanilic acid, M,N-dimethylthio-, O-2-naphthyl ester","Carbanilic acid, N,M-dimethylthio-, O-2-naphthyl ester","Chinofungin","Dermoxin","Dr. Scholl\'s athlete\'s foot spray","Dungistop"'
        self.assertEqual(pharm.format_text_list(test_str), ref_str)

    def test_format_bool(self):
        self.assertEqual(pharm.format_bool('PK', 'PK'), 'True')
        self.assertEqual(pharm.format_bool('', 'PK'), '')
        self.assertEqual(pharm.format_bool(np.nan, 'PK'), '')
        self.assertEqual(pharm.format_bool('PD', 'PD'), 'True')
        self.assertEqual(pharm.format_bool('', 'PD'), '')
        self.assertEqual(pharm.format_bool(np.nan, 'PD'), '')

    def test_get_enum(self):
        test_str = 'ClinicalAnnotation,MultilinkAnnotation'
        ref_str = ('dcid:RelationshipEvidenceTypeClinicalAnnotation,' +
                   'dcid:RelationshipEvidenceTypeMultilinkAnnotation')
        self.assertEqual(pharm.get_enum(test_str, config.EVIDENCE_ENUM_DICT),
                         ref_str)

    def test_get_xref_mcf(self):
        test_str = '"HMDB:HMDB60705","PubChem Compound:131769925"'
        ref_str = ('humanMetabolomeDatabaseID: "HMDB60705"\n' +
                   'pubChemCompoundID: "131769925"\n')
        self.assertEqual(
            pharm.get_xref_mcf(test_str, config.DRUG_XREF_PROP_DICT), ref_str)

    def test_get_compound_type(self):
        test_to_ref_strs = {
            'Drug,"Metabolite"': 'dcs:ChemicalCompound,dcs:Drug',
            'Metabolite,"Biological Intermediate"': 'dcid:ChemicalCompound',
            'Prodrug': 'dcid:Drug',
        }

        for test, ref in test_to_ref_strs.items():
            self.assertEqual(pharm.get_compound_type(test), ref)

    def test_get_gene_mcf(self):
        row = {
            'PharmGKB Accession Id':
                'PA24444',
            'NCBI Gene ID':
                '8309',
            'HGNC ID':
                '120',
            'Ensembl Id':
                'ENSG00000168306',
            'Name':
                'acyl-CoA oxidase 2',
            'Symbol':
                'ACOX2',
            'Alternate Names':
                '"3-alpha,7-alpha,12-alpha-trihydroxy-5-beta-cholestanoyl-CoA 24-hydroxylase","acyl-CoA oxidase 2, branched chain","branched chain acyl-CoA oxidase","trihydroxycoprostanoyl-CoA oxidase"',
            'Alternate Symbols':
                '"BRCACOX","BRCOX","THCCox"',
            'Cross-references':
                '"ALFRED:LO061936Z","Comparative Toxicogenomics Database:8309","Ensembl:ENSG00000168306","GenAtlas:ACOX2","GO:GO:0003995"',
        }
        gene_templater = pharm.mcf_template_filler.Filler(
            config.GENE_TEMPLATE, required_vars=['dcid'])
        gene_dcid = 'bio/test_dcid'

        ref_mcf = gene_templater.fill({
            'dcid': gene_dcid,
            'name': row['Name'],
            'symbol': row['Symbol'],
            'alt_symbols': row['Alternate Symbols'],
            'pharm_id': row['PharmGKB Accession Id'],
            'ncbi_ids': '"8309"',
            'hgnc_ids': '"120"',
            'ensembl_ids': '"ENSG00000168306"',
        })
        xref_mcf = ('alfredID: "LO061936Z"\n' +
                    'comparativeToxicogenomicsDBID: "8309"\n' +
                    'ensemblID: "ENSG00000168306"\n' + 'genAtlasID: "ACOX2"\n' +
                    'geneOntologyID: "GO:0003995"\n')

        self.assertEqual(pharm.get_gene_mcf(row, gene_dcid), ref_mcf + xref_mcf)

    def test_get_drug_mcf(self):
        row = {
            'PharmGKB Accession Id':
                'PA166181082',
            'Name':
                '3,4-dihydroxyphenylacetaldehyde',
            'Type':
                '"Metabolite","Biological Intermediate"',
            'Cross-references':
                '"ChEBI:CHEBI:27978","HMDB:HMDB0003791","PubChem Compound:119219"',
            'SMILES':
                'C1=CC(=C(C=C1CC=O)O)O',
            'InChI':
                'InChI=1S/C8H8O3/c9-4-3-6-1-2-7(10)8(11)5-6/h1-2,4-5,10-11H,3H2',
            'InChI Key':
                'IADQVXRMSNIUEL-UHFFFAOYSA-N',
            'PubChem Compound Identifiers':
                '119219',
            'Trade Names':
                'test1,"test2"',
            'RxNorm Identifiers':
                'rx_test',
            'ATC Identifiers':
                'atc_test',
        }
        drug_templater = pharm.mcf_template_filler.Filler(
            config.DRUG_TEMPLATE, required_vars=['dcid'])
        drug_dcid = 'bio/test_dcid'

        ref_mcf = drug_templater.fill({
            'dcid': drug_dcid,
            'type': 'dcid:ChemicalCompound',
            'dc_name': 'test_dcid',
            'name': row['Name'],
            'inchi': row['InChI'],
            'smiles': row['SMILES'],
            'inchi_key': 'IADQVXRMSNIUEL-UHFFFAOYSA-N',
            'pharm_id': row['PharmGKB Accession Id'],
            'pubchem_compound_ids': '"119219"',
            'atc_ids': '"atc_test"',
            'rx_ids': '"rx_test"',
            'trade_names': '"test1","test2"',
        })
        xref_mcf = ('chebiID: "CHEBI:27978"\n' +
                    'humanMetabolomeDatabaseID: "HMDB0003791"\n' +
                    'pubChemCompoundID: "119219"\n')

        self.assertEqual(pharm.get_drug_mcf(row, drug_dcid), ref_mcf + xref_mcf)

    def test_get_relation_mcf(self):
        row = {
            'Evidence': 'ClinicalAnnotation,VariantAnnotation',
            'Association': 'associated',
            'PK': 'PK',
            'PD': 'PD',
            'PMIDs': '27163851;32423989',
        }
        relation_templater = pharm.mcf_template_filler.Filler(
            config.RELATION_TEMPLATE, required_vars=['dcid'])
        drug_dcid = 'bio/drug_dcid'
        gene_dcid = 'bio/gene_dcid'

        ref_mcf = relation_templater.fill({
            'dcid': 'bio/CGA_drug_dcid_gene_dcid',
            'gene_dcid': gene_dcid,
            'drug_dcid': drug_dcid,
            'name': 'CGA_drug_dcid_gene_dcid',
            'evid_enums': ('dcid:RelationshipEvidenceTypeClinicalAnnotation,'
                           'dcid:RelationshipEvidenceTypeVariantAnnotation'),
            'assoc_enums': 'dcid:RelationshipAssociationTypeAssociated',
            'pk_bool': 'True',
            'pd_bool': 'True',
            'pubmed_ids': '"27163851","32423989"',
        })

        self.assertEqual(pharm.get_relation_mcf(row, drug_dcid, gene_dcid),
                         ref_mcf)


unittest.main(argv=['first-arg-is-ignored'], exit=False)
