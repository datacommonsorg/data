# Indonesia Census - Education (`Indonesia_Census_Education`) StatVar Import Document

## 1. Overview & Provenance

* **Import Name:** `Indonesia_Census_Education`
* **Import Group:** `international_stats`
* **Source Agency:** Badan Pusat Statistik (BPS - Statistics Indonesia)
* **Provenance URL:** `https://www.bps.go.id/en/statistics-table?subject=521`
* **Data Download URL (BPS WebAPI & SIMDASI API):**
  * `https://webapi.bps.go.id/v1/api/list/model/th/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/list/model/data/lang/eng/domain/0000/var/{var_id}/`
  * `https://webapi.bps.go.id/v1/api/interoperabilitas/datasource/simdasi/id/25/tahun/{year}/id_tabel/{table_id}/wilayah/0000000/`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 05 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `2011` – `2025`
* **Total Observations:** `24,342` observations across `78` `StatisticalVariable` nodes and `39` places (`country/IDN` and `38` Provinces `wikidataId/Q...`).

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

Comparison against the legacy `20240402` Education & Literacy CSVs (`gs://unresolved_mcf/country/indonesia/20240402/`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `15,453` | Legacy manual import across 60 Education and Literacy CSV files covering `2013–2022` (`35` places, `78` StatVars) |
| **Current Observations** | `24,342` | Automated pipeline covering `2011–2025` across all `39` places and `78` StatVars |
| **Added Observations** | `+8,889` | `2023–2025` annual education/literacy updates, `2011–2012` national literacy by sex, and 4 new Papua provinces (`wikidataId/Q115253263`, `wikidataId/Q112810104`, `wikidataId/Q61439296`, `wikidataId/Q12486766`) |
| **Modified Observations** | `8` | Official BPS SIMDASI historical revisions in `2021–2022` for `Count_School_LocalGovernmentOwnedEstablishment_RaudatulAthfal_UnderMinistryOfReligion` |
| **Deleted Observations** | `0` (`0.0%`) | Zero deletions |
| **Schema Diffs** | `0` | 100% exact DCID match across all `78` StatisticalVariables |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`460` literacy + `25,176` school `NumRowSuccesses`).
* **Missing Reference / Empty Token Warnings:** `0` (`indonesia_education_schema.mcf` defines the 8 provisional enum values, and splitting literacy vs. schools eliminates empty `unit`/`scalingFactor` cells).
* **Remaining Source-Data Warnings (`indonesia_schools_output`):**
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` (`11`) & `StatsCheck_MaxPercentFluctuationGreaterThan500` (`1`): Authentic BPS source jumps — primarily Banten public university students (`2018: 18,512` → `2019: 1,036,054` when Universitas Terbuka was included under Banten in SIMDASI) and small provincial Kemenag counts in Papua, North Kalimantan, and North Maluku.
  * `StatsCheck_Data_Holes` (`30`): Authentic 1-year `NA` gap in BPS/Ministry of Religious Affairs (EMIS) `2023/2024` reporting for Papua (`wikidataId/Q5095`) across `RA`, `MI`, `MTs`, and `MA` tables.

---

## 5. Pipeline Files & How to Run

### Pipeline Files
- `download.py`: Queries the BPS WebAPI (`var_id=1458` and `var_id=1460`) and the BPS SIMDASI API (`id/25`, with fallback to BPS `Statistik Indonesia` yearbook PDFs), writing `input_files/indonesia_literacy_input.csv` and `input_files/indonesia_schools_input.csv`.
- `download_test.py`: Unit tests verifying API key redaction, place name normalization, Indonesian dot-separated integer cleaning, multi-table downloading, yearbook PDF fallback parsing, split CSV output formatting, and error handling.
- `indonesia_education_pvmap.csv`: Property-Value mappings for all 78 education and literacy indicators.
- `indonesia_education_metadata.csv`: Configuration parameters for `stat_var_processor.py`.
- `indonesia_education_places_resolved.csv`: Place name to Data Commons DCID mapping covering Indonesia (`country/IDN`) and all 38 provinces (`AdministrativeArea1`).
- `indonesia_education_schema.mcf`: Provisional schema definitions for the 8 Indonesia education enum values referenced by the school StatVars.
- `manifest.json`: Import automation specification for `Indonesia_Census_Education`.
- `requirements.txt`: Per-import dependency (`pymupdf`) for the BPS yearbook PDF fallback.
- `validation_config.json`: Validation rules enforcing `MAX_DATE_CONSISTENT` and `SQL_VALIDATOR` checks on StatVar count, total observation count, non-negative values, and date freshness.
- `test_data/`: Sample literacy and school inputs (`indonesia_literacy_input.csv`, `indonesia_schools_input.csv`) and expected processor outputs (`indonesia_literacy_output.{csv,tmcf}`, `indonesia_schools_output.{csv,tmcf}`).

### Running Locally

1. **Install the per-import requirement (for BPS yearbook PDF fallback) and download the source data into `input_files/`:**
   ```bash
   pip install -r statvar_imports/indonesia_census/education/requirements.txt
   python3 statvar_imports/indonesia_census/education/download.py \
     --output_dir=statvar_imports/indonesia_census/education/input_files
   ```

2. **Run `stat_var_processor.py` for literacy and schools:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/education/input_files/indonesia_literacy_input.csv \
     --pv_map=statvar_imports/indonesia_census/education/indonesia_education_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/education/indonesia_education_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/education/indonesia_education_places_resolved.csv \
     --output_columns=observationAbout,observationDate,value,variableMeasured,unit,scalingFactor \
     --output_path=statvar_imports/indonesia_census/education/output_files/indonesia_literacy_output \
     --output_counters=statvar_imports/indonesia_census/education/counters/indonesia_literacy_counters.csv

   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/indonesia_census/education/input_files/indonesia_schools_input.csv \
     --pv_map=statvar_imports/indonesia_census/education/indonesia_education_pvmap.csv \
     --config_file=statvar_imports/indonesia_census/education/indonesia_education_metadata.csv \
     --places_resolved_csv=statvar_imports/indonesia_census/education/indonesia_education_places_resolved.csv \
     --output_columns=observationAbout,observationDate,value,variableMeasured \
     --output_path=statvar_imports/indonesia_census/education/output_files/indonesia_schools_output \
     --output_counters=statvar_imports/indonesia_census/education/counters/indonesia_schools_counters.csv
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/indonesia_census/education -p "*_test.py"
   ```
