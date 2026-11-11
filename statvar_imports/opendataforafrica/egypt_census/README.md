# Egypt Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Egypt Open Data for Africa](https://egypt.opendataforafrica.org/)
- **Publisher**: Central Agency for Public Mobilization and Statistics (CAPMAS), Egypt
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — Cloudflare anti-bot challenges on `egypt.opendataforafrica.org` require semi-automated SDMX XML downloads staged to GCS rather than `auto1w`)
- **Schedule**: Weekly (Every Monday at 05:00 UTC — `0 5 * * 1`)
- **Coverage**: Demographics, Economy, Labor Force, Education, Health, and Vital Statistics (1988 – 2018)
- **Entity Resolution**:
  - National level: `country/EGY`
  - Governorate / Sub-national level: `AdministrativeArea1` (27 active governorates + 2 historical governorates: Helwan `wikidataId/Q771345` and 6th of October `wikidataId/Q335708`) resolved via `places_resolved.csv` to Wikidata / Data Commons DCIDs.

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring scripts, inputs, and validation configuration |
| `validation_config.json` | Import validation rules for data freshness and record retention |
| `download.sh` | Shell script to fetch raw census CSVs from GCS storage into `input_files/` |
| `convert_sdmx_xml_to_csv.py` | Python utility for converting Open Data for Africa SDMX XML files to CSVs using `sdmx1` |
| `convert_sdmx_xml_to_csv_test.py` | Hermetic unit tests for `convert_sdmx_xml_to_csv.py` |
| `*_pvmap.csv` | Property-Value schema mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Processor configuration files declaring header rows and column mappings |
| `places_resolved.csv` | Unified place resolver mapping for Governorate place identifiers and names |
| `*_indicator.csv` | Indicator reference definitions |
| `input_files/` | Raw input data CSVs (synced to GCS `source_files`) |
| `counters/` | Runtime counters output directory (`.gitignore` excluded from Git) |
| `test_data/` | Small hermetic unit test input/output fixtures (<= 20 rows) |

## 3. Dataset Mapping Index

The import processes 17 tables from CAPMAS Egypt Open Data:

1. `actytif`: Health Services Statistics of Egypt — hospitals, beds, ambulances, traffic accidents, and medical incidents (governorates via `places_resolved.csv`, 2001–2011)
2. `behvqtc`: Population by Governorate, Urban/Rural, Gender, and Age Groups (governorates via `places_resolved.csv`, 2017)
3. `bluhqme`: Employed Persons (15+ Years) by Governorate, Economic Activity, and Sex (governorates via `places_resolved.csv`, 2017)
4. `cjczlcd`: Health Facilities, Doctors, and Nursing Staff by Sector and Gender (`country/EGY`, 2014)
5. `lxoyale`: Households, Residents in Households, and Population by Governorate and Urban/Rural (governorates via `places_resolved.csv`, 2017)
6. `mptocre`: Unemployment Rates (15–64 Years) by Age Group, Educational Status, and Gender (`country/EGY`, 2017)
7. `pqpump`: Estimate of Employed Persons (15+ Years) by Governorate and Egypt Total (governorates via `places_resolved.csv`, 2012–2017)
8. `szfufmb`: Population by Marital Status, Urban/Rural, Gender, and Age Group (`country/EGY`, 2017)
9. `txbrrac`: Enrolled Students in Higher Education by Institution Type and Gender (`country/EGY`, 2012–2016)
10. `ujtdaag`: Life Expectancy at Birth by Sex (`country/EGY`, 2006–2018)
11. `ulouknf`: Labor Force (15+ Years), Employed, Unemployed, and Unemployment Rate by Gender and Quarter (`country/EGY`, 2017-Q1–2017-Q4)
12. `viytqvf`: Total Fertility Rate of Women in Egypt (`country/EGY`, 1988–2014)
13. `wcssteb`: Pre-University Education Students and Teachers by Stage and Gender (`country/EGY`, 2012–2016)
14. `wtxyghf`: Higher Education Teaching Staff by Institution Type and Gender (`country/EGY`, 2012–2016)
15. `xovpotd`: Socio-Economic Indicators: Population, Labor Force, Employment, Unemployment, and Nominal/Real GDP (`country/EGY`, 1993–2014)
16. `zkjifzd`: Higher Education Graduates by Institution Type and Gender (`country/EGY`, 2012–2017)
17. `zpdksog`: Infant Mortality Count and Infant Mortality Rate by Governorate and Urban/Rural (governorates via `places_resolved.csv`, 2017)

