# Sweden Census: Health & Vital Statistics (Deaths, Fertility Rate, Live Births)

## 1. Import Overview

This directory contains the automated Data Commons import pipeline for **Sweden Census — Category 2: Health & Vital Statistics (Deaths, Fertility Rate, and Live Births)** from **Statistics Sweden (Statistiska centralbyrån, SCB)**.

| Field | Details |
| :--- | :--- |
| **Source Agency** | Statistics Sweden (SCB / *Statistiska centralbyrån*) |
| **Import Type** | Automated (Python PxWeb REST API downloader + `stat_var_processor.py`) |
| **Authentication** | None (Public SCB PxWeb REST API; rate-limited to 10 requests / 10 seconds) |
| **SCB Table IDs** | 1) `BE0101I/DodaFodelsearK` & `BE0101I/DodaFodelsearKCKM` (*Döda efter region, ålder och kön*)<br>2) `BE0101H/FruktsamhetSum` (*Summerad fruktsamhet efter region och kön*)<br>3) `BE0101G/BefUtvKon1749` (*Folkmängd och befolkningsförändringar i Sverige efter kön*) |
| **REST API Endpoints** | 1) `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101I/DodaFodelsearK`<br>2) `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101I/DodaFodelsearKCKM`<br>3) `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101H/FruktsamhetSum`<br>4) `https://api.scb.se/OV0104/v1/doris/sv/ssd/START/BE/BE0101/BE0101G/BefUtvKon1749` |
| **Geographic Coverage** | 322 Places in Sweden: `1` Country (`country/SWE`), `3` NUTS1 (`nuts/SE1`–`SE3`), `8` NUTS2 (`nuts/SE11`–`SE33`), `21` NUTS3 Counties (`nuts/SE110`–`SE332`), and `289` Municipalities (`wikidataId/Q*`) |
| **Temporal Coverage** | `1749–2025` Live Births / `1968–2025` Deaths / `2000–2025` Fertility Rate (Annual, dynamically discovers `2026+`) |
| **Release Frequency** | Annual (scheduled weekly refresh cron `0 08 * * 1`) |
| **Total Unique StatVars** | **30** unique `StatisticalVariable` DCIDs (`1` Total Death + `2` Gender Death + `22` Age×Gender Death + `2` Fertility Rate + `3` Live Births) |
| **Total SVObs (`1749–2025`)** | **112,171** (`105,507` historical `1749–2022` + `6,664` new `2023–2025`) |

---

## 2. Sub-Imports & Marginal Breakdowns (13 CSVs)

| # | Sub-Import File Stem | Group | Place Level | Places | Mapped Cols | Unique SVs | PVMap | Metadata Config | StatVar Remap |
| :-: | :--- | :--- | :--- | ---: | :-: | ---: | :--- | :--- | :--- |
| 1 | `Death_NUTS1` | **Group 1: Deaths Total** | NUTS1 | 3 | 2 | 1 | `deaths_total_pvmap.csv` | `deaths_total_metadata.csv` | `deaths_total_statvar_remap.csv` |
| 2 | `Death_NUTS2` | **Group 1: Deaths Total** | NUTS2 | 8 | 2 | 1 | `deaths_total_pvmap.csv` | `deaths_total_metadata.csv` | `deaths_total_statvar_remap.csv` |
| 3 | `Death_NUTS3` | **Group 1: Deaths Total** | NUTS3 | 21 | 2 | 1 | `deaths_total_pvmap.csv` | `deaths_total_metadata.csv` | `deaths_total_statvar_remap.csv` |
| 4 | `Death_Muncipality` | **Group 1: Deaths Total** | Municipality | 289 | 2 | 1 | `deaths_total_pvmap.csv` | `deaths_total_metadata.csv` | `deaths_total_statvar_remap.csv` |
| 5 | `Death_gender_NUTS1` | **Group 2: Deaths Gender** | NUTS1 | 3 | 3 | 2 | `deaths_gender_pvmap.csv` | `deaths_gender_metadata.csv` | `deaths_gender_statvar_remap.csv` |
| 6 | `Death_gender_NUTS2` | **Group 2: Deaths Gender** | NUTS2 | 8 | 3 | 2 | `deaths_gender_pvmap.csv` | `deaths_gender_metadata.csv` | `deaths_gender_statvar_remap.csv` |
| 7 | `Death_gender_NUTS3` | **Group 2: Deaths Gender** | NUTS3 | 21 | 3 | 2 | `deaths_gender_pvmap.csv` | `deaths_gender_metadata.csv` | `deaths_gender_statvar_remap.csv` |
| 8 | `Death_gender_Muncipality` | **Group 2: Deaths Gender** | Municipality | 289 | 3 | 2 | `deaths_gender_pvmap.csv` | `deaths_gender_metadata.csv` | `deaths_gender_statvar_remap.csv` |
| 9 | `Death_age_gender_NUTS1` | **Group 3: Deaths Age×Gender** | NUTS1 | 3 | 3 | 22 | `deaths_age_gender_pvmap.csv` | `deaths_age_gender_metadata.csv` | `deaths_age_gender_statvar_remap.csv` |
| 10 | `Death_age_gender_NUTS2` | **Group 3: Deaths Age×Gender** | NUTS2 | 8 | 3 | 22 | `deaths_age_gender_pvmap.csv` | `deaths_age_gender_metadata.csv` | `deaths_age_gender_statvar_remap.csv` |
| 11 | `Death_age_gender_NUTS3` | **Group 3: Deaths Age×Gender** | NUTS3 | 21 | 3 | 22 | `deaths_age_gender_pvmap.csv` | `deaths_age_gender_metadata.csv` | `deaths_age_gender_statvar_remap.csv` |
| 12 | `FertilityRate_gender_Muncipality` | **Group 4: Fertility Rate** | Municipality | 288 | 2 | 2 | `fertility_pvmap.csv` | `fertility_metadata.csv` | *(None needed)* |
| 13 | `LiveBirth_gender_total_country` | **Group 5: Live Births** | Country | 1 | 1 | 3 | `livebirth_pvmap.csv` | `livebirth_metadata.csv` | `livebirth_statvar_remap.csv` |

