# Kenya Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Kenya Open Data for Africa](https://kenya.opendataforafrica.org/)
- **Publisher**: Kenya National Bureau of Statistics (KNBS)
- **Import Type**: `Semi-Automated`
- **Schedule**: Weekly (`30 05 * * 1` via Cloud Batch)
- **Coverage**: Demographics, Health, Education, Economy (2002 – present)
- **Entity Resolution**:
  - National level: `country/KEN`
  - County / Sub-national level: `AdministrativeArea1` resolved via mapping CSVs (`*_places_resolved.csv`) to Wikidata / Data Commons DCIDs.

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Cloud Batch import manifest declaring scripts, inputs, GCS source files, and resource limits |
| `validation_config.json` | Import validation rules (freshness SQL, deletion threshold <= 0.1%, 0 lint errors) |
| `download.sh` | Shell script to fetch raw census CSVs from GCS storage into `input_files/` |
| `download.py` | Python utility for parsing Open Data for Africa StructureSpecificData SDMX XML files to CSVs |
| `download_test.py` | Hermetic unit tests for `download.py` XML parsing, atomic writes, and GCS pull routines |
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

## 4. Semi-Automated Ingestion Workflow

Due to Cloudflare bot protection on `kenya.opendataforafrica.org`, programmatic scraping and automated HTTP requests directly against the portal fail with HTTP 403. Consequently, upstream source data updates follow a semi-automated workflow with GCS backing.

### 4.1 Manual Workflow (Updating Upstream Source Files)
When updated census data is published on Kenya Open Data for Africa:
1. **Navigate to Dataset**: Open the source URL for each dataset in a local browser (e.g. `https://kenya.opendataforafrica.org/<dataset_id>`).
2. **Download SDMX XML**: Copy the SDMX data link (or click **Export** $\rightarrow$ **SDMX**), right-click and select **"Save Link As..." / "Save As..."** to save the `.xml` file locally into an `xml/` directory (e.g., `xml/dlrrjxg.xml`, `xml/egdxgkd.xml`).
3. **Convert XML to CSV**: Execute `download.py` to convert the raw SDMX XML files into normalized CSV files in `input_files/`:
   ```bash
   python3 download.py --xml_dir xml/
   ```
4. **Stage to GCS**: Upload the refreshed CSV files to Google Cloud Storage:
   ```bash
   gcloud storage cp input_files/*.csv gs://unresolved_mcf/opendataforafrica/kenya_census/input_files/
   ```

### 4.2 Automated Ingestion Workflow (Cloud Batch Execution)
During automated weekly runs (`30 05 * * 1`), Cloud Batch executes the following pipeline:
1. **Download Step (`download.sh`)**: Pulls the verified CSVs from `gs://unresolved_mcf/opendataforafrica/kenya_census/input_files/` into `input_files/`.
2. **Transform (`stat_var_processor.py`)**: Runs each of the 12 table configurations, resolving place DCIDs and generating TMCF, CSV, and StatVar MCF outputs.
3. **Resolution, Differ & Validation (`genmcf`, differ, import_validation)**: Generates resolved MCFs, compares against baseline version, and verifies validation rules.

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

Run the hermetic unit tests for the Python download routine:

```bash
.env/bin/python -m unittest statvar_imports/opendataforafrica/kenya_census/download_test.py
```

### 6.2 Pre-Submission Validation Rules

`validation_config.json` configures import-specific rules:
- `check_all_statvars_freshness`: SQL validator ensuring `MaxDate >= '2009' AND total_svs > 0` across all active StatVars.
- `check_deleted_records_percent`: Strict cap with `threshold: 0.1` (0.1%), matching rule description.
- Default lint checks (`check_lint_error_count` and `check_missing_refs_count` at threshold 0) are inherited from the base validation framework.
