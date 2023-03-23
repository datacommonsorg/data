
# Importing ontology dataset of molecular interaction from the European Bioinformatics Institute (EMBL-EBI)

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-urls)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [License](#license)
    5. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)
    3. [Tests](#tests)


## About the Dataset
“The [International Committee on Taxonomy of Viruses (ICTV)](https://ictv.global/) authorizes and organizes the taxonomic classification of and the nomenclatures for viruses. The ICTV has developed a universal taxonomic scheme for viruses, and thus has the means to appropriately describe, name, and classify every virus that affects living organisms. The members of the International Committee on Taxonomy of Viruses are considered expert virologists. The ICTV was formed from and is governed by the Virology Division of the International Union of Microbiological Societies. Detailed work, such as delimiting the boundaries of species within a family, typically is performed by study groups of experts in the families.” Description from [Wikipedia](https://en.wikipedia.org/wiki/International_Committee_on_Taxonomy_of_Viruses).

The ICTV Master Species List is curated by virology experts, which have established over 100 international study groups, which organize discussions on emerging taxonomic issues in their field, oversee the submission of proposals for new taxonomy, and prepare or revise the relevant chapter(s) in ICTV reports. ICTV is open to submissions of proposals for taxonomic changes from an individual, however in practice proposals are usually submitted by members of the relevant study groups.

### Download URLs

The release history and the most recent release of the Master Species List can be found [here](https://ictv.global/msl).

The release history and the most recent release of the Virus Metadata Resource can be found [here](https://ictv.global/vmr).


### Overview

This directory stores all scripts used to import data on viurses and virus isolates from the ICTV. This includes the master species list, which includes the full viral taxonomy (realm -> species) and information on the genomic composition and taxonomic history for all species. The import also includes the Virus Metadata Resource, which includes information regarding the exemplar isolates for each species selected by the ICTV and additional virus isolates within the ICTV dataset.


### Notes and Caveats



### License

The data is published under the Creative Commons Attribution ShareAlike 4.0 International [(CC BY-SA 4.0)] (https://creativecommons.org/licenses/by-sa/4.0/).
 
### Dataset Documentation and Relevant Links

- Documentation can be found in one of the excel sheets in a downloaded dataset from ICTV.
- Taxonomy Browser User Interface: https://ictv.global/taxonomy

## About the import

### Artifacts

#### New Classes

Virus, VirusIsolate, VirusGenomeSegment

#### New Properties

- Virus: proposalForLastChange, taxonHistoryURL, versionOfLastChange, virusGenomeComposition, virusHost, virusLastTaxonomicChange, virusSource, virusRealm, virusSubrealm, virusKingdom, virusSubkingdom, virusPhylum, virusSubphylum, virusClass, virusSubclass, virusOrder, virusSuborder, virusFamily, virusSubfamily, virusGenus, virusSubgenus, virusSpecies
- VirusIsolate: genomeCoverage, isExemplarVirusIsolate, ofVirusSpecies, virusIsolateDesignation
- VirusGenomeSegment: genomeSegmentOf

#### New Enumerations

GenomeCoverageEnum, VirusGenomeCompositionEnum, VirusHostEnum, VirusSourceEnum

#### Schema MCFs

[ICTV_schema.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/ICTV_schema.mcf)
[ICTV_schema_enum.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/ICTV_schema_enum.mcf)

#### tMCFs

- [VirusMasterSpeciesList.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCF/VirusMasterSpeciesList.tmcf)
- [VirusTaxonomy.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCF/VirusTaxonomy.tmcf)
- [VirusGenomeSegmeng.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCF/VirusGenomeSegment.tmcf)

#### Scripts 

- [download.sh](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/download.sh)
- [format_virus_master_species_list.py](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/format_virus_master_species_list.py)
- [format_virus_metadata_resource.py](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/format_virus_metadata_resource.py)

### Import Procedure

To download the most recent versions of the Master Species List and Virus Metadata Resource from ICTV run:

```bash
download.sh
```

To test the script, run:

```bash
```

### Tests

#### Dataset Specific Tests

To test the import to evaluate whether the data is formatted as expected or if changes were made in the formatting in the most recent release run the following commands to evaluate each cleaned csv individually.

VirusSpecies:
'''bash
'''

VirusIsolates:
'''bash
'''

VirusGenomeSegment:
'''bash
'''

#### Data Commons Import Tests

Please run all cleaned CSV + tMCF pairs through our Data Commons import tool to run general Data Commons formatting tests.
