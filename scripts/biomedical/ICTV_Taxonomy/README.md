
# Importing Master Species List and Virus Metadata Resource from the International Committee on Taxonomy of Viruses (ICTV)

## Table of Contents

1. [About the Dataset](#about-the-dataset)
    1. [Download URL](#download-urls)
    2. [Overview](#overview)
    3. [Notes and Caveats](#notes-and-caveats)
    4. [dcid Generation](#dcid-generation)
       1. [Virus](#virus)
       2. [VirusIsolate](#virusisolate)
       3. [VirusGenomeSegment](#virusgenomesegment)
       4. [Illegal Characters](#illegal-characters)
    5. [License](#license)
    6. [Dataset Documentation and Relevant Links](#dataset-documentation-and-relevant-links)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
       1. [New Schema](#new-schema)
       2. [Scripts](#scripts)
       3. [tMCFs](#tmcfs)
       4. [Log Files](#log-files)
    2. [Import Procedure](#import-procedure)
    3. [Tests](#tests)


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

#### Virus
Dcids were generated by converting the Virus’s species name to pascal case (i.e. bio/<Species>).

#### VirusIsolate
Unique information regarding the VirusIsolate was added to the end of the Virus dcid to generate a unique VirusIsolate dcid. In the cases for which the isolate had a designation, then this was converted to pascal case and used as the dcid (i.e. bio/<Species><IsolateDesignation>). In cases where there was no isolate designation indicated then the GenBank Accession Number was used to generate the dcid if there was one unique one for that isolate (i.e. bio/<Species><GenBankAccession>). In cases in which there were multiple GenBank Accession numbers associated with a virus isolate, these were daisy chained with ‘_’s to create the dcid for the VirusIsolate (i.e. bio/<Species><GenBankAccession1>_<GenBankAccession2>). In the event both the isolate designation and the GenBank Accession for a VirusIsolate is missing then the word ‘Isolate’ was added to the pascal case name of the species to create the VirusIsolate dcid (i.e. bio/<Species>Isolate).

Note: This resulted in collisions for four VirusIsolates. These errors were recorded in the [format_virus_metadata_resource.log](https://github.com/datacommonsorg/data/new/master/scripts/biomedical/ICTV_Taxonomy/logs/format_virus_metadata_resource.log) file.

#### VirusGenomeSegment
The GenBank Accession number for a VirusGenomeSegment was tacked onto the corresponding VirusIsolate dcid to generate a unique VirusGenomeSegment dcid (i.e. <VirusIsolate_dcid><GenBankAccession>).

#### Illegal Characters
Only ASCII characters are allowed to be used in dcids. Additionally, a number of characters that are illegal to include in the dcid were replaced in place with the following characters specified below:

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

#### Scripts 

##### Bash Scripts

- [download.sh](scripts/download.sh) downloads the most recent release of the ICTV Master Species List and Virus Metadata Resource.
- [run.sh](scripts/run.sh) creates new viral taxonomy enum and converts data into formatted CSV for import of data on viruses, virus isolates, and viral genome fragments into the knowledge graph.
- [tests.sh](scripts/tests.sh) runs standard tests on CSV + tMCF pairs to check for proper formatting.

##### Python Scripts

- [create_virus_taxonomic_ranking_enums.py](scripts/create_virus_taxonomic_ranking_enums.py) creates the viral taxonomy enum mcf file from the Virus Metadata Resource file.
- [format_virus_master_species_list.py](scripts/format_virus_master_species_list.py) parses the raw Master Species List xslx file into virus csv file.
- [format_virus_metadata_resource.py](scripts/format_virus_metadata_resource.py) parses the raw Virus Metadata Resource file into virus isolates and viral genome segements csv files.

#### tMCFs

- [VirusSpecies.tmcf](tMCFs/VirusSpecies.tmcf) contains the tmcf mapping to the csv of viruses.
- [VirusIsolates.tmcf](tMCFs/VirusIsolates.tmcf) contains the tmcf mapping to the csv of virus isolates.
- [VirusGenomeSegments.tmcf](tMCFs/VirusGenomeSegments.tmcf) contains the tmcf mapping to the csv of viral genome segments.

#### Log Files

- [format_virus_metadata_resource.log](logs/format_virus_metadata_resource.log) log file from script converting the Virus Metadata Resource into formatted CSV file.

### Import Procedure

Download the most recent versions of the Master Species List and Virus Metadata Resource from ICTV by running:

```bash
sh download.sh
```

Generate the enummeration schema MCF, which represents virus taxonomic ranks by running:

```bash
sh run.sh
```

### Tests

The first step of `tests.sh` is to downloads Data Commons's java -jar import tool, storing it in a `tmp` directory. This assumes that the user has Java Runtime Environment (JRE) installed. This tool is described in Data Commons documentation of the [import pipeline](https://github.com/datacommonsorg/import/). The relases of the tool can be viewed [here](https://github.com/datacommonsorg/import/releases/). Here we download version `0.1-alpha.1k` and apply it to check our csv + tmcf import. It evaluates if all schema used in the import is present in the graph, all referenced nodes are present in the graph, along with other checks that issue fatal errors, errors, or warnings upon failing checks. Please note that empty tokens for some columns are expected as this reflects the original data. The imports create the Virus nodes that are then refrenced within this import. This resolves any concern about missing reference warnings concerning these node types by the test.

To run tests:

```bash
sh tests.sh
```

This will generate an output file for the results of the tests on each csv + tmcf pair

