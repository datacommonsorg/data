# Importing WHO GHO Data Into Data Commons

Author: chejennifer

## Table of Contents

1. [About the Dataset](#about-the-dataset)
1. [Import Procedure](#import-procedure)

## About the Dataset

### Overview
This directory imports [WHO GHO Data](https://www.who.int/data/gho) into Data Commons. The WHO’s Global Health Observatory website provides access to data for over 2300 indicators and each indicator can be further broken down by 0-3 different dimension types. 

These indicators fall under a wide range of categories including: 
- BMI, nutrition, health technologies, tobacco control. Child health, communicable diseases, mental health, immunization, violence prevention, STIs, health equity, health regulations, WASH (water, sanitation, and hygiene), violence against women, tropical diseases, public health and environment, dementia, women and health, resources for substance use disorders, world health statistics, HIV/AIDS, noncommunicable diseases, health workforce, global health estimates, antimicrobial resistance, malaria, air pollution, global information system on alcohol and health, health systems, maternal and reproductive health, universal health coverage, tuberculosis

### Notes and Caveats
1. WHO GHO has data with observations for place types that are not already in our schema. This import only imports the data for Country level.

#### Template MCFs
- [who_stats.tmcf](who_stats.tmcf)

#### Other Files
- [curated_dim_map.json](curated_dim_map.json): manually curated schema mapping for dimension types and values, and the manually curated list of dimensions that indicate populationType of person
- [curated_dim.mcf](curated_dim.mcf): The manually curated schema for select dimension types and values
#### Scripts
- [import_data.py](import_data.py): Script to generate the clean csv, statistical variable mcf files, and schema mcf files needed for importing the WHO GHO dataset.
- [download_data.py](download_data.py): Script to download all the who gho observations data from the who site.
## Import Procedure

>To import WHO GHO data:
1. Get the raw data in one of 2 ways:
    - To get the pre-downloaded data from our Google Cloud Storage, run and then unzip the file:
     ```
     gsutil cp gs://datcom-source-data/who/gho/indicator_data.zip .
     ```
    - To download data using the WHO API (this can take about 1 hour), run:
     ```
     python3 download_data.py --output=<folder to download data into>
     ```
2. Process the raw data to get all the pieces needed for import by running:
```
python3 import_data.py --data_dir=<folder holding the raw data> --curated_dim_file=curated_dim_map.json
```