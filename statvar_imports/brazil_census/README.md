# Brazil Census (Censo Demográfico) Data Commons Imports

## Overview

This directory contains the consolidated automated Data Commons import pipeline (`Brazil_Census`) for demographic, socioeconomic, education, and literacy datasets from the **Instituto Brasileiro de Geografia e Estatística (IBGE)** Census of Brazil (*Censo Demográfico*) and annual municipal population estimates (*EstimaPop*).

All sub-imports are organized into dedicated, year-agnostic topic folders under a single consolidated [`manifest.json`](manifest.json) (`import_name: "Brazil_Census"`) and a single root [`validation_config.json`](validation_config.json). Each topic pipeline dynamically fetches live `2022+` releases (and annual Table 6579 estimates) from official IBGE SIDRA REST APIs into `input_files/<topic>.csv`, syncs immutable pre-2022 historical CSVs (`1940`, `1991`, `2000`, `2010`) from `gs://unresolved_mcf/country/brazil/history/` into `history/<topic>_historical.csv`, archives raw upstream payloads in `raw_files/`, and processes both live and historical CSVs together in Cloud Batch via `stat_var_processor.py`.

Each subfolder contains:
- `download.py`: Automated live `2022+` IBGE SIDRA REST API extraction and `history/*_historical.csv` sync script (archiving raw SIDRA JSON payloads under `raw_files/`)
- `download_test.py`: Hermetic unit tests
- `<topic>_pvmap.csv`: Property-value mapping definition (plus `brazil_literacy/brazil_literacy_rates_pvmap.csv` for literacy rates)
- `<topic>_metadata.csv`: Configuration parameters for `stat_var_processor.py` (plus `brazil_literacy/brazil_literacy_rates_metadata.csv`)
- `<topic>.tmcf`: Pre-generated template MCF where applicable (outputs `brazil_literacy_rates` uses `stat_var_processor.py` PVMAP directly)
- `input_files/<topic>.csv`: Live `2022+` tabular input data (`Ano,Localidade,...`) (plus companion `brazil_literacy/input_files/brazil_literacy_rates.csv`)
- `history/<topic>_historical.csv`: Synced immutable pre-2022 historical baseline CSV (or `brazil_literacy/rates/history/brazil_literacy_rates_historical.csv`)
- `raw_files/`: Archived raw upstream SIDRA JSON payloads
- `counters/<topic>_counters.csv`: Processing counters and metrics
- `README.md`: Dataset documentation and provenance

Shared top-level files in `statvar_imports/brazil_census/`:
- `brazil_download_utils.py`: Shared HTTP retry session (`get_robust_session`), `raw_files/` staging (`get_raw_dir`), immutable `< 2022` GCS sync (`get_history_path`, `sync_historical_csv`), IBGE SIDRA API fetcher (`fetch_sidra_data`), canonical location resolution (`resolve_sidra_loc`), and atomic writes (`write_df_atomically`) used across all 7 topic download scripts
- `manifest.json`: Consolidated Data Commons import specification (`Brazil_Census`) covering all 7 topic download scripts and 8 `import_inputs`
- `validation_config.json`: Custom consolidated validation rules (date freshness, historical start dates, StatVar counts, and minimum place count checks; inherits default checks including `check_deleted_records_percent` $\le 0.1\%$ from `tools/import_validation/validation_config.json`)
- `brazil_places_resolved.csv`: Shared entity mapping to Wikidata and Data Commons DCIDs for all 5,603 Brazilian places in Data Commons KG (1 country, 5 macro-regions, 27 states, and 5,570 municipalities, plus historical/alias/encoding variants; IBGE 2024 municipality `5101837` is skipped until added to Data Commons `geos`)

---

## Sub-Imports Inventory (`Brazil_Census`)

| # | Topic Directory | Output Table(s) | Observation Period | Granularity | Upstream Source |
|---|---|---|---|---|---|
| 1 | [`brazil_education/`](brazil_education/) | `brazil_education.csv` | 2000–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 1972](https://sidra.ibge.gov.br/tabela/1972), Tables 10057–10059 & IBGE FTP |
| 2 | [`brazil_literacy/`](brazil_literacy/) | `brazil_literacy.csv`, `brazil_literacy_rates.csv` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9952](https://sidra.ibge.gov.br/tabela/9952), Table 9543 & Table 9542 |
| 3 | [`brazil_population_by_age_and_sex/`](brazil_population_by_age_and_sex/) | `brazil_population_by_age_and_sex.csv` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) & Table 1378 |
| 4 | [`brazil_population_by_race/`](brazil_population_by_race/) | `brazil_population_by_race.csv` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9605](https://sidra.ibge.gov.br/tabela/9605) |
| 5 | [`brazil_population_by_religion/`](brazil_population_by_religion/) | `brazil_population_by_religion.csv` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9537](https://sidra.ibge.gov.br/tabela/9537) & Table 2094 |
| 6 | [`brazil_population_by_residence/`](brazil_population_by_residence/) | `brazil_population_by_residence.csv` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9923](https://sidra.ibge.gov.br/tabela/9923) & Table 608 |
| 7 | [`brazil_total_population/`](brazil_total_population/) | `brazil_total_population.csv` | 1991–2026+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514), Table 1378 & Table 6579 |

---

## Automation Manifest

The consolidated manifest [`manifest.json`](manifest.json) declares the `Brazil_Census` import specification across all 8 output tables (configured for weekly Cloud Batch execution via `cron_schedule: "0 10 * * 1"`, with unchanged weeks cleanly no-oping as `ImportStatus.SKIP`) and references the shared [`brazil_places_resolved.csv`](brazil_places_resolved.csv) and [`validation_config.json`](validation_config.json).

### Custom Downloader Rationale

The shared repo utilities (`util/download_util.py`, `util/download_util_script.py`, `tools/download_utils/requests_wrappers.py`) only fetch/retry/cache individual URLs and save or unzip raw payloads. The `brazil_census` sub-imports use custom `download.py` modules (with shared `urllib3.util.Retry` sessions, `raw_files/` archiving, `sync_historical_csv` for immutable `< 2022` `history/` files, and `fallback_to_cached` atomic CSV writes) because IBGE ingestion requires:
- **SIDRA JSON envelope & split queries**: `apisidra.ibge.gov.br` wraps column metadata in element `[0]` (`raw_json[1:]`), uses sentinel strings (`"-"`, `"..."`, `".."`, `"X"`), and enforces cell limits requiring split requests (e.g., `TABLE_2022_EDUCATION_SPECS` chunks and macro `n1/n2/n3` vs. municipal `n6` splits).
- **Immutable `history/` GCS sync**: Downloads finalized pre-2022 historical CSVs (`1940`, `1991`, `2000`, `2010`) from `gs://unresolved_mcf/country/brazil/history/` without re-parsing legacy workbooks during weekly refreshes.
- **Derived metrics & unindexed entity guards**: Computes broad age cohorts (`0To14`, `15To59`, `60OrMore`) and Table `9542` literacy-rate fractions, parses `D3N` year strings dynamically, and skips unindexed 2024 municipality `5101837`.

---

## Unit Testing

To execute all hermetic unit tests across all 7 topic sub-imports:
```bash
./run_tests.sh -p statvar_imports/brazil_census
```
