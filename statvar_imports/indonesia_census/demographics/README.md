# Indonesia Census - Demographic Population (`Indonesia_Census_Demographics`) StatVar Import

## 1. Overview & Provenance
* **Import Name:** `Indonesia_Census_Demographics`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/`
* **Data Download URL (BPS WebAPI):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/ind/domain/0000/var/{2790,2791,2792}/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/0000/var/{2790,2791,2792}/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Geographic Coverage:**
  * Country (`country/IDN`)
  * 38 Provinces (`AdministrativeArea1`, `wikidataId/Q...`, including the 4 new Papua provinces split in late 2022: `Southwest Papua`, `South Papua`, `Central Papua`, `Highland Papua`)
  * 514 Regencies and Cities (`AdministrativeArea2` / `City`, `Kabupaten` / `Kota`, `wikidataId/Q...`)

---

## 2. Datasets & Architecture

This import downloads and processes Indonesia's demographic population statistics from the BPS WebAPI (`download.py` + `stat_var_processor.py`):

* **Historical Baseline in GCS (`1971–2022`)**:
  * `gs://unresolved_mcf/country/indonesia/demographics/historical/idn_population_historical_1971_2022.csv` (`3,339` observations)
  * `gs://unresolved_mcf/country/indonesia/demographics/historical/idn_age_gender_historical_2010_2022.csv` (`8,935` observations)
  * Automatically copied by `download.py` into `output_files/` along with `output_files/common_tmcf.tmcf` on every run.
* **BPS Variable IDs (`2023–2026+`)**:
  * `var_id=2790`: *Jumlah Penduduk menurut Kabupaten/Kota dan Kelompok Umur* (Total Population by Regency/City and Age Group)
  * `var_id=2791`: *Jumlah Penduduk Laki-Laki menurut Kabupaten/Kota dan Kelompok umur* (Male Population by Regency/City and Age Group)
  * `var_id=2792`: *Jumlah Penduduk Perempuan menurut Kabupaten Kota dan Kelompok Umur* (Female Population by Regency/City and Age Group)
* **Generated Input Files**:
  * `input_files/idn_population.csv` (processed with `idn_population_pvmap.csv`)
  * `input_files/idn_age_gender.csv` (processed with `idn_age_gender_pvmap.csv`)
* **StatVars (`51` active)**:
  * `dcid:Count_Person`
  * `dcid:Count_Person_Male`, `dcid:Count_Person_Female`
  * 16 five-year age brackets (`0To4Years` .. `75OrMoreYears`) across Total, Male, and Female (`Count_Person_{Age}`, `Count_Person_{Age}_Male`, `Count_Person_{Age}_Female`).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the legacy CNS Demographic CSVs (`/cns/jv-d/home/datcom/v3_mcf/country/indonesia/`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `12,274` | Legacy CNS demographic CSVs covering `1971–2022` |
| **Current Observations** | `125,086` | Automated pipeline covering `1971–2022` historical + `2023–2026` BPS WebAPI data across all `553` places |
| **Added Observations** | `+112,812` | `2023–2026` annual population (`+2,212` obs) and age/gender breakdown (`+110,600` obs) across 553 places |
| **Modified Observations** | `0` | 100% exact value match across all `12,274` historical CNS observations |
| **Deleted Observations** | `0` (`0.0%`) | Zero deletions |
| **Schema Diffs** | `0` | All StatVars resolve to existing standard Data Commons `StatisticalVariable`s |

---

## 4. How to Run

1. **Set your BPS WebAPI key (or rely on the default GCS key path `gs://unresolved_mcf/country/indonesia/config.json` via `--api_key_gcs_path` in Cloud Batch) and run `download.py` to copy historical baseline CSVs from GCS into `output_files/` and download fresh BPS WebAPI data into `input_files/`:**
   ```bash
   export BPS_API_KEY="<your_bps_api_key>"
   python3 statvar_imports/indonesia_census/demographics/download.py \
     --output_dir=statvar_imports/indonesia_census/demographics/input_files \
     --historical_output_dir=statvar_imports/indonesia_census/demographics/output_files
   ```

2. **Process the downloaded CSVs using `stat_var_processor.py`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/demographics/input_files/idn_population.csv \
     --pv_map=statvar_imports/indonesia_census/demographics/idn_population_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/demographics/idn_demographic_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/demographics/idn_places_resolved.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/demographics/output_files/idn_population \
     --output_counters=statvar_imports/indonesia_census/demographics/counters/idn_population_counters.csv

   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/demographics/input_files/idn_age_gender.csv \
     --pv_map=statvar_imports/indonesia_census/demographics/idn_age_gender_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/demographics/idn_demographic_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/demographics/idn_places_resolved.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/demographics/output_files/idn_age_gender \
     --output_counters=statvar_imports/indonesia_census/demographics/counters/idn_age_gender_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/demographics -p "*_test.py"
   ```


