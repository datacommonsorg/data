# Sweden Census: Educational Attainment (16–74 Years)

## 1. Import Overview

This directory contains the automated Data Commons import pipeline for **Sweden Census — Category 3: Education (Educational Attainment of Population Aged 16–74 Years)** from **Statistics Sweden (Statistiska centralbyrån, SCB)**.

| Field | Details |
| :--- | :--- |
| **Source Agency** | Statistics Sweden (SCB / *Statistiska centralbyrån*) |
| **SCB Table ID** | `UF0506B/Utbildning` (*Befolkning 16–74 år efter region, utbildningsnivå, ålder och kön*) |
| **Source URL** | [SCB Statistikdatabasen — UF0506B/Utbildning](https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__UF__UF0506__UF0506B/Utbildning/table/tableViewLayout1/) |
| **REST API Endpoint** | `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/UF/UF0506/UF0506B/Utbildning` |
| **Geographic Coverage** | 321 Sub-national Places in Sweden: `3` NUTS1 (`nuts/SE1`–`SE3`), `8` NUTS2 (`nuts/SE11`–`SE33`), `21` NUTS3 Counties (`nuts/SE110`–`SE332`), and `289` Municipalities (`wikidataId/Q*`) |
| **Temporal Coverage** | `1985–2025` (Annual, dynamically discovers new years `2026+` via SCB API) |
| **Release Frequency** | Annual (published in April each year; scheduled weekly cron `0 05 * * 1`) |
| **Total Unique StatVars** | **126** unique `StatisticalVariable` DCIDs (`6` Total + `12` Gender + `36` Age + `72` Age×Gender) |
| **Total SVObs (`1985–2025`)** | **805,158** (`746,240` historical `1985–2022` + `58,918` new `2023–2025`) |

---

## 2. Sub-Imports & Marginal Breakdowns (17 CSVs)

To preserve true marginal totals across `EducationalAttainment`, `Gender`, and `Age`, the import is organized into **4 structural groups** across **17 CSV sub-imports**:

| # | Sub-Import File Stem | Group | Place Level | Places | Mapped Cols | Unique SVs | PVMap (`education_common_pvmap.csv` +) | Metadata Config | StatVar Remap |
| :-: | :--- | :--- | :--- | ---: | :-: | ---: | :--- | :--- | :--- |
| 1 | `education_nuts1` | **Group 1: Total** | NUTS1 | 3 | 3 | 6 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_total_statvar_remap.csv` |
| 2 | `education_nuts2` | **Group 1: Total** | NUTS2 | 8 | 3 | 6 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_total_statvar_remap.csv` |
| 3 | `education_nuts3` | **Group 1: Total** | NUTS3 | 21 | 3 | 6 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_total_statvar_remap.csv` |
| 4 | `education_municipality` | **Group 1: Total** | Municipality | 289 | 3 | 6 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_total_statvar_remap.csv` |
| 5 | `education_gender_nuts1` | **Group 2: Gender** | NUTS1 | 3 | 4 | 12 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_gender_statvar_remap.csv` |
| 6 | `education_gender_nuts2` | **Group 2: Gender** | NUTS2 | 8 | 4 | 12 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_gender_statvar_remap.csv` |
| 7 | `education_gender_nuts3` | **Group 2: Gender** | NUTS3 | 21 | 4 | 12 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_gender_statvar_remap.csv` |
| 8 | `education_gender_municipality` | **Group 2: Gender** | Municipality | 289 | 4 | 12 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_gender_statvar_remap.csv` |
| 9 | `education_age_nuts1` | **Group 3: Age** | NUTS1 | 3 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 10 | `education_age_nuts2` | **Group 3: Age** | NUTS2 | 8 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 11 | `education_age_nuts3` | **Group 3: Age** | NUTS3 | 21 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 12 | `education_age_municipality_1` | **Group 3: Age** | Municipality (Part 1) | 107 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 13 | `education_age_municipality_2` | **Group 3: Age** | Municipality (Part 2) | 96 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 14 | `education_age_municipality_3` | **Group 3: Age** | Municipality (Part 3) | 86 | 3 | 36 | `education_total_pvmap.csv` | `education_total_metadata.csv` | `education_age_statvar_remap.csv` |
| 15 | `education_age_gender_nuts1` | **Group 4: Age×Gender** | NUTS1 | 3 | 4 | 72 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_age_gender_statvar_remap.csv` |
| 16 | `education_age_gender_nuts2` | **Group 4: Age×Gender** | NUTS2 | 8 | 4 | 72 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_age_gender_statvar_remap.csv` |
| 17 | `education_age_gender_nuts3` | **Group 4: Age×Gender** | NUTS3 | 21 | 4 | 72 | `education_gender_pvmap.csv` | `education_gender_metadata.csv` | `education_age_gender_statvar_remap.csv` |

---

## 3. Dimension & Property-Value Mappings

