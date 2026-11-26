# Egypt Census Data Commons Import

## 1. Overview & Dataset Information

- **Source**: [Egypt Open Data for Africa](https://egypt.opendataforafrica.org/)
- **Publisher**: Central Agency for Public Mobilization and Statistics (CAPMAS), Egypt
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — Cloudflare anti-bot challenges on `egypt.opendataforafrica.org` require semi-automated SDMX XML downloads converted locally to CSVs and staged to GCS rather than `auto1w`, matching `Kenya_Census`)
- **Schedule**: `0 5 * * 1` (Mondays at 05:00 UTC; semi-automated Cloud Batch schedule)
- **Coverage**: Demographics, Economy, Labor Force, Education, Health, and Vital Statistics at country and governorate level (1988 – present)
- **Entity Resolution**:
  - National level: `country/EGY`
  - Governorate / Sub-national level: `AdministrativeArea1` (27 active governorates + 2 historical governorates: Helwan `wikidataId/Q771345` and 6th of October `wikidataId/Q335708`) pre-resolved via `places_resolved.csv` (`NoEntityResolution` at KG load time).

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring `download.sh`, 17 `stat_var_processor.py` runs, `filter_existing_statvars.py`, `import_inputs`, and validation config |
| `validation_config.json` | Scoped SQL freshness rules and primary vs. pre-primary invariant check complementing default pipeline checks |
| `download.sh` | Shell script fetching pre-converted census CSVs from GCS into `input_files/` and caching `stat_vars.mcf` once at `/tmp/egypt_census_stat_vars.mcf` |
| `convert_sdmx_xml_to_csv.py` | Python utility for converting Open Data for Africa SDMX XML files (`xml/*.xml`) into normalized CSVs (`input_files/*.csv`) using `sdmx1` |
| `filter_existing_statvars.py` | Python post-filter stripping existing KG StatVars from `output/*_stat_vars.mcf` locally against `/tmp/egypt_census_stat_vars.mcf` |
| `convert_sdmx_xml_to_csv_test.py` | Hermetic unit tests for `convert_sdmx_xml_to_csv.py`, `filter_existing_statvars.py`, manifest wiring, PVMaps, and `test_data/` fixtures |
| `common_pvmap.csv` | Shared PVMap handling dynamic annual/quarterly `TIME_PERIOD`, `OBS_VALUE`, and `FREQ` mappings |
| `*_pvmap.csv` | Per-table Property-Value schema mappings for `stat_var_processor.py` |
| `*_metadata.csv` | Per-table processor configurations (`generate_statvar_mcf,True`, `generate_schema_mcf,False`, `recon_lookup_api,False`, `output_only_new_statvars,False`) |
| `places_resolved.csv` | Unified place resolver mapping ISO region codes, English names, and Arabic governorate names (including tatweel/footnote variants) to DCIDs |
| `statvar_remap.csv` | StatVar DCID remap table resolving collisions with legacy US BLS/Census StatVars in `mptocre`, `szfufmb`, and `wtxyghf` |
| `existing_schema.mcf` | Existing Data Commons schema declarations passed via `--existing_schema_mcf` so even manual `schema_generator.py` runs emit `0` `Property` redefinitions |
| `input_files/` | Normalized input CSVs staged in GCS and synced to `source_files/` (`.gitignore` excluded from Git) |
| `counters/` | Runtime processor counter CSVs uploaded under `source_files/` (`.gitignore` excluded from Git) |
| `test_data/` | Representative hermetic input/output CSV and TMCF fixtures (`<table>_input.csv`, `<table>_output.csv`, `<table>_output.tmcf`) |

## 3. Dataset Mapping Index

The import processes 17 tables from CAPMAS Egypt Open Data:

