
# Importing Master Species List and Virus Metadata Resource from the International Committee on Taxonomy of Viruses (ICTV)

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-urls)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [dcid Generation](#dcid-generation)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)
    4. [Tests](#tests)


## About the Datasets
“The [International Committee on Taxonomy of Viruses (ICTV)](https://ictv.global/) authorizes and organizes the taxonomic classification of and the nomenclatures for viruses. The ICTV has developed a universal taxonomic scheme for viruses, and thus has the means to appropriately describe, name, and classify every virus that affects living organisms. The members of the International Committee on Taxonomy of Viruses are considered expert virologists. The ICTV was formed from and is governed by the Virology Division of the International Union of Microbiological Societies. Detailed work, such as delimiting the boundaries of species within a family, typically is performed by study groups of experts in the families.” Description from [Wikipedia](https://en.wikipedia.org/wiki/International_Committee_on_Taxonomy_of_Viruses).

The ICTV Master Species List is curated by virology experts, which have established over 100 international study groups, which organize discussions on emerging taxonomic issues in their field, oversee the submission of proposals for new taxonomy, and prepare or revise the relevant chapter(s) in ICTV reports. ICTV is open to submissions of proposals for taxonomic changes from an individual, however in practice proposals are usually submitted by members of the relevant study groups.

The ICTV chooses an exemplar virus for each species and the Virus Metadata Resource provides a list of these exemplars. An exemplar virus serves as an example of a well-characterized virus isolate of that species and includes the GenBank accession number for the genomic sequence of the isolate as well as the virus name, isolate designation, suggested abbreviation, genome composition, and host source.

### Download URLs

The release history and the most recent release of the Master Species List can be found [here](https://ictv.global/msl).

The release history and the most recent release of the Virus Metadata Resource can be found [here](https://ictv.global/vmr).


### Overview

This directory stores all scripts used to import data on viurses and virus isolates from the ICTV. This includes the master species list, which includes the full viral taxonomy (realm -> species) and information on the genomic composition and taxonomic history for all species. The import also includes the Virus Metadata Resource, which includes information regarding the exemplar isolates for each species selected by the ICTV and additional virus isolates within the ICTV dataset.


### Notes and Caveats
Viruses are not considered alive and are therefore not classified under “The Tree of Life”. They instead have their own taxonomic classification system described here. However, the viral classification system mirrors “The Tree of Life” by copying their Kingdom -> Phylum -> Class -> Order -> Family -> Genus -> Species hierarchical classes, while adding a level above called Domain and sublevels under each one. This similarity in naming can lead to confusion between the two classification systems. In particular, in datasets species of viruses may be included  without distinction alongside species of bacteria, archaea, or animals. To mitigate this potential confusion Viruses have their own distinct schema, which they do not share with non-viral biological entity.

Not all levels of the viral classification are currently in use. As of release 37, Subrealm, Subkingdom, and Subclass are not in use. These classifications are defined here in the schema in case they are used in future releases. In addition, for each species there is a classification defined for each of the main classes (Domain, Kingdom, Phylum, Class, Order, Family, Genus, and Species), however there are missing classifications for some or all of the subclasses (Subkingdom, Subphylum, Subclass, Suborder, SubFamily, and Subgenus). To account for this, references will be made to the parent of the next main class in addition to the parent subclass.

“The ICTV chooses an exemplar virus for each species and the VMR provides a list of these exemplars. An exemplar virus serves as an example of a well-characterized virus isolate of that species and includes the GenBank accession number for the genomic sequence of the isolate as well as the virus name, isolate designation, suggested abbreviation, genome composition, and host source.” Additional isolates for each species within the ICTV database are also noted.


### dcid Generation
A ‘bio/’ prefix was attached to all dcids in this import. Each line in each input file is considered its own unique Virus or VirusIsolate. In cases where there are multiple lines that generate the same dcid for a Virus, VirusIsolate, or VirusGenomeSegment then an error message is printed out stating the non-unique dcid generated for a given entity.

####Virus
Dcids were generated by converting the Virus’s species name to pascal case (i.e. bio/<Species>).

####VirusIsolate
Unique information regarding the VirusIsolate was added to the end of the Virus dcid to generate a unique VirusIsolate dcid. In the cases for which the isolate had a designation, then this was converted to pascal case and used as the dcid (i.e. bio/<Species><IsolateDesignation>). In cases where there was no isolate designation indicated then the GenBank Accession Number was used to generate the dcid if there was one unique one for that isolate (i.e. bio/<Species><GenBankAccession>). In cases in which there were multiple GenBank Accession numbers associated with a virus isolate, these were daisy chained with ‘_’s to create the dcid for the VirusIsolate (i.e. bio/<Species><GenBankAccession1>_<GenBankAccession2>). In the event both the isolate designation and the GenBank Accession for a VirusIsolate is missing then the word ‘Isolate’ was added to the pascal case name of the species to create the VirusIsolate dcid (i.e. bio/<Species>Isolate).

Note: This resulted in collisions for four VirusIsolates. These errors were recorded in the [format_virus_metadata_resource.log](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/logs/format_virus_metadata_resource.log) file.

####VirusGenomeSegment
The GenBank Accession number for a VirusGenomeSegment was tacked onto the corresponding VirusIsolate dcid to generate a unique VirusGenomeSegment dcid (i.e. <VirusIsolate_dcid><GenBankAccession>).

####Illegal Characters
Only ASCII characters are allowed to be used in dcids. Additionally, the following characters are illegal to be included in the dcid: :, ;, <space>, [, ], -, –, ‘, #. They were replaced in place with the following characters specified below:

| Illegal Character | Replacement Character |
| ----------------- | --------------------- |
| : | _ |
| ; | _ |
| <space>   |   |
| [ | ( |
| ] | ) |
| - | _ |
| – | _ |
| ‘ | _ |
| # |   |


### License

The data is published under the Creative Commons Attribution ShareAlike 4.0 International [(CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/).
 
### Dataset Documentation and Relevant Links

- Documentation can be found in one of the excel sheets in a downloaded dataset from ICTV.
- Taxonomy Browser User Interface: https://ictv.global/taxonomy

## About the import

### Artifacts

#### New Schema

Classes, properties, and enumerations that were added in this import to represent the data.

* Classes
    * Virus, VirusIsolate, VirusGenomeSegment
* Properties
    * Virus: proposalForLastChange, taxonHistoryURL, versionOfLastChange, virusGenomeComposition, virusHost, virusLastTaxonomicChange, virusSource, virusRealm, virusSubrealm, virusKingdom, virusSubkingdom, virusPhylum, virusSubphylum, virusClass, virusSubclass, virusOrder, virusSuborder, virusFamily, virusSubfamily, virusGenus, virusSubgenus, virusSpecies
    * VirusIsolate: genomeCoverage, isExemplarVirusIsolate, ofVirusSpecies, virusIsolateDesignation
    * VirusGenomeSegment: genomeSegmentOf
* Enumerations
    * GenomeCoverageEnum, VirusGenomeCompositionEnum, VirusHostEnum, VirusSourceEnum
* Enumerations Generated Via Script
    * VirusRealmEnum, VirusSubrealmEnum, VirusKingdomEnum, VirusSubkingdomEnum, VirusPhylumEnum, VirusSubphylumEnum, VirusClassEnum, VirusSubclassEnum, VirusOrderEnum, VirusSuborderEnum, VirusFamilyEnum, VirusSubfamilyEnum, VirusGenusEnum, VirusSubgenusEnum

#### Schema MCFs

- [ICTV_schema.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/ICTV_schema.mcf)
- [ICTV_schema_enum.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/ICTV_schema_enum.mcf)
- [ICTV_schema_taxonomic_ranking_enum.mcf](https://github.com/datacommonsorg/schema/blob/main/biomedical_schema/ICTV_schema_taxonomic_ranking_enum.mcf)

#### tMCFs

- [VirusMasterSpeciesList.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCFs/VirusMasterSpeciesList.tmcf)
- [VirusTaxonomy.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCFs/VirusTaxonomy.tmcf)
- [VirusGenomeSegmeng.tmcf](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/tMCFs/VirusGenomeSegment.tmcf)

#### Scripts 

- [download.sh](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/scripts/download.sh)
- [create_virus_taxonomic_ranking_enums.py](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/scripts/create_virus_taxonomic_ranking_enums.py)
- [format_virus_master_species_list.py](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/scripts/format_virus_master_species_list.py)
- [format_virus_metadata_resource.py](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/scripts/format_virus_metadata_resource.py)

#### Log Files

- [format_virus_metadata_resource.log](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/logs/format_virus_metadata_resource.log)

### Import Procedure

Download the most recent versions of the Master Species List and Virus Metadata Resource from ICTV by running:

```bash
sh download.sh
```

Generate the enummeration schema MCF, which represents virus taxonomic ranks by running:

```bash
python3 scripts/create_virus_taxonomic_ranking_enums.py import_files/ICTV_Master_Species_List_2021_v3.xlsx ICTV_schema_taxonomic_ranking_enum.mcf
```

Clean and format Master Species List as a CSV that matches the corresponding tMCF by running:

```bash
python3 scripts/format_virus_master_species_list.py input/ICTV_Master_Species_List.xlsx VirusSpecies.csv
```

Clean and format Virus Metadata Resource as a CSV that matches the corresponding tMCF by running:

```bash
python3 scripts/format_virus_metadata_resource.py input/ICTV_Virus_Metadata_Resource.xlsx VirusIsolates.csv VirusGenomeSegments.csv > format_virus_metadata_resource.log
```

### Tests

#### Dataset Specific Tests

To test the import to evaluate whether the data is formatted as expected or if changes were made in the formatting in the most recent release run the following commands to evaluate each cleaned csv individually.

VirusSpecies:
```bash
```

VirusIsolates:
```bash
```

VirusGenomeSegment:
```bash
```

#### Data Commons Import Tests

Please run all cleaned CSV + tMCF pairs through our lint test using our Data Commons import tool, which conducts general formatting tests.