### Educational Attainment (`UtbildningsNiva`, 6 Mapped Levels)
- `1` (`förgymnasial utbildning kortare än 9 år`) $\rightarrow$ `educationalAttainment: [- 9 Grade]` (`9OrLessGrade` in remapped DCID)
- `3` (`gymnasial utbildning, högst 2 år`) $\rightarrow$ `educationalAttainment: dcs:UpperSecondaryEducation`
- `4` (`gymnasial utbildning, 3 år`) $\rightarrow$ `educationalAttainment: dcs:UpperSecondaryEducation3Years`
- `5` (`eftergymnasial utbildning, mindre än 3 år`) $\rightarrow$ `educationalAttainment: dcs:PostSecondaryEducationLessThan3Years`
- `6` (`eftergymnasial utbildning, 3 år eller mer`) $\rightarrow$ `educationalAttainment: dcs:Graduate`
- `7` (`forskarutbildning`) $\rightarrow$ `educationalAttainment: dcs:PostGraduate`
- `2` (`förgymnasial utbildning, 9 (10) år`) and `US` (`uppgift saknas`) $\rightarrow$ Intentionally excluded to match the existing Sweden Education schema and historical baseline (`6` education levels per marginal slice).

### Age Groups (`Alder`, 6 Brackets)
- `16-24` (`16-24 år`) $\rightarrow$ `[16 24 Years]`
- `25-34` (`25-34 år`) $\rightarrow$ `[25 34 Years]`
- `35-44` (`35-44 år`) $\rightarrow$ `[35 44 Years]`
- `45-54` (`45-54 år`) $\rightarrow$ `[45 54 Years]`
- `55-64` (`55-64 år`) $\rightarrow$ `[55 64 Years]`
- `65-74` (`65-74 år`) $\rightarrow$ `[65 74 Years]`
- `tot16-74` (`totalt 16-74 år`) $\rightarrow$ Aggregate marginal row used in Group 1 (`Total`) and Group 2 (`Gender`).

### Gender (`Kon`, 2 Values)
- `1` (`män`) $\rightarrow$ `dcs:Male`
- `2` (`kvinnor`) $\rightarrow$ `dcs:Female`

---

## 4. Directory Layout

```text
statvar_imports/sweden_census/education/
├── README.md                                 # Documentation
├── manifest.json                             # Automated import specification
├── validation_config.json                    # Import validation rules
├── download_education.py                     # SCB PxWeb REST API downloader (17 CSVs)
├── run.sh                                    # Runs stat_var_processor.py across all 17 CSVs
├── education_test.py                         # Unit test suite
├── sweden_places_resolved.csv                # 321 resolved Sweden place DCIDs
├── education_common_pvmap.csv                # Shared PVMap (region, ages, gender, ignore, years 1985-2035)
├── education_total_pvmap.csv                 # No-gender education level PVMap (Groups 1 & 3)
├── education_gender_pvmap.csv                # With-gender education level PVMap (Groups 2 & 4)
├── education_total_metadata.csv              # 3-column processor config (Groups 1 & 3)
├── education_gender_metadata.csv             # 4-column processor config (Groups 2 & 4)
├── education_total_statvar_remap.csv         # Group 1 DCID remap (6 SVs)
├── education_gender_statvar_remap.csv        # Group 2 DCID remap (12 SVs)
├── education_age_statvar_remap.csv           # Group 3 DCID remap (36 SVs)
├── education_age_gender_statvar_remap.csv    # Group 4 DCID remap (72 SVs)
├── test_data/                                # Sample inputs & expected outputs for E2E/unit testing
├── input_files/                              # Raw wide-format CSVs downloaded from SCB API
├── output/                                   # Generated SVObs CSVs and TMCFs (17 pairs)
└── counters/                                 # Generated stat_var_processor counter CSVs
```

---

## 5. How to Run Locally

### Step 1: Download Raw CSVs from Statistics Sweden API
```bash
python3 download_education.py --output_dir=input_files
```
- Queries `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/UF/UF0506/UF0506B/Utbildning` to discover all available years (`1985` to latest upstream year) and generates all 17 wide-format CSVs in `input_files/`.
- Respects SCB's `10 requests / 10 seconds` rate limit (`1.2s` sleep between POST requests) with exponential backoff retry.

### Step 2: Process All 17 CSVs via `stat_var_processor.py`
```bash
bash run.sh
```
- Runs `stat_var_processor.py` on all 17 files in `input_files/` and writes cleaned `.csv` and `.tmcf` files to `output/` and diagnostics to `counters/`.

### Step 3: Run Unit Tests
```bash
python3 education_test.py
```

---

## 6. Data Notes & Implementation Details

1. **Historical Place Set (`321` Places / `2463 Åsele` Exclusion)**:
   - In the historical import baseline, municipality `2463 Åsele` was marked `#ignore,skip` in the PVMaps, yielding `289` resolved municipalities (`107` + `96` + `86` across the 3 Group 3 municipality splits) + `3` NUTS1 + `8` NUTS2 + `21` NUTS3 = `321` resolved places. This preserves `100.00%` parity across all `746,240` historical records (`1985–2022`) with `0` deleted records and `0` unresolved place errors.
2. **Suppressed & Missing Observations (`".."` / `"."` / `"-"` / `""`)**:
   - SCB returns `".."` for municipalities in historical years prior to their formation (e.g., Knivsta `0330` prior to 2003). For legacy years (`<= 2022`), unobserved/pre-formation cells emit `0` to maintain 100% zero-deletion parity with the historical Data Commons baseline; for post-2022 years (`> 2022`), completely suppressed/missing cells are left blank (`""`) rather than coerced to `0`.
3. **Future-Proof Year Keys (`1985–2035`)**:
   - `education_common_pvmap.csv` pre-populates year keys `1985` through `2035` (`observationDate`) so future annual releases (`2026+`) are ingested automatically without manual PVMap edits.
