
# PharmGKB Import: Drugs, Chemicals, Genes, and Relationships

Author: @calinc

## About the Dataset

### Download URL

The zip files for drugs, chemicals, genes, and relationships can be found at https://www.pharmgkb.org/downloads

### Overview

This dataset is being imported for the ingestion of Drug-Gene association information into the Data Commons knowledge graph.
Three files from PharmGKB will be ingested for this import
*  Relationships.tsv - contains information about different relationships between drugs, genes, diseases, genetic variants, etc. This import is interested ONLY in the gene-drug associations. Entities are mapped by their PharmGKB ID
*  Genes.tsv - contains information about genes and helps mapping pharmGKB IDs to dcids
*  Drugs.tsv - contains information about drugs and helps mapping pharmGKB IDs to dcids, types include:
  * Drug = A chemical substance used in the treatment, cure,prevention, or diagnosis of disease.
  * Drug Class = A drug class is a group of medications that may work in the same way, have a similar chemical structure, or are used to treat the same health condition.
  * Prodrug = A compound that must undergo chemical conversion by metabolic processes before becoming the pharmacologically active drug for which it is a prodrug.
* Chemicals.tsv - contains same information (column names) as Drugs.tsv, but for chemicals with types including:
  * Metabolite = Any intermediate or product resulting from metabolism.
  * Ion = An atomic or molecular particle having a net electric charge.
  * Biological Intermediate = An endogenous small molecule or ion.
  * Small Molecule = An electrically neutral entity consisting of more than one atom.
  * As well as the Drug, Drug Class, and Prodrug types

## Import Files

### Raw Data
- `chemicals.zip`, `drugs.zip`, `genes.zip`, and `relationships.zip` are automatically downloaded when running pharm.py.
- Each zipfile contains a `.tsv` file of the necessary data, along with a README, and License, Creation, and Version information files.

### MCF
- `pharmgkb.mcf` is generated.

### Py Files
- `pharm.py` downloads the raw data and write the mcf file
- `config.py` contains enum and property label dictionaries as well as template strings used in pharm.py. Review this file to see what data was ingested into Data Commons via this import.
- `tests.py` contains unit tests for pharm.py


### Notes
The `.csv` files found in `./conversion` are used to convert external ids such as PharmGKB IDs into dcids in order to match each drug to an existing node in Data Commons. For the drugs that the dcid could not be found, a new drug node was created with the PharmGKB ID as the dcid.

Only the rows of `relationships.tsv` that contain Chemical-Gene and Gene-Chemical associations were ingested in this import. The information in these rows were converted to ChemicalCompoundGeneAssociation type nodes for Data Commons. All other rows from `relationships.tsv` were ignored.

## Generating MCF
To download raw data and generate the output MCF `pharmgkb.mcf`, run

``` bash
$python3 pharm.py
```

To run the unit tests for pharm.py run:

```bash
$python3 tests.py
```
