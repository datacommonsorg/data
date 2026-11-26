# Indonesia Census - Education (`Indonesia_Census_Education`) StatVar Import Document

## 1. Overview & Provenance

* **Import Name:** `Indonesia_Census_Education`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL (human-facing):** `https://www.bps.go.id/en/statistics-table?subject=521` *(Note: `www.bps.go.id` enforces a Cloudflare bot challenge returning HTTP 403 to automated GCP clients; programmatic downloads use `https://webapi.bps.go.id/v1/api/...`, with developer portal `https://webapi.bps.go.id/developer/` reachable directly from GCP.)*
* **Data Download URL (BPS WebAPI & SIMDASI API):**
  * Portal: `https://webapi.bps.go.id/developer/`
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/simdasi/id/25/tahun/{year}/id_tabel/{table_id}/wilayah/0000000/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `2011` – `2025`
* **Total Observations:** `25,636` observations across `78` `StatisticalVariable` nodes and `39` places (`country/IDN` and `38` Provinces `wikidataId/Q...`).

---

## 2. Datasets Covered

1. **Literacy Rate of Population Aged 15 Years and Over by Province (`var_id = 1458`, `domain = 0000`, `2013–2025`)**
   - **Source URL:** `https://www.bps.go.id/en/statistics-table/2/MTQ1OCMy/literacy-rate-of-population-aged-15-years-and-over-by-province.html`
   - **Geographic Coverage:** Country (`country/IDN`) and Provinces (`AdministrativeArea1`, `39` unique places including the 4 new Papua provinces).
   - **StatVar (`1`):** `dcid:Count_Person_15OrMoreYears_Literate_AsAFractionOf_Count_Person_15OrMoreYears` (`unit: Percent`, `scalingFactor: 100`).

2. **Literacy Rate of Population Aged 15 Years and Over by Sex (`var_id = 1460`, `domain = 0000`, `2011–2025`)**
   - **Source URL:** `https://www.bps.go.id/en/statistics-table/2/MTQ2MCMy/literacy-rate-of-population-aged-15-years-and-over-by-sex.html`
   - **Geographic Coverage:** Country (`country/IDN`).
   - **StatVars (`3`):**
     - `dcid:Count_Person_15OrMoreYears_Male_Literate_AsAFractionOf_Count_Person_15OrMoreYears_Male` (`unit: Percent`, `scalingFactor: 100`)
     - `dcid:Count_Person_15OrMoreYears_Female_Literate_AsAFractionOf_Count_Person_15OrMoreYears_Female` (`unit: Percent`, `scalingFactor: 100`)
     - `dcid:Count_Person_15OrMoreYears_Literate_AsAFractionOf_Count_Person_15OrMoreYears` (`unit: Percent`, `scalingFactor: 100`)

