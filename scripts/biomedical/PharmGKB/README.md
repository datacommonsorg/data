# Importing the PharmGKB data - Genes, Drugs, Chemicals and Other Mappings

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Download Data](#download-data)
    2. [Database Overview](#database-overview)
    3. [Schema Overview](#schema-overview)
       1. [New Schema](#new-schema)
       2. [dcid Generation](#dcid-generation)
       3. [Edges](#edges)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
       1. [Scripts](#scripts)
       2. [tMCFs](#tmcfs)
       3. [Mapping Files](#mapping-files)
    2. [Import Procedure](#import-procedure)
    3. [Test](#test)

## About the Dataset

The Pharmacogenomics Knowledge Base, PharmGKB, is an interactive tool for researchers investigating how genetic variation affects drug response. [PharmGKB]https://www.pharmgkb.org/) displays genotype, molecular, and clinical knowledge integrated into pathway representations and Very Important Pharmacogene (VIP) summaries with links to additional external resources. Users can search and browse the knowledgebase by genes, variants, drugs, diseases, and pathways. The Primary Data contains summary information on chemicals, drugs, genes, genetic variants, and phenotypes.

### Download Data

Data from PharmGKB can be downloaded [here](https://www.pharmgkb.org/downloads). PharmGKB is updated on a monthly basis. In this import we include the "Variant, Gene and Drug Relationship Data" in the `relationships.zip` file. We also include all of the Primary Data: `genes.zip`, `drugs.zip`, `chemicals.zip`, `variants.zip`, and `phenotypes.zip`.

### Database Overview

This dataset brings in various PharmGKB annotated biological entities including:

- Genes
- Drugs
- ChemicalCompounds
- GeneticVariants
- Diseases (phenotypes)
- MeSHDescriptors (phenotypes)

<br> </br>
These entities, in turn, contain mappings to other databases including but not limited to NCBI, HGNC, Ensembl, HMDB, KEGG, PubChem, UMLS, DrugBank, ChemSpider,and MeSH. In addition, this dataset brings in the interactions between the entities, including:

- ChemicalCompoundChemicalCompoundAssociations
- ChemicalCompoundGeneAssociations
- ChemicalCompoundGeneticVariantAssociations
- GeneGeneAssociations
- GeneGeneticVariantAssociations
- GeneticVariantGeneticVariantAssociations
- DiseaseDiseaseAssociations
- DiseaseGeneAssocations
- DiseaseGeneticVariantAssocations

In this import we will process the following files:

* Primary Data
  * `chemicals.tsv`
  * `drugs.tsv`
  * `genes.tsv`
  * `phenotypes.tsv`
  * `variants.tsv`
* Variant, Gene and Drug Relationship Data
  * `relationships.tsv`

### Schema Overview

#### New Schema

##### Classes
* ChemicalCompoundChemicalCompoundAssociation
    * Thing -> BiomedicalEntity -> MedicalEntity -> Substance -> ChemicalSubstance -> ChemicalCompound -> ChemicalCompoundChemicalCompoundAssociation
* ChemicalCompoundGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> MedicalEntity -> Substance -> ChemicalSubstance -> ChemicalCompound -> ChemicalCompoundGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation -> ChemicalCompoundGeneticVariantAssociation
* DiseaseDiseaseAssociation
    * Thing -> BiomedicalEntity -> Disease -> DiseaseAssociation -> DiseaseDiseaseAssociation
* DiseaseGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> Disease -> DiseaseAssociation -> DiseaseGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation > DiseaseGeneticVariantAssociation
* GeneGeneAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation -> GeneGeneAssociation
* GeneGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation -> GeneGeneticVariantAssociation
* GeneticVariantGeneticVariantAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation -> GeneticVariantGeneticVariantAssociation
* GenomicCoordinates
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GenomicCoordinates

##### Properties
* BiomedicalEntity
    * clinicalAnnotationCount
    * clinicalAnnotationCountLevel1_2
    * clinicalGuidelineAnnotationCount
    * drugLabelAnnotationCount
    * geneticVariantAnnotationCount 
* ChemicalCompound
    * drugType
    * medicalDictionaryForRegulatoryActivitiesId
    * metabolicPathwayCount
    * rxConceptUniqueId
    * pkgbTags
    * topClinicalAnnotationLevel
    * veryImportantPharmacogeneCount
* Drug
    * canadianDrugsProductDatabaseDrugIdNumber
    * dailyMedSetId
    * dosageGuideline
    * dosageGuidelineSource
    * drugBrandMixture
    * drugGenericName
    * drugHasPrescribingInfo
    * drugHasRxAnnotation
    * drugLabelHasDosingInformation
    * drugTradeName
    * fdaTopPharmacogeneticLevel
    * nationalClinicalTrialNumber
    * nationalDrugFileReferenceTerminologyCode
    * pharmacogeneticAssociation
    * topCpicLevel
    * topPharmacogeneticLevel
* Gene
    * hasCpicDosingGuideline
    * hasGenomicCoordinates
    * hasGeneticVariantAnnotation
    * isVeryImportantPharmacogene
* GeneticAssociation
    * variantID
* GenomeAnnotation
    * chrom
    * chromStart
    * chromEnd
  * PharmGkbClinicalLevelEnum
      * pharmGkbStandardScoringRange
      * pharmGkbRareVariantScoringRange 

##### Enumerations
* CPICLevelEnum
    * CPICLevelA
    * CPICLevelA_B
    * CPICLevelB
    * CPICLevelB_C
    * CPICLevelC
    * CPICLevelC_D
    * CPICLevelD
* DrugTypeEnum
    * DrugTypeBiologicalIntermediate
    * DrugTypeIon
    * DrugTypeMetabolite
    * DrugTypeProdrug
    * DrugTypeSmallMolecule
    * DrugTypeUnknown 
* DosageGuidelineSourceEnum
    * DosageGuidelineSourceAmericanCollegeOfRheumatology
    * DosageGuidelineSourceAustralasianAntifungalGuidelinesSteeringCommittee
    * DosageGuidelineSourceCysticFibrosisFoundation
    * DosageGuidelineSourceClinicalPharmacogenomicsImplementationConsortium
    * DosageGuidelineSourceCanadianPharmacogenomicsNetworkForDrugSafety
    * DosageGuidelineSourceDutchPharmacogeneticsWorkingGroup
    * DosageGuidelineSourceFrenchNationalNetworkOfPharmacogenetics
    * DosageGuidelineSourceCpicNoRecommendation
    * DosageGuidelineSourceSeffSeom
* PGxLevelEnum
    * PGxLevelTestingRequired
    * PGxLevelTestingRecommended
    * PGxLevelActionablePGx
    * PGxLevelInformativePGx
* PharmacogeneticAssociationEnum
    * PharmacogeneticAssociationParmacokineticOnly
    * PharmacogeneticAssociationPotentialSafetyImpact
    * PharmacogeneticAssociationTherapeuticManagementRecommended
* PharmGkbClinicalLevelEnum
    *  PharmGkbClinicalLevelOneA
    *  PharmGkbClinicalLevelOneB
    *  PharmGkbClinicalLevelTwoA
    *  PharmGkbClinicalLevelTwoB
    *  PharmGkbClinicalLevelThree
    *  PharmGkbClinicalLevelFour

#### dcid Generation

##### ChemicalCompounds and Drugs

The dcids were generated for ChemicalCompounds and Drug nodes by adding the prefix 'chem/CID' to the PubChem compound identifier for that chemical (e.g. chem/CID903). In cases in which no PubChem compound was provided then the name of the chemical was converted into pascal case and the prefix 'chem' was added (e.g. chem/DoxorubicinSemiquinoneRadical). The PubChem compound identifiers were found in two columns: 'PubChem Compound Identifiers' and 'Cross References'. In cases in which no value was detected in the 'ATC Identifiers' column it was filled in from the 'Cross References' column if it was present there as a <database>:<ID> pair. The PubChem Chemical Compound identifiers were extracted from the 'Cross References' column, which stored a ',' seperated list of <database>:<ID> pairs (e.g. ChEBI:CHEBI:175132, HMDB:HMDB13884, PubChem Compound:101987375). Each database was expanded into its own column with the ID as the values.

##### Genes and GenomicCoordinates

Dcids for Genes were generated by using the 'Symbol' column, which contained the gene symbols. The prefix 'bio/' was added to the gene symbol to generate the Gene dcids (e.g. bio/TP53). GenomicCoordinate nodes were generated in the following format: bio/<genome_assembly>_<gene_symbol>_coordinates (e.g. bio/GRCh38_A1BG_coordinates). For each gene the genomic coordinates in GRCh37 and GRCh38 genome assemblies, which were generated from the 'Chromosome', 'Chromosomal Start - GRCh37', 'Chromosomal Stop - GRCh37', 'Chromosomal Start - GRCh38', and 'Chromosomal Stop - GRCh38' columns.

##### GeneticVariants and Genes

The dcid for GeneticVariants was generated by adding the prefix 'bio/' to the 'Variant Name' file, which stored the rsID for the genetic variant (e.g. bio/rs1000002). PharmGKB also provides genes with which genetic variants are associated. To generate the dcid for the associated Genes the prefix 'bio/' was added to the 'Gene Symbols' (e.g. bio/TP53). PLease note that '@' is an illegal character for dcids. Therefore any occurance of '@' in a gene symbol was replaced with '_Cluster' when generating the dcid. For example, the dcid for 'HOXD@' is 'bio/HOXD_Cluster'.

##### Phenotypes: MeSHDescriptors, MeSHSupplementaryConceptRecordss, and MeSHQualifiers

The dcid for phenotypes was generated using the MeSH descriptor (vast majority), MeSH supplementary concept record (a few), or MeSH qualifier associated with each phenotype. This information was stored in the 'External Vocabulary' file in a ',' seperated list of <database>:<Identifier>(<name>) (e.g. MeSH:D054868(Jacobsen Distal 11q Deletion Syndrome), SnoMedCT:4325000(11q partial monosomy syndrome), UMLS:C0795841(C0795841), NDFRT:N0000181176(Jacobsen Distal 11q Deletion Syndrome [Disease/Finding])). In cases in which a MeSH identifier was present the dcid was generated by adding the 'bio/' prefix (e.g. bio/D054868). MeSHDescriptors, which are indicated by the identifier starting with a 'D' (e.g. D054868) were then saved to 'phenotypes.csv'. The MeSHSupplementaryConceptRecordss, which are indicated by the identifier starting with a 'C' (e.g. C536109) and were saved to 'phenotypes_mesh_supplementary_concept_record.csv'. The MeSHQualifier, which are indicated by the identifier starting with a 'Q' (e.g Q000601) and were saved to 'phenotypes_mesh_qualifier.csv'. The vast majority of phenotypes were MeShDescriptors, only a few were associated with a MeSHSupplementaryConceptRecord or MeSHQualifier. Phenotypes that were not associated with a MeSH identifier were dropped and not included in the import.

##### Associations

The dcid for all association types were generated by <prefix>/<dcid_of_entity_1_minus_prefix>_<dcid_of_entity_2_minus_prefix>. Which was entity 1 vs entity 2 is dictated by the node type name. For example, for ChemicalCompoundGeneAssociation the ChemicalCompound (chem/CID33) would be entity 1 and Gene (bio/ALDH1A1) would be entity 2 (e.g. chem/CID33_ALDH1A1). In cases in which the association is between two entities of the same type (e.g. ChemicalCompoundChemicalCompoundAssociation) then the order of the entities in the dcids is alphabetically listed (e.g. chem/CID3121_CID64778). The prefix 'chem/' is used for the ChemicalCompoundChemicalCompoundAssociations, ChemicalCompoundGeneAssociations, and ChemicalCompoundGeneticVariantAssociations. The prefix 'bio/' was used for the DiseaseDiseaseAssociations, DiseaseGeneAssociations, DiseaseGeneticVariantAssociations, GeneGeneAssociations, GeneGeneticVariantAssociations, and GeneticVariantGeneticVariantAssociations.

The dcids for chemicals were extracted by mapping the PharmGKB to corresponding dcid using the ['chemicals_pharmgkbId_to_dcid.csv'](mapping_files/chemicals_pharmgkbId_to_dcid.csv) and ['drugs_pharmgkbId_to_dcid.csv'](mapping_files/drugs_pharmgkbId_to_dcid.csv). Diseases were mapped to MeSHDescriptor nodes by matching on name using the Data Commons API. In cases, where no match was found these were manually annotated and recorded in the ['diseases_pharmgkbId_to_dcid.csv'](mapping_files/diseases_pharmgkbId_to_dcid.csv) mapping file. For Genes, the dcid was generated using the name column, which stores the gene symbol. For variants, the name was used to generate the dcid in cases in which the rsID was present. When the variant recorded was too generarl to be attributed to a specific variant (e.g. 'CYB5R3 deficiency'), then these relationships were dropped and not included in the generated CSV files.

#### Edges

##### ChemicalCompounds and Drugs

Links were established between ChemicalCompound and Drug nodes and corresponding AnatomicalTherapeuticChemicalCode, MeSHConcept, and MeSHDescriptor nodes. ATC identifiers were recorded in two columns: 'ATC Identifiers' and 'External Vocabulary'. In cases in which no value was detected in the 'ATC Identifiers' column it was filled in from the 'External Vocabulary' column if it was present there as a <database>:<ID> pair. Links to these nodes were achieved by using the 'External Vocabulary' column, which was a ',' seperated list of <database>:<ID> pairs (e.g. ATC:A14AA07, MeSH:C033625, MeSH:C452866). Each database was expanded into its own column with the ID as the values. For ATC, this was converted to the corresponding dcid for AnatomicalTherapeuticChemicalCode nodes by adding the prefix 'chem/' to the code (e.g. chem/A14AA07). These dcids were stored as values for property 'atcCode'. For MeSH, thd prefix 'bio/' was added (e.g. bio/C033625). Then this column was split into two columns with one representing the MeSHConcept dcids - indicated by dcids beginning with 'bio/C' - and the other representing MeSHDescriptor dcids - indicated by dcids beginning with 'bio/D'. The dcids for corresponding MeSHConcept and MeSHDescriptor nodes were stored as values of property 'medicalSubjectHeadingID'.

##### Genes

Genes were linked to GenomicCoordinate nodes using the property 'hasGenomicCoordinates'. 

##### GeneticVariants

GeneticVariants were linked to Gene nodes using the property 'geneSymbol'.

##### Associations

For all association type nodes, they contain two links back to the corresponding entities participating in the associations. These are stored in the 'compoundID', 'diseaseID', 'geneID', and 'geneticVariantID', whichever one is appropriate. ChemicalCompounds and Drugs are linked to corresponding AnatomicalTherapeuticChemicalCodes, MeSHConcept, and MeSHDescriptor nodes.

### Notes and Caveats

PharmGKB has its own identifier - PharmGKB ID - that distinguishes each entity in its database. Therefore, as part of the import process we had to map chemicals, drugs, diseases, genes, genetic variants, and phenotypes to existing nodes in the graph. For chemicals and drugs this was done by using the corresponding PubChem Compound Identifier (CID), which is the preferred dcid method for these entities in Data Commons. In cases in which the chemical or drug was too general to have a specific CID (e.g. 'estrogens') then the name was used to generate the dcid. Mapping files between chemical and drugs PharmGKB IDs and the dcids used to represent this data were generated as part of processing the primary data: [`chemicals_pharmgkbId_to_dcid.csv`](mapping_files/chemicals_pharmgkbId_to_dcid.csv) and [`drugs_pharmgkbId_to_dcid.csv`](mapping_files/drugs_pharmgkbId_to_dcid.csv). These files were used to generate the chemical compound association dcids and the edges to the corresponding ChemicalCompound and Drug nodes as part of the relationships data import. Diseases were mapped to existing MeSHDescriptor nodes by matching on names of exisiting MeSHDescrptor nodes in the graph using the Data Commons API. In cases, in which no match was found using the API, these cases were manually mapped the PharmGKBId to the MeSHDescriptor dcid using the provided disease name. These mappings are represented in the [`diseases_pharmgkbId_to_dcid.csv`](mapping_files/diseases_pharmgkbId_to_dcid.csv). This information was used to generate the disease association dcids and the edges to MeSHDescriptor nodes. Phenotypes were provided with the corresponding MeSH Descriptor ID or MeSH Concept, which was used to map them respectively to existing MeSHDescriptor or MeSHConcept nodes in the graph. Phenotypes that did not have a MeSH ID were not included in the import. PharmGKB provided the gene symbol for all genes, so we were able to successfully map this data to existing data commons Gene nodes. Finally, for genetic variants we used the rsIDs, which were represented as the name to map them to existing GeneticVariant nodes. For the primary data all names were rsIDs. However, for the variants in the relationship file, sometimes the name for the variant participating in the relationship was not attributed to a single variant (e.g. 'CYB5R3 deficiency'). In these cases these variant relationships were excluded in the import.

For drugs and chemicals the PharmGKB database condensed all cross-references in one column. As part of the cleaning this column was exploded so that each database was mapped to a distinct property represented as it's own column. Also, we did not include the genomic location of the genetic variants provided by PharmGKB in this import as it was not in a format that is easily parsed into the geneomic assembly, chromosome, and position of the variant needed to generate a GenomicPosition node. Plus, this information is already available in the graph from NCBI dbSNP. In addition, the relationships data contains information on haplotypes. As haplotypes are not represented in the Data Commons graph these relationships were not included in the important. Furthermore, although all relationship types are represented into a single input file as part of cleaning up this file we expanded this into nine cleaned csv output files with each file representing each type of unique association. This is necessary to map the data appropriately to nodes and properties in the corresponding tMCF files.

### License

PharmGKB is under a Creative Commons Attribution-ShareAlike 4.0 International License. More information on that can be viewed [here](https://www.pharmgkb.org/page/dataUsagePolicy).
More information about the license can be viewed [here](https://creativecommons.org/licenses/by-sa/4.0/).

###  Dataset Documentation and Releavant Links

[PharmGKB](https://www.pharmgkb.org/) is partnered with CPIC, PharmVar, PharmCat, PGRN, ClinGen and Global Core Biodata Resource. Data from PharmGKB can be downloaded [here](https://www.pharmgkb.org/downloads). In addition to downloading the data directly, PharmGKB has their own [REST API](https://api.pharmgkb.org/swagger/). Documentation for PharmGKB can be found [here](https://www.pharmgkb.org/whatIsPharmgkb). Additional updates are released on their [blog](https://blog.clinpgx.org/).

To cite PharmGKB please use the following publications:
M. Whirl-Carrillo<sup>1</sup>, R. Huddart<sup>1</sup>, L. Gong, K. Sangkuhl, C.F. Thorn, R. Whaley and T.E. Klein. ["An evidence-based framework for evaluating pharmacogenomics knowledge for personalized medicine"](https://pubmed.ncbi.nlm.nih.gov/34216021/). *Clinical Pharmacology & Therapeutics* (2021) Sep;110(3):563-572.

<sup>1</sup>co-first authors

PMID: 34216021
PMCID: PMC8457105
DOI: 10.1002/cpt.2350

M. Whirl-Carrillo, E.M. McDonagh, J.M. Hebert, L. Gong, K. Sangkuhl, C.F. Thorn, R.B. Altman and T.E. Klein. ["Pharmacogenomics knowledge for personalized medicine"](https://pubmed.ncbi.nlm.nih.gov/22992668/). *Clinical Pharmacology & Therapeutics* (2012) Oct;92(4):414-7.

PMID: 22992668
PMCID: PMC3660037
DOI: 10.1038/clpt.2012.96

Additional information regarding citing PharmGKB can be found [here](https://www.pharmgkb.org/page/citingPharmgkb).


## About the Import

### Artifacts

#### Bash Scripts

- [download.sh](scripts/download.sh) downloads the most recent release of Primary Data and relationships data from PharmGKB.
- [run.sh](scripts/run.sh) converts data into formatted CSVs for import of data using files from download location.
- [tests.sh](scripts/tests.sh) runs standard tests to check for proper formatting of CSV files.

#### Python Scripts

- ['format_chemicals.py'](scripts/format_chemicals.py) formats the chemicals into a CSV file for import.
- ['format_drugs.py'](scripts/format_drugs.py) formats the drugs into a CSV file for import.
- ['format_genes.py'](scripts/format_genes.py) formats the genes into a CSV file for import.
- ['format_phenotypes.py'](scripts/format_phenotypes.py) formats the phenotypes (MeSHDescriptors) into a CSV file for import.
- ['format_variants.py'](scripts/format_variants.py) formats the genetic variants into a CSV file for import.
- ['format_relationships.py'](scripts/format_relationships.py) formats the relationship data into nine CSV file, one for each association type represented in the data, for import.

#### tMCFs

- ['chem_chem.tmcf'](tMCFs/chem_chem.tmcf) maps the `chem_chem.csv` output file from `format_relationship.py` to entities and properties for import.
- ['chem_gene.tmcf'](tMCFs/chem_gene.tmcf) maps the `chem_gene.csv` output file from `format_relationship.py` to entities and properties for import.
- ['chem_var.tmcf'](tMCFs/chem_var.tmcf) maps the `chem_var.csv` output file from `format_relationship.py` to entities and properties for import.
- ['chemicals.tmcf'](tMCFs/chemicals.tmcf) maps the `chemicals.csv` output file from `format_chemicals.py` to entities and properties for import.
- ['disease_disease.tmcf'](tMCFs/disease_disease.tmcf) maps the `disease_disease.csv` output file from `format_relationship.py` to entities and properties for import.
- ['disease_gene.tmcf'](tMCFs/disease_gene.tmcf) maps the `disease_gene.csv` output file from `format_relationship.py` to entities and properties for import.
- ['disease_var.tmcf'](tMCFs/disease_var.tmcf) maps the `disease_var.csv` output file from `format_relationship.py` to entities and properties for import.
- ['drugs.tmcf'](tMCFs/drugs.tmcf) maps the `drugs.csv` output file from `format_drugs.py` to entities and properties for import.
- ['gene_gene.tmcf'](tMCFs/gene_gene.tmcf) maps the `gene_gene.csv` output file from `format_relationship.py` to entities and properties for import.
- ['gene_var.tmcf'](tMCFs/gene_var.tmcf) maps the `gene_var.csv` output file from `format_relationship.py` to entities and properties for import.
- ['genes.tmcf'](tMCFs/genes.tmcf) maps the `genes.csv` output file from `format_genes.py` to entities and properties for import.
- ['phenotypes.tmcf'](tMCFs/phenotypes.tmcf) maps the `phenotypes.csv` output file from `format_phenotypes.py` to entities and properties for import - these are the cases were the entity is MeSHDescriptor.
- ['phenotypes_mesh_supplementary_concept_record.tmcf'](tMCFs/phenotypes_mesh_supplementary_concept_record.tmcf) maps the `phenotypes.csv` output file from `format_phenotypes.py` to entities and properties for import - these are the cases in which the entity is MeSHSupplementaryConceptRecords.
- ['phenotypes_mesh_qualifier.tmcf'](tMCFs/phenotypes_mesh_qualifier.tmcf) maps the `phenotypes.csv` output file from `format_phenotypes.py` to entities and properties for import - these are the cases in which the entity is MeSHQualifier.
- ['var_var.tmcf'](tMCFs/var_var.tmcf) maps the `var_var.csv` output file from `format_relationship.py` to entities and properties for import.
- ['variants.tmcf'](tMCFs/variants.tmcf) maps the `variants.csv` output file from `format_variants.py` to entities and properties for import.

#### Mapping Files
- ['chemicals_pharmgkbId_to_dcid.csv'](mapping_files/chemicals_pharmgkbId_to_dcid.csv) is a mapping file between PharmGKB IDs for chemicals to corresponding dcid; this is generated by `format_chemicals.py` and used as input for `format_relationships.py`.
- ['diseases_pharmgkbId_to_dcid.csv'](mapping_files/diseases_pharmgkbId_to_dcid.csv) is a manually annotaed mapping file for mapping PharmGKB Ids for diseases to MeSHDescriptor dcids in cases where the data commons API failed to return a match on the name; this is used for input for `format_relationships.py`.
- ['drugs_pharmgkbId_to_dcid.csv'](mapping_files/drugs_pharmgkbId_to_dcid.csv') is a mapping file between PharmGKB IDs for drugs to corresponding dcid; this is generated by `format_drugs.py` and used as input for `format_relationships.py`.

### Import Procedure

Download the most recent versions of NCBI Taxonomy data:

```bash
sh download.sh
```

Generate the enum schema MCF & formatted CSV:

```bash
sh run.sh
```


### Test 

The first step of `tests.sh` is to downloads Data Commons's java -jar import tool, storing it in a `tmp` directory. This assumes that the user has Java Runtime Environment (JRE) installed. This tool is described in Data Commons documentation of the [import pipeline](https://github.com/datacommonsorg/import/). The relases of the tool can be viewed [here](https://github.com/datacommonsorg/import/releases/). Here we download version `0.1-alpha.1k` and apply it to check our csv + tmcf import. It evaluates if all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other checks that issue fatal errors, errors, or warnings upon failing checks. Please note that empty tokens for some columns are expected as this reflects the original data. All referenced nodes are created as part of the same csv+tmcf import pair, therefore any Existence Missing Reference warnings can be ignored.

```bash
sh tests.sh
```
