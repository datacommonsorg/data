## Importing Gene Ontology Data
Author: Padma Gundapaneni @padma-g

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-url)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [License](#license)
    5. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)

## About the Dataset

### Download URL
The data can be downloaded from https://www.ebi.ac.uk/QuickGO/annotations and http://current.geneontology.org/products/pages/downloads.html in the .gaf file format. The downloaded data is tab-separated.

### Overview
The Gene Ontology Annotation data comes from two sources:

    1. The [https://www.ebi.ac.uk/GOA/index](Gene Ontology Annotation Database) created by the European Bioinformatics Institute (EMBL-EBI)
    
    2. The [http://current.geneontology.org/products/pages/downloads.html](set of Gene Ontology Annotations) compiled by the Gene Ontology (GO) Consortium.

The GO Consortium’s [http://geneontology.org/docs/introduction-to-go-resource/](resource) “provides a computational representation of our current scientific knowledge about the functions of genes (or, more properly, the protein and non-coding RNA molecules produced by genes) from many different organisms, from humans to bacteria.”

EMBL-EBI’s [https://www.ebi.ac.uk/GOA/newto](GO annotation program) “aims to provide high-quality Gene Ontology (GO) annotations to proteins in the [https://www.uniprot.org/](UniProt) Knowledgebase (UniProtKB), RNA molecules from [http://rnacentral.org/](RNACentral) and protein complexes from the [https://www.ebi.ac.uk/complexportal/home](Complex Portal).” 

In this effort, we imported the gene ontology annotation data for the following species: Homo sapiens (human), Mus musculus (mouse), Drosophila melanogaster (fruit fly), Caenorhabditis elegans (roundworm), Saccharomyces cerevisiae (baker’s yeast), Danio rerio (zebrafish), Gallus gallus (chicken)

The CSVs for the annotations contain the following information:
    * DB, DBObjectID, DBObjectSymbol, Qualifier, GOID, DBReference, EvidenceCode, With/From, Aspect, DBObjectName, DBObjectSynonym, DBObjectType, Taxon, Date, AssignedBy

Relevant to this import are: 
* **DB**: Database from which annotated entity has been taken.
* **DBObjectID**: A unique identifier in the database for the item being annotated.
* **DBObjectSymbol**: A unique and valid symbol (gene name) that corresponds to the DB_Object_ID.
* **Qualifier**: Flags that modify the interpretation of an annotation.
* **GOID**: The GO identifier for the term attributed to the DB_Object_ID.
* **DBReference**: A single reference cited to support an annotation.
* **EvidenceCode**: One of the evidence codes supplied by the GO Consortium.
* **With/From**: Additional identifier(s) to support annotations using certain evidence codes.
* **Aspect**: One of the three ontologies, corresponding to the GO identifier applied. P (biological process), F (molecular function) or C (cellular component).
* **DBObjectName**: The full entity name, if available from the resource that supplies the object identifier.
* **Taxon**: Identifier for the species being annotated or the gene product being defined.
* **Date**: The date of the last annotation update in the format 'YYYYMMDD'.
* **AssignedBy**: Attribution for the source of the annotation.

### Notes and Caveats

DataCommons currently has genes linked to proteins for only the human species. It does not have genes linked to proteins for non-human species and these connections will be made in the future.

### License
The data is published by the European Bioinformatics Institute (EMBL-EBI) and the Gene Ontology Consortium.

#### References

* Ashburner et al. Gene ontology: tool for the unification of biology. Nat Genet. May 2000;25(1):25-9.
Huntley RP, Sawford T, Mutowo-Meullenet P, Shypitsyna A, Bonilla C, Martin MJ, O’Donovan C

* The GOA database: Gene Ontology annotation updates for 2015.
Nucleic Acids Res. 2015 Jan; 43:D1057-63.

* The Gene Ontology resource: enriching a GOld mine. Nucleic Acids Res. Jan 2021;49(D1):D325-D334.

### Dataset Documentation and Relevant Links
The dataset documentation is accessible on the GO Consortium’s website: http://geneontology.org/docs/go-annotation-file-gaf-format-2.2/ 

## About the Import

### Artifacts

#### Scripts
`generate_gene_symbols.py`

`parse_goa_file.py`

#### Files

`human_gene_to_uniprot.tab`

### Import Procedure

#### Processing Steps
To generate a file like `human_gene_to_uniprot.tab`, containing the gene symbol to UniProt pairings for a given species, run the following to extract all the unique gene symbols from an annotation file:

```bash
$python3 generate_gene_symbols.py goa_file_name.gaf species_name output_file.csv
```

Then, upload the file containing gene symbols entries to UniProt Retrieve/ID mapping to generate the UniProt pairings and save the resulting file as a tab-separated file. Here are further instructions on how to do the mapping.

The file with gene symbol and UniProt pairings will be used by `parse_goa_file.py`. To generate the final cleaned annotation file, run:

```bash
$python3 parse_goa_file.py goa_file_name.gaf species_name output_file.csv uniprot_pairings_file.tab
```
