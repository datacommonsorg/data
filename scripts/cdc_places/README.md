# CDC PLACES Project Import

This directory contains materials for importing data from the [CDC PLACES](https://www.cdc.gov/places/) project.

The CDC provides the PLACES dataset in multiple schemas and formats on their [Data Portal](https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places&sortBy=newest&utf8).

The processing script in this directory uses the CSV format of *[Local Data for Better Health, Place Data](https://chronicdata.cdc.gov/500-Cities-Places/PLACES-Local-Data-for-Better-Health-Place-Data-202/eav7-hnsx)* schema.

## Processing Script

The processing script contains subcommands for producing the requisite input data. To view usage, run the script with the `--help` flag.

    $ python3 ./scripts/cdc_places/process_csv.py --help

### Generating Statistical Variables

The `generate_stat_vars` command generates Stastical Variables in MCF format for each of the PLACES Measures. The output can be written to a file or printed to standard output.

    $ python3 ./scripts/cdc_places/process_csv.py generate_stat_vars --input "/path/to/input.csv" [--output "/path/to/output.mcf"]

The output is included in this directory as `stat_vars.mcf`.

### Pre-processing CSV data

The `preprocess_csv` command generates a CSV file that can be imported into the Data Commons Knowledge Graph. The command generates an output CSV which has redundant columns removed and includes additional columns for resolving entities in the KG.

    $ python3 ./scripts/cdc_places/process_csv.py preprocess_csv --input "/path/to/input.csv" --output "/path/to/output.csv"
