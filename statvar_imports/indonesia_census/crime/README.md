# Indonesia Census - Crime (`Indonesia_Census_Crime`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Crime`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia) / Indonesian National Police Headquarters (*Mabes Polri*)
* **Provenance URL:** `https://www.bps.go.id/en/statistics-table/2/MTAxIzI=/number-of-crime-according-to-police-territorial-jurisdiction.html`
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/domain/0000/var/101/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/101/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `2000` – `2024`
* **Total Observations:** `802` observations across `1` `StatisticalVariable` (`dcid:Count_CriminalActivities`) and `35` places (`country/IDN` and `34` Regional Police / Provincial Jurisdictions `wikidataId/Q...`).

---

## 2. Datasets Covered

1. **Number Of Crime According To Police Territorial Jurisdiction (`var_id=101`, `2000–2024`)**
   - **Geographic levels:** Country (`country/IDN`) and 34 Regional Police (*Kepolisian Daerah / Polda*) jurisdictions mapped to Indonesian Provinces (`wikidataId/Q1823` through `wikidataId/Q5096` and `wikidataId/Q3125978`).
   - **Extracted file:** `input_files/crime_according_to_police_territorial_jurisdiction.csv`
   - **StatVar (`1`):** `dcid:Count_CriminalActivities` (`populationType: CriminalActivities`, `measuredProperty: count`, `statType: measuredValue`).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the legacy CNS Crime CSVs (`/cns/jv-d/home/datcom/v3_mcf/country/indonesia/20240402/Crime_According_To_Police_Territorial_Jurisdiction_2000-2022*.csv`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `709` | Legacy CNS import across 8 multi-year CSV slices covering `2000–2022` (34 places; `METRO JAYA` was unresolved in legacy `place_resolver`) |
| **Current Observations** | `802` | Automated pipeline covering `2000–2024` across all `35` jurisdictions |
| **Added Observations** | `+93` | `2023–2024` annual crime statistics across 34 jurisdictions (`+68` obs) plus resolved `METRO JAYA` (`wikidataId/Q3630`) across `2000–2024` (`+25` obs) |
| **Modified Observations** | `0` | 100% exact value match across all `709` historical CNS observations |
| **Deleted Observations** | `0` (`0.0%`) | Zero deletions |
| **Schema Diffs** | `0` | Resolves to existing standard `dcid:Count_CriminalActivities` in `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`802` `NumRowSuccesses`, `803` `NumNodeSuccesses`).
* **Warnings Breakdown (`3` warnings):**
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` (`11`), `StatsCheck_MaxPercentFluctuationGreaterThan500` (`1`), & `StatsCheck_3_Sigma` (`2`): Expected year-over-year variations in reported crime counts across multi-decade (`2000–2024`) provincial police jurisdiction series.

---

## 5. How to Run

1. **Download and preprocess the source data into `input_files/crime_according_to_police_territorial_jurisdiction.csv`:**
   ```bash
   python3 statvar_imports/indonesia_census/crime/download.py \
     --output_dir=statvar_imports/indonesia_census/crime/input_files
   ```

2. **Run `stat_var_processor.py` to generate `output_files/indonesia_crime_output.csv` and `output_files/indonesia_crime_output.tmcf`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/crime/input_files/crime_according_to_police_territorial_jurisdiction.csv \
     --pv_map=statvar_imports/indonesia_census/crime/indonesia_crime_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/crime/indonesia_crime_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/crime/indonesia_crime_places_resolved.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/crime/output_files/indonesia_crime_output \
     --output_counters=statvar_imports/indonesia_census/crime/counters/indonesia_crime_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/crime -p "*_test.py"
   ```