---

## 3. Directory Layout

```text
statvar_imports/sweden_census/health/
├── README.md                                 # Documentation
├── manifest.json                             # Automated import specification
├── validation_config.json                    # Import validation rules
├── download_health.py                        # SCB PxWeb REST API downloader (13 CSVs)
├── run.sh                                    # Runs stat_var_processor.py across all 13 CSVs
├── health_test.py                            # Unit test suite running on test_data/
├── sweden_places_resolved.csv                # Resolved Sweden place DCIDs
├── deaths_total_pvmap.csv                    # Group 1 PVMap (1 SV)
├── deaths_total_metadata.csv                 # Group 1 processor config (mapped_columns=2)
├── deaths_total_statvar_remap.csv            # Group 1 DCID remap
├── deaths_gender_pvmap.csv                   # Group 2 PVMap (2 SVs)
├── deaths_gender_metadata.csv                # Group 2 processor config (mapped_columns=3)
├── deaths_gender_statvar_remap.csv           # Group 2 DCID remap
├── deaths_age_gender_pvmap.csv               # Group 3 PVMap (22 SVs)
├── deaths_age_gender_metadata.csv            # Group 3 processor config (mapped_columns=3)
├── deaths_age_gender_statvar_remap.csv       # Group 3 DCID remap
├── fertility_pvmap.csv                       # Group 4 PVMap (2 SVs)
├── fertility_metadata.csv                    # Group 4 processor config (mapped_columns=2)
├── livebirth_pvmap.csv                       # Group 5 PVMap (3 SVs)
├── livebirth_metadata.csv                    # Group 5 processor config (mapped_columns=1)
├── livebirth_statvar_remap.csv               # Group 5 DCID remap
├── test_data/                                # Sample inputs & expected outputs for unit testing
├── input_files/                              # Raw wide-format CSVs downloaded from SCB API
├── output/                                   # Generated SVObs CSVs and TMCFs (13 pairs)
└── counters/                                 # Generated stat_var_processor counter CSVs
```

---

## 4. Prerequisites & How to Run Locally

### Prerequisites
- Python 3.9+ with `absl-py`, `requests`, and `urllib3` installed (standard Data Commons `requirements.txt`).
- No API key or authentication is required to query the public Statistics Sweden (SCB) PxWeb v1 REST API.

### Step 1: Download Raw CSVs from Statistics Sweden API
```bash
python3 download_health.py --output_dir=input_files
```
- Queries the 4 SCB PxWeb endpoints (`DodaFodelsearK`, `DodaFodelsearKCKM`, `FruktsamhetSum`, `BefUtvKon1749`) to discover all available years up to the latest upstream release and writes all 13 wide-format CSVs into `input_files/`.
- Respects SCB's `10 requests / 10 seconds` rate limit (`1.2s` sleep between POST requests) with exponential backoff retry on HTTP `429`/`5xx` responses.

### Step 2: Process All 13 CSVs via `stat_var_processor.py`
```bash
bash run.sh
```
- Runs `stat_var_processor.py` on all 13 files in `input_files/` and writes cleaned `.csv` and `.tmcf` files to `output/` and diagnostics to `counters/`.

### Step 3: Run Unit Tests
```bash
python3 health_test.py
```

---

## 5. Data Notes, Refresh Procedure & Troubleshooting

1. **Historical Place Set (`322` Places / `2463 Åsele` Exclusion)**:
   - In the historical import baseline, municipality `2463 Åsele` was marked `#IgnoreRow,True` in the PVMaps, yielding `289` resolved municipalities in Deaths (`288` in Fertility Rate, where `2418 Malå` has suppressed `".."` values across all years) + `3` NUTS1 + `8` NUTS2 + `21` NUTS3 + `1` Country (`country/SWE`) = `322` resolved places. This preserves `100.00%` parity across all `105,507` historical records (`1749–2022`) with `0` deleted records and `0` unresolved place errors.
2. **CKM Table Merge for 2025+ Deaths (`DodaFodelsearK` + `DodaFodelsearKCKM`)**:
   - Starting in 2025, SCB publishes sub-national death counts in the CKM-adjusted companion table `BE0101I/DodaFodelsearKCKM` (where total age is coded `TotSA` and age 100+ is coded `100+1`, compared to `tot` and `100+` in `DodaFodelsearK`). `download_health.py` automatically merges both tables into a unified `1968–latest` time series.
3. **Suppressed & Missing Observations (`".."` / `"."` / `"-"` / `""`)**:
   - In Deaths tables, suppressed or unavailable cell counts are converted to `0` during age-bracket and NUTS rollup aggregation. In Fertility Rate (`FruktsamhetSum`), suppressed municipal cells are preserved as `".."` and skipped by `stat_var_processor.py`, matching the historical CNS baseline.
4. **Future-Proof Year Keys (`1749–2035`)**:
   - All 5 PVMaps pre-populate explicit year keys through `2035` (`observationDate`) so annual refreshes through `2035` are ingested automatically without manual PVMap edits. To extend past `2035`, append new year rows to the 5 `*_pvmap.csv` files.
