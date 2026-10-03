# Importing the Anatomical Therapeutic Chemical (ATC) code data

## Table of Contents

- [Anatomical Therapeutic Chemical (ATC) code data](#importing-the-anatomical-therapeutic-chemical-atc-code-data)
  - [Table of Contents](#table-of-contents)
  - [About the Dataset](#about-the-dataset)
    - [Download Data](#download-data)
    - [Overview](#overview)
    - [Notes and Caveats](#notes-and-caveats)
    - [License](#license)
  - [About the import](#about-the-import)
    - [Artifacts](#artifacts)
      - [Scripts](#scripts)
      - [Files](#files)
  - [Example](#example)

## About the Dataset

[The Anatomical Therapeutic Chemical (ATC)](https://www.who.int/tools/atc-ddd-toolkit/atc-classification) is a classification system of active substances which are divided into different groups and classes, as per their therapeutic, pharmacological and chemical properties and the organ or system they act on. Drugs are classified into groups as per the following five levels:

**Level 1**
The system has fourteen main anatomical or pharmacological groups.

**Level 2**
Pharmacological or Therapeutic subgroup.

**Levels 3 & 4**
Chemical, Pharmacological or Therapeutic subgroup.

**Level 5**
Chemical substance.

Here's an example of the complete classification for metformin which illustrates the structure of the code.

| ATC Level | ATC code       | ATC name |
|---------|---------|---------------------------------|
| Level 1 | A       | Alimentary tract and metabolism |
| Level 2 | A10     | Drugs used in diabetes          |
| Level 3 | A10B    | Blood glucose lowering drugs    |
| Level 4 | A10BA   | Biguanides                      |
| Level 5 | A10BA02 | Metformin                       |

### Download Data

The ATC data can be scraped from the WHO's searchable version of the ATC index which can be found [here](https://www.whocc.no/atc_ddd_index/).

In order to scrape the data and fetch the raw csv version of it, we used an R script adopted from this [github repository](https://github.com/fabkury/atcd). This script queries for and read all ATC classes and their corresponding subfields (Defined Daily Dosage - DDD, Unit of Measure (UOM), Administration route, Note) and writes it into one flat CSV file.

For the ease of the users, we have pre-run the R script, fetched the information in a raw .csv format and uploaded it to this directory.

In order to format the ATC files from its raw .csv format, we've created a `format_atc.py` python script that the user has to run.
See [Notes and Caveats](#notes-and-caveats) for additional information on formatting) for further data preprocessing.

### Overview

This directory stores the script used to clean and convert the The Anatomical Therapeutic Chemical codes data into a `.csv` format, which is ready for ingestion into the Data Commons knowledge graph alongside a `.tmcf` file that maps the `.csv` to the defined schema. In this import the data is ingested as [AnatomicalTherapeuticChemicalCode](https://datacommons.org/browser/AnatomicalTherapeuticChemicalCode) entities into the graph.

The ATC code ID is mapped to other properties, namely, its name, averageDailyDosage, unitOfMeasure, routeOfAdministration, anatomicalTherapeuticChemicalCodeLevel, and note regarding the code.

### Notes and Caveats

As discussed above, the data was not directly downloadable from the WHO website. Hence, it had to be scraped from the website and converted to one big downloadable and parsable `.csv` file.

### License

## About the import

### Artifacts

#### Scripts

##### Python Script

[`format_atc.py`](format_atc.py) parses the raw .csv file and converts it into a .csv with ATC codes mapped to their corresponding properties.

#### Files

##### Data File

[`atc-raw.csv`](atc-raw.csv) contains scraped raw atc codes data

##### tMCF File

[`atc_output.tmcf`](atc_output.tmcf) contains the tmcf mapping to the csv file, to generate an accurate tmcf-csv pair.

### Example

```
python3 format_atc.py atc-raw.csv atc_output.csv
```
