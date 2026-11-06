# Argentina Census (`Argentina_Census`) StatVar Import Document

## 1. Overview & Provenance
* **Import Name:** `Argentina_Census`
* **Import Group:** `international_stats` (`auto1w`)
* **Source Agency:** Instituto Nacional de Estadística y Censos (INDEC), Republic of Argentina
* **Provenance URL:** `https://www.indec.gob.ar/`
* **Data Download Landing Page:** `https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-24-84`
* **Release Frequency / Refresh Schedule:** Weekly check (`0 5 * * 1`, `P1Y` source release frequency)
* **Date Range in KG:** `1980` – `2023`
* **Total Observations:** `53,281` across `1,034` unique `StatisticalVariable`s and `529` places (`country/ARG`, `24` AA1 Jurisdictions including `Ciudad Autónoma de Buenos Aires` `wikidataId/Q1486` and `Buenos Aires` Province `wikidataId/Q44754`, and `504` AA2 Departments/Partidos/Comunas).

---

## 2. Datasets Covered

1. **Population by Single Age, 5-Year Age Group, and Sex (`1980, 1991, 2001, 2010, 2022`)**
   - **Geographic levels:** Country (`country/ARG`) and 24 Jurisdictions (23 Provinces + `Ciudad Autónoma de Buenos Aires`, AA1).
   - **Extracted file:** `input_files/argentina_population.csv`
   - **StatVars:** `Count_Person`, `Count_Person_Male`, `Count_Person_Female`, `Count_Person_<Age>`, `Count_Person_<Age>_Male`, `Count_Person_<Age>_Female` (single-year ages `0`–`99`, `100OrMoreYears`, 5-year cohorts `0To4Years`–`95To99Years`, `85OrMoreYears`, `95OrMoreYears`, `99OrMoreYears`).