1. `actytif`: Health Services Statistics of Egypt — hospitals, beds, ambulances, traffic accidents, and medical incidents (`REGIONID_LOCATION` via `places_resolved.csv`, 2001+)
2. `behvqtc`: Population by Governorate, Urban/Rural, Gender, and Age Groups (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+; 236 duplicate age-total rows deferred to `lxoyale`, retaining the 3 unique Alexandria Rural totals)
3. `bluhqme`: Employed Persons (15+ Years, scaled from hundreds via `#Multiply,100`) by Governorate, Economic Activity, and Sex (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+)
4. `cjczlcd`: Health Facilities, Doctors, and Nursing Staff by Sector and Gender (`country/EGY`, 2014+)
5. `lxoyale`: Households, Residents in Households, and Total Population by Governorate and Urban/Rural (`REGIONID_LOCATION` via `places_resolved.csv`, 2017+)
6. `mptocre`: Labor-Force Unemployment Rates (15–64 Years) by Age Group, Educational Status, and Gender (`country/EGY`, 2017+)
7. `pqpump`: Estimate of Employed Persons (15+ Years, scaled from hundreds via `#Multiply,100`) by Governorate and Egypt Total (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2012+)
8. `szfufmb`: Population by Marital Status, Urban/Rural, Gender, and Age Group (`country/EGY`, 2017+)
9. `txbrrac`: Enrolled Students in Higher Education by Institution Type and Gender (`country/EGY`, 2012+)
10. `ujtdaag`: Life Expectancy at Birth by Sex (`country/EGY`, 2006+)
11. `ulouknf`: Labor Force (15+ Years), Employed, Unemployed, and Labor-Force Unemployment Rate by Gender and Quarter (`country/EGY`, 2017-Q1+)
12. `viytqvf`: Total Fertility Rate of Women in Egypt (`country/EGY`, 1988+)
13. `wcssteb`: Pre-University Education Students and Teachers by Stage (Pre-Primary, Primary, Preparatory/Middle, General/Technical Secondary, Community, Special) and Gender (`country/EGY`, 2012+)
14. `wtxyghf`: Higher Education Teaching Staff by Institution Type and Gender (`country/EGY`, 2012+)
15. `xovpotd`: Socio-Economic Indicators: Resident/Total Population, Labor Force, Employment, Unemployment, and Real/Nominal GDP (`country/EGY`, 1993+)
16. `zkjifzd`: Higher Education Graduates by Institution Type and Gender (`country/EGY`, 2012+)
17. `zpdksog`: Infant Mortality Count and Infant Mortality Rate by Governorate and Urban/Rural (`NAMEARAB_GOVERNORATES` via `places_resolved.csv`, 2017+)

## 4. Ingestion Workflow

### 4.1 Upstream Source Data Updates
When updated census or statistical data is published on Egypt Open Data for Africa:
1. **Download SDMX XML**: Save the SDMX `.xml` file locally for each dataset into an `xml/` directory (e.g., `xml/actytif.xml`, `xml/behvqtc.xml`, ..., `xml/zpdksog.xml`).
2. **Convert XML to CSV**: Execute `convert_sdmx_xml_to_csv.py` locally to convert the raw SDMX XML files into normalized CSV files in `input_files/`:
   ```bash
   python3 convert_sdmx_xml_to_csv.py --xml_dir xml/ --output_dir input_files/ --verify_expected_tables
   ```
3. **Stage to GCS**: Upload the refreshed CSV files to Google Cloud Storage:
   ```bash
   gcloud storage cp input_files/*.csv gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/
   ```

### 4.2 Automated Ingestion Pipeline
During scheduled import runs (`0 5 * * 1`, Mondays at 05:00 UTC) or on-demand triggers after refreshed CSVs are staged to GCS, `manifest.json` executes:
1. **Download (`download.sh`)**: Copies staged CSV files from `gs://unresolved_mcf/opendataforafrica/egypt_census/input_files/*.csv` directly into `input_files/` and downloads `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf` once to `/tmp/egypt_census_stat_vars.mcf`.
2. **Transform (`stat_var_processor.py` + `filter_existing_statvars.py`)**: Processes all 17 tables against `--existing_statvar_mcf=/tmp/egypt_census_stat_vars.mcf`, writing `.csv`, `.tmcf`, and `_stat_vars.mcf` into `output/`, then filters `output/*_stat_vars.mcf` locally so `"node_mcf": "output/<table>*_stat_vars.mcf"` ingests only genuinely new StatVars without DC API `/v2/node` `429` errors or `definition` merge-conflict counters.
3. **Validation**: Runs default pipeline checks (`DELETED_RECORDS_PERCENT`, `EMPTY_IMPORT_CHECK`, `MISSING_REFS_COUNT`, `LINT_ERROR_COUNT`) plus the 4 `SQL_VALIDATOR` rules in `validation_config.json`.

