# Import Overview
This import processes County Business Patterns (CBP) data from the U.S. Census Bureau. This data provides statistics on the number of establishments, employment figures, and payroll information. The data is available at various geographic levels, including national, state, county, and ZIP code.

## Source URL
- https://www.census.gov/data/datasets/2023/econ/cbp/2023-cbp.html
- https://www2.census.gov/programs-surveys/cbp/datasets/{}/cbp{}co.zip
- https://www2.census.gov/programs-surveys/cbp/datasets/{}/cbp{}msa.zip
- https://www2.census.gov/programs-surveys/cbp/datasets/{}/zbp{}totals.zip
- https://www2.census.gov/programs-surveys/cbp/datasets/{}/zbp{}detail.zip

## Import Type
custom script

## Source Data Availability
The data is available annually. The scripts are parameterized to download data for a specific year.

# PreProcessing Steps
No preprocessing required.

# Autorefresh Type:
fully auto refresh

# Script Execution Details
First, run `main.py` to download the data.
flags: data_start_year - this is the default flag which refers to the start year.
       data_end_year - this is the default flag which refers to the current year.
       output_dir - this is also the default flag which refers to the output directory for processed output from 'main.py' script.
The `shard_input_csv.sh` script performs the following preprocessing steps:
1.  Creates directories for shards, debug outputs, and final processed outputs.
2.  Splits the large input CSV files into smaller shards of 500,000 rows each.
3.  Processes the generated shards in parallel using the `stat_var_processor.py` script.
4.  The processing script uses `censuscountybusinesspatterns_pvmap.csv` and `censuscountybusinesspatterns_metadata.csv` for mapping and metadata.
5.  The final processed outputs are saved in the `gcs_output/output` directory.
# Commands to run 
1. python3 main.py
2. ./shard_input_csv.sh

#### Cleaned Data
The cleaned data is generated in the `gcs_output/output` directory with filenames like `output_*.csv`.

#### Template MCFs
The template MCF file used is `CensusCountyBusinessPatterns.tmcf`.

#### StatisticalVariable Instance MCF
The StatisticalVariable instance MCF files are generated in the `processed_outputs` directory with filenames like `output_*_stat_vars.mcf`.

#### Scripts
- `main.py`: Downloads the source data.
- `shard_input_csv.sh`: Preprocesses the data.
- `write_mcf.py`: Generates the MCF files.
- `cbp_co.py`: Processes county-level data.
- `cbp_msa.py`: Processes MSA-level data.
- `zbp.py`: Processes ZIP code-level data.
- `zbp_detail.py`: Processes detailed ZIP code-level data.