2. **Urban and Rural Population by Age and Sex (`1980, 1991, 2001, 2010`)**
   - **Geographic levels:** Country (`country/ARG`) and 24 Jurisdictions (AA1; note that INDEC's 1991/2001 C101/C104–C106 tables omit `Ciudad Autónoma de Buenos Aires` as it has no rural population).
   - **Extracted file:** `input_files/argentina_urban_rural.csv`
   - **StatVars:** `Count_Person_Urban`, `Count_Person_Rural`, `Count_Person_Urban_Male`, `Count_Person_Urban_Female`, `Count_Person_Rural_Male`, `Count_Person_Rural_Female`, and age/sex breakdowns (`Count_Person_<Age>_Urban_<Gender>`, `Count_Person_<Age>_Rural_<Gender>`). Note: In the 2001 urban/rural workbook (`c01totalpais7.xls`), the `1-4` age group is mapped to `0-1` (`Count_Person_0To1Years_*`) to preserve backwards compatibility with the 144 legacy 2001 production observations.
3. **Department / Partido / Comuna (AA2) Total Population (`2001, 2010, 2022`)**
   - **Geographic levels:** 504 Departments / Partidos / Comunas (489 Provincial Departments/Partidos + 15 CABA Comunas, AA2).
   - **Extracted file:** `input_files/argentina_population_aa2.csv`
   - **StatVars:** `Count_Person`.
4. **Literacy and Illiteracy for Population Aged 10+ Years (`2010`)**
   - **Geographic levels:** Country (`country/ARG`) and 24 Jurisdictions (AA1).
   - **Extracted file:** `input_files/argentina_literacy.csv`
   - **StatVars:** `Count_Person_10OrMoreYears`, `Count_Person_10OrMoreYears_Literate`, `Count_Person_10OrMoreYears_Illiterate`, `Count_Person_10OrMoreYears_Illiterate_AsAFractionOf_Count_Person_10OrMoreYears` (`unit: Percent`, `scalingFactor: 100`).
5. **Infant Mortality Rate per 1,000 Live Births (`2005–2023`)**
   - **Geographic levels:** Country (`country/ARG`) and 24 Jurisdictions (AA1).
   - **Extracted file:** `input_files/argentina_infant_mortality.csv`
   - **StatVars:** `Count_MortalityEvent_AsAFractionOf_Count_BirthEvent_LiveBirth` (`scalingFactor: 1000`).

---

## 3. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the previous production `Argentina_Census` manual import (`/cns/jv-d/home/datcom/v3_mcf/country/argentina/output_files/`, `41,104` observations across `148` legacy CSVs):

| Metric | Count | Explanation |
|---|---|---|
| **Previous Observations** | `41,104` | Legacy manual import covering 1980–2010 Census & 2005–2021 Infant Mortality |
| **Current Observations** | `53,281` | Refreshed automated import covering 1980–2022 Census & 2005–2023 Infant Mortality across all 24 Jurisdictions + 504 AA2 places |
| **Buenos Aires Province (`wikidataId/Q44754`) vs. CABA (`wikidataId/Q1486`) Place Split** | Corrected | Legacy manual import mapped `"Buenos Aires"` (Province, ~17.5M pop) to `wikidataId/Q1486` (Autonomous City of Buenos Aires / CABA, ~3.1M pop) and omitted CABA. This refresh maps `Buenos Aires` (Province) to `wikidataId/Q44754` and adds `Ciudad Autónoma de Buenos Aires` (`wikidataId/Q1486`) and its 15 Comunas (`wikidataId/Q5780334`, etc.). As a result, historical `wikidataId/Q1486` rows in `argentina_population`, `argentina_literacy`, and `argentina_infant_mortality` are updated from Buenos Aires Province values to true CABA values, while Buenos Aires Province's series (including its 147 urban/rural rows from 1991/2001/2010) are emitted under `wikidataId/Q44754`. |
| **Other Legacy Bug Fixes in `2010`** | `15` Modified + `1` DCID Typo | `13` department-level `Count_Person` rows in Chubut where legacy truncated Spanish thousands separators (`.` in `11.141 -> 11`, `131.313 -> 131`, `186.583 -> 187`, etc.), `1` row in `Count_Person_10OrMoreYears_Literate` for Chaco (`wikidataId/Q44757`, `80602 -> 806020`), `1` row in `Count_Person_10OrMoreYears_Illiterate_AsAFractionOf_Count_Person_10OrMoreYears` for Neuquén (`wikidataId/Q44800`, `23 -> 2.3`), and `1` trailing-parenthesis DCID typo fixed for Libertador General San Martín (`wikidataId/Q1120737)` -> `wikidataId/Q1120737`, value `4707`). |
| **Schema Diffs** | `0` | All `1,034` StatVars resolve to existing definitions in `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` |

### Detailed Breakdown of Legacy 2010 Parsing Bug Fixes

| Diff Type | Year | Place (`observationAbout`) | Place Name | `variableMeasured` | Legacy Value | Current Value | Root Cause |
|---|---|---|---|---|---|---|---|
| `DELETED` (re-emitted as `ADDED` on clean DCID) | `2010` | `wikidataId/Q1120737)` -> `wikidataId/Q1120737` | Libertador General San Martín (San Luis) | `Count_Person` | `4707` | `4707` | Fixed trailing parenthesis typo in legacy `argentina_population_aa2_2010.csv:453` |
| `MODIFIED` | `2010` | `wikidataId/Q1007366` | Gaiman (Chubut) | `Count_Person` | `11` | `11141` | Legacy truncated `.` thousands separator (`11.141`) |
| `MODIFIED` | `2010` | `wikidataId/Q1008487` | Gastre (Chubut) | `Count_Person` | `1` | `1427` | Legacy truncated `.` thousands separator (`1.427`) |
| `MODIFIED` | `2010` | `wikidataId/Q1088518` | Rawson (Chubut) | `Count_Person` | `131` | `131313` | Legacy truncated `.` thousands separator (`131.313`) |
| `MODIFIED` | `2010` | `wikidataId/Q1088722` | Sarmiento (Chubut) | `Count_Person` | `11` | `11396` | Legacy truncated `.` thousands separator (`11.396`) |
| `MODIFIED` | `2010` | `wikidataId/Q1088724` | Río Senguer (Chubut) | `Count_Person` | `6` | `5979` | Legacy truncated `.` thousands separator (`5.979`) |
| `MODIFIED` | `2010` | `wikidataId/Q290328` | Telsen (Chubut) | `Count_Person` | `2` | `1644` | Legacy truncated `.` thousands separator (`1.644`) |
| `MODIFIED` | `2010` | `wikidataId/Q368780` | Florentino Ameghino (Chubut) | `Count_Person` | `2` | `1627` | Legacy truncated `.` thousands separator (`1.627`) |
| `MODIFIED` | `2010` | `wikidataId/Q372333` | Languiñeo (Chubut) | `Count_Person` | `3` | `3085` | Legacy truncated `.` thousands separator (`3.085`) |
| `MODIFIED` | `2010` | `wikidataId/Q374155` | Futaleufú (Chubut) | `Count_Person` | `43` | `43076` | Legacy truncated `.` thousands separator (`43.076`) |
| `MODIFIED` | `2010` | `wikidataId/Q662056` | Cushamen (Chubut) | `Count_Person` | `21` | `20919` | Legacy truncated `.` thousands separator (`20.919`) |
| `MODIFIED` | `2010` | `wikidataId/Q690540` | Escalante (Chubut) | `Count_Person` | `187` | `186583` | Legacy truncated `.` thousands separator (`186.583`) |
| `MODIFIED` | `2010` | `wikidataId/Q980073` | Paso de Indios (Chubut) | `Count_Person` | `2` | `1867` | Legacy truncated `.` thousands separator (`1.867`) |
| `MODIFIED` | `2010` | `wikidataId/Q980641` | Tehuelches (Chubut) | `Count_Person` | `5` | `5390` | Legacy truncated `.` thousands separator (`5.390`) |
| `MODIFIED` | `2010` | `wikidataId/Q44757` | Chaco | `Count_Person_10OrMoreYears_Literate` | `80602` | `806020` | Legacy truncated trailing zero (`80602` vs `806,020`) |
| `MODIFIED` | `2010` | `wikidataId/Q44800` | Neuquén | `Count_Person_10OrMoreYears_Illiterate_AsAFractionOf_Count_Person_10OrMoreYears` | `23` | `2.3` | Legacy dropped decimal point (`23%` vs `2.3%`) |

---

## 4. Explanations for `genmcf` Data Warnings (`report.json`)

* **Fatal / Error Count:** `0` fatal, `0` errors (`53,281` `NumRowSuccesses`, `53,281` `NumNodeSuccesses`).
* **Warnings Breakdown:**
  * `StrSplit_EmptyToken_unit` (`53,256`) & `StrSplit_EmptyToken_scalingFactor` (`52,781`): Expected behavior from `stat_var_processor.py` outputting a unified CSV table with columns `observationDate,observationAbout,variableMeasured,value,unit,scalingFactor`. Pure population count observations do not have a `unit` or `scalingFactor`; only the illiteracy percentage (`25` rows, `unit: Percent, scalingFactor: 100`) and infant mortality rate (`475` rows, `scalingFactor: 1000`) populate those columns.
  * `StatsCheck_Data_Holes`: Expected because national population censuses in Argentina are conducted decennially (`1980`, `1991`, `2001`, `2010`, `2022`) rather than every single year.
  * `StatsCheck_MaxPercentFluctuationGreaterThan100` & `StatsCheck_MaxPercentFluctuationGreaterThan500`: Expected inter-censal population growth over 10- to 12-year intervals (`1980 -> 1991 -> 2001 -> 2010 -> 2022`), especially in older age cohorts (`80+` years) and fast-growing provinces/departments.


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
     --statvar_dcid_remap_csv=statvar_imports/argentina_census/argentina_statvar_remap.csv \
     --output_path=statvar_imports/argentina_census/output_files/argentina_census_output \
     --output_counters=statvar_imports/argentina_census/counters/argentina_census_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

3. **Run unit tests:**
   ```bash
   python3 -m unittest discover -v -s statvar_imports/argentina_census -p "*_test.py"
   ```
