# Mexico: National Institute of Statistics and Geography (INEGI) — `MexicoCensus`

## Import Overview
This import (`MexicoCensus`) ingests national (`country/MEX`) and state-level demographic, vital statistics, health, education, religion, migration, and quarterly unemployment statistics from Mexico's **Instituto Nacional de Estadística y Geografía (INEGI)** across **21 datasets**:

- **Demographics & Population**: Total Population, Population Density, Median Age, Average Annual Population Growth Rate, and International Migration (Foreign-Born Population).
- **Vital Statistics & Mortality**: Registered Births, Registered Deaths, Infant Mortality, Male Mortality Rate (Excess Male Mortality Index), Life Expectancy, Diabetes Deaths, Homicides, and Suicides.
- **Education**: Literacy Status (Ages 6 to 14), Literate Population (Ages 15 and Older), School Enrollment, and Student-to-Teacher / Student-to-School Ratios.
- **Religion**: Catholic Population, Irreligious Population, and Population of Other Religions (Non-Catholic).
- **Labor / Employment**: National Quarterly Unemployed Population (Total, With Work Experience, and Without Work Experience).

- **Source URL**: `https://www.inegi.org.mx/temas/`
- **Import Type**: Automated Python API Downloader (`download.py`) + Data Commons `stat_var_processor.py`
- **Source Data Availability**: `P3M` (Quarterly), `P1Y` (Annual), `P5Y` (5-Year Intercensal / Survey), `P10Y` (Decennial Census)
- **Autorefresh Type**: Fully Automated (`manifest.json`)
- **Geographic Coverage**: Country (`country/MEX`) and States

---

## Dataset Details

The import comprises **21 datasets** configured in `config.json` and `manifest.json`:

| # | Dataset Name | Description | Release Frequency |
|---:|:---|:---|:---|
| 1 | `Mexico_Migration` | Foreign-born population residing in Mexico by state, sex, and country of birth (`USA`, `GTM`, `JPN`, `ESP`, `FRA`, and `OtherCountries`). | `P10Y` |
| 2 | `Mexico_Avg_Annual_Growth_Rate` | Average annual population growth rate (`GrowthRate_Count_Person`) by state over 5-year periods. | `P5Y` |
| 3 | `Mexico_Births_Registered` | Registered live births (`Count_BirthEvent`) by state and sex. | `P1Y` |
| 4 | `Mexico_Death_Diabetes` | Registered deaths caused by diabetes mellitus (`Count_MortalityEvent_Diabetes`) by state, 5-year age group, and sex. | `P1Y` |
| 5 | `Mexico_Deaths_Registered` | Total registered deaths (`Count_Death`) by state of residence and sex. | `P1Y` |
| 6 | `Mexico_Homicide_Population` | Registered deaths by homicide (`Count_MortalityEvent_Assault(Homicide)`) by state of residence and sex. | `P1Y` |
| 7 | `Mexico_Infant_Mortality` | Registered deaths of infants under 1 year of age (`Count_Death_LessThan1Year`) by state of residence and sex. | `P1Y` |
| 8 | `Mexico_LifeExpectancy` | Life expectancy at birth (`LifeExpectancy_Person`) by state and sex. | `P1Y` |
| 9 | `Mexico_Literacy_Status_6To14` | Population aged 6 to 14 years by state, sex, and ability to read and write (literate vs. illiterate). | `P5Y` |
| 10 | `Mexico_Literate_15OrMore` | Population aged 15 years and older by state, sex, and literacy condition (literate vs. illiterate). | `P5Y` |
| 11 | `Mexico_Male_Mortality_Rate` | Male-to-female mortality ratio (`Count_Death_Male_AsAFractionOf_Count_Person_Male`) by state of residence. | `P1Y` |
| 12 | `Mexico_Median_Age` | Median age of the population (`Median_Age_Person`) by state. | `P5Y` |
| 13 | `Mexico_Population_Density` | Population density (`Count_Person_PerArea`, in `PersonPerSquareKilometer`) by state. | `P5Y` |
| 14 | `Mexico_Religion_Catholic` | Population aged 5 years and older professing Catholicism by state, 5-year age group, and sex. | `P10Y` |
| 15 | `Mexico_Religion_Irreligion` | Population aged 5 years and older with no religion by state, 5-year age group, and sex. | `P10Y` |
| 16 | `Mexico_Religion_OtherReligionThanCatholicism` | Population aged 5 years and older professing a religion other than Catholicism by state, 5-year age group, and sex. | `P10Y` |
| 17 | `Mexico_SchoolEnrollment` | Student enrollment (`Count_Student`) by state, education level, and sex across school cycles. | `P1Y` |
| 18 | `Mexico_Student_Teacher_Ratio` | Student-to-teacher and student-to-school ratios by state and education level across school cycles. | `P1Y` |
| 19 | `Mexico_Suicide_Population` | Registered deaths by suicide (`Count_Death_IntentionalSelfHarm(Suicide)`) by state of residence and sex. | `P1Y` |
| 20 | `Mexico_Total_Population` | Total population (`Count_Person`) by state, 5-year age group, and sex. | `P5Y` |
| 21 | `Mexico_Unemployed_Population` | National quarterly unemployed population (`Count_Person_Unemployed`, total and by work experience). | `P3M` |

---

## Import Procedure & Download Script Details

### 1. `download.py` and `config.json`
`download.py` is the unified Python downloader that fetches all 21 datasets from INEGI's APIs and writes the raw CSV files into `input_files/`. All API base URLs, GCS bucket paths, and dataset identifiers are externalized in `config.json` (no URLs or bucket paths are hardcoded in `download.py`).

#### Supported CLI Flag in `download.py`
- `--config_path`: Path to the JSON configuration file (defaults to `config.json`).

---

### 2. How `download.py` Fetches Data (`GET` & `POST` Workflows)

#### A. INEGI PxWeb API Workflow (`source_type: "pxweb"` — 20 Datasets)
For the 20 PxWeb datasets, `download.py` (`fetch_pxweb_raw_table`) executes a 3-step HTTP workflow against `pxweb_api_base_url`:
1. **`GET /tabquery?pxq=<pxq_id>`**:
   - Retrieves the saved table layout (`stub` row dimensions, `heading` column dimensions, and `file` identifier). Preserving the `/tabquery` axis order ensures tables are not transposed.
2. **`GET /tabulado?lang=es&file=<file_id>`**:
   - Retrieves the live table metadata (`title` and `variables` array with dimension `code`, `values`, and `valueTexts`).
   - `reconcile_variable_codes` reconciles any renamed dimension names between `/tabquery` and `/tabulado`, and `is_footnote_value` separates trailing footnote rows (`Nota:`, `Fuente:`) from data value codes.
3. **`POST /datatable?lang=es&file=<file_id>`**:
   - Submits a JSON query payload (`build_pxweb_datatable_payload`) requesting `"filter": "item"` with the explicit list of valid value codes for each dimension.
   - `unpack_pxweb_datatable` reconstructs the full INEGI tabular CSV layout (institutional header row, table title row, 1- or 2-level column headers, 1- or 2-column row stubs, numeric cells with `|<footnote>` suffixes stripped, and trailing footnote rows).

#### B. INEGI ServicioCuadros API Workflow (`source_type: "cuadros"` — `Mexico_Unemployed_Population`)
For `Mexico_Unemployed_Population`, `download.py` (`fetch_cuadros_raw_table`) executes a `GET` request against `cuadros_api_base_url`:
- **`GET <cuadros_api_base_url>/446566|446713|446718/false/0700/es/json/<start_year>/<current_year>/0/0/3`**:
  - Fetches quarterly series JSON for indicator IDs `446566` (`Total`), `446713` (`With experience`), and `446718` (`Without experience`) from `start_year` through the current year.
  - `parse_cuadros_response` formats the response into year header rows and Roman-numeral quarter rows (`I`, `II`, `III`, `IV`).

---

### 3. Handling the 2 Historical Single-Year Overwritten Datasets (`Mexico_Literacy_Status_6To14` & `Mexico_Literate_15OrMore`)

Unlike multi-year INEGI tables that retain prior years as columns, `Educacion/Educacion_01` (`Mexico_Literacy_Status_6To14`) and `Educacion/Educacion_02` (`Mexico_Literate_15OrMore`) are **single-year cross-sectional snapshot tables** where INEGI overwrites the table in-place whenever a new census or intercensal survey is released (the reference year appears only in the table title row).

To preserve all historical years without storing data files in the GitHub repository, these two datasets are configured in `config.json` with `"archive_by_year": true` and `"historical_dir": "gs://unresolved_mcf/mexico_census/historical_inputs"`. When `download.py` runs (`_write_year_archived_dataset`):
1. **Pull Historical Snapshots from GCS $\to$ Local `historical_inputs/`**:
   - Connects to `gs://unresolved_mcf/mexico_census/historical_inputs/` and downloads all previously archived `<Dataset>_*_input.csv` snapshots into the local `historical_inputs/` folder.
2. **Save & Upload Current Year Snapshot $\to$ Local `historical_inputs/` and GCS**:
   - Extracts the 4-digit reference year from Row 2 (the INEGI table title) of the freshly downloaded table via `_extract_snapshot_year`.
   - Writes `historical_inputs/<Dataset>_<Year>_input.csv` locally and uploads it back to `gs://unresolved_mcf/mexico_census/historical_inputs/<Dataset>_<Year>_input.csv` so future source updates are automatically archived alongside prior years.
3. **Copy All Year Snapshots $\to$ `input_files/`**:
   - Copies all `<Dataset>_*_input.csv` files from `historical_inputs/` into `input_files/` so `stat_var_processor.py` processes all historical and current snapshots together via the wildcard `--input_data=input_files/<Dataset>_*_input.csv`.

---

## Other Scripts & Configuration Files Used

- **`../../../tools/statvar_importer/stat_var_processor.py`**:
  - Core Data Commons processor that reads each dataset's raw input CSV(s) from `input_files/`, applies the dataset PVMap and shared place mapping, and generates the cleaned CSV, `.tmcf`, and `_stat_vars.mcf` files in `output/`.
- **`config.json`**:
  - Stores `pxweb_api_base_url`, `cuadros_api_base_url`, `historical_gcs_path`, and the per-dataset API parameters for all 21 datasets.
- **`manifest.json`**:
  - Defines the automated import execution sequence (`download.py` followed by 21 `stat_var_processor.py` invocations), `source_files`, `import_inputs`, and `validation_config.json`.
- **`metadata.csv`**:
  - Shared `stat_var_processor.py` configuration file defining provenance URL and description parameters.
- **`pvmap/place_mapping.csv`**:
  - Shared place-resolution PVMap (`#Header,observationAbout`) that maps `"Estados Unidos Mexicanos"` / `"Total"` to `country/MEX` and all 32 Mexican state names (including INEGI footnote-suffixed and historical variants) to their `wikidataId/Q...` DCIDs.
- **`pvmap/<Dataset>_pvmap.csv`**:
  - 21 dataset-specific Property-Value maps translating Spanish row stubs, column headers, and time periods into Data Commons `StatVarObservation` properties.
  - For datasets where 4-digit observation counts can collide with 4-digit year headers (`Mexico_Deaths_Registered`, `Mexico_Death_Diabetes`, `Mexico_Homicide_Population`, `Mexico_Religion_Irreligion`, `Mexico_Religion_OtherReligionThanCatholicism`, `Mexico_Total_Population`), year keys are scoped with a leading colon (`:YEAR`) so only header-row cells match year keys.
- **`validation_config.json`**:
  - Differ validation rules applied during automated import runs.

---

## Script Execution Details

### Step 1: Download All Raw Input Files
Run from `statvar_imports/mexico_subnational_population_statistics/mexico_census/`:
```bash
python3 download.py --config_path=config.json
```

### Step 2: Process Datasets with `stat_var_processor.py`

#### Standard Datasets (19 Datasets — Single Input File)
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/<Dataset>_input.csv \
  --pv_map=pvmap/<Dataset>_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/<Dataset>_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

#### Year-Archived Literacy Datasets (2 Datasets — Wildcard Multi-Input)
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/Mexico_Literacy_Status_6To14_*_input.csv \
  --pv_map=pvmap/Mexico_Literacy_Status_6To14_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/Mexico_Literacy_Status_6To14_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/Mexico_Literate_15OrMore_*_input.csv \
  --pv_map=pvmap/Mexico_Literate_15OrMore_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/Mexico_Literate_15OrMore_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

---

## Cleaned Data, MCFs, and Template MCFs

### Output File Paths
For each of the 21 datasets (`<Dataset>`), `stat_var_processor.py` generates:
- **Cleaned CSV**: `output/<Dataset>_output.csv`
- **Template MCF**: `output/<Dataset>_output.tmcf`
- **StatVar Node MCF** (when custom StatVars are emitted): `output/<Dataset>_output_stat_vars.mcf` and `output/<Dataset>_output_stat_vars_schema.mcf`

### Cleaned CSV Columns
Depending on whether a property is constant across all rows of a dataset (written to `.tmcf`) or varies per row (written as a CSV column), `output/<Dataset>_output.csv` contains:
- `observationDate`: Reference year (`YYYY`) or quarter end-month (`YYYY-03`, `YYYY-06`, `YYYY-09`, `YYYY-12`).
- `observationAbout`: Resolved place DCID (`country/MEX` or state `wikidataId/Q...`).
- `value`: Numeric observation value.
- `variableMeasured`: Target Data Commons `StatisticalVariable` DCID.
- `unit` (when multiple units exist in the same dataset, such as headcounts and `Percent` in the literacy datasets): Unit DCID.
