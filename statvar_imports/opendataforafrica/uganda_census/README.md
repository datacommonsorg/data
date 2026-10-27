# Uganda Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Uganda Open Data for Africa](https://uganda.opendataforafrica.org/)
- **Publisher**: Uganda Bureau of Statistics (UBOS)
- **Import Type**: `Semi-Automated`
- **Schedule**: Weekly (`0 5 * * 1`)
- **Coverage**: Demographics, Health, Education, Census populations (1969 – 2016)
- **Entity Resolution**:
  - National level: `country/UGA`
  - District level: Resolved via `places_resolved.csv` to Wikidata / Data Commons DCIDs.
  - Special area: Conflict Areas mapped to `country/UGA_ConflictAreas` via `qiubrhc_places.mcf`.

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring scripts, inputs, and validation configuration |
| `validation_config.json` | Import validation rules for data freshness and record retention |
| `download.sh` | Shell script to stage place MCF and fetch raw census CSVs from GCS storage into `input_files/` |
| `convert_sdmx_xml_to_csv.py` | Python utility for converting Open Data for Africa SDMX XML files to CSVs using `sdmx1` |
| `convert_sdmx_xml_to_csv_test.py` | Hermetic unit tests for `convert_sdmx_xml_to_csv.py` |
| `qiubrhc_places.mcf` | Provisional place node definition for `country/UGA_ConflictAreas` |
| `places_resolved.csv` | Unified place resolver mapping from district names/codes to Data Commons DCIDs |
| `*_pvmap.csv` | Property-Value schema mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Processor configuration files declaring header rows and column mappings |
| `*_indicator.csv` | Indicator reference definitions |
| `input_files/` | Raw input data CSVs (synced to GCS `source_files`) |
| `counters/` | Runtime counters output directory (`.gitignore` excluded from Git) |
| `test_data/` | Small hermetic unit test input fixtures (<= 50 rows) |
| `output/` | Generated CSV observations, TMCF, and StatVar MCF files |

## 3. Dataset Mapping Index

The import processes 4 tables from UBOS Open Data:

1. `fidjrwf`: Uganda Regional Population Statistics (1969 – 2016)
2. `ewvclpb`: Uganda Regional Education Statistics (2011 – 2016)
3. `yvitjl`: Uganda Regional Health Statistics Database (2005 – 2016)
   - *Legacy Note*: Hospital bed counts by ownership (`KN.PH.BEDS.*`) are mapped to legacy `Count_HealthEstablishment*` StatVars from `Uganda_stat_var.mcf` (where PHP = Private Health Practitioners is mapped to `PartialHospitalizationProgram`) for backward compatibility.
4. `qiubrhc`: Uganda Census Populations by District (1980, 1991, 2002, 2014)

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Updates
When updated census data is published on Uganda Open Data for Africa:
1. **Download SDMX XML**: Save the SDMX `.xml` file locally for each dataset into an `xml/` directory (e.g., `xml/fidjrwf.xml`, `xml/ewvclpb.xml`, `xml/yvitjl.xml`, `xml/qiubrhc.xml`).
2. **Convert XML to CSV**: Execute `convert_sdmx_xml_to_csv.py` to convert the raw SDMX XML files into normalized CSV files in `input_files/`:
   ```bash
   python3 convert_sdmx_xml_to_csv.py --xml_dir xml/
   ```
3. **Stage to GCS**: Upload the refreshed CSV files to Google Cloud Storage:
   ```bash
   gcloud storage cp input_files/*.csv gs://unresolved_mcf/opendataforafrica/uganda_census/input_files/
   ```

### 4.2 Automated Ingestion Pipeline
During scheduled import runs, the automated pipeline executes:
1. **Download (`download.sh`)**: Stages `qiubrhc_places.mcf` to `output/` and fetches staged CSV files into `input_files/`.
2. **Transform (`stat_var_processor.py`)**: Runs each of the 4 table configurations, resolving place DCIDs and generating TMCF, CSV, and StatVar MCF outputs.
3. **Validation**: Validates data freshness, record deletion thresholds, and schema lint rules.

### 4.3 Refresh Schedule
The automated pipeline executes on a weekly schedule (`0 5 * * 1` - at 05:00 UTC every Monday) via Cloud Batch / GCP Cloud Run.

## 5. Running the Data Processor

Run `stat_var_processor.py` using repo-relative paths from the repository root:

```bash
# 1. Population Statistics (fidjrwf)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/uganda_census/input_files/fidjrwf.csv \
  --pv_map=statvar_imports/opendataforafrica/uganda_census/fidjrwf_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/uganda_census/fidjrwf_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/uganda_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/uganda_census/output/fidjrwf \
  --output_counters=statvar_imports/opendataforafrica/uganda_census/counters/fidjrwf_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 2. Education Statistics (ewvclpb)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/uganda_census/input_files/ewvclpb.csv \
  --pv_map=statvar_imports/opendataforafrica/uganda_census/ewvclpb_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/uganda_census/ewvclpb_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/uganda_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/uganda_census/output/ewvclpb \
  --output_counters=statvar_imports/opendataforafrica/uganda_census/counters/ewvclpb_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 3. Health Statistics (yvitjl)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/uganda_census/input_files/yvitjl.csv \
  --pv_map=statvar_imports/opendataforafrica/uganda_census/yvitjl_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/uganda_census/yvitjl_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/uganda_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/uganda_census/output/yvitjl \
  --output_counters=statvar_imports/opendataforafrica/uganda_census/counters/yvitjl_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 4. Census Populations (qiubrhc)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/uganda_census/input_files/qiubrhc.csv \
  --pv_map=statvar_imports/opendataforafrica/uganda_census/qiubrhc_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/uganda_census/qiubrhc_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/uganda_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/uganda_census/output/qiubrhc \
  --output_counters=statvar_imports/opendataforafrica/uganda_census/counters/qiubrhc_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 6. Testing & Validation

### 6.1 Unit Tests

Run the hermetic unit tests via `run_tests.sh`:

```bash
./run_tests.sh -p statvar_imports/opendataforafrica/uganda_census
```

Or via `unittest`:

```bash
.env/bin/python -m unittest statvar_imports/opendataforafrica/uganda_census/convert_sdmx_xml_to_csv_test.py
```

### 6.2 Pre-Submission Validation Rules

The import configuration in `validation_config.json` enforces:
- `check_all_statvars_freshness`: `SQL_VALIDATOR` freshness check ensuring all active StatVars meet the freshness boundary (`MaxDate >= '2002'`).
- `check_deleted_records_percent`: `DELETED_RECORDS_PERCENT` ensuring deleted records do not exceed `0.1%` (`threshold: 0.1`).
Zero lint errors is enforced by default in the execution pipeline.
