# Sweden Census: Demographic Population Statistics (1860–2025)

## 1. Import Overview

This directory contains the automated Data Commons import pipeline for **Sweden Census — Category 1: Demographic (Population by Region, Marital Status, Age, and Sex)** from **Statistics Sweden (Statistiska centralbyrån, SCB)**.

| Field | Details |
| :--- | :--- |
| **Source Agency** | Statistics Sweden (SCB / *Statistiska centralbyrån*) |
| **Import Type** | Automated (Python PxWeb REST API downloader + `stat_var_processor.py`) |
| **Authentication** | None (Public SCB PxWeb REST API; rate-limited to 10 requests / 10 seconds) |
| **SCB Table IDs** | `BE0101A/BefolkningR1860N` (National `1860–2024`) & `BE0101A/BefolkningNy` (Sub-National `1968–2025`) |
| **Source URL** | [SCB Statistikdatabasen — BE0101A](https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__BE__BE0101__BE0101A/) |
| **REST API Endpoints** | `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningR1860N`<br>`https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101A/BefolkningNy` |
| **Geographic Coverage** | **322** Places in Sweden: `1` Country (`country/SWE`), `3` NUTS1 (`nuts/SE1`–`SE3`), `8` NUTS2 (`nuts/SE11`–`SE33`), `21` NUTS3 Counties (`nuts/SE110`–`SE332`), and `289` Municipalities (`wikidataId/Q*`) |
| **Temporal Coverage** | `1860–2024` (National, 165 years) & `1968–2025` (Sub-National, 58 years; dynamically discovers new years via SCB API) |
| **Release Frequency** | Annual (scheduled weekly cron `0 05 * * 1`) |
| **Total Unique StatVars** | **139** unique `StatisticalVariable` DCIDs across all breakdowns |
| **Total SVObs (`1860–2025`)** | **441,402** (`426,062` historical `1860–2022` + `15,340` new `2023–2025`) |

---

## 2. Sub-Imports & Marginal Breakdowns (23 CSVs)

All **23** CSV sub-imports are processed using a single unified PVMap (`demographic_pvmap.csv`), a single metadata config (`demographic_metadata.csv`), a single StatVar remap (`demographic_statvar_remap.csv`), and a single resolved place dictionary (`sweden_places_resolved.csv`):

