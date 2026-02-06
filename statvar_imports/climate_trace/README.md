# ClimateTrace Greenhouse Gas Emissions Data Processor

The ClimateTrace dataset offers comprehensive and up-to-date greenhouse gas emissions data, derived from satellite imagery and various public sources, for countries worldwide.

This project is designed to download, process, and segregate this data. It automates the collection of country-specific and gas-specific emissions data, transforms it into a standardized format, and prepares it for further analysis or ingestion into systems like Data Commons.

## Features

*   **Dynamic Data Acquisition**: Fetches a comprehensive list of countries from the ClimateTrace API and merges it with a local file (`check_country.csv`) to ensure all required locations are included.
*   **Parallel Data Download**: Efficiently downloads multiple country-gas data zip files concurrently.
*   **Data Segregation**: Extracts and consolidates emissions data, segregating it by greenhouse gas type (CO2, CH4, N2O, CO2e_20yr, CO2e_100yr).
*   **Data Standardization**: Maps raw statistical variable names to Data Commons identifiers (`dcid`) for consistency and interoperability.
*   **Output Generation**: Produces clean, aggregated CSV files for each gas type, ready for further processing or analysis.

## Data Sources

The primary data source for this project is the [ClimateTrace API](https://www.climatetrace.org/). It also uses a local `check_country.csv` file to augment the list of countries.

## Setup and Usage

To use this project, simply run the main script. It will automatically generate the required download links in memory and proceed with the download and segregation process.

```bash
# Ensure your virtual environment is activated and has pandas installed
/path/to/your/venv/bin/python download_and_segregate_by_gas.py
```

The script will create separate CSV files for each gas type in the `input_files/` directory.

### Processing Data

After downloading, you can process the generated CSV files using the `stat_var_processor.py` tool. Here's an example:

```bash
 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/all_countries_co2.csv \
  --pv_map=climate_pvmap_sectors.csv \
  --config_file=common_metadata.csv \
  --output_path=output/sectors_CO2_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## Project Structure

*   `download_and_segregate_by_gas.py`: A single, integrated script that generates a country list, downloads zip files, and segregates data by gas type.
*   `check_country.csv`: A user-maintained list of country ISO codes to ensure they are included in the download, even if not present in the API list.
*   `common_metadata.csv`: Defines common metadata parameters for data processing.
*   `statvar_remap.csv`: Contains the mapping from internal statistical variable names to Data Commons IDs.
*   `input_files/`: Directory containing the segregated CSV files (e.g., `all_countries_co2.csv`) after running the main script.
*   `output/`: Directory containing further processed and standardized output files (e.g., TMCF, MCF files).
