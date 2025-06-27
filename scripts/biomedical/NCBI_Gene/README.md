# Importing NCBI Gene 

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Database Overview](#database-overview)
    3. [Schema Overview](#schema-overview)
       1. [New Schema](#new-schema)
       2. [dcid Generation](#dcid-generation)
       3. [enum Generation](#enum-generation)
       4. [Edges](#edges)
    4. [Notes and Caveats](#notes-and-caveats)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)
    3. [Test](#test)
    4. [Sample](#sample-data)


## About the Dataset

"[NCBI Gene](https://www.ncbi.nlm.nih.gov/gene) supplies gene-specific connections in the nexus of map, sequence, expression, structure, function, citation, and homology data. Unique identifiers are assigned to genes with defining sequences, genes with known map positions, and genes inferred from phenotypic information. These gene identifiers are used throughout NCBI's databases and tracked through updates of annotation. Gene includes genomes represented by [NCBI Reference Sequences](https://www.ncbi.nlm.nih.gov/refseq/) (or RefSeqs) and is integrated for indexing and query and retrieval from NCBI's Entrez and [E-Utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) systems. Gene comprises sequences from thousands of distinct taxonomic identifiers, ranging from viruses to bacteria to eukaryotes. It represents chromosomes, organelles, plasmids, viruses, transcripts, and millions of proteins."

### Download URL

NCBI Gene data can be downloaded from the National Center for Biotechnology Information (NCBI) using their FTP Site
1. [NCBI Gene](https://ftp.ncbi.nih.gov/gene/DATA/gene_info.gz). 
2. [gene2pubmed](https://ftp.ncbi.nih.gov/gene/DATA/gene2pubmed.gz).
3. [gene_neighbors](https://ftp.ncbi.nih.gov/gene/DATA/gene_neighbors.gz). 
4. [gene_orthologs](https://ftp.ncbi.nih.gov/gene/DATA/gene_orthologs.gz).
5. [gene_group](https://ftp.ncbi.nih.gov/gene/DATA/gene_group.gz). 
6. [mim2gene_medgen](https://ftp.ncbi.nih.gov/gene/DATA/mim2gene_medgen).
7. [gene2go](https://ftp.ncbi.nih.gov/gene/DATA/gene2go.gz). 
8. [gene2accession](https://ftp.ncbi.nih.gov/gene/DATA/gene2accession.gz).
9. [gene2ensembl](https://ftp.ncbi.nih.gov/gene/DATA/gene2ensembl.gz). 
10. [generifs_basic](https://ftp.ncbi.nih.gov/gene/GeneRIF/generifs_basic.gz).


### Database Overview

[NCBI Gene](https://www.ncbi.nlm.nih.gov/gene) is a comprehensive resource containing information about genes from a wide range of species. It serves as a central hub for gene-specific data, integrating information from various sources and providing links to other relevant resources. It includes:
* gene identification (e.g. official gene symbols, aliases, and cross-references to other databases)
* sequence information (e.g. genomic location and reference sequences (RefSeqs) for genomic DNA, transcripts, proteins, and mature peptides)
* functional information (gene function descriptions, associated pathways, related biological processes, orthologs, and related genes)
* phenotypic associations, (i.e. links to phenotypes and diseases associated with the gene)
* links to relevant scientific papers (i.e. PubMed IDs)

### Schema Overview

##### Classes

* Gene
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> Gene
* GeneMendelianInheritanceInManIdentifierAssociation
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneticAssociation -> GeneMendelianInheritanceInManIdentifierAssociation
* GeneOntologyTerm
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneOntologyTerm
* GeneReferenceIntoFunction
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GeneReferenceIntoFunction
* GenomicCoordinates
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GenomicCoordinates
* GenomicRegion
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> GenomicRegion
* MaturePeptide
    * Thing -> BiomedicalEntity -> MedicalEntity -> Substance -> ChemicalSubstance -> ChemicalCompound -> Protein -> MaturePeptide
* MendelianInheritanceInManEntity
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation ->  MendelianInheritanceInManEntity
* Protein
    * Thing -> BiomedicalEntity -> MedicalEntity -> Substance -> ChemicalSubstance -> ChemicalCompound -> Protein
* RnaTranscript
    * Thing -> BiomedicalEntity -> BiologicalEntity -> GenomeAnnotation -> RnaTranscript
* Taxon
  * Thing -> BiomedicalEntity -> BiologicalEntity -> Taxon
* UmlsConceptUniqueIdentifier
    * Thing -> BiomedicalEntity -> UmlsConceptUniqueIdentifier
  
##### Properties

* Gene
    * geneID
    * synonym
    * chrom
    * cytogeneticMapLocation
    * description
    * fullName
    * nomenclatureStatus
    * dateModified
    * refSeqFunctionElementFeatureAnnotation
    * geneSymbol
    * pubMedID
    * geneOrtholog
    * genePotentialReadthroughSibling
    * geneReadthroughChild
    * geneReadthroughParent
    * geneReadthroughSibling
    * geneRegionMember
    * geneRegionParent
    * relatedFunctionalGene
    * relatedPseudogene
    * ncbiSequenceGiNumber
    * refSeqGenomicAccessionVersion
    * ensemblGeneId
    and multiple database id's

* GeneMendelianInheritanceInManIdentifierAssociation
    * geneOmimRelationshipComment
    * geneOmimRelationshipSource
    * geneOmimRelationshipType
 
* GeneOntologyTerm
    * geneID
    * geneGeneOntologyTermRelationshipQualifier
    * geneOntologyCategory
    * geneOntologyEvidenceCode
    * geneOntologyId
    * pubMedId 
 
* GeneReferenceIntoFunction
    * dateModified
    * geneID
    * geneReferenceIntoFunction
    * pubMedID

* GenomicCoordinates
    * chrom
    * chromEnd
    * chromStart
    * inGenomeAssembly
    * strandOrientation
 
 * GenomicRegion
    * encodesGene
    * hasGenomicCoordinates
    * ncbiSequenceGiNumber
    * refSeqGenomicAccessionVersion
 
* MaturePeptide
    * ncbiMaturePeptideGiNumber
    * maturedFromProtein
    * refSeqMaturePeptideAccession
    * transcribedFromGene
    * translatedFromRna
 
* MendelianInheritanceInManEntity
    * umlsConceptUniqueID
    * onlineMendelianInheritanceInManID

* Protein
    * ncbiProteinGiNumber
    * refSeqProteinAccession
    * transcribedFromGene
    * translatedFromRna
      
* RnaTranscript
    * ensemblProteinId
    * ensemblRnaId
    * ncbiRnaNucleotideGiNumber
    * refSeqRnaNucleotideAccession
    * transcribedFromGene

* Taxon
    * ncbiTaxId
 
* UmlsConceptUniqueIdentifier
    * umlsConceptUniqueID
  
##### Enumerations

 * GeneFeatureTypeEnum
 * GeneOntologyCategoryEnum
 * GOTermEvidenceCodeEnum
 * GOTermQualifierEnum
 * GeneOmimRelationshipCommentEnum
 * GeneOmimRelationshipSourceEnum
 * GeneOmimRelationshipTypeEnum
 * RefSeqStatusEnum
 
##### Enumeartions Generated By Script

* GeneFeatureTypeRegulatoryEnum
* GeneFeatureTypeMiscellaneousEnum
* GeneFeatureTypeMiscellaneousRecombinationEnum

#### dcid Generation

* **Gene:** The data for each entry in NCBI Gene was stored as a Gene entity. The dcid for these entities was generated by adding the prefix 'bio/' to the gene symbol for *Homo sapiens* (i.e. when NCBI TaxID is 9606) genes only (e.g. bio/TP53). In cases in which there is an '@' in the human gene symbol replace it with '_Cluster' (e.g. HOXA@ is bio/HOXA_Cluster). For all other species, the dcid for genes is generated by adding the prefix 'bio/ncbi_' to the NCBI Gene ID. For example, the dcid for Trp53 in *Mus musculus* would be bio/ncbi_22059.
* **GeneMendelianInheritanceInManIdentifierAssociation:** The dcids for GeneMendelianInheritanceInManIdentifierAssociation are generated as the referenced gene dcid followed by "_omim_" and then the OMIM ID (e.g. bio/ncbi_216_omim_100640).
* **GeneReferenceIntoFunction:** The dcids for GeneReferenceIntoFunction nodes are generated by joining with an 'PubMed' flanked by '_'s the dcid of the referenced gene with the PubMed ID of the paper with the referenced function as in <Gene_dcid>_PubMed_<PubMed_ID> (e.g. bio/ncbi_715746_PubMed_19537945).
* **GenomicCoordinates:** The dcids for GenomicCoordinates of Genes are generated in the following format: 'bio/<chromosome_genomic_accession.version>_<start>_<stop>' where start and stop indicate the starting and stoping position for the Gene in the chromosome (or other genomic scaffold unit) of the specified genome assembly version. The dcids for GenomicCoordinates of RnaTranscripts are generated in the following format: 'bio/<genomic_nucleotide_accession.version>_<start>_<end>' where genomic_nucleotide_accession.version is the identifier for the matching RefSeq genomic nucleotide region and the start and end indicated the starting and stoping position for the Gene in the chromosome (e.g. bio/NC_001321.1_8388_9068).
* **GeneOntologyTerm:** The dcids for GeneOntologyTerm nodes are generated by adding the prefix 'bio/' to the Gene Ontology (GO) Term Accession replacing the ':' with '_' (e.g. bio/GO_0005105).
* **MaturePeptide:** The dcids for Proteins are generated by adding the prefix 'bio/' to the peptide_accession.version (e.g. bio/XM_064049720.1)
* **MendelianInheritanceInManEntity:** The dcids for MendelianInheritanceInManEntity nodes is generated by adding the prefix 'bio/omim_' to omim IDs (e.g. bio/omim_136350).
* **Protein:** The dcids for Proteins are generated by adding the prefix 'bio/' to the protein_accession.version (e.g. bio/AVV84537.1).
* **RnaTranscript**: The dcids for RnaTranscripts are generated by adding the prefix 'bio/' to the RNA_nucleotide_accession.version (e.g. bio/XM_062216974.1).
* **Taxon:** The dcid for Taxon nodes were generated by adding the prefix 'bio/' to the scientific name for the Taxon in which the scientific name was reperesented in pascal case and text (e.g. bio/HomoSapiens). In <> was connected by an '_' (e.g. scientifc name Bacteria <Bacteria> for ncbi tax id '2' was represented as bio/Bacteria_Bacteria).
* **UmlsConceptUniqueIdentifier:** The dcids for UmlsConceptUniqueIdentifiers are generated by adding the prefix 'bio/' to the UMLS CUIs (e.g. bio/C1563720). 

#### enum Generation

The schema for the GeneFeatureTypeRegulatoryEnum, GeneFeatureTypeMiscellaneousEnum and GeneFeatureTypeMiscellaneousRecombinationEnum are autogenerated by `format_ncbi_gene.py`.

A sample auto generated schema file saves at [ncbi_gene_schema_enum.mcf](/scripts/biomedical/NCBI_Gene/test_data/sample_enum/ncbi_gene_schema_enum.mcf) for reference.

#### Edges

Links were established between the entity classes included in this import. In the table below we document this info, alphabatizing on the entity entity type of the outgoing link. We include the entity type of the corresponding linked node along with the property whose value is the link.

| Entity Type of Outgoing Link | Entity Type of Ingoing Link | Property |
| -------- | ------- | ------- |
| Gene | Gene | geneOrtholog |
| Gene | Gene | genePotentialReadthroughSibling |
| Gene | Gene | geneReadthroughChild |
| Gene | Gene | geneReadthroughParent |
| Gene | Gene | geneReadthroughSibling |
| Gene | Gene | geneRegionMember |
| Gene | Gene | geneRegionParent |
| Gene | Gene | relatedFunctionalGene |
| Gene | Gene | relatedPseudogene |
| Gene | GenomicCoordinates | hasGenomicCoordinates |
| Gene | Taxon | ofSpecies |
| GeneOntologyTerm | Gene | geneID |
| GeneReferenceIntoFunction | Gene | geneID |
| GenomicRegion | Gene | encodeGene |
| GenomicRegion | GenomicCoordinates | hasGenomicCoordinates |
| MendelianInheritanceInManEntity | UmlsConceptUniqueIdentifier | umlsConceptUniqueID |
| MaturePeptide | Gene | transcribedFromGene |
| MaturePeptide | Protein | maturedFromProtein |
| MaturePeptide | RnaTranscript | translatedFrom |
| Protein | Gene | transcribedFromGene |
| Protein | RnaTranscript | translatedFrom |
| RnaTranscript | Gene | transcribedFromGene |

### Notes and Caveats
    
This import relies on the ncbi_tax_id_dcid_mapping file, which is generated as output from the Taxonomy import. This maps the NCBI Tax ID to the dcid representing the corresponding preexisting dcid in the graph. According to NCBI, Gene "most of the files in this path are re-calculated daily. Gene does not, however, compare previous and current data, so the date on the file may change without any change in content." This necessitates regular updates.

For the `gene_info.csv` file, the property 'dbXrefs' is a list of <database>:<ID> pairs split by a '|' delimeter. This property was represented in a seperate csv file where each database is a column and each row was an individual Gene. This was brought in as it's own CSV+tMCF file pair in addition to the CSV+tMCF file pair representing the remaining information in the `gene_info.csv` input file. Each database is represented as it's own property within the graph with the value being the ID, rather than listing all alternative IDs in a list in a single property like the input file. This allows for searching for a particular database ID in Biomedical Data Commons.

For the `gene_neighbors.csv` file we only ingested the genomic coordinate information for the Genes. We did not include information regarding neighboring genes. We dropped the following columns prior to ingestion: 'GeneIDs on left', 'distance to left', 'GeneIDs on right', 'distance to right', and 'overlapping GeneIDs'.

For the `gene_ortholog.csv` and the `gene_group.csv` files we represented the different relationships as their own distinct properties (e.g. 'geneOrtholog', 'genePotentialReadthroughSibling' 'geneReadthroughChild', etc.),  whose value is a link to the corresponding Gene. Since these values could be comma seprated lists in which multiple Genes could be assigned the same relationship to a single Gene, we directly referenced these nodes by converting these lists of Genes to the appropriately referenced dcid for the Gene in Biomedical Data Commons (e.g. dcid:bio/ncbi_112291008). All Gene nodes and thus their dcids used in the NCBI Gene import are initiated by ingesting the `gene_info.csv` file, so we are guarenteed their existence in the graph. An additional check for the existence of these referenced genes is made in the import script when converting the input of the NCBI Gene ID to the corresponding Gene dcid.

The `gene2accession.csv` file contained paired pieces of information (the accession.version and GI) on the following related entity types Genomic Nucleotide (i.e. GenomicRegion), RNA Nucleotide (i.e. RnaTranscript), Protein (Protein), and Mature Peptide (i.e. MaturePeptide). The information for each of these distict, but related entity types may or may not be available for each Gene in the `gene2accession.csv` file. To maintain the specificity of the information and links between each of the related entity types regardless of the presence or absence of information on those entities for any given Gene, links were made between all potential pairs of related entity types: Gene, GenomicRegion, RnaTranscript, Protein, and MaturePeptide. The nature of these links are described in the [Edges](#edges) subsection.

### License

This data is from an NIH National Library of Medicine (NLM) genome unrestricted-access data repository and made accessible under the [NIH Genomic Data Sharing (GDS) Policy](https://osp.od.nih.gov/scientific-sharing/genomic-data-sharing/) and the [NLM Accessibility policy](https://www.nlm.nih.gov/accessibility.html). Additional information on "NCBI Website and Data Usage Policies" can be found [here](https://www.ncbi.nlm.nih.gov/home/about/policies/).

### Dataset Documentation and Relevant Links

The database original documentation is accessible on [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/). NCBI Gene datasets can be accessed using [FTP Download](https://ftp.ncbi.nlm.nih.gov/gene/).

## About the import

### Artifacts

#### Scripts

##### Bash Scripts

- [download.sh](download.sh) downloads the most recent release of the NCBI Gene data.
- [run.sh](run.sh) it divides large files into smaller shards, generates a cleaned CSV output, and creates an enum schema MCF.
- [tests.sh](tests.sh) runs standard tests on CSV + tMCF pairs to check for proper formatting.

##### Python Scripts

- [format_ncbi_gene.py](scripts/format_ncbi_gene.py) creates the Gene schema enum MCF and formatted CSV files.
- [format_ncbi_taxonomy_test.py](scripts/format_ncbi_gene_test.py) unittest script to test standard test cases on gene enum MCF & cleaned output CSV.

#### tMCFs
[ncbi_gene_gene.tmcf](tMCFs/ncbi_gene_gene.tmcf)
[ncbi_gene_gene_db.tmcf](tMCFs/ncbi_gene_gene_db.tmcf) 
[ncbi_gene_ensembl.tmcf](tMCFs/ncbi_gene_ensembl.tmcf) 
[ncbi_gene_gene_group](tMCFs/ncbi_gene_gene_group.tmcf) 
[ncbi_gene_gene_rif.tmcf](tMCFs/ncbi_gene_gene_rif.tmcf) 
[ncbi_gene_genomic_coordinates.tmcf](tMCFs/ncbi_gene_genomic_coordinates.tmcf) 
[ncbi_gene_go_terms.tmcf](tMCFs/ncbi_gene_go_terms.tmcf) 
[ncbi_gene_ortholog.tmcf](tMCFs/ncbi_gene_ortholog.tmcf) 
[ncbi_gene_phenotype_associations.tmcf](tMCFs/ncbi_gene_phenotype_associations.tmcf) 
[ncbi_gene_pubmed.tmcf](tMCFs/ncbi_gene_pubmed.tmcf) 
[ncbi_gene_rna_transcript.tmcf](tMCFs/ncbi_gene_rna_transcript.tmcf)

### Import Procedure

Download the most recent versions of NCBI Gene data:

```bash
sh download.sh
```

Generate the enum schema MCF & formatted CSV:

```bash
sh run.sh
```

### Tests

The first step of `tests.sh` is to downloads Data Commons's java -jar import tool, storing it in a `tmp` directory. This assumes that the user has Java Runtime Environment (JRE) installed. This tool is described in Data Commons documentation of the [import pipeline](https://github.com/datacommonsorg/import/). The relases of the tool can be viewed [here](https://github.com/datacommonsorg/import/releases/). Here we download version `0.1-alpha.1k` and apply it to check our csv + tmcf import. It evaluates if all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other checks that issue fatal errors, errors, or warnings upon failing checks. Please note that empty tokens for some columns are expected as this reflects the original data. The imports create the Virus nodes that are then referenced within this import. This resolves any concern about missing reference warnings concerning these node types by the test.

To run tests:

```bash
sh tests.sh
```

This will generate an output file for the results of the tests on each csv + tmcf pair

### Sample Data

This sample [dataset](/scripts/biomedical/NCBI_Gene/test_data/) is a representative subset of the larger dataset. It was selected using stratified sampling to ensure that it covers most of the of scenarios in the data cleaning functionality This can be used for testing purpose.

The sample input and output data are located at the following links:

Input data: [input_link](test_data/input)
Output data: [output_link](test_data/expected_output)
