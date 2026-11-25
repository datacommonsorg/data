# Egypt Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Egypt Open Data for Africa](https://egypt.opendataforafrica.org/)
- **Publisher**: Central Agency for Public Mobilization and Statistics (CAPMAS), Egypt
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — Cloudflare anti-bot challenges on `egypt.opendataforafrica.org` require semi-automated SDMX XML/CSV staging to GCS, followed by automated Cloud Batch execution and `auto1w` ingestion)
- **Schedule**: Weekly (Every Monday at 05:00 UTC — `0 5 * * 1`)
- **Coverage**: Demographics, Economy, Labor Force, Education, Health, and Vital Statistics at country and governorate level (1988+)
- **Entity Resolution**:
  - National level: `country/EGY`
  - Governorate / Sub-national level: `AdministrativeArea1` (27 active governorates + 2 historical governorates: Helwan `wikidataId/Q771345` and 6th of October `wikidataId/Q335708`) pre-resolved via `places_resolved.csv` (`NoEntityResolution` at KG load time).

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring download, XML conversion, processor scripts, inputs, and validation |
| `validation_config.json` | Scoped SQL freshness validation rules complementing default pipeline checks |
| `download.sh` | Shell script fetching staged raw inputs from GCS into `raw_inputs/` and copying staged CSVs to `input_files/` |
| `convert_sdmx_xml_to_csv.py` | Python utility converting Open Data for Africa SDMX XML files in `raw_inputs/` to normalized CSVs in `input_files/` |
| `convert_sdmx_xml_to_csv_test.py` | Hermetic unit tests for `convert_sdmx_xml_to_csv.py` |
| `common_pvmap.csv` | Shared PVMap handling dynamic annual/quarterly `TIME_PERIOD`, `OBS_VALUE`, and `FREQ` mappings |
| `*_pvmap.csv` | Per-table Property-Value schema mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Per-table processor configuration files (`generate_statvar_mcf` and `generate_schema_mcf` enabled) |
| `places_resolved.csv` | Unified place resolver mapping ISO region codes, English names, and Arabic governorate names to DCIDs |
| `statvar_remap.csv` | StatVar DCID remap table resolving collisions with legacy US BLS/Census StatVars in `mptocre`, `szfufmb`, and `wtxyghf` |
| `existing_schema.mcf` | Existing Data Commons schema declarations passed via `--existing_schema_mcf` so processor schema generation recognizes metadata properties and compound enum values |
| `test_data/` | Representative hermetic input/output CSV and TMCF fixtures (`<table>_input.csv`, `<table>_output.csv`, `<table>_output.tmcf`) |

## 3. Dataset Mapping Index

The import processes 17 tables from CAPMAS Egypt Open Data:

1. `actytif`: Health Services Statistics of Egypt — hospitals, beds, ambulances, traffic accidents, and medical incidents (`REGIONID_LOCATION` via `places_resolved.csv`, 2001+)
2. `behvqtc`: Population by Governorate, Urban/Rural, Gender, and Age Groups (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+; age-total rows deferred to `lxoyale`)
3. `bluhqme`: Employed Persons (15+ Years, scaled from hundreds via `#Multiply,100`) by Governorate, Economic Activity, and Sex (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+)
4. `cjczlcd`: Health Facilities, Doctors, and Nursing Staff by Sector and Gender (`country/EGY`, 2014+)
5. `lxoyale`: Households, Residents in Households, and Total Population by Governorate and Urban/Rural (`REGIONID_LOCATION` via `places_resolved.csv`, 2017+)
6. `mptocre`: Labor-Force Unemployment Rates (15–64 Years) by Age Group, Educational Status, and Gender (`country/EGY`, 2017+)
7. `pqpump`: Estimate of Employed Persons (15+ Years, scaled from hundreds via `#Multiply,100`) by Governorate and Egypt Total (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2012+)
8. `szfufmb`: Population by Marital Status, Urban/Rural, Gender, and Age Group (`country/EGY`, 2017+)
9. `txbrrac`: Enrolled Students in Higher Education by Institution Type and Gender (`country/EGY`, 2012+)
10. `ujtdaag`: Life Expectancy at Birth by Sex (`country/EGY`, 2006+)
11. `ulouknf`: Labor Force (15+ Years), Employed, Unemployed, and Labor-Force Unemployment Rate by Gender and Quarter (`country/EGY`, 2017-Q1+)
12. `viytqvf`: Total Fertility Rate of Women in Egypt (`country/EGY`, 1988+)
13. `wcssteb`: Pre-University Education Students and Teachers by Stage (Pre-Primary, Primary, Preparatory/Middle, General/Technical Secondary, Community, Special) and Gender (`country/EGY`, 2012+)
14. `wtxyghf`: Higher Education Teaching Staff by Institution Type and Gender (`country/EGY`, 2012+)
15. `xovpotd`: Socio-Economic Indicators: Resident/Total Population, Labor Force, Employment, Unemployment, and Real/Nominal GDP (`country/EGY`, 1993+)
16. `zkjifzd`: Higher Education Graduates by Institution Type and Gender (`country/EGY`, 2012+)
17. `zpdksog`: Infant Mortality Count and Infant Mortality Rate by Governorate and Urban/Rural (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+)

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Staging
When updated data is published on Egypt Open Data for Africa:
1. Stage refreshed SDMX `.xml` or `.csv` files to `gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/`:
   ```bash
   gcloud storage cp xml/*.xml gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/
   ```

### 4.2 Automated Pipeline Execution
During scheduled runs (`0 5 * * 1`), `manifest.json` executes:
1. **`download.sh`**: Downloads staged files from GCS into `raw_inputs/` (preserving raw downloads untouched) and copies any pre-staged CSVs into `input_files/`.
2. **`convert_sdmx_xml_to_csv.py`**: Converts any `.xml` files in `raw_inputs/` into normalized `.csv` files in `input_files/` and verifies all 17 table CSVs are present and non-empty.
3. **`stat_var_processor.py`**: Processes all 17 tables using `--pv_map=common_pvmap.csv,<table>_pvmap.csv`, generating `.csv`, `.tmcf`, `_stat_vars.mcf`, and `_stat_vars_schema.mcf` in `output/`.
4. **Validation**: Runs default pipeline checks (`DELETED_RECORDS_PERCENT`, `EMPTY_IMPORT`, `MISSING_REFS_COUNT`, `LINT_ERROR_COUNT`) plus the scoped freshness SQL rules in `validation_config.json`.

## 5. Running Locally & Testing

```bash
# Run unit tests
./run_tests.sh -p statvar_imports/opendataforafrica/egypt_census

# Example single-table processor run from repo root
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/egypt_census/input_files/behvqtc.csv \
  --pv_map=statvar_imports/opendataforafrica/egypt_census/common_pvmap.csv,statvar_imports/opendataforafrica/egypt_census/behvqtc_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/egypt_census/behvqtc_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/egypt_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/egypt_census/output/behvqtc \
  --output_counters=statvar_imports/opendataforafrica/egypt_census/counters/behvqtc_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --existing_schema_mcf=statvar_imports/opendataforafrica/egypt_census/existing_schema.mcf
```
