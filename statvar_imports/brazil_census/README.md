# Brazil Census (Censo Demográfico) Data Commons Imports

## Overview

This directory contains the consolidated automated Data Commons import pipeline (`Brazil_Census`) for demographic, socioeconomic, education, and literacy datasets from the **Instituto Brasileiro de Geografia e Estatística (IBGE)** Census of Brazil (*Censo Demográfico*) and annual municipal population estimates (*EstimaPop*).

All sub-imports are organized into dedicated, year-agnostic topic folders under a single consolidated [`manifest.json`](manifest.json) (`import_name: "Brazil_Census"`) and a single root [`validation_config.json`](validation_config.json). Each topic pipeline dynamically fetches past, present (2010, 2022, 2024–2026+), and future releases from official IBGE SIDRA REST APIs, merges historical census baselines (1940, 1991, 2000, 2010), archives raw upstream payloads in `raw_files/`, and generates clean tabular input datasets.

Each subfolder contains:
- `download.py`: Automated multi-year extraction script (queries official IBGE SIDRA REST API, merges historical census baselines, and archives raw payloads under `raw_files/`)
- `download_test.py`: Hermetic unit tests
- `<topic>.tmcf`: Template MCF mapping data columns to Data Commons schema
- `<topic>_pvmap.csv`: Property-value mapping definition
- `<topic>_metadata.csv`: Configuration parameters for `stat_var_processor.py`
- `input_files/<topic>.csv`: Processed tabular input data (`Ano,Localidade,...`) (plus `brazil_literacy/brazil_literacy_rates.csv`)
- `raw_files/`: Archived raw upstream SIDRA JSON and IBGE XLS/CSV payloads
- `counters/<topic>_counters.csv`: Processing counters and metrics
- `README.md`: Dataset documentation and provenance

Shared top-level files in `statvar_imports/brazil_census/`:
- `manifest.json`: Consolidated Data Commons import specification (`Brazil_Census`) covering all 7 topic download scripts and 8 `import_inputs`
- `validation_config.json`: Consolidated validation rules (threshold $\le 0.1\%$ deletions, date freshness and historical start date checks, place count checks)
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

The consolidated manifest [`manifest.json`](manifest.json) declares the `Brazil_Census` import specification across all 8 output tables and references the shared [`brazil_places_resolved.csv`](brazil_places_resolved.csv) and [`validation_config.json`](validation_config.json).

---

## Unit Testing

To execute all hermetic unit tests across all 7 topic sub-imports:
```bash
./run_tests.sh -p statvar_imports/brazil_census
```
