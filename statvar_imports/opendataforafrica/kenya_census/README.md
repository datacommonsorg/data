# Kenya Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Kenya Open Data for Africa](https://kenya.opendataforafrica.org/)
- **Publisher**: Kenya National Bureau of Statistics (KNBS)
- **Import Type**: `Semi-Automated`
- **Schedule**: Quarterly
- **Coverage**: Demographics, Health, Education, Economy (2002 – present)
- **Entity Resolution**:
  - National level: `country/KEN`
  - County / Sub-national level: `AdministrativeArea1` resolved via mapping CSV (`places_resolved.csv`) to Wikidata / Data Commons DCIDs.

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
| `places_resolved.csv` | Unified place resolver mapping for County / AdministrativeUnit place identifiers |
| `*_indicator.csv` | Indicator reference definitions |
| `input_files/` | Raw input data CSVs (synced to GCS `source_files`) |
| `counters/` | Runtime counters output directory (`.gitignore` excluded from Git) |
| `test_data/` | Small hermetic unit test input fixtures (<= 5 rows) |

## 3. Dataset Mapping Index

The import processes 12 tables from KNBS Open Data:

1. `dlrrjxg`: Mortality events by age group and sex (`country/KEN`)
2. `egdxgkd`: KCSE secondary examination candidates and grades (`country/KEN`)
3. `emxkej`: Population census demographics by gender and age group (`country/KEN`)
4. `fwjfdnc`: Household characteristics and census demographics (counties via `places_resolved.csv`)
5. `gxbucsd`: School enrollment by administrative unit (counties via `places_resolved.csv`)
6. `ixdvqrf`: Birth events by sex (`country/KEN`)
7. `rsfzlbg`: County population indicators (counties via `places_resolved.csv`)
8. `srricmg`: National household expenditure categories (`country/KEN`)
9. `tdxdksf`: KCPE primary examination mean assessment scores (`country/KEN`)
10. `vdbvyfd`: Health and hospital deliveries by county (counties via `places_resolved.csv`)
11. `welrttb`: Employment and labor force status (`country/KEN`)
12. `xszlbb`: National economic production and industry indicators (`country/KEN`)

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Updates
When updated census data is published on Kenya Open Data for Africa:
1. **Download SDMX XML**: Save the SDMX `.xml` file locally for each dataset into an `xml/` directory (e.g., `xml/dlrrjxg.xml`, `xml/egdxgkd.xml`).
2. **Convert XML to CSV**: Execute `convert_sdmx_xml_to_csv.py` to convert the raw SDMX XML files into normalized CSV files in `input_files/`:
   ```bash
   python3 convert_sdmx_xml_to_csv.py --xml_dir xml/
   ```
3. **Stage to GCS**: Upload the refreshed CSV files to Google Cloud Storage:
   ```bash
   gcloud storage cp input_files/*.csv gs://unresolved_mcf/opendataforafrica/kenya_census/input_files/
   ```

### 4.2 Automated Ingestion Pipeline
During scheduled import runs, the automated pipeline executes:
1. **Download (`download.sh`)**: Fetches the staged CSV files into `input_files/`.
2. **Transform (`stat_var_processor.py`)**: Runs each of the 12 table configurations, resolving place DCIDs and generating TMCF, CSV, and StatVar MCF outputs.
3. **Validation**: Validates data freshness, record deletion thresholds, and schema lint rules.

## 5. Running the Data Processor

Run `stat_var_processor.py` using repo-relative paths from the repository root:

```bash
# Example 1: National table (dlrrjxg)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/kenya_census/input_files/dlrrjxg.csv \
  --pv_map=statvar_imports/opendataforafrica/kenya_census/dlrrjxg_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/kenya_census/dlrrjxg_metadata.csv \
  --output_path=statvar_imports/opendataforafrica/kenya_census/output/dlrrjxg \
  --output_counters=statvar_imports/opendataforafrica/kenya_census/counters/dlrrjxg_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# Example 2: County-resolved table (vdbvyfd)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/kenya_census/input_files/vdbvyfd.csv \
  --pv_map=statvar_imports/opendataforafrica/kenya_census/vdbvyfd_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/kenya_census/vdbvyfd_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/kenya_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/kenya_census/output/vdbvyfd \
  --output_counters=statvar_imports/opendataforafrica/kenya_census/counters/vdbvyfd_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 6. Testing & Validation

### 6.1 Unit Tests

Run the hermetic unit tests for the XML conversion routine:

```bash
.env/bin/python -m unittest statvar_imports/opendataforafrica/kenya_census/convert_sdmx_xml_to_csv_test.py
```

### 6.2 Pre-Submission Validation Rules

The import configuration in `validation_config.json` enforces:
- Freshness checks ensuring active observations across StatVars.
- Record retention limits between import versions.
- Base validation checks for lint errors and reference resolution.

