# Sri Lanka Census (`Srilanka_Census`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Srilanka_Census`
* **Import Group:** `international_stats` (`auto1w`)
* **Source Agencies:** Department of Census and Statistics of Sri Lanka / UNFPA & The World Bank (via Humanitarian Data Exchange — HDX)
* **Provenance URL:** `https://data.humdata.org/dataset/cod-ps-lka`
* **Data Download URLs:**
  * `https://data.humdata.org/dataset/cod-ps-lka`
  * `https://data.humdata.org/dataset/world-bank-agriculture-and-rural-development-indicators-for-sri-lanka`
  * `https://data.humdata.org/dataset/world-bank-education-indicators-for-sri-lanka`
* **Release Frequency / Refresh Schedule:** Weekly check (`30 05 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `1960` – `2025`
* **Total Observations:** `13,130` active observations in `latest` + `182` historical observations (`13,312` total) across `197` unique `StatisticalVariable`s (`191` active + `6` historical) and `35` places (`country/LKA`, `9` AdministrativeArea1 Provinces `LK1`–`LK9`, and `25` AdministrativeArea2 Districts `LK11`–`LK92`).

---

## 2. Datasets Covered

1. **Subnational Population Statistics (`cod-ps-lka`, `2022–2023`)**
   - **Geographic levels:** Country (`country/LKA`), 9 Provinces (`LK1`–`LK9`), and 25 Districts (`LK11`–`LK92`).
   - **Extracted file:** `input_files/srilanka_population.csv`
   - **StatVars (`57`):** `Count_Person`, `Count_Person_Male`, `Count_Person_Female`, and 5-year age/gender cohorts (`Count_Person_<Age>`, `Count_Person_<Age>_Male`, `Count_Person_<Age>_Female` for `0To4Years` through `75To79Years` and `80OrMoreYears`).
2. **World Bank Agriculture and Rural Development Indicators (`1960–2024`)**
   - **Geographic levels:** Country (`country/LKA`).
   - **Extracted file:** `input_files/srilanka_agriculture.csv`
   - **StatVars (`19` active + `6` historical):** Agricultural land (`Area_Farm`, `Area_Farm_AsAFractionOf_Area`, `Area_Farm_IrrigatedLand_AsAFractionOf_Area_Farm`, `Area_Farm_ArableLand`, `Area_Farm_PermanentCrops`, `Area_Forest`), crop/cereal production and yield, livestock production index, fertilizer consumption, agricultural machinery, and rural population (`Count_Person_Rural`, `Count_Person_Rural_AsAFractionOf_Count_Person`, `GrowthRate_Count_Person_Rural`).
3. **World Bank Education Indicators (`1960–2025`)**
   - **Geographic levels:** Country (`country/LKA`).
   - **Extracted file:** `input_files/srilanka_education.csv`
   - **StatVars (`115`):** School enrollment, gross/net intake, progression, completion, persistence, literacy rates, pupil-teacher ratios, education expenditure, and Barro-Lee educational attainment across age/sex cohorts (`15To19Years` through `75To79Years`, `15OrMoreYears`, `25OrMoreYears`, `15To24Years`).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the previous production `Srilanka_Census` import (`/cns/jv-d/home/datcom/v3_resolved_mcf/country/srilanka/latest/`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `10,754` | Legacy import covering 1960–2021 WDI indicators and 2022 subnational population |
| **Current Observations** | `13,312` | `13,130` active observations in `latest` + `182` archived in `historical` |
| **Added Observations** | `+2,558` | 2023 subnational population across Country, 9 Provinces, and 25 Districts (`+1,995` obs) plus 2022–2025 WDI Agriculture & Education updates (`+563` obs) |
| **Modified Observations** | `588` | Official World Bank WDI historical revisions across 1960–2021 national series |
| **Deleted Observations** | `0` (`0.0%`) | Zero deletions (`182` observations from 6 discontinued WDI agriculture indicators are preserved in `gs://unresolved_mcf/country/srilanka/historical/` and `gs://resolved_mcf/country/srilanka/historical/`) |
| **Schema Diffs** | `0` | All `197` StatVars resolve to existing definitions in `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`13,130` `NumRowSuccesses`, `13,130` `NumNodeSuccesses`).
* **Warnings Breakdown:**
  * `StrSplit_EmptyToken_unit` (`9,365`) & `StrSplit_EmptyToken_scalingFactor` (`10,840`): Expected behavior from `stat_var_processor.py` outputting a unified CSV table (`srilanka_census_output.csv`) with columns `observationAbout,observationDate,value,variableMeasured,unit,scalingFactor`. Pure count and index observations do not use a `unit` or `scalingFactor`; only percentage, currency, and area/mass rate StatVars populate those columns.
  * `StatsCheck_Data_Holes` (`113`): Expected because UNESCO/World Bank education survey indicators and Barro-Lee educational attainment series (`BAR.NOED.*`, `BAR.PRM.*`, `BAR.SEC.*`, `BAR.TER.*`) are reported at 5-year intervals (`1970, 1975, ..., 2015`) or in years when national household surveys were conducted.
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` (`118`), `StatsCheck_MaxPercentFluctuationGreaterThan500` (`27`), & `StatsCheck_3_Sigma` (`6`): Expected historical year-over-year variations over the 65-year span (`1960–2025`) in national fertilizer consumption, agricultural raw material imports/exports, and cohort-specific out-of-school / enrollment counts.

---

## 5. How to Run

1. **Download and preprocess the source data into `input_files/*.csv`:**
   ```bash
   python3 statvar_imports/srilanka_census/download.py \
     --output_dir=statvar_imports/srilanka_census/input_files \
     --pv_map=statvar_imports/srilanka_census/srilanka_census_pvmap.csv
   ```

2. **Run `stat_var_processor.py` to generate `output_files/srilanka_census_output.csv` and `output_files/srilanka_census_output.tmcf`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/srilanka_census/input_files/*.csv \
     --pv_map=statvar_imports/srilanka_census/srilanka_census_pvmap.csv \
     --config_file=statvar_imports/srilanka_census/srilanka_census_metadata.csv \
     --places_resolved_csv=statvar_imports/srilanka_census/srilanka_places_resolved.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/srilanka_census/output_files/srilanka_census_output \
     --output_counters=statvar_imports/srilanka_census/counters/srilanka_census_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/srilanka_census -p "*_test.py"
   ```