3. **Number of Schools, Teachers, and Students by Province across 9 Education Levels (`2016–2025`)**
   - **Source URL:** `https://www.bps.go.id/en/statistics-table?subject=521`
   - **Geographic Coverage:** Country (`country/IDN`) and Provinces (`AdministrativeArea1`, `39` unique places).
   - **StatVars (`75` across Public, Private, and Public+Private ownership):**
     - Under Ministry of Education, Culture, Research, and Technology (`UnderMinistryOfResearchTechnologyAndHigherEducation`):
       - Primary Schools (`SD`, `id_tabel = UkJNaEl6ZHRVYXNaMzZhZG9BbS9ZZz09`)
       - Junior High Schools (`SMP`, `id_tabel = dzdoVmp3YWdGNU0yWEgraVIwbmRqZz09`)
       - Senior High Schools (`SMA`, `id_tabel = a1lFcnlHNXNYMFlueG8xL0ZOZnU0Zz09`)
       - Vocational High Schools (`SMK`, `id_tabel = MU90V01YZ0RxenhmbFdsU21iUHh2Zz09`)
       - Higher Education / Universities (`Perguruan Tinggi`, `id_tabel = cmdTdG5vU0IwKzBFR20rQnpuZEYzdz09`)
     - Under Ministry of Religious Affairs (`UnderMinistryOfReligion`):
       - Islamic Kindergarten (`Raudatul Athfal / RA`, `id_tabel = SmNxWnFzemcvcUkvdndUbTJGc2RQdz09`)
       - Islamic Elementary Schools (`Madrasah Ibtidaiyah / MI`, `id_tabel = TE9sZFVvdVErcU9Ka0VreVUrNnZEQT09`)
       - Islamic Junior High Schools (`Madrasah Tsanawiyah / MTs`, `id_tabel = Uys0Mk9kelpxamVmMUYrMkRHSFcyZz09`)
       - Islamic Senior High Schools (`Madrasah Aliyah / MA`, `id_tabel = UE1YYmk0TnR5TnoycHlYbzNnbkFIZz09`)

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the legacy production Education (`gs://unresolved_mcf/country/indonesia/20240402/`, 53 CSVs) & Literacy (`gs://unresolved_mcf/country/indonesia/idn_literacyrate_*.csv`, 7 CSVs) files:

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `15,453` | Legacy manual import across 60 Education and Literacy CSV files covering `2013–2022` (`35` places, `78` StatVars) |
| **Current Observations** | `25,636` | Automated pipeline covering `2011–2025` across all `39` places and `78` StatVars |
| **Added Observations** | `+10,603` | `+10,183` net new observations (`2023–2025` annual updates `+8,600` including `644` for the 4 new Papua provinces `Q115253263`, `Q112810104`, `Q61439296`, `Q12486766`; missing legacy school years `2017` `MI`/`MTs`/`MA` `+945` and `2018` `SMA`/`SMK` `+630`; `2011–2013` national literacy by sex `+8`) plus `+420` Raudatul Athfal School/Teacher observations migrated to corrected `LocalGovernmentOwned__PrivatelyOwned` DCIDs |
| **Modified Observations** | `1,153` | `0` diffs across all `45` Kemendikbud (`SD`/`SMP`/`SMA`/`SMK`/`Univ`) StatVars and `2014–2022` literacy; `1` fix for a legacy `2013` manual bug where `country/IDN` Total literacy (`93.92`) had been populated with the Male rate (`96.47`); `1,152` official BPS finalized yearbook revisions for Kemenag (`RA`/`MI`/`MTs`/`MA`) in `2017`, `2018`, `2021`, and `2022` |
| **Deleted Observations** | `420` (`2.72%`) | One-time schema bugfix: exclusively `210` obs each from the 2 un-ingested legacy Raudatul Athfal staging StatVars that had mismatched `establishmentOwnership` (`LocalGovernmentOwned` for Schools, `PrivatelyOwned` for Teachers), now unified under `LocalGovernmentOwned__PrivatelyOwned` (`0` rows exist in production KG; the default `0.1%` deletion threshold is intentionally kept unchanged) |
| **Schema Diffs** | `+10` / `-2` / `73` mod | `+8` provisional enum nodes (`indonesia_education_schema.mcf`) and `+2` / `-2` corrected Raudatul Athfal StatVar DCIDs; `73` unchanged school StatVar DCIDs updated with sentence-cased English `name` properties |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`25,636` `NumRowSuccesses`, `25,719` `NumNodeSuccesses`, `180,372` `NumPVSuccesses`).
* **Existence / Missing Reference Warnings:** `0` across `182,436` live KG existence checks (`Existence_NumChecks: 182,436`; provisional enum definitions are provided consistently via `indonesia_education_schema.mcf` matching `Provisional_Indonesia_Census_Education_Schema.mcf` in the companion schema CL).
* **Expected / Source-Data Warnings (`indonesia_education_output`):**
  * `StrSplit_EmptyToken_unit` (`25,176`) & `StrSplit_EmptyToken_scalingFactor` (`25,176`): Expected on the `25,176` non-percentage school/teacher/student count rows in the combined CSV (only the `460` literacy rate rows populate `unit=Percent` and `scalingFactor=100`).
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` (`11`) & `StatsCheck_MaxPercentFluctuationGreaterThan500` (`1`): Authentic BPS source jumps — primarily Banten (`wikidataId/Q3540`) public university students (`2018: 18,512` → `2019: 1,036,054`, `+5,496.66%` when Universitas Terbuka was included under Banten in SIMDASI) and teachers (`689` → `1,461`, `+112.05%`), public university students in Papua (`30,781` → `65,473`) and Maluku (`17,875` → `41,415`), and small-base provincial Kemenag counts in Papua, North Kalimantan (`wikidataId/Q3903`), and North Maluku (`wikidataId/Q5094`).
  * `StatsCheck_Data_Holes` (`30`): Authentic, officially documented 1-year source reporting gap for **Papua (`wikidataId/Q5095`)** in **`2023` (`2023/2024` academic year)** across all `30` Ministry of Religious Affairs (`UnderMinistryOfReligion`) StatVars (`3` `RaudatulAthfal` + `9` `MadrasahIbtidaiyah` + `9` `MadrasahTsanawiyah` + `9` `MadrasahAliyah`, each spanning `2017–2025`):
    * Following the late-2022 administrative split of Papua into four provinces (Papua, Papua Selatan, Papua Tengah, and Papua Pegunungan), the Ministry of Religious Affairs (Kemenag EMIS) did not report `2023/2024` counts for any of those four provinces.
    * Both **BPS *Statistik Indonesia 2024*** (`pub_id=c1bacde03256343b2bf769b0`, e.g., RA table p. 243) and **BPS *Statistik Indonesia 2025*** (`pub_id=8cfe1a589ad3693396d3db9f`, e.g., RA table p. 256) explicitly print `NA` for Papua in `2023/2024` with the table footnote: *"Tidak termasuk Provinsi Papua, Papua Selatan, Papua Tengah, dan Papua Pegunungan / Excluding Papua, Papua Selatan, Papua Tengah, and Papua Pegunungan Provinces."*
    * Kemenag EMIS reporting resumed for Papua in `2024/2025` (temporarily aggregating the newly split provinces) and was fully disaggregated across all four provinces in `2025/2026` (**BPS *Statistik Indonesia 2026***, `pub_id=a43f03f45543dc4e9942f44c`, p. 275). *(Similarly, Papua Barat Daya (`wikidataId/Q115253263`) prints `...` in `2024/2025` with the BPS note that its counts were temporarily included under Papua Barat before re-separating in `2025/2026`.)* Because this `2023` gap is an official source omission, values are left absent rather than interpolated.

---

## 5. Pipeline Files & How to Run

### Pipeline Files
- `download.py`: Queries the BPS WebAPI (`var_id=1458` and `var_id=1460`) and the BPS SIMDASI API (`id/25`, with header-verified fallback to BPS `Statistik Indonesia` yearbook PDFs), saving raw key-redacted JSONs and PDFs to `raw_files/` and writing `input_files/indonesia_education_input.csv`.
- `download_test.py`: Unit tests verifying API key redaction, HTTP method/status logging, downward seed-year probing, raw payload retention, place name normalization, Indonesian dot-separated integer cleaning, multi-table downloading, header-verified yearbook PDF fallback parsing, CSV output formatting, and error handling.
- `indonesia_education_pvmap.csv`: Property-Value mappings with sentence-cased English `name` and Indonesian `alternateName` for all 78 education and literacy indicators and the 39 Indonesia country/province DCIDs (`observationAbout:*`, also used as the province allowlist by `download.py`'s yearbook PDF parser).
- `indonesia_education_metadata.csv`: Configuration parameters for `stat_var_processor.py` (retaining default `reconcile_nodes`, `drop_statvars_without_svobs`, and `spell_check` with allowlisted Indonesian school proper nouns).
- `indonesia_education_schema.mcf`: Provisional enum schema definitions (`isProvisional: dcs:True`) for the 8 new `SchoolLevelEnum`, `SchoolManagementEnum`, and `EstablishmentOwnershipEnum` values, matching `Provisional_Indonesia_Census_Education_Schema.mcf` in the companion schema CL and passed to `--existing_schema_mcf`.
- `manifest.json`: Import automation specification for `Indonesia_Census_Education`.
- `requirements.txt`: Per-import dependency (`pymupdf`) for the BPS yearbook PDF fallback.
- `validation_config.json`: Validation rules enforcing separately scoped `MAX_DATE_CONSISTENT` checks (Susenas literacy vs. SIMDASI school StatVars) and a January-safe `SQL_VALIDATOR` checking StatVar count (`= 78`), observation count (`>= 24,000`), non-negative values, percentage bounds (`<= 100`), place coverage (`>= 35`), and annual freshness (`>= YEAR(CURRENT_DATE) - 2`).
- `test_data/`: Sample input (`indonesia_education_input.csv`) and expected processor outputs (`indonesia_education_output.csv`, `indonesia_education_output.tmcf`).

### Running Locally

1. **Install the per-import requirement (for BPS yearbook PDF fallback), set your BPS API key, and download the source data into `input_files/indonesia_education_input.csv` (and raw payloads into `raw_files/`):**
   ```bash
   export BPS_API_KEY=<your-bps-api-key>  # or pass --api_key=<your-bps-api-key>
   pip install -r statvar_imports/indonesia_census/education/requirements.txt
   python3 statvar_imports/indonesia_census/education/download.py \
     --output_dir=statvar_imports/indonesia_census/education/input_files \
     --raw_output_dir=statvar_imports/indonesia_census/education/raw_files
   ```

2. **Run `stat_var_processor.py` to generate `output_files/indonesia_education_output.{csv,tmcf}` and `_stat_vars.mcf`:**
   ```bash
   export DC_API_KEY=<your-dc-api-key>

   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/education/input_files/indonesia_education_input.csv \
     --pv_map=statvar_imports/indonesia_census/education/indonesia_education_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/education/indonesia_education_metadata.csv \
     --existing_schema_mcf=statvar_imports/indonesia_census/education/indonesia_education_schema.mcf \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=statvar_imports/indonesia_census/education/output_files/indonesia_education_output \
     --output_counters=statvar_imports/indonesia_census/education/counters/indonesia_education_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/education -p "*_test.py"
   ```
