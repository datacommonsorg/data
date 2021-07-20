# Importing VMH Metabolome and Microbiome data

## Table of Contents

- [Importing VMH Metabolome and Microbiome data](#importing-vmh-metabolome-and-microbiome-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download URL](#download-url)
    - [Overview](#overview)
    - [Schema Overview](#schema-overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
  - [Examples](#examples)

## About the Dataset

### Download URL

The human metabolite and reaction data can be downloaded from the Virtual Metabolic Human database using their web [interface](https://www.vmh.life/#human/all).The gut microbiome data can be downloaded [here](https://www.vmh.life/#microbes/search). The data is in tab delimited format. The data is roughly in tab delimited format (see [Notes and Caveats](#notes-and-caveats) for additional information on formatting).

### Overview

This directory stores the scripts used to convert the datasets obtained from VHM into modified versions, for effective ingestion of data into the Data Commons knowledge graph.

The VHM database explicity connects human metabolism with genetics and human-associated microbial metabolism. It consists of five interconnected resources: `Human metabolism`, `Gut microbiome`, `Disease`, `Nutrition` and `ReconMaps`. More information on the database can be found on their official [website](https://www.vmh.life/#home) and [manuscript](https://academic.oup.com/nar/article/47/D1/D614/5146204).
For the knowledge graph, three files are imported:

- <u>recon-store-metabolites-1.tsv</u> : contains information on chemical properties of metabolites, and identifiers for various databases to query the metabolites. In order to generate dcids, the keggID for each metabolite was converted to the ChEMBL ID, using the [bioservices packages](https://bioservices.readthedocs.io/en/master/compound_tutorial.html). For the metabolites, with missing keggIDs, the chemical formulae were used to generate the dcids.
- <u>recon-store-reactions-1.tsv</u> : contains information on the chemical equations and formulae of metabolic reactions, biochemical subsytem where the reactions take place and identifiers for various databases, to query the reactions. The reaction and metabolite abbreviations were mapped to one another using the longest substring match and the dcid for longest matched metabolite was appended to the respective reaction column. In addition, for generation of reaction dcids, the humanGEMIDs were obtained for reactions, using the metaNetX IDs and [Human1 data](https://raw.githubusercontent.com/khoahoang1891999/Importing-Human1-data/main/data/reactions.tsv). For reactions with no metaNetX IDs, the chemical abbreviations were used are reactions dcids.
  In addition, this file was also used to generate a new file `subsystem.csv` which contains all the unique biochemical subsystems from the above reactions and the subsystem names were used to generate their corresponding dcids.ß
- <u>recon-store-microbes-1.tsv</u>: contains information on microbial taxonomic classification, phenotype, metrics about genes, reactions and metabolites linked to microbes and identifiers for various databases, to query the microbes. The datacommons was queried for pre-exisiting microbe dcids using the scientific name, and for the ones with no node on datacommons, new dcids were generated using their genus and specie names. The dates were converted to ISO format.

### Schema Overview

The schema representing reaction, metabolite and microbiome data from VMH is defined in [VMH.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list.mcf) and [VMH_enum.mcf](https://raw.githubusercontent.com/suhana13/ISB-project/main/combined_list_enum.mcf). The tmcfs for each of the corresponding csv files can be found [here](https://github.com/suhana13/data/tree/add_Virtual_metabolic_human_data/scripts/biomedical/VirtualMetabolicHuman/tmcf).

The imported data, contains several instances of entities "Metabolite", "ChemicalReaction", "memberOfMetabolicReactionSubsystem", and "Microbe".

The Metabolite entity is used to describe chemical substances which are intermediates or end products in a metabolic reaction. It has several text value properties, representing "abbreviation", "chemicalName", "chemicalFormula", "chemicalCharge", "averageMolecularWeight", "monoIsotropicWeight", "keggID", "pubChemID", "chebiID", "humanMetabolomeDatabaseID", "parkinsonsDiseaseMapName", "reconMap", "reconMap3", "foodb", "chemSpiderID", "bioCyc", "biggID", "wikipediaNameReference", "drugBankID", "seedID", "metaNetXID", "knapsack", "metlin", "casRegistry", "epaId", "inChIKey", "inCHIString", "simplifiedMolecularInputLineEntrySystem"

The ChemicalReaction entity describes chemical reactions. It has several text value properties, including "abbreviation", "reactionDescription", "chemicalEquation", "enzymeCommissionNumber", "keggReactionID", "keggOrthologyID", "cogID", "seed", "metaNetXID". The "memberOfMetabolicReactionSubsystem" returns the "MetabolicReactionSubsystem" property whose value in turn, is a text representing theh biochemical subsystem in which the reaction occurs.

The Microbe entity describes the microscopic organims in the biological world. It has several text value properties including "organismTaxonomicPhylum", "organismTaxonomicClass", "organismTaxonomicOrder", "organismTaxonomicFamily", "organismTaxonomicGenus", "dataDraftCreator", "dateOfDraftCreation", "integratedMicrobialGenomeID", "ncbiID", "kBaseID". It also has properties with quantity values like "microbeGeneInteractionMetric", "microbeReactionMetric", "microbeMetaboliteMetric", "microbePhenotypeMetric". Lastly, "OxygenRequirementStatus", "MicrobialMetabolismType", "BacteriaGramStainType", "PathogenMethodOfInvasion", are of type enumeration.

### Notes and Caveats

The identifiers for a lot of databases (like KEGG, metaNetX), were missing in the dataset. So, the dcids couldnt be based off of them, and thus, chemical names were used for the rest of them.
The runtime for the python scripts maybe more because the downloaded dataset had to be mapped to other datasets, for extraction of required information.The runtime will vary based on the user system RAM, but it can range from anywhere between 1 minute to 15 minutes.

### License

This data is under a [Creative Commons CC0 license](https://creativecommons.org/publicdomain/zero/1.0/).

## About the import

### Artifacts

#### Scripts

`format_metabolite.py`
`format_reaction.py`
`format_reaction_subsystem.py`
`format_microbes.py`

## Examples

To generate the formatted metabolite file:

```
python format_metabolite.py recon-store-metabolites-1.tsv metabolite.csv hmdb.xml
```

where
`format_metabolite.py` - python script
`recon-store-metabolites-1.tsv` - unformatted input tsv
`metabolite.csv` - formatted output csv
`hmdb.xml` - xml file from hmdb with metabolites

To generate the formatted reaction file:

```
format_reaction.py recon-store-reactions-1.tsv chemical_reactions.csv reactions.tsv metabolite.csv
```

where
`format_reaction.py` - python script
`recon-store-reactions-1.tsv` - unformatted reaction tsv from VHM
`chemical_reactions.csv` - formatted output csv
`reactions.tsv` - input tsv with reactions from human 1d
`metabolite.csv` - the output file obtained above

To generate the formatted reaction subsystem file:

```
format_reaction_subsystem.py chemical_reactions.csv ubsystem.csv
```

where
`format_reaction_subsystem.py` - python script
`chemical_reactions.csv` - output file obtained from above
`subsystem.tsv` - output subsystem file

To generate the formatted microbes file:

```
format_microbes.py recon-store-microbes-1.tsv microbe.csv
```

where
`format_microbes.py` - python script
`recon-store-microbes-1.tsv` - input microbe tsv
`microbe.csv` - output formatted csv