## 5. Upstream Source Data Caveats

- **`behvqtc` (Alexandria Rural age-total retention)**: Upstream `lxoyale.csv` publishes 236 governorate/national urban, rural, and total population rows matching `behvqtc.csv` age totals (`اجمالى:  فئـــــــات الســــــن`), but omits Alexandria Governorate (`EG-ALX`, `wikidataId/Q29943`) Rural (`KN.AN3`) totals (`Count_Person_Rural=68,293`, `Count_Person_Rural_Male=35,825`, `Count_Person_Rural_Female=32,468`, matching the sum of Alexandria's 20 rural age brackets). `behvqtc_pvmap.csv` uses declarative template guards (`IgnoreRuralTotal`/`IgnoreAgeTotal` with `#IgnoreRow,{@IgnoreAgeTotal}`) to retain only those `3` unique Alexandria Rural totals while dropping the `236` `lxoyale`-overlapping age-total rows (`4,764` SVObs, `0` cross-table duplicates).
- **`actytif` (`KN.S49` ambulance accident casualty deaths)**: In CAPMAS's *Health Services Statistics of Egypt* workbook, `KN.S49` (`Death`: `15,264–19,294`/year nationwide for `2004–2010`) is the first casualty outcome under section header `KN.S48` (*"Damages from accidents"* transported by ambulances), summing with `KN.S50..S62, S64` to the exact integer to `KN.S63` (*"Total Damages from accidents"*) across all `202/202` place-year pairs. `actytif_pvmap.csv` maps `KN.S49` with `causeOfDeath,Accident` (`dcid:Count_MortalityEvent_Accident`) rather than unstratified all-cause mortality (`dcid:Count_Death`).
- **`szfufmb` (`NeverMarried` `18+` legal marriage age domain)**: CAPMAS 2017 Census tabulates `MARITAL_STATUS=5` (`لم يتزوج`, `NeverMarried`) strictly for ages `18+` (while `37,842,662` unmarried minors `<18` are tabulated separately in `MARITAL_STATUS=3` `اقل من السن`). `szfufmb_pvmap.csv` suppresses the `36` `<18` (`أقل من 15 سنة`, `15 سنة`, `16 سنة`, `17 سنة`) literal `0` rows for `لم يتزوج` via `#IgnoreRow,{@IgnoreUnder18}` (retaining `<18` early-marriage rows for `عقد قران`, `متزوج`, `مطلق`, `ارمل` and legitimate `60+` `0` rows for `عقد قران`, `855 -> 819` SVObs) and maps `لم يتزوج`'s age-total row (`"اجمالى:  فئـــــــات الســــــن"`) to `age,[18 - Years]` (`Count_Person_18OrMoreYears_*NeverMarried*`).
- **`wcssteb` (`ID=1`/`ID=2` stage-label swap + SQL invariant)**: Upstream OpenDataForAfrica `wcssteb` inverted the stage labels on `ID=1` (`قبل الابتدائي` / `Before primary school`) and `ID=2` (`الابتدائي` / `Primary`), verified against official Egypt MOETE/CAPMAS statistics (`11,074,835` primary vs. `1,244,052` pre-primary KG students and `99.5%` female KG staffing in `2016`). `wcssteb_pvmap.csv` maps `ID=1` -> `PrimarySchool` and `ID=2` -> `PrePrimarySchool`, guarded against future upstream un-swapping by `check_wcssteb_primary_exceeds_preprimary_enrollment_and_teachers` (`PrimaryMin > PrePrimaryMax`) in `validation_config.json`.
- **`wtxyghf` (`2016` university faculty outlier suppression)**: Upstream `wtxyghf.csv` (`2016`) drops public/Al-Azhar university teaching staff by `92.9%` (`97,949 -> 6,991`) and spikes private university teaching staff by `+189%` (`8,745 -> 25,271`, matching the `25,271` male student count in `txbrrac.csv`). `wtxyghf_pvmap.csv` (`TIME_PERIOD:2016` `EmptyRef` suppression on the two university series, while keeping dynamic `2017+` years open) deterministically drops only those `2` corrupted `2016` rows (`30 -> 28` SVObs), with `MaxDate >= '2015'` enforced in `validation_config.json`.
- **`cjczlcd` (`ID_SECTORS=2` `GovernmentOwned`)**: CAPMAS `ID_SECTORS=2` represents governmental and public-business sector health facilities and staff (`17` facilities + `454` private = `471` total in `2014`) and is mapped to `establishmentOwnership,GovernmentOwned` (`Count_HealthEstablishment_GovernmentOwnedEstablishment_HealthFacility` and `Count_Person_GovernmentOwnedEstablishment_{Female,Male}_{Doctor,Nurse}Occupation`).
- **`zpdksog` (14-governorate `Total == Urban` IMR and `Port Said`/`Suez` `0` Rural IMR)**: In upstream CAPMAS/Knoema `zpdksog.csv` (matching the `20250312` baseline `.xlsx`), 14 of 27 governorates publish `ID_AREA=1` (Total IMR) equal to `ID_AREA=2` (Urban IMR) and predominantly urban governorates `Port Said` and `Suez` publish `Rural IMR = 0` despite small rural infant death counts (`8` and `22`); these observations are retained as-published for fidelity with the official CAPMAS/OpenDataForAfrica source and `20250312` KG baseline.

## 6. Running Locally & Testing

```bash
# Run hermetic unit tests from repo root
./run_tests.sh -p statvar_imports/opendataforafrica/egypt_census

# Example single-table processor run from repo root
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/egypt_census/input_files/behvqtc.csv \
  --pv_map=statvar_imports/opendataforafrica/egypt_census/common_pvmap.csv,statvar_imports/opendataforafrica/egypt_census/behvqtc_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/egypt_census/behvqtc_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/egypt_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/egypt_census/output/behvqtc \
  --output_counters=statvar_imports/opendataforafrica/egypt_census/counters/behvqtc_counters.csv \
  --existing_statvar_mcf=/tmp/egypt_census_stat_vars.mcf \
  --existing_schema_mcf=statvar_imports/opendataforafrica/egypt_census/existing_schema.mcf
```

## 7. Production Deployment & Post-Merge Runbook

Execute the initial production cutover and future refreshes in the following strict order:

1. **Merge GitHub PR `#2394`** into `datacommonsorg/data` `master` first so `Egypt_Census.mcf` `dataTransformationLogic` (`https://github.com/datacommonsorg/data/blob/master/statvar_imports/opendataforafrica/egypt_census/README.md`) resolves HTTP `200 OK`.
2. **Verify Staged GCS Artifacts**: Confirm the vetted Cloud Batch run `<version>` is staged in `gs://unresolved_mcf/country/egypt/latest/`, `gs://resolved_mcf/country/egypt/latest/`, and `gs://datcom-prod-imports/statvar_imports/opendataforafrica/egypt_census/Egypt_Census/<version>/`.
3. **Run CNS `AutoCopy`**: Copy staged CSVs, TMCF, and resolved `nodes.mcf@17` shards into `/cns/jv-d/home/datcom/v3_mcf/country/egypt/latest/` and `/cns/jv-d/home/datcom/v3_resolved_mcf/country/egypt/latest/`.
4. **Submit Google3 `cl/1018979293`**: Land the `egypt_common_schema.mcf`, `egypt_stat_var.mcf`, `Egypt_Census.mcf` provenance, and `Egypt_Census.textproto` (`import_groups: "country"`) manifest updates after CNS artifacts and GitHub `README.md` are live.
5. **Promote `latest_version.txt`**: Update `latest_version.txt` in both `gs://datcom-import-test/statvar_imports/opendataforafrica/egypt_census/Egypt_Census/` and `gs://datcom-prod-imports/statvar_imports/opendataforafrica/egypt_census/Egypt_Census/` to `<version>` so future weekly `0 5 * * 1` semi-automated runs diff and validate against the refreshed baseline.
