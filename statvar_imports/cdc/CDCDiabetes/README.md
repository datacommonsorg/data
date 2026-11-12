# CDC US Diabetes Surveillance System (`CDCDiabetes`) StatVar Import

## 1. Overview & Provenance
* **Import Name:** `CDCDiabetes`
* **Source Agency:** U.S. Centers for Disease Control and Prevention (CDC) — United States Diabetes Surveillance System (USDSS)
* **Provenance URL:** `https://usdss.cdc.gov/diabetes/surveillance.html`
* **Data Download URLs (CDC USDSS API):**
  * `https://usdss.cdc.gov/diabetes/data/surveillance/SurveillanceIndicatorsYearsList_Counties.json`
  * `https://usdss.cdc.gov/diabetes/InitAppData_a76d04a7-0f44-4f44-9147-3be5354c46ba.json` (dynamically discovered via `surveillance_entry.*.app.js`)
  * `POST https://usdss.cdc.gov/webapi/Diabetes/AllCountiesDataOneYear`
* **Release Frequency / Refresh Schedule:** Weekly check (`30 05 * * 1`, `P1Y` source release frequency)
* **Geographic Coverage:**
  * `3,159` US Counties and county-equivalents (`dcid:geoId/{FIPS:05d}`, including the 8 pre-2022 Connecticut counties `geoId/09001..09015` in `2004–2021` and 9 Connecticut planning regions `geoId/09110..09190` in `2022–2024+`)

---

## 2. Datasets & Architecture

This import downloads and processes county-level age-adjusted prevalence and standard error estimates for adults aged 20+ years from the CDC USDSS API (`download.py` + `stat_var_processor.py`):

* **Historical Baseline in GCS (`2004–2021`)**:
  * `gs://unresolved_mcf/cdc/diabetes/historical/cdc_diabetes_historical_2004_2021.csv` (`1,016,418` observations consolidated from the 162 `20240112` CNS/GCS CSVs)
  * Automatically copied by `download.py` into `output_files/` along with `output_files/common_tmcf.tmcf` on every run.
* **CDC USDSS Indicators & Stratifications (`2022–2024+`)**:
  * `IndicatorID=151`: *Diagnosed Diabetes* (Age-Adjusted Percentage, Adults Aged 20+ Years)
  * `IndicatorID=201`: *Obesity* (Age-Adjusted Percentage, Adults Aged 20+ Years)
  * `IndicatorID=202`: *Leisure-Time Physical Inactivity* (Age-Adjusted Percentage, Adults Aged 20+ Years)
  * `SexID=591` (Total), `SexID=592` (Male), `SexID=593` (Female)
  * Standard error derived from the 95% confidence interval upper limit: `stdError = round((UpperLimit - Percentage) / 1.96, 5)`
* **Generated Input & PVMap Files**:
  * `input_files/cdc_diabetes.csv` (processed with `cdc_diabetes_pvmap.csv` and `cdc_diabetes_metadata.csv`)
* **StatVars (`18` active across 3 conditions × 3 sex groups × 2 `statType`s)**:
  * **Diagnosed Diabetes:** `Percent_Person_20OrMoreYears_WithDiabetes`, `dc/d4j16hnl53es2`, `dc/xmpy89x1nh8cg`, `dc/xwtlmj1vg7618`, `dc/nh3s4skee5483`, `dc/ryjdx30rfbfbb`
  * **Obesity:** `Percent_Person_20OrMoreYears_Obesity`, `dc/bzfel0wfs6qhf`, `dc/x13tvt8jsgrm4`, `dc/73vt0flpsz26b`, `dc/4lvmzr1h1ylk1`, `dc/h3vxgc4gwl4c7`
  * **Physical Inactivity:** `Percent_Person_20OrMoreYears_PhysicalInactivity`, `dc/1yfe8eezs4jbc`, `dc/ty7pq88d26963`, `dc/bv6fv4et0d8pd`, `dc/tcqb49dvg7k53`, `dc/t1hj2ymqdg5s6`

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

| Metric | Count | Explanation |
| :--- | :--- | :--- |
| **Previous Observations** | `1,016,418` | Consolidated legacy CSVs covering `2004–2021` across `3,151` counties |
| **Current Observations** | `1,181,088` | Automated pipeline covering `2004–2021` historical (`1,016,418`) + `2022–2024` CDC USDSS API data (`164,670`) across `3,159` counties |
| **Added Observations** | `+164,670` | `2022–2024` county-level prevalence and standard error observations across `3,144` counties (`18` StatVars) |
| **Modified Observations** | `0` | 100% exact value match across all `1,016,418` historical observations |
| **Deleted Observations** | `0` (`0.0%`) | Zero deletions |
| **Schema Diffs** | `0` | All `18` StatVars resolve to existing production Data Commons `StatisticalVariable`s |

---

## 4. How to Run

From the repository root (`data/`):

1. **Run `download.py` to copy the `2004–2021` historical baseline CSV from GCS into `output_files/` and download fresh `2022+` CDC USDSS API data into `input_files/`:**
   ```bash
   python3 statvar_imports/cdc/CDCDiabetes/download.py \
     --output_dir=statvar_imports/cdc/CDCDiabetes/input_files \
     --historical_output_dir=statvar_imports/cdc/CDCDiabetes/output_files
   ```

2. **Process the downloaded CSV using `stat_var_processor.py`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/cdc/CDCDiabetes/input_files/cdc_diabetes.csv \
     --pv_map=statvar_imports/cdc/CDCDiabetes/cdc_diabetes_pvmap.csv \
     --config_file=statvar_imports/cdc/CDCDiabetes/cdc_diabetes_metadata.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/cdc/CDCDiabetes/output_files/cdc_diabetes \
     --output_counters=statvar_imports/cdc/CDCDiabetes/counters/cdc_diabetes_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/cdc/CDCDiabetes -p "*_test.py"
   ```
