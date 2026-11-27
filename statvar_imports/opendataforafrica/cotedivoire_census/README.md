# Côte d'Ivoire Census Data Commons Import (`Cotedivoire_Census`)

## 1. Overview & Dataset Information

- **Source**: [Côte d'Ivoire Open Data for Africa](https://cotedivoire.opendataforafrica.org/)
- **Publisher**: National Institute of Statistics / National Agency of Statistics (ANStat), Côte d'Ivoire
- **License**: Creative Commons Attribution 4.0 ([Terms of Use](https://cotedivoire.opendataforafrica.org/legal/termsofuse), `dcid:CreativeCommonsAttributionLicense`)
- **Import Type**: `Semi-Automated` (`GCPCloudRunSemiAutomaticRefresh` — Cloudflare anti-bot challenges on `cotedivoire.opendataforafrica.org` return `HTTP 403` to headless GCP VMs, requiring manual browser SDMX XML/CSV staging to GCS followed by automated Cloud Batch conversion, processing, validation, and `country` import-group CNS promotion matching `Kenya_Census`)
- **Schedule**: Weekly (Every Monday at 05:30 UTC — `30 05 * * 1`)
- **Coverage**: Demographics, Census (RGPH 2014 & RGPH 2021), Economy, Industrial Production, Commercial Turnover, Labor Force, Education, Health, and Vital Statistics at country, autonomous district, region, department, and sub-prefecture levels (1988+)
- **Entity Resolution**:
  - National level: `country/CIV`
  - Sub-national levels: Autonomous districts, regions, departments, and sub-prefectures pre-resolved to Wikidata DCIDs (`wikidataId/Q*`) via `places_resolved.csv` (for `{Data}` tables) and explicit `dcid:wikidataId/Q*` mappings in `jgwlmgg_pvmap.csv` and `ojtbus_pvmap.csv` (`IdBasedKgResolution`).

## 2. Directory Layout & Artifacts

| File / Directory | Purpose |
| :--- | :--- |
| `manifest.json` | Import manifest declaring download, XML-to-CSV conversion, 16 `stat_var_processor.py` runs, inputs, source artifacts, and validation |
| `validation_config.json` | Scoped SQL non-empty and `MaxDate` freshness validation rules complementing base pipeline checks |
| `download.sh` | Shell script fetching staged raw inputs from `gs://unresolved_mcf/opendataforafrica/cotedivoire_census/input_files/*` into `raw_inputs/` and copying pre-staged `*.csv` files into `input_files/` |
| `convert_sdmx_xml_to_csv.py` | Python utility converting Open Data for Africa SDMX `.xml` files in `raw_inputs/` into UTF-8 NFC normalized `.csv` files in `input_files/` (`OBS_VALUE` ordered last, scientific notation expanded) |
| `convert_sdmx_xml_to_csv_test.py` | Hermetic `unittest` test suite covering `sdmx1` and `ElementTree` XML conversion, French accents/hex-escape decoding, CLI flags, and static config/fixture checks |
| `*_pvmap.csv` | Per-table Property-Value schema mappings for `stat_var_processor.py` |
| `rgph_ignored_places_pvmap.csv` | Shared PVMap (`#IgnoreRow,True`) filtering unmapped and duplicate-Wikidata `KN.A*` locality codes in `hxghsjf` and `hznvdtd` before place resolution |
| `*_metadata.csv` | Per-table processor configuration files (`generate_statvar_mcf` and `generate_schema_mcf` enabled) |
| `places_resolved.csv` | Unified place resolver mapping `291` disjoint place keys (`252` RGPH `KN.A*` codes + `26` French region names + `13` `R1..D12` education region/department codes) to `wikidataId/Q*` |
| `test_data/` | Representative `< 100`-row input, expected CSV, and expected TMCF fixtures (`<table>_input.csv`, `<table>_output.csv`, `<table>_output.tmcf`) for all 16 tables |

## 3. Dataset Mapping Index (16 Tables)

1. `CIEI2010R`: Economic Indicators (Nominal GDP, Nominal Per-Capita GDP, Real GDP Growth Rate, Exports, Imports, Expenditure Share of GDP, Total & Outstanding Debt; `country/CIV`, 2002+)
2. `akfhutb`: Detailed Health Sector Indicators — hospitals, clinics, pharmacies, maternity centers, hospital beds, doctors, nurses, midwives, lab technicians, pharmacists, BCG vaccination, malaria incidence, and skilled birth attendance (`country/CIV`, 2001+)
3. `bdwcmfd`: Demographic & Vital Statistics — mean age at childbearing, life expectancy by sex, infant/under-5/crude mortality rates, and population growth rate (`country/CIV`, 2015+)
4. `hxghsjf`: General Population and Housing Census (RGPH 2014) — population by sex, sex ratio, households, and household size across `252` localities (`ID_REGION` via `places_resolved.csv` + `rgph_ignored_places_pvmap.csv`, 2014)
5. `hznvdtd`: General Population and Housing Census (RGPH 2021) — population by sex, sex ratio, households, and household size across `252` localities (`ID_REGION` via `places_resolved.csv` + `rgph_ignored_places_pvmap.csv`, 2021)
6. `jgwlmgg`: R3 Population & Labor Force Statistics by Gender across 7 departments (`ID_DEPARTEMENT` mapped directly to `dcid:wikidataId/Q*`, 2017+)
7. `jynwpug`: Harmonised Industrial Production Index (IHPI, Base 2015) across 31 industrial sectors (`country/CIV`, monthly `P1M`, 2018-12+)
8. `kcnetge`: Public General Secondary Teachers by Category (1st Cycle, 2nd Cycle, Contractual) and Gender across 4 departments (`ID_DÉPARTEMENT` via `places_resolved.csv`, 2020+)
9. `ojtbus`: Population in Labor Force by Gender across 2 departments (`ID_DEPARTEMENT` mapped directly to `dcid:wikidataId/Q*`, 2017+)
10. `qdanpdb`: Quarterly Turnover Index in Commerce and Services (Base 2008) across 15 commercial sectors (`country/CIV`, quarterly `P3M`, 2015-Q1+)
11. `rimffwf`: Private General Secondary Teachers by Category (Permanent, Civil Servant Vacancy, Non-Civil Servant Vacancy) and Gender across 4 departments (`ID_DÉPARTEMENT` via `places_resolved.csv`, 2020+)
12. `saxmnv`: General Secondary Education Classrooms, Students, and Teachers by Cycle (Lower/Upper Secondary) across 4 departments (`ID_DÉPARTEMENT` via `places_resolved.csv`, 2020+)
13. `wayfqyd`: School Establishments, Classrooms, Students, and Teachers by Public/Private/Total Status and Gender across 13 regions/departments (`ID_DÉPARTEMENT` via `places_resolved.csv`, 2021+)
14. `wwamxhe`: Regional Population by Sex across 26 regions/autonomous districts (`NOM_REGION` via `places_resolved.csv`, 2013+)
15. `yukugyf`: National Population by 5-Year Age Groups (`0-4` through `80+`; `country/CIV`, 1988+)
16. `yxrzxug`: National Population by Sex (`country/CIV`, 1995+)

## 4. Semi-Automated Refresh Procedure

### 4.1 Manual Browser SDMX Download & GCS Staging
Because `cotedivoire.opendataforafrica.org` blocks automated server requests via Cloudflare (`HTTP 403`):
1. Open each dataset URL (`https://cotedivoire.opendataforafrica.org/<table_id>`) in an authenticated desktop browser, export the full dataset in **SDMX (`.xml`)** format, and name each file `<table_id>.xml` (for all 16 table IDs above).
2. Upload the 16 `.xml` files (or pre-normalized `<table_id>.csv` files) to the GCS staging prefix (when replacing pre-staged `.csv` files with fresh `.xml` exports, remove superseded `.csv` objects in GCS or sync via `gcloud storage rsync --delete-unmatched-destination-objects` so stale `.csv` files are not redundantly archived under `source_files`):
   ```bash
   gcloud storage cp xml/*.xml gs://unresolved_mcf/opendataforafrica/cotedivoire_census/input_files/
   ```

### 4.2 Automated Pipeline Execution
On each scheduled run (`30 05 * * 1`), `manifest.json` executes:
1. **`download.sh`**: Pulls all staged files from `gs://unresolved_mcf/opendataforafrica/cotedivoire_census/input_files/*` into `raw_inputs/` (retaining raw downloads untouched for `source_files` archival) and copies any pre-staged `*.csv` files into `input_files/`.
2. **`convert_sdmx_xml_to_csv.py`**: Converts any `.xml` files in `raw_inputs/` into normalized `.csv` files in `input_files/` and verifies all 16 expected table CSVs exist and are non-empty (`--verify_expected_tables`).
3. **`stat_var_processor.py`**: Processes each of the 16 tables into `output/<table>.csv`, `output/<table>.tmcf`, and any new schema nodes `output/<table>*.mcf`, writing counters to `counters/<table>_counters.csv`.
4. **Validation**: Runs global validation rules (`DELETED_RECORDS_PERCENT <= 0.1`, `EMPTY_IMPORT_CHECK`, `MISSING_REFS_COUNT`, `LINT_ERROR_COUNT`) merged with `validation_config.json`.

## 5. Running Locally & Testing

All commands below assume working directory is the repository root (`data/`):

```bash
# 1. Run hermetic unit tests
./run_tests.sh -p statvar_imports/opendataforafrica/cotedivoire_census

# 2. Run Python lint and formatting checks
./run_tests.sh -l

# 3. Convert local SDMX XMLs to CSVs
.env/bin/python statvar_imports/opendataforafrica/cotedivoire_census/convert_sdmx_xml_to_csv.py \
  --xml_dir=statvar_imports/opendataforafrica/cotedivoire_census/raw_inputs \
  --output_dir=statvar_imports/opendataforafrica/cotedivoire_census/input_files \
  --allow_empty_xml_dir \
  --verify_expected_tables

# 4. Example single-table StatVar Processor run (hxghsjf)
.env/bin/python tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/opendataforafrica/cotedivoire_census/input_files/hxghsjf.csv \
  --pv_map=statvar_imports/opendataforafrica/cotedivoire_census/hxghsjf_pvmap.csv,statvar_imports/opendataforafrica/cotedivoire_census/rgph_ignored_places_pvmap.csv \
  --config_file=statvar_imports/opendataforafrica/cotedivoire_census/hxghsjf_metadata.csv \
  --places_resolved_csv=statvar_imports/opendataforafrica/cotedivoire_census/places_resolved.csv \
  --output_path=statvar_imports/opendataforafrica/cotedivoire_census/output/hxghsjf \
  --output_counters=statvar_imports/opendataforafrica/cotedivoire_census/counters/hxghsjf_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

## 6. Known Pre-Existing KG Issues (Deferred for Phase 1 Baseline Parity)

To preserve 1:1 StatVar parity (`0%` deletions against the existing Knowledge Graph baseline) during this semi-automation migration, the following three pre-existing live-KG mappings are intentionally kept unchanged and annotated with `TODO(b/587181425)` comments for a coordinated follow-up schema/data PR and CL:

1. **`CIEI2010R_pvmap.csv`**: Monetary indicators (`KN.B1`, `KN.B8`, `KN.B9`, `KN.B25`, `KN.B26`) use `#Multiply,1000000` (`10^6`) instead of `1000000000` (`10^9`), and `KN.B1`, `KN.B2`, `KN.B8`, `KN.B9`, `KN.B25`, `KN.B26` use `unit,XAF` instead of `unit,XOF`.
2. **`bdwcmfd_pvmap.csv`**: Under-5 mortality (`Taux de Mortalité des populations de moins de 5 ans`) maps to `age,Years5Onwards` (`Count_MortalityEvent_5OrMoreYears_AsAFractionOf_Count_BirthEvent_LiveBirth`).
3. **`kcnetge_pvmap.csv`**: Lower-secondary teachers (`CEN6`, *Professeur de Collège (1er Cycle)*) map to `facultyType,UniversityAndCollegeTeacher`.
