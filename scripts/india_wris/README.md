# India Water Resources Information System (WRIS) Water Quality Import

## 1. Overview & Dataset Information

- **Import Name**: `IndiaWRISWaterQuality`
- **Source**: [India Water Resources Information System (WRIS)](https://indiawris.gov.in/wris/#/DataDownload)
- **Publisher**: National Water Informatics Centre (NWIC), Ministry of Jal Shakti (aggregating Central Ground Water Board (CGWB) and Central Water Commission (CWC) monitoring stations)
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — `indiawris.gov.in` is geo-fenced to Indian IP addresses and requires interactive CAPTCHA + email export, so raw source exports are staged to GCS `gs://unresolved_mcf/india_wris/water_quality/input_files/`)
- **Schedule**: `0 4 * * 1` (Weekly on Monday at 04:00 UTC)
- **Coverage**:
  - **Ground Water Quality (`India_WRIS_Ground`)**: `2000-05` to `2023-04` (`P1Y` observation period across 27 chemical and trace-element parameters)
  - **Ground Water Quality Retained (`India_WRIS_Ground_Prod_Retained`)**: `2000` to `2018` (`P1Y` observation period retaining historical station observations dropped by upstream source exports)
  - **Surface Water Quality (`India_WRIS_Surface`)**: `2001-01` to `2020-03` (`P1M` observation period across 27 chemical and trace-element parameters)
- **Entity Resolution**:
  - Station level (`WaterQualitySite`): `indiaWris/<LGD_DistrictCode>_<StationName>`
  - Contained in District (`Place`): Resolved via `IndiaDistrictsMapper` (`lgdCode`)

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring scripts, `import_inputs`, `source_files`, and `validation_config.json` |
| `validation_config.json` | Scoped `SQL_VALIDATOR` freshness and completeness rules for Ground and Surface Water |
| `download.sh` | Shell script to fetch staged input CSVs from `gs://unresolved_mcf/india_wris/water_quality/input_files/` into `input_files/` |
| `base.py` | Shared `WaterQualityBase` class handling empty-row filtering, station/state/district LGD normalization, deduplication, and atomic CSV/MCF/TMCF generation |
| `util/groundWater.json` | Column-to-StatVar and unit definitions for the 27 Ground Water parameters |
| `util/surfaceWater.json` | Column-to-StatVar and unit definitions for the 27 Surface Water parameters |
| `India_WRIS_Ground/preprocess.py` | CLI entry point for generating `India_WRIS_Ground.{csv,mcf,tmcf}` and `India_WRIS_Ground_Prod_Retained.{csv,tmcf}` |
| `India_WRIS_Ground/preprocess_test.py` | Hermetic unit tests for Ground Water and Retained preprocessing |
| `India_WRIS_Surface/preprocess.py` | CLI entry point for generating `India_WRIS_Surface.{csv,mcf,tmcf}` |
| `India_WRIS_Surface/preprocess_test.py` | Hermetic unit tests for Surface Water preprocessing |
| `India_WRIS_Rainfall/` | Companion India WRIS Rainfall dataset directory |

## 3. Ingestion Workflow

### 3.1 Upstream Source Data Updates (Semi-Automated Staging)
When refreshed water quality data is exported from `https://indiawris.gov.in/wris/#/DataDownload`:
1. Select `Env & Water Quality` -> `Ground Water Quality` (Agency: `CGWB`) or `Surface Water Quality` (Agency: `CWC`), complete the CAPTCHA, and download the `.zip` archive.
2. Extract the raw CSV and stage the updated files to GCS:
   ```bash
   gcloud storage cp groundWater.csv surfaceWater.csv India_WRIS_Ground_Prod_Retained.csv \
     gs://unresolved_mcf/india_wris/water_quality/input_files/
   ```

### 3.2 Automated Ingestion Pipeline
During import execution, the pipeline runs sequentially from `scripts/india_wris/`:
1. **Download (`download.sh`)**: Fetches `groundWater.csv`, `India_WRIS_Ground_Prod_Retained.csv`, and `surfaceWater.csv` from `gs://unresolved_mcf/india_wris/water_quality/input_files/` into `input_files/`.
2. **Ground Water Preprocessing (`India_WRIS_Ground/preprocess.py`)**:
   - Applies the 16 canonical state, district, and station name normalizations (e.g., `Janjgir - Champa` -> `janjgir-champa`, `Bijapur` -> `vijayapura`, `Puruliya` -> `Purulia`, `West Nimar` -> `Khargone`, `Darjiling` -> `Darjeeling`, `Hugli` -> `hooghly`, `Kodarma` -> `Koderma`, `Kumuram Bheem` -> `kumuram bheem asifabad`, `Shrawasti` -> `Shravasti`, `Baramula` -> `Baramulla`, `Rajauri` -> `Rajouri`, `Khammam`/`Rangareddy` -> `Telangana`, `Daman`/`Diu` -> `dadra and nagar haveli and daman and diu`).
   - Deduplicates station-date records and generates `output/India_WRIS_Ground.{csv,mcf,tmcf}` and sanitized `output/India_WRIS_Ground_Prod_Retained.{csv,tmcf}`.
3. **Surface Water Preprocessing (`India_WRIS_Surface/preprocess.py`)**:
   - Resolves district LGD codes and station DCIDs and generates `output/India_WRIS_Surface.{csv,mcf,tmcf}`.
4. **Validation (`validation_config.json`)**:
   - Enforces non-empty StatVar generation and scoped `MaxDate` freshness checks across all Ground Water, Retained, and Surface Water StatVars.

## 4. Running Locally & Testing

Run preprocessing from the repository root:

```bash
.env/bin/python scripts/india_wris/India_WRIS_Ground/preprocess.py \
  --input_csv=scripts/india_wris/input_files/groundWater.csv \
  --retained_input_csv=scripts/india_wris/input_files/India_WRIS_Ground_Prod_Retained.csv \
  --output_dir=scripts/india_wris/output

.env/bin/python scripts/india_wris/India_WRIS_Surface/preprocess.py \
  --input_csv=scripts/india_wris/input_files/surfaceWater.csv \
  --output_dir=scripts/india_wris/output
```

Run hermetic unit tests via `run_tests.sh`:

```bash
./run_tests.sh -p scripts/india_wris
```