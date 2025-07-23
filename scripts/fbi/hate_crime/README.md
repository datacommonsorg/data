# Importing FBI Hate Crime Data

This directory contains scripts to import FBI Hate Crime Data into Data Commons. It supports two main import processes:
1.  **FBIHatecrimePublications**: Processes individual data tables from the FBI's annual Hate Crime Statistics publications. This is a semi-autorefresh import.
2.  **FBIHateCrime**: Generates detailed aggregations from a master hate crime incident file.

---

## 1. FBI Hate Crime Publications Import (`FBIHatecrimePublications`)

This process imports data from specific tables published annually by the FBI.

### Details

#### Implementation
Each publication table (e.g., Table 1, Table 14) has a corresponding directory (`table1/`, `table14/`) containing a `preprocess.py` script. These scripts read the source data from the local `hate_crime_publication_data` directory, process it, and generate cleaned CSV, TMCF, and MCF files within their respective directories.

#### Configuration & Maintenance
Given that the headers in the downloaded source files change annually, a `table_config.json` file is required. This configuration file contains the specific headers to be processed for each year. Annually, it is necessary to review the newly downloaded source files, confirm their headers, and update the `table_config.json` accordingly, making this a semi-autorefresh import.

#### Combining Tables 1-10
A shell script, `run.sh`, is provided to combine the cleaned CSV outputs from `table1/` through `table10/` into a single file: `tables1-10/t1tot10_combined.csv`. It also copies the TMCF file from `table1/` to serve as the template for the combined data, as these tables represent a single logical dataset in the manifest.

#### Data Caveats
- The output MCF generated from these files is not used due to the change in populationType from 'CriminalIncidents' to 'HateCrimeIncidents' and removal of the 'isHateCrime' property in the statvar definitions. The definitions for the statvars come from the hate crime aggregation scripts.
- New Jersey is missing data for the year 2012 in publications 11 and 12.
- Data for a few locations of crime (publication 10) are missing for certain years.

### Steps

#### Step 1: Download Raw Data
Run the script to download the latest hate crime publication tables. This script will create a `hate_crime_publication_data` directory and place the downloaded files inside.

```bash
python3 download_fbi_publication_data.py
```

#### Step 2: Preprocess Publication Tables
For each publication table you want to import, run its preprocessing script.

```bash
# Navigate to the table's directory
cd table<publication_number>

# Run the preprocessing script
python3 preprocess.py
```

#### Step 3: Combine Tables 1-10
After preprocessing tables 1 through 10, run the combination script from the `hate_crime` directory:

```bash
sh run.sh
```

---

## 2. FBI Hate Crime Aggregations Import (`FBIHateCrime`)

This process generates a wide range of statistical aggregations from a single, master CSV file containing individual hate crime incidents.

### Details

#### Implementation
The `preprocess_aggregations.py` script reads the master `hate_crime.csv` file from the local `hate_crime_data/` directory. It processes this file to create numerous aggregations based on different facets like bias motivation, location, offender demographics, etc.

The script outputs individual CSV files for each aggregation to ease debugging, along with a final combined `aggregation.csv` file. All outputs are placed in the `aggregations/` directory.

#### Final MCF Modifications
The output MCF file requires manual changes to align with the final StatVar definitions:
- Drop the `isHateCrime` property.
- Change `populationType` to `HateCrimeIncidents`.
- Convert `biasMotivation: dcs:TransgenderOrGenderNonConforming` to `biasMotivation: dcs:gender` and add `targetedGender: dcs:TransgenderOrGenderNonConforming`.
- Add the `offenderType` property with values from `KnownOffender`, `KnownOffenderRace`, `KnownOffenderEthnicity`, or `KnownOffenderAge` where applicable.

### Steps

#### Step 1: Download Master Data File
Run the script to download the master hate crime data file. This will download and place the `hate_crime.csv` file into the `hate_crime_data/` directory.

```bash
python3 download_fbi_hate_crime_data.py
```

#### Step 2: Run Aggregation Script
To generate all aggregations from the master file:

```bash
python3 preprocess_aggregations.py
```

---

## Future Improvements & TODOs : b/

* Automate MCF modifications : Current output MCF requires manual modifications to use it further, need to make the script do these manaul changes.

