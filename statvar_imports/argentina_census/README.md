# Argentina Census (`Argentina_Census`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Argentina_Census`
* **Import Group:** `international_stats` (`auto1w`)
* **Source Agency:** Instituto Nacional de Estadística y Censos (INDEC), Republic of Argentina
* **Provenance URL:** `https://www.indec.gob.ar/`
* **Data Download Landing Page:** `https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-24-84`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 5 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `1980` – `2023`
* **Total Observations:** `51,318` across `1,034` unique `StatisticalVariable`s and `514` places (`country/ARG`, `23` AA1 Provinces, and `490` AA2 Departments/Partidos).

---

## 2. Datasets Covered

1. **Population by Single Age, 5-Year Age Group, and Sex (`1980, 1991, 2001, 2010, 2022`)**
   - **Geographic levels:** Country (`country/ARG`) and 23 Provinces (AA1).
   - **Extracted file:** `input_files/argentina_population.csv`
   - **StatVars:** `Count_Person`, `Count_Person_Male`, `Count_Person_Female`, `Count_Person_<Age>`, `Count_Person_<Age>_Male`, `Count_Person_<Age>_Female` (single-year ages `0`–`99`, `100OrMoreYears`, 5-year cohorts `0To4Years`–`95To99Years`, `85OrMoreYears`, `95OrMoreYears`, `99OrMoreYears`).
2. **Urban and Rural Population by Age and Sex (`1980, 1991, 2001, 2010`)**
   - **Geographic levels:** Country (`country/ARG`) and 23 Provinces (AA1).
   - **Extracted file:** `input_files/argentina_urban_rural.csv`
   - **StatVars:** `Count_Person_Urban`, `Count_Person_Rural`, `Count_Person_Urban_Male`, `Count_Person_Urban_Female`, `Count_Person_Rural_Male`, `Count_Person_Rural_Female`, and age/sex breakdowns (`Count_Person_<Age>_Urban_<Gender>`, `Count_Person_<Age>_Rural_<Gender>`).
3. **Department (AA2) Total Population (`2001, 2010, 2022`)**
   - **Geographic levels:** 490 Departments / Partidos (AA2).
   - **Extracted file:** `input_files/argentina_population_aa2.csv`
   - **StatVars:** `Count_Person`.
4. **Literacy and Illiteracy for Population Aged 10+ Years (`2010`)**
   - **Geographic levels:** Country (`country/ARG`) and 23 Provinces (AA1).
   - **Extracted file:** `input_files/argentina_literacy.csv`
   - **StatVars:** `Count_Person_10OrMoreYears`, `Count_Person_10OrMoreYears_Literate`, `Count_Person_10OrMoreYears_Illiterate`, `Count_Person_10OrMoreYears_Illiterate_AsAFractionOf_Count_Person_10OrMoreYears` (`unit: Percent`, `scalingFactor: 100`).
5. **Infant Mortality Rate per 1,000 Live Births (`2005–2023`)**
   - **Geographic levels:** Country (`country/ARG`) and 23 Provinces (AA1).
   - **Extracted file:** `input_files/argentina_infant_mortality.csv`
   - **StatVars:** `Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth` (`scalingFactor: 1000`).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the previous production `Argentina_Census` import (`/cns/jv-d/home/datcom/v3_resolved_mcf/country/argentina/latest/`):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `41,104` | Legacy import covering 1980–2010 Census & 2005–2019 Infant Mortality |
| **Current Observations** | `51,318` | Refreshed import covering 1980–2022 Census & 2005–2023 Infant Mortality |
| **Added Observations** | `+10,215` | 2022 National Census (`c2022_*_c4_*.xlsx` age/sex for Country + 23 Provinces, `c2022_*_c1_*.xlsx` AA2 department totals) and 2020–2023 Infant Mortality rates (`tasa_mortalidad_infantil_2005_2023.xls`) |
| **Modified Observations** | `15` | Official INDEC historical revisions in the updated `tasa_mortalidad_infantil_2005_2023.xls` publication |
| **Deleted Observations** | `1` (`0.002%`) | Single historical observation revised/suppressed in upstream INDEC publication (`DELETED_RECORDS_PERCENT` = `0.002%`, well below the `0.1%` threshold) |
| **Schema Diffs** | `0` | All `1,034` StatVars resolve to existing definitions in `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`51,318` `NumRowSuccesses`, `51,318` `NumNodeSuccesses`).
* **Warnings Breakdown:**
  * `StrSplit_EmptyToken_unit` (`51,294`) & `StrSplit_EmptyToken_scalingFactor` (`50,838`): Expected behavior from `stat_var_processor.py` outputting a unified CSV table with columns `observationDate,observationAbout,variableMeasured,value,unit,scalingFactor`. Pure population count observations do not have a `unit` or `scalingFactor`; only the illiteracy percentage (`24` rows, `unit: Percent, scalingFactor: 100`) and infant mortality rate (`456` rows, `scalingFactor: 1000`) populate those columns.
  * `StatsCheck_Data_Holes` (`8,819`): Expected because national population censuses in Argentina are conducted decennially (`1980`, `1991`, `2001`, `2010`, `2022`) rather than every single year.
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` (`1,588`) & `StatsCheck_MaxPercentFluctuationGreaterThan500` (`65`): Expected inter-censal population growth over 10- to 12-year intervals (`1980 -> 1991 -> 2001 -> 2010 -> 2022`), especially in older age cohorts (`80+` years) and fast-growing provinces/departments.

---

## 5. How to Run

1. **Download and extract the source data into `input_files/*.csv`:**
   ```bash
   python3 statvar_imports/argentina_census/download.py
   ```

2. **Run `stat_var_processor.py` to generate `output_files/argentina_census_output.csv` and `output_files/argentina_census_output.tmcf`:**
   ```bash
   python3 tools/statvar_importer/stat_var_processor.py \
     --input_data=statvar_imports/argentina_census/input_files/*.csv \
     --pv_map=statvar_imports/argentina_census/argentina_census_pvmap.csv \
     --config_file=statvar_imports/argentina_census/argentina_census_metadata.csv \
     --places_resolved_csv=statvar_imports/argentina_census/argentina_places_resolved.csv \
     --output_path=statvar_imports/argentina_census/output_files/argentina_census_output \
     --output_counters=statvar_imports/argentina_census/counters/argentina_census_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/argentina_census -p "*_test.py"
   ```
