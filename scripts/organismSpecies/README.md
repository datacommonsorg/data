# Importing the UniProt’ Controlled Vocabulary of Species into Data Commons 

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

Data is available for downloading at [UniProt Species Download](https://www.uniprot.org/docs/speclist).
 
### Overview

As shown on [UniProt Controlled Vocabulary help page](https://www.uniprot.org/help/controlled_vocabulary): “The Controlled vocabulary of species contains two sublists: the Real organism codes, which are used in both UniProtKB/Swiss-Prot and UniProtKB/TrEMBL and which correspond to a specific and specified organism; the Virtual organism codes that regroup organisms at a certain taxonomic level. They generally correspond to a 'pool' of organisms and are used only in UniProtKB/TrEMBL.”

We imported this species dataset and created [Species](https://datacommons.org/browser/Species) class in Data Commons. We imported 26423 Species instances in total. The [Protein](https://datacommons.org/browser/Protein) class and [Gene](https://datacommons.org/browser/Gene) class link to [Species](https://datacommons.org/browser/Species) class through the property [ofSpecies](https://datacommons.org/browser/ofSpecies) in Data Commons.

### Notes and Caveats

There are eight species in Data Commons already, and they are 'HomoSapiens', 'CaenorhabditisElegans', 'DanioRerio', 'DrosophilaMelanogaster', 'GallusGallus', 'MusMusculus', 'SaccharomycesCerevisiae', 'XenopusLaevis'. During the importing, we kept the DCID of these eight species to remain the existing links in Data Commons.

### License

The dataset is available under [(CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license as shown by the [UniProt License and Disclaimer](https://www.uniprot.org/help/license). 

### Dataset Documentation and Relevant Links

- Dataset website: [UniProt Species Taxonomy Results Page](https://www.uniprot.org/taxonomy/)
- Dataset explannation: [UniProt Controlled Vocabulary help page](https://www.uniprot.org/help/controlled_vocabulary)

## About the import

### Artifacts

#### Scripts 

[parse_species.py](https://github.com/datacommonsorg/data/blob/master/scripts/organismSpecies/parse_species.py) 

[parse_species_test.py](https://github.com/datacommonsorg/data/blob/master/scripts/organismSpecies/parse_species_test.py) 


### Import Procedure

#### Processing Steps 


To generate 'newSpecies.mcf' which contains the data MCF of all species, run:

```bash
python3 parse_species.py -f speclist.txt --old_mcf Species.mcf --output_mcf newSpecies.mcf
```

'Species.mcf' file contains the eight old species instances.

To test the script, run:

```bash
python3 parse_species_test.py
```