| # | Sub-Import File Stem | Group | Place Level | Places | Dim Cols | Unique SVs | Output SVObs | PVMap | Metadata Config | StatVar Remap |
| :-: | :--- | :--- | :--- | ---: | :-: | ---: | ---: | :--- | :--- | :--- |
| 1 | `population_country` | **1A: National Total** | Country (`country/SWE`) | 1 | 1 | 1 | 165 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 2 | `population_gender_country` | **1A: National Gender** | Country (`country/SWE`) | 1 | 1 | 2 | 330 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 3 | `population_age_country` | **1A: National Age** | Country (`country/SWE`) | 1 | 1 | 12 | 1,980 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 4 | `population_age_gender_country` | **1A: National Age×Gender** | Country (`country/SWE`) | 1 | 2 | 24 | 3,960 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 5 | `population_nuts1` | **1B: Sub-National Total** | NUTS1 | 3 | 1 | 1 | 171 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 6 | `population_nuts2` | **1B: Sub-National Total** | NUTS2 | 8 | 1 | 1 | 456 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 7 | `population_nuts3` | **1B: Sub-National Total** | NUTS3 | 21 | 1 | 1 | 1,197 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 8 | `population_municipality` | **1B: Sub-National Total** | Municipality | 289 | 1 | 1 | 16,473 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 9 | `population_gender_nuts1` | **1B: Sub-National Gender** | NUTS1 | 3 | 2 | 2 | 342 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 10 | `population_gender_nuts2` | **1B: Sub-National Gender** | NUTS2 | 8 | 2 | 2 | 912 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 11 | `population_gender_nuts3` | **1B: Sub-National Gender** | NUTS3 | 21 | 2 | 2 | 2,394 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 12 | `population_gender_municipality` | **1B: Sub-National Gender** | Municipality | 289 | 2 | 2 | 32,946 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 13 | `population_maritalstatus_nuts1` | **1B: Sub-National Marital** | NUTS1 | 3 | 2 | 4 | 684 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 14 | `population_maritalstatus_nuts2` | **1B: Sub-National Marital** | NUTS2 | 8 | 2 | 4 | 1,824 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 15 | `population_maritalstatus_nuts3` | **1B: Sub-National Marital** | NUTS3 | 21 | 2 | 4 | 4,788 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 16 | `population_maritalstatus_municipality` | **1B: Sub-National Marital** | Municipality | 289 | 2 | 4 | 65,892 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 17 | `population_maritalstatus_gender_nuts1` | **1B: Marital×Gender** | NUTS1 | 3 | 3 | 8 | 1,368 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 18 | `population_maritalstatus_gender_nuts2` | **1B: Marital×Gender** | NUTS2 | 8 | 3 | 8 | 3,648 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 19 | `population_maritalstatus_gender_nuts3` | **1B: Marital×Gender** | NUTS3 | 21 | 3 | 8 | 9,576 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 20 | `population_maritalstatus_gender_municipality` | **1B: Marital×Gender** | Municipality | 289 | 3 | 8 | 131,784 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 21 | `population_age_maritalstatus_gender_nuts1` | **1B: Age×Marital×Gender** | NUTS1 | 3 | 4 | 88 | 15,048 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 22 | `population_age_maritalstatus_gender_nuts2` | **1B: Age×Marital×Gender** | NUTS2 | 8 | 4 | 88 | 40,128 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |
| 23 | `population_age_maritalstatus_gender_nuts3` | **1B: Age×Marital×Gender** | NUTS3 | 21 | 4 | 88 | 105,336 | `demographic_pvmap.csv` | `demographic_metadata.csv` | `demographic_statvar_remap.csv` |

---

## 3. Dimension & Property-Value Mappings

### Gender (`Kon`, 2 Values)
- `1` (`män`) $\rightarrow$ `gender: dcs:Male`
- `2` (`kvinnor`) $\rightarrow$ `gender: dcs:Female`

### Marital Status (`Civilstand`, 4 Values)
- `OG` (`ogifta`) $\rightarrow$ `maritalStatus: dcs:Unmarried`
- `G` (`gifta`) $\rightarrow$ `maritalStatus: dcs:Married`
- `ÄNKL` (`änkor/änklingar`) $\rightarrow$ `maritalStatus: dcs:Widowed`
- `SK` (`skilda`) $\rightarrow$ `maritalStatus: dcs:Divorced`

### Age Groups (`Alder`, 13 Total Brackets Across National & Sub-National)
- Shared 10-year brackets (`0–94` years):
  - `0-4 år` $\rightarrow$ `[0 4 Years]`
  - `5-14 år` $\rightarrow$ `[5 14 Years]` (remapped to `Years5To14` for the 3 national 1-way/2-way StatVars via `demographic_statvar_remap.csv`)
  - `15-24 år` $\rightarrow$ `[15 24 Years]`
  - `25-34 år` $\rightarrow$ `[25 34 Years]`
  - `35-44 år` $\rightarrow$ `[35 44 Years]`
  - `45-54 år` $\rightarrow$ `[45 54 Years]`
  - `55-64 år` $\rightarrow$ `[55 64 Years]`
  - `65-74 år` $\rightarrow$ `[65 74 Years]`
  - `75-84 år` $\rightarrow$ `[75 84 Years]`
  - `85-94 år` $\rightarrow$ `[85 94 Years]`
- National upper brackets (`BefolkningR1860N`, 12 brackets total):
  - `95-104 år` $\rightarrow$ `[95 104 Years]`
  - `105+ år` $\rightarrow$ `[105 - Years]`