### Geography Resolution Notes
- **Governorate `8` (`EG-SHR` / الشرقية = Al-Sharqia) & Governorate `11` (`EG-GH` / الغربية = Gharbia)**: Corrected in `places_resolved.csv` from legacy literal translation entities (`wikidataId/Q130840` and `wikidataId/Q127167`) to their canonical Egyptian governorate DCIDs (`wikidataId/Q31074` Al-Sharqia Governorate and `wikidataId/Q30835` Gharbia Governorate).
- **Governorate `13` (`EG-BH` / البحيرة = Beheira)**: Added `"The lake",wikidataId/Q30630` in `places_resolved.csv` to restore 12 previously unmapped Beheira observations in `pqpump`.
- **Infant Mortality (`zpdksog`)**: Mapped `NAMEARAB_GOVERNORATES` via `places_resolved.csv` to eliminate a 1-index offset where `ID_GOVERNORATES=28` (`EG`) was previously mapped to South Sinai (`wikidataId/Q30815`).

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Updates
When updated census data is published on Egypt Open Data for Africa:
1. **Download SDMX XML**: Save the SDMX `.xml` file locally for each dataset into an `xml/` directory (e.g., `xml/actytif.xml`, `xml/behvqtc.xml`).
2. **Convert XML to CSV**: Execute `convert_sdmx_xml_to_csv.py` to convert the raw SDMX XML files into normalized CSV files in `input_files/`:
   ```bash
   python3 convert_sdmx_xml_to_csv.py --xml_dir xml/
   ```
3. **Stage to GCS**: Upload the refreshed CSV files to Google Cloud Storage:
   ```bash
   gcloud storage cp input_files/*.csv gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/
   ```

### 4.2 Automated Ingestion Pipeline
During scheduled import runs, the automated pipeline executes:
1. **Download (`download.sh`)**: Fetches the staged CSV files into `input_files/`.
2. **Transform (`stat_var_processor.py`)**: Runs each of the 17 table configurations, resolving place DCIDs and generating TMCF, CSV, and StatVar MCF outputs.
3. **Validation**: Validates data freshness, record deletion thresholds, and schema lint rules.

## 5. Running the Data Processor

Run `stat_var_processor.py` using repo-relative paths from the repository root:

```bash
# Example 1: National table (cjczlcd)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/egypt_census/input_files/cjczlcd.csv \
  --pv_map=statvar_imports/opendataforafrica/egypt_census/cjczlcd_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/egypt_census/cjczlcd_metadata.csv \
  --output_path=statvar_imports/opendataforafrica/egypt_census/output/cjczlcd \
  --output_counters=statvar_imports/opendataforafrica/egypt_census/counters/cjczlcd_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Example 2: Governorate-resolved table (behvqtc)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/egypt_census/input_files/behvqtc.csv \
  --pv_map=statvar_imports/opendataforafrica/egypt_census/behvqtc_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/egypt_census/behvqtc_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/egypt_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/egypt_census/output/behvqtc \
  --output_counters=statvar_imports/opendataforafrica/egypt_census/counters/behvqtc_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 6. Testing & Validation

### 6.1 Unit Tests

Run the hermetic unit tests for the XML conversion routine via `unittest discover` or `run_tests.sh`:

```bash
./run_tests.sh -p statvar_imports/opendataforafrica/egypt_census
# or directly:
.env/bin/python3 -m unittest discover -v -s statvar_imports/opendataforafrica/egypt_census -p "*_test.py"
```

### 6.2 Pre-Submission Validation Rules

The import configuration in `validation_config.json` enforces:
- Scoped freshness checks ensuring active observations across all 1,365 StatVars.
- Record retention limits (`threshold: 0.1`) between import versions.
- Base validation checks for lint errors (`0`) and reference resolution (`0`).
