### US EPA GHGRP Import
This directory contains scripts and configurations to download, preprocess, and import data from the U.S. Environmental Protection Agency's Greenhouse Gas Reporting Program (GHGRP).

GHGRP collects greenhouse gas emissions data from large facilities in the U.S., including power plants, oil & gas systems, and other industrial sources. This import prepares standardized observations and metadata for integration into the Data Commons knowledge graph.

### 1. Source Information
***Base Data URL Template:***
`https://www.epa.gov/system/files/other-files/{year}-10/{year_minus_1}_data_summary_spreadsheets.zip`

***Crosswalk File URL:***
`https://www.epa.gov/system/files/documents/{yr}-04/ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx`

**Source Data Type: Excel (.xlsx) files, per year**

***Release Frequency:*** Annual (typically in October for the previous calendar year)

`Download Coverage:`
Currently supports years 2010–latest

### 2. Directory Structure and File Outputs
`Input Files` (after running download.py)
Stored in: `tmp_data/`

**Yearly GHGRP Excel files:**

ghgp_data_2010.xlsx
ghgp_data_2011.xlsx
...
ghgp_data_2023.xlsx

**Extracted facility-specific CSVs from sheets:**

2015_oil_and_gas.csv
2016_direct_emitters.csv
2017_gathering_and_boosting.csv
...

**Crosswalk file:**

`crosswalks.csv`

`Output Files `(after running process.py)
Stored in: `import_data/`

**Observational data:**

all_data.csv
observations.tmcf

**Metadata and schema files:**

gas_node.mcf
gas_sv.mcf
sources_node.mcf
sources_sv.mcf
schema.mcf

### 3. Running the Pipeline
**Step 1: Download Data and Extract Sheets**
Run the following to download Excel files and extract relevant sheets into CSVs:

`python3 download.py`

**Step 2: Process Extracted Files into Import Artifacts**

`python3 process.py`

### 4. Testing
Run Unit Tests
From repo root:

`python3 -m unittest discover -v -s ../ -p "*_test.py"`

Or via the test runner:

`cd ../../../`
`./run_tests.sh -p scripts/us_epa/ghgrp`

To test the Downloader class in isolation:

`python3 download_test.py`

### 5. Validation

**Lint the generated files using the Data Commons Import Tool:**

dc-import lint import_data/*
Sample Lint Report Output

{
  "counterSet": {
    "counters": {
      "Existence_NumChecks": "4362098",
      "Existence_NumDcCalls": "29",
      "NumNodeSuccesses": "396460",
      "NumPVSuccesses": "3171680",
      "NumRowSuccesses": "396460"
    }
  }
}

### 6. Update Cadence & Refresh Process
Frequency: Yearly (manual refresh when new data is published by EPA)

Autorefresh: Full automated

Steps to Refresh:

Run download.py and process.py

`python3 download.py`

`python3 process.py`

Validate outputs with dc-import lint

Upload artifacts to GCS and ingest into Data Commons

### 7. Notes
This import assumes EPA facilities are already linked via the facility crosswalk (see: Facility README).