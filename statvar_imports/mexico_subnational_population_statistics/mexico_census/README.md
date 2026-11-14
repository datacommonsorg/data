# Mexico: National Institute of Statistics and Geography (INEGI) — `MexicoCensus_Demographics`, `MexicoCensus_Health`, `MexicoCensus_Education`

## Import Overview
This directory ingests national (`country/MEX`) and state-level demographic, vital statistics, health, education, religion, migration, and quarterly unemployment statistics from Mexico's **Instituto Nacional de Estadística y Geografía (INEGI)** across **21 datasets** organized into **3 imports** in `manifest.json`:

1. **`MexicoCensus_Demographics` (Demographics — 12 Datasets)**: Total Population, Population Density, Median Age, Average Annual Population Growth Rate, International Migration, Registered Births, Religion (Catholic, Irreligion, Other Religions), Literacy Status (Ages 6–14 and Ages 15+), and National Quarterly Unemployed Population.
2. **`MexicoCensus_Health` (Health — 7 Datasets)**: Registered Deaths, Infant Mortality, Life Expectancy, Male Mortality Rate (Excess Male Mortality Index), Diabetes Deaths, Homicides, and Suicides.
3. **`MexicoCensus_Education` (Education — 2 Datasets)**: School Enrollment and Student-to-Teacher / Student-to-School Ratios.

- **Source URL**: `https://www.inegi.org.mx/temas/`
- **Import Type**: Automated Python API Downloader (`download.py`) + Data Commons `stat_var_processor.py`
- **Source Data Availability**: `P3M` (Quarterly), `P1Y` (Annual), `P5Y` (5-Year Intercensal / Survey), `P10Y` (Decennial Census)
- **Autorefresh Type**: Fully Automated (`manifest.json`)
- **Geographic Coverage**: Country (`country/MEX`) and States

---

## Dataset Details

The **21 datasets** configured in `config.json` and `manifest.json` are grouped across the 3 imports as follows:

| # | Import Name | Dataset Name | Description | Release Frequency |
|---:|:---|:---|:---|:---|
| 1 | `MexicoCensus_Demographics` | `Mexico_Migration` | Foreign-born population residing in Mexico by state, sex, and country of birth (`USA`, `GTM`, `JPN`, `ESP`, `FRA`, and `OtherCountries`). | `P10Y` |
| 2 | `MexicoCensus_Demographics` | `Mexico_Avg_Annual_Growth_Rate` | Average annual population growth rate (`GrowthRate_Count_Person`) by state over 5-year periods. | `P5Y` |
| 3 | `MexicoCensus_Demographics` | `Mexico_Births_Registered` | Registered live births (`Count_BirthEvent`) by state and sex. | `P1Y` |
| 4 | `MexicoCensus_Demographics` | `Mexico_Literacy_Status_6To14` | Population aged 6 to 14 years by state, sex, and ability to read and write (literate vs. illiterate). | `P5Y` |
| 5 | `MexicoCensus_Demographics` | `Mexico_Literate_15OrMore` | Population aged 15 years and older by state, sex, and literacy condition (literate vs. illiterate). | `P5Y` |
| 6 | `MexicoCensus_Demographics` | `Mexico_Median_Age` | Median age of the population (`Median_Age_Person`) by state. | `P5Y` |
| 7 | `MexicoCensus_Demographics` | `Mexico_Population_Density` | Population density (`Count_Person_PerArea`, in `PersonPerSquareKilometer`) by state. | `P5Y` |
| 8 | `MexicoCensus_Demographics` | `Mexico_Religion_Catholic` | Population aged 5 years and older professing Catholicism by state, 5-year age group, and sex. | `P10Y` |
| 9 | `MexicoCensus_Demographics` | `Mexico_Religion_Irreligion` | Population aged 5 years and older with no religion by state, 5-year age group, and sex. | `P10Y` |
| 10 | `MexicoCensus_Demographics` | `Mexico_Religion_OtherReligionThanCatholicism` | Population aged 5 years and older professing a religion other than Catholicism by state, 5-year age group, and sex. | `P10Y` |
| 11 | `MexicoCensus_Demographics` | `Mexico_Total_Population` | Total population (`Count_Person`) by state, 5-year age group, and sex. | `P5Y` |
| 12 | `MexicoCensus_Demographics` | `Mexico_Unemployed_Population` | National quarterly unemployed population (`Count_Person_Unemployed`, total and by work experience). | `P3M` |
| 13 | `MexicoCensus_Health` | `Mexico_Death_Diabetes` | Registered deaths caused by diabetes mellitus (`Count_MortalityEvent_Diabetes`) by state, 5-year age group, and sex. | `P1Y` |
| 14 | `MexicoCensus_Health` | `Mexico_Deaths_Registered` | Total registered deaths (`Count_Death`) by state of residence and sex. | `P1Y` |
| 15 | `MexicoCensus_Health` | `Mexico_Homicide_Population` | Registered deaths by homicide (`Count_MortalityEvent_Assault(Homicide)`) by state of residence and sex. | `P1Y` |
| 16 | `MexicoCensus_Health` | `Mexico_Infant_Mortality` | Registered deaths of infants under 1 year of age (`Count_Death_Upto1Years`) by state of residence and sex. | `P1Y` |
| 17 | `MexicoCensus_Health` | `Mexico_LifeExpectancy` | Life expectancy at birth (`LifeExpectancy_Person`) by state and sex. | `P1Y` |
| 18 | `MexicoCensus_Health` | `Mexico_Male_Mortality_Rate` | Male-to-female mortality ratio (`Count_Death_Male_AsAFractionOf_Count_Death_Female`) by state of residence. | `P1Y` |
| 19 | `MexicoCensus_Health` | `Mexico_Suicide_Population` | Registered deaths by suicide (`Count_MortalityEvent_IntentionalSelf-Harm(Suicide)`) by state of residence and sex. | `P1Y` |
| 20 | `MexicoCensus_Education` | `Mexico_SchoolEnrollment` | Student enrollment (`Count_Student`) by state, education level, and sex across school cycles. | `P1Y` |
| 21 | `MexicoCensus_Education` | `Mexico_Student_Teacher_Ratio` | Student-to-teacher and student-to-school ratios by state and education level across school cycles. | `P1Y` |

---

## Import Procedure & Download Script Details

### 1. `download.py` and `config.json`
`download.py` is the unified Python downloader that fetches all 21 datasets from INEGI's APIs and writes the raw CSV files into `input_files/`. All API base URLs, GCS bucket paths, and dataset identifiers are externalized in `config.json` (no URLs or bucket paths are hardcoded in `download.py`).
- **TLS / `SSLError` Fallback**: All requests attempt standard TLS verification (`verify=True`) first. An `SSLError` fallback (`verify=False`) is included because `www.inegi.org.mx` serves an incomplete intermediate certificate chain that is missing from the default CA bundle in the Cloud Batch container environment (`[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate`).

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

To preserve all historical years without storing data files in the GitHub repository, these two datasets are configured in `config.json` with `"archive_by_year": true` and `"historical_dir": "gs://unresolved_mcf/mexico_census/demographics/latest/historical_inputs"`. When `download.py` runs (`_write_year_archived_dataset`):
1. **Pull Historical Snapshots from GCS $\to$ Local `historical_inputs/`**:
   - Connects to `gs://unresolved_mcf/mexico_census/demographics/latest/historical_inputs/` and downloads all previously archived `<Dataset>_*_input.csv` snapshots into the local `historical_inputs/` folder.
2. **Save & Upload Current Year Snapshot $\to$ Local `historical_inputs/` and GCS**:
   - Extracts the 4-digit reference year from Row 2 (the INEGI table title) of the freshly downloaded table via `_extract_snapshot_year`.
   - Writes `historical_inputs/<Dataset>_<Year>_input.csv` locally and uploads it back to `gs://unresolved_mcf/mexico_census/demographics/latest/historical_inputs/<Dataset>_<Year>_input.csv` so future source updates are automatically archived alongside prior years.
3. **Copy All Year Snapshots $\to$ `input_files/`**:
   - Copies all `<Dataset>_*_input.csv` files from `historical_inputs/` into `input_files/` so `stat_var_processor.py` processes all historical and current snapshots together via the wildcard `--input_data=input_files/<Dataset>_*_input.csv`.

---

## Other Scripts & Configuration Files Used

- **`../../../tools/statvar_importer/stat_var_processor.py`**:
  - Core Data Commons processor that reads each dataset's raw input CSV(s) from `input_files/`, applies the dataset PVMap and shared place mapping, and generates the cleaned CSV, `.tmcf`, and `_stat_vars.mcf` files in `output/`.
- **`config.json`**:
  - Stores `pxweb_api_base_url`, `cuadros_api_base_url`, `historical_gcs_path`, and the per-dataset API parameters for all 21 datasets.
- **`manifest.json`**:
  - Defines the automated import execution sequence (`download.py` followed by 21 `stat_var_processor.py` invocations across 3 vertical imports), `source_files`, and `import_inputs`.
- **`metadata.csv`**:
  - Shared `stat_var_processor.py` configuration file defining provenance URL and description parameters.
- **`pvmap/place_mapping.csv`**:
  - Shared place-resolution PVMap (`#Header,observationAbout`) that maps `"Estados Unidos Mexicanos"` / `"Total"` to `country/MEX` and all 32 Mexican state names (including INEGI footnote-suffixed and historical variants) to their `wikidataId/Q...` DCIDs.
- **`pvmap/MexicoCensus_Demographics_pvmap.csv`, `pvmap/MexicoCensus_Health_pvmap.csv`, `pvmap/MexicoCensus_Education_pvmap.csv`**:
  - 3 vertical-specific Property-Value maps (one per import in `manifest.json`) that combine the mappings for all 21 datasets across Demographics (12 datasets), Health (7 datasets), and Education (2 datasets), translating input filenames, Spanish row stubs, column headers, and time periods into Data Commons `StatVarObservation` properties.
  - For PxWeb datasets where 4-digit observation counts can collide with 4-digit year headers, year keys are scoped with a leading colon (`:YEAR`) so only header-row cells match year keys, while `Mexico_Unemployed_Population` year headers in Column 0 are scoped under their sequential column-header chain (`Period:2019`, `2019:2020`, ...).

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
  --pv_map=pvmap/MexicoCensus_<Vertical>_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/<Dataset>_output \
  --output_counters=counters/<Dataset>_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

#### Year-Archived Literacy Datasets (2 Datasets — Wildcard Multi-Input)
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/Mexico_Literacy_Status_6To14_*_input.csv \
  --pv_map=pvmap/MexicoCensus_Demographics_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/Mexico_Literacy_Status_6To14_output \
  --output_counters=counters/Mexico_Literacy_Status_6To14_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf

python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/Mexico_Literate_15OrMore_*_input.csv \
  --pv_map=pvmap/MexicoCensus_Demographics_pvmap.csv,pvmap/place_mapping.csv \
  --config_file=metadata.csv \
  --output_path=output/Mexico_Literate_15OrMore_output \
  --output_counters=counters/Mexico_Literate_15OrMore_counters.csv \
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
As configured via `output_columns` in `metadata.csv`, every `output/<Dataset>_output.csv` contains a fixed 7-column schema:
- `observationAbout`: Resolved place DCID (`country/MEX` or state `wikidataId/Q...`).
- `observationDate`: Reference year (`YYYY`) or quarter end-month (`YYYY-03`, `YYYY-06`, `YYYY-09`, `YYYY-12`).
- `value`: Numeric observation value.
- `variableMeasured`: Target Data Commons `StatisticalVariable` DCID.
- `unit`: Unit DCID (e.g., `PersonPerSquareKilometer`, `Year`, `Percent`), or empty when not applicable.
- `scalingFactor`: Scaling factor (e.g., `100`), or empty when not applicable.
- `observationPeriod`: Observation period (e.g., `P5Y`), or empty when not applicable.
