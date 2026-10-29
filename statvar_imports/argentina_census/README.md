# Argentina Census (`Argentina_Census`) StatVar Import

This directory contains the automated `stat_var_processor.py` import pipeline for `Argentina_Census`, sourced from Argentina's **Instituto Nacional de Estadística y Censos (INDEC)** (`https://www.indec.gob.ar/`).

## Datasets Covered

1. **Population by Single Age, 5-Year Age Group, and Sex (`1980, 1991, 2001, 2010, 2022`)**
   - Geographic levels: Country (`country/ARG`) and 23 Provinces (AA1).
   - Output input file: `input_files/argentina_population.csv`
2. **Urban and Rural Population by Age and Sex (`1980, 1991, 2001, 2010`)**
   - Geographic levels: Country (`country/ARG`) and 23 Provinces (AA1).
   - Output input file: `input_files/argentina_urban_rural.csv`
3. **Department (AA2) Population (`2001, 2010, 2022`)**
   - Geographic levels: 489 Departments / Partidos (AA2).
   - Output input file: `input_files/argentina_population_aa2.csv`
4. **Literacy and Illiteracy for Population Aged 10+ Years (`2010`)**
   - Geographic levels: Country (`country/ARG`) and 23 Provinces (AA1).
   - Output input file: `input_files/argentina_literacy.csv`
5. **Infant Mortality Rate per 1,000 Live Births (`2005–2023`)**
   - Geographic levels: Country (`country/ARG`) and 23 Provinces (AA1).
   - Output input file: `input_files/argentina_infant_mortality.csv`

## How to Run

1. **Download and extract the source data into `input_files/*.csv`:**
   ```bash
   python3 statvar_imports/argentina_census/download.py
   ```

2. **Run `stat_var_processor.py` to generate `output_files/argentina_census_output.csv` and `output_files/argentina_census_output.tmcf`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/argentina_census/input_files/*.csv \
     --pv_map=statvar_imports/argentina_census/argentina_census_pvmap.csv \
     --config_file=statvar_imports/argentina_census/argentina_census_metadata.csv \
     --places_resolved_csv=statvar_imports/argentina_census/argentina_places_resolved.csv \
     --output_path=statvar_imports/argentina_census/output_files/argentina_census_output \
     --output_counters=statvar_imports/argentina_census/counters/argentina_census_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

3. **Run unit and integration tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/argentina_census -p "*_test.py"
   ```
