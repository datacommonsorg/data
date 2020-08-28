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
"""Contains dictionaries and string templates used in pharm.py."""

EVIDENCE_ENUM_DICT = {
    'ClinicalAnnotation': 'RelationshipEvidenceTypeClinicalAnnotation',
    'MultilinkAnnotation': 'RelationshipEvidenceTypeMultilinkAnnotation',
    'GuidelineAnnotation': 'RelationshipEvidenceTypeGuidelineAnnotation',
    'LabelAnnotation': 'RelationshipEvidenceTypeLabelAnnotation',
    'VariantAnnotation': 'RelationshipEvidenceTypeVariantAnnotation',
    'DataAnnotation': 'RelationshipEvidenceTypeDataAnnotation',
    'Literature': 'RelationshipEvidenceTypeLiterature',
    'VipGene': 'RelationshipEvidenceTypeVipGene',
    'Pathway': 'RelationshipEvidenceTypePathway',
}
ASSOCIATION_ENUM_DICT = {
    'associated': 'RelationshipAssociationTypeAssociated',
    'not associated': 'RelationshipAssociationTypeNotAssociated',
    'ambiguous': 'RelationshipAssociationTypeAmbiguous'
}
GENE_XREF_PROP_DICT = {
    'HGNC': 'hgncID',
    'Ensembl': 'ensemblID',
    'OMIM': 'omimID',
    'NCBI Gene': 'ncbiGeneID',
    'RefSeq DNA': 'refSeqID',
    'RefSeq Protein': 'refSeqID',
    'RefSeq RNA': 'refSeqID',
    'UniProtKB': 'uniProtID',
    'ALFRED': 'alfredID',
    'Comparative Toxicogenomics Database': 'comparativeToxicogenomicsDBID',
    'GenAtlas': 'genAtlasID',
    'GeneCard': 'geneCardID',
    'GO': 'geneOntologyID',
    'HumanCyc Gene': 'humanCycGeneID',
    'ModBase': 'modBaseID',
    'MutDB': 'mutDBID',
    'UCSC Genome Browser': 'ucscGenomeBroswerID',
    'IUPHAR Receptor': 'iupharReceptorID',
    'URL': 'url',
    'GenBank': 'genBankID'
}
DRUG_XREF_PROP_DICT = {
    'ChEBI': 'chebiID',
    'Chemical Abstracts Service': 'chemicalAbstractServiceID',
    'ChemSpider': 'chemSpiderID',
    'DrugBank': 'drugBankID',
    'KEGG Compound': 'keggCompoundID',
    'KEGG Drug': 'keggDrugID',
    'PubChem Compound': 'pubChemCompoundID',
    'PubChem Substance': 'pubChemSubstanceID',
    'URL': 'url',
    'IUPHAR Ligand': 'iupharLigandID',
    'PDB': 'proteinDataBankID',
    'FDA Drug Label at DailyMed': 'fdaDailyMedDrugLabel',
    'Drugs Product Database (DPD)': 'drugsProductDatabaseID',
    'Therapeutic Targets Database': 'therapeuticTargetsDatabaseID',
    'ClinicalTrials.gov': 'clinicalTrialsGovID',
    'BindingDB': 'bindingDBID',
    'National Drug Code Directory': 'nationalDrugCodeDirectoryID',
    'UniProtKB': 'uniProtID',
    'GenBank': 'genBankID',
    'HMDB': 'humanMetabolomeDatabaseID',
    'ATCC': 'americanTypeCultureCollectionID',
    'HET': 'hetID',
    'DrugBank Metabolite': 'drugBankMetaboliteID',
    'RXNorm Identifiers': 'rxNormID',
}
GENE_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:Gene
fullName: "{name}"
geneSymbol: "{symbol}"
alternateGeneSymbol: {alt_symbols}
pharmGKBID: "{pharm_id}"
ncbiGeneID: {ncbi_ids}
hgncID: {hgnc_ids}
ensemblID: {ensembl_ids}
'''
DRUG_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: {type}
name: "{dc_name}"
commonName: "{name}"
propietaryName: {trade_names}
simplifiedMolecularInputLineEntrySystem: "{smiles}"
iupacInternationalChemicalID: "{inchi}"
inChIKey: "{inchi_key}"
pharmGKBID: "{pharm_id}"
rxNormID: {rx_ids}
americanTypeCultureCollectionID: {atc_ids}
pubChemCompoundID: {pubchem_compound_ids}
'''
RELATION_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:ChemicalCompoundGeneAssociation
name: "{name}"
geneID: dcid:{gene_dcid}
compoundID: dcid:{drug_dcid}
pubMedID: {pubmed_ids}
isPharmacokineticRelationship: {pk_bool}
isPharmacodynamicRelationship: {pd_bool}
relationshipAssociationType: {assoc_enums}
relationshipEvidenceType: {evid_enums}
'''