- Sub-National upper bracket (`BefolkningNy`, 11 brackets total):
  - `95+ år` $\rightarrow$ `[95 - Years]`

---

## 4. Directory Layout

```text
statvar_imports/sweden_census/demographic/
├── README.md                                 # Documentation
├── manifest.json                             # Automated import specification
├── validation_config.json                    # Import validation rules
├── download_demographic.py                   # SCB PxWeb REST API downloader using download_util (23 CSVs)
├── run.sh                                    # Runs stat_var_processor.py across all 23 CSVs
├── demographic_test.py                       # Unit & configuration test suite
├── sweden_places_resolved.csv                # 321 resolved Sweden sub-national place DCIDs
├── demographic_pvmap.csv                     # Unified PVMap (places, gender, marital, ages, None:1860-2035)
├── demographic_metadata.csv                  # Unified processor configuration (mapped_columns=4)
├── demographic_statvar_remap.csv             # 3-row DCID remap for Count_Person_Years5To14*
├── test_data/                                # Sample inputs & expected outputs for unit testing
├── input_files/                              # Raw wide-format CSVs downloaded from SCB API (23 CSVs)
├── output/                                   # Generated SVObs CSVs and TMCFs (23 pairs)
└── counters/                                 # Generated stat_var_processor counter CSVs (23 CSVs)
```

---

## 5. How to Run Locally

### Step 1: Download Raw CSVs from Statistics Sweden API
```bash
python3 download_demographic.py --output_dir=input_files
```
- Queries `BefolkningR1860N` (`1860–latest`) and `BefolkningNy` (`1968–latest`) on Statistics Sweden's PxWeb v1 API and writes all 23 wide-format CSVs to `input_files/`.
- Respects SCB's `10 requests / 10 seconds` rate limit (`1.2s` sleep between POST requests) with exponential backoff retry.

### Step 2: Process All 23 CSVs via `stat_var_processor.py`
```bash
bash run.sh
```
- Runs `stat_var_processor.py` across all 23 CSVs in `input_files/` using `demographic_pvmap.csv`, `demographic_metadata.csv`, `demographic_statvar_remap.csv`, and `sweden_places_resolved.csv`, writing cleaned `.csv` and `.tmcf` files to `output/` and diagnostics to `counters/`.

### Step 3: Run Unit Tests
```bash
python3 demographic_test.py
```

---

## 6. Data Notes & Implementation Details

1. **Unified Single-Config Architecture (`demographic_metadata.csv` + `demographic_pvmap.csv`)**:
   - **Country vs. Sub-National `observationAbout`**: `Cell:3:1,observationAbout,dcid:country/SWE` and `region,observationAbout,{Data}` allow the same PVMap to handle both the 4 national files (where cell `3:1` is `""`, `kön`, or `ålder` and falls through to `Cell:3:1`) and the 19 sub-national files (where cell `3:1` is `region`, which takes precedence over `Cell:3:1`).
   - **Header-Scoped Year Keys (`None:1860`–`None:2035`)**: Prefixing year keys with `None:` ensures they match **only on Row 3** (where `get_last_column_header_key(col_index)` is `None`) and resolve `{Key}` to the 4-digit year. On data rows (`Row 4+`), `get_last_column_header_key(col_index)` is the column header, preventing numeric population values in `1860..2024` within columns `2..4` from colliding with year keys when `mapped_columns=4`.
2. **Historical Place Set (`321` Sub-National Places / `2463 Åsele` Exclusion)**:
   - Municipality `2463 Åsele` is marked `#ignore,skip` in `demographic_pvmap.csv` to match the historical Sweden Census place set (`289` municipalities + `3` NUTS1 + `8` NUTS2 + `21` NUTS3 = `321` sub-national places + `country/SWE` = `322` total places) with `0` unresolved places.
