# Ethiopia Statistics (`EthiopiaStatistics`)

## 1. Overview & Dataset Information

- **Source**: [Ethiopia Open Data for Africa](https://ethiopia.opendataforafrica.org/)
- **Publisher**: Central Statistical Agency (CSA) of Ethiopia
- **Import Name**: `EthiopiaStatistics`
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — raw API JSONs and normalized CSVs are refreshed via `download.py` and staged to GCS under `gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/`, aligned with `Kenya_Census` rather than `auto1w`)
- **Schedule**: `0 5 * * 1` (Mondays at 05:00 UTC; semi-automated Cloud Batch schedule)
- **Coverage**: Demographics, Population, Health, Education, and Employment (2000 – 2022)
- **Place Types**: Country (`country/ETH`), AdministrativeArea1 (Regions / Chartered Cities), and AdministrativeArea2 (Zones in `xtqdbuc`), resolved to Wikidata / Data Commons DCIDs.

## 2. Datasets

Five datasets from `ethiopia.opendataforafrica.org` are fetched and normalized by `download.py` (using `util/download_util.py` against the Knoema REST API `/api/1.0/meta/dataset/<id>`, `/api/1.0/meta/dataset/<id>/dimension/<dim>`, and paginated `/api/1.0/data/raw`) and staged to GCS (both raw JSONs in `raw_files/` and normalized CSVs in `input_files/`) for `download.sh`:

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
| `manifest.json` | Import automation manifest declaring `download.sh`, `stat_var_processor.py` runs, `import_inputs`, `source_files` (including `raw_files/*` and `input_files/*`), and `validation_config.json` |
| `validation_config.json` | Scoped SQL freshness validation rules merged with Data Commons default validation rules |
| `download.sh` | Shell script run by Cloud Batch to fetch staged CSVs (`input_files/*`) and verbatim raw API JSONs (`raw_files/*`) from `gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/` |
| `download.py` | Operator refresh utility using `util/download_util.py` to fetch raw API JSON into `raw_files/` and normalize CSVs into `input_files/` prior to GCS staging |
| `download_test.py` | Hermetic unit tests for `download.py` (pagination, filtering, null/missing-key handling, transformations, error handling) |
| `*_pvmap.csv` | Property-Value mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Processor configuration files for each dataset |
| `*_places_resolved.csv` | Place name / code to Data Commons DCID resolution tables |
| `test_data/` | Sample input fixtures and expected processor outputs |
| `raw_files/`, `input_files/`, `output/`, `counters/` | Runtime-generated directories (excluded from Git via `.gitignore`) |

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Updates (Operator Refresh)
When updated statistics are published on Ethiopia Open Data for Africa:
1. **Download & Normalize CSVs**: Run `download.py` from the repository root (with `.env` dependencies installed via `./run_tests.sh -r`):
   ```bash
   .env/bin/python statvar_imports/opendataforafrica/ethiopia_statistics/download.py \
     --raw_dir=statvar_imports/opendataforafrica/ethiopia_statistics/raw_files \
     --output_dir=statvar_imports/opendataforafrica/ethiopia_statistics/input_files
   ```
   Raw API responses are preserved verbatim under `raw_files/<dataset_id>_raw.json`, and normalized CSVs are written atomically to `input_files/`.
2. **Stage to GCS**: Upload both the refreshed CSVs and verbatim raw API JSONs to Google Cloud Storage:
   ```bash
   gcloud storage cp \
     statvar_imports/opendataforafrica/ethiopia_statistics/input_files/*.csv \
     gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/input_files/
   gcloud storage cp \
     statvar_imports/opendataforafrica/ethiopia_statistics/raw_files/*_raw.json \
     gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/raw_files/
   ```

### 4.2 Semi-Automated Ingestion Pipeline
During scheduled import runs (`0 5 * * 1`, Mondays at 05:00 UTC) or on-demand triggers after refreshed inputs are staged to GCS, the pipeline executes:
1. **Download (`download.sh`)**: Pulls the staged CSVs (`input_files/*`) and verbatim raw API JSONs (`raw_files/*`) from `gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/`.
2. **Transform (`stat_var_processor.py`)**: Processes all five tables, resolving place DCIDs and generating TMCF, CSV, and StatVar MCF outputs.
3. **Validation**: Enforces scoped freshness rules in `validation_config.json`, `ImportDiffer` checks against the previous baseline, and default lint/existence rules.

## 5. Running `stat_var_processor.py` Locally

Run from `statvar_imports/opendataforafrica/ethiopia_statistics/` (matching `manifest.json`):

```bash
# Fetch staged input CSVs and raw JSONs from GCS
./download.sh

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

## 6. Testing & Validation

Run unit tests from the repository root:

```bash
./run_tests.sh -p statvar_imports/opendataforafrica/ethiopia_statistics
# or directly:
.env/bin/python -m unittest discover -v -s statvar_imports/opendataforafrica/ethiopia_statistics -p "*_test.py"
```

Validation in `validation_config.json` enforces non-tautological `MaxDate` freshness checks across all five tables (`>= 2022` for 2022 projections, `>= 2007` for 2007 census breakdowns, `>= 2011` with at least 144 StatVars at `>= 2014` for DHS 2014, and `>= 2011` for demographics and annual population series) alongside default Data Commons validation rules (deletion threshold, empty import check, missing references, and lint error count).

## 7. URL Accessibility & Cloudflare Notes

- Similar to `Kenya_Census`, the browser-facing Knoema HTML URLs on `ethiopia.opendataforafrica.org` (`/`, `/data/#menu=topic`, `/udghlsf`, `/xtqdbuc`, `/teakvke`, `/xpcyhcf`, `/yusibcg`, and `/legal/termsofuse`) return Cloudflare HTTP `403` challenges to headless GCP/Cloudtop HTTP clients (`curl`), while remaining accessible in interactive browsers.
- The Knoema REST API endpoints (`/api/1.0/meta/dataset/<id>`, `/api/1.0/data/raw`) return HTTP `200`, and staged source inputs/raw JSONs are served via GCS (`gs://unresolved_mcf/opendataforafrica/ethiopia_statistics/`).
