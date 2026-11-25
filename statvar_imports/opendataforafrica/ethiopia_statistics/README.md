# Ethiopia Statistics (`EthiopiaStatistics`)

## 1. Overview & Dataset Information

- **Source**: [Ethiopia Open Data for Africa](https://ethiopia.opendataforafrica.org/)
- **Publisher**: Central Statistical Agency (CSA) of Ethiopia
- **Import Name**: `EthiopiaStatistics`
- **Schedule**: `0 5 * * 1` (Mondays at 05:00 UTC)
- **Coverage**: Demographics, Population, Health, Education, and Employment (2000 – 2022)
- **Place Types**: Country (`country/ETH`), AdministrativeArea1 (Regions / Chartered Cities), and AdministrativeArea2 (Zones in `xtqdbuc`), resolved to Wikidata / Data Commons DCIDs.

## 2. Datasets

`download.py` fetches all five datasets directly from the `ethiopia.opendataforafrica.org` Knoema REST API (`/api/1.0/meta/dataset/<id>`, `/api/1.0/meta/dataset/<id>/dimension/<dim>`, and paginated `/api/1.0/data/raw`) using `util/download_util.py`:

| Dataset ID | Source Dataset | Output Input CSV | Years |
| :--- | :--- | :--- | :--- |
| `udghlsf` | Regional Population Distribution and Daily per Capita Calorie Intake, 2000-2011, Ethiopia | `input_files/ethiopia_demographics.csv` | 2000, 2005, 2011 |
| `xtqdbuc` | Ethiopia Statistics, 2011 (5 population indicators) | `input_files/ethiopia_population_all_year.csv` | 2000 – 2011 |
| `teakvke` | Population and Households of Ethiopia, 2007 (Country + Admin1 population by sex & residence) | `input_files/ethiopia_population_2007.csv` | 2007 |
| `xpcyhcf` | Population Projection by Region and Sex (2022) | `input_files/ethiopia_population_projection_2022.csv` | 2022 |
| `yusibcg` | Demographic and Health Survey, 2014, Ethiopia (full paginated download) | `input_files/ethiopia_yusibcg.csv` | 2011, 2014 |

## 3. Directory Layout & Key Files

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import automation manifest declaring `download.py`, `stat_var_processor.py` runs, `import_inputs`, `source_files`, and `validation_config.json` |
| `validation_config.json` | Scoped SQL freshness validation rules merged with Data Commons default validation rules |
| `download.py` | Direct API downloader using `util/download_util.py`; saves raw API JSON to `raw_files/` and normalized CSVs to `input_files/` |
| `download_test.py` | Hermetic unit tests for `download.py` (pagination, filtering, transformations, error handling) |
| `*_pvmap.csv` | Property-Value mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Processor configuration files for each dataset |
| `*_places_resolved.csv` | Place name / code to Data Commons DCID resolution tables |
| `test_data/` | Sample input fixtures and expected processor outputs |
| `raw_files/`, `input_files/`, `output/`, `counters/` | Runtime-generated directories (excluded from Git via `.gitignore`) |

## 4. Prerequisites & Running Locally

Run commands from the repository root (`data/`), or from this import directory with import-relative paths. Ensure Python dependencies from `import-automation/executor/requirements.txt` are installed (e.g. via `./run_tests.sh -r`, which creates `.env/`).

### 4.1 Download Source Data

```bash
.env/bin/python statvar_imports/opendataforafrica/ethiopia_statistics/download.py \
  --raw_dir=statvar_imports/opendataforafrica/ethiopia_statistics/raw_files \
  --output_dir=statvar_imports/opendataforafrica/ethiopia_statistics/input_files
```

Raw API responses are preserved verbatim under `raw_files/<dataset_id>_raw.json`, and normalized CSVs are written atomically to `input_files/`.

### 4.2 Run `stat_var_processor.py`

Run from `statvar_imports/opendataforafrica/ethiopia_statistics/` (matching `manifest.json`):

```bash
# 1. Ethiopia Demographics (udghlsf)
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/ethiopia_demographics.csv \
  --pv_map=ethiopia-Ethiopia_Demographics_pvmap.csv \
  --config_file=ethiopia-Ethiopia_Demographics_metadata.csv \
  --places_resolved_csv=ethiopia-Ethiopia_Demographics_places_resolved.csv \
  --output_path=output/ethiopia_demographics \
  --output_counters=counters/ethiopia_demographics_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 2. Ethiopia Population All Year (xtqdbuc)
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/ethiopia_population_all_year.csv \
  --pv_map=ethiopia-Ethiopia_Population_all_year_pvmap.csv \
  --config_file=ethiopia-Ethiopia_Population_all_year_metadata.csv \
  --output_path=output/ethiopia_population_all_year \
  --output_counters=counters/ethiopia_population_all_year_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 3. Ethiopia Population 2007 (teakvke)
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/ethiopia_population_2007.csv \
  --pv_map=ethiopia_population_2007_pvmap.csv \
  --config_file=ethiopia_population_2007_metadata.csv \
  --places_resolved_csv=ethiopia_population_2007_places_resolved.csv \
  --output_path=output/ethiopia_population_2007 \
  --output_counters=counters/ethiopia_population_2007_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 4. Ethiopia Population Projection 2022 (xpcyhcf)
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/ethiopia_population_projection_2022.csv \
  --pv_map=ethiopia-Population_Projection_by_Region_and_Sex_2022_pvmap.csv \
  --config_file=ethiopia-Population_Projection_by_Region_and_Sex_2022_metadata.csv \
  --output_path=output/ethiopia_population_projection_2022 \
  --output_counters=counters/ethiopia_population_projection_2022_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

# 5. Ethiopia DHS 2014 (yusibcg)
../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/ethiopia_yusibcg.csv \
  --pv_map=ethiopia-yusibcg_pvmap.csv \
  --config_file=ethiopia-yusibcg_metadata.csv \
  --places_resolved_csv=ethiopia-yusibcg_places_resolved.csv \
  --output_path=output/ethiopia_yusibcg \
  --output_counters=counters/ethiopia_yusibcg_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 5. Testing & Validation

Run unit tests from the repository root:

```bash
./run_tests.sh -p statvar_imports/opendataforafrica/ethiopia_statistics
# or directly:
.env/bin/python -m unittest discover -v -s statvar_imports/opendataforafrica/ethiopia_statistics -p "*_test.py"
```

Validation in `validation_config.json` enforces scoped `MaxDate` freshness checks alongside default Data Commons validation rules (deletion threshold, empty import check, missing references, and lint error count).

## 6. Refresh & Deployment Notes

- All five datasets are downloaded directly from `ethiopia.opendataforafrica.org` APIs without manual staging.
- Direct HTTP reachability from GCP Cloud Batch (`us-central1`) to `ethiopia.opendataforafrica.org` APIs has been verified without Cloudflare/bot challenges, and `ImportDiffer` against the CNS production baseline passes with 0 deletions across all five datasets.
