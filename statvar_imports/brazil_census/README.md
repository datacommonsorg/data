# Brazil Census (Censo Demográfico) Data Commons Imports

## Overview

This directory contains automated Data Commons import pipelines for demographic, socioeconomic, education, and literacy datasets from the **Instituto Brasileiro de Geografia e Estatística (IBGE)** Census of Brazil (*Censo Demográfico*).

All imports are organized into dedicated, year-agnostic topic folders. Each topic pipeline dynamically fetches past, present (2010, 2022), and future census releases from official IBGE SIDRA REST APIs, merges historical census baselines, and generates clean tabular input datasets.

Each subfolder contains:
- `download.py`: Automated multi-year extraction script (queries official IBGE SIDRA REST API and merges historical census baselines)
- `download_test.py`: Hermetic unit tests
- `validation_config.json`: Strict validation rules (threshold $\le 0.1\%$ deletions, zero lint errors, zero missing references)
- `<topic>.csv`: Cleaned observations CSV
- `<topic>.tmcf`: Template MCF mapping data columns to Data Commons schema
- `<topic>_pvmap.csv`: Property-value mapping definition
- `<topic>_metadata.csv`: Configuration parameters for `stat_var_processor.py`
- `input_files/<topic>.csv`: Raw tabular source data (`Ano,Localidade,...`)
- `counters/<topic>_counters.csv`: Processing counters and metrics
- `README.md`: Dataset documentation and provenance

Shared top-level files in `statvar_imports/brazil_census/`:
- `manifest.json`: Consolidated Data Commons import specification for all 7 topic pipelines
- `brazil_places_resolved.csv`: Shared entity mapping to Wikidata and Data Commons DCIDs for all 5,598 Brazilian places (country, 5 macro-regions, 27 states, and 5,565 municipalities)

---

## Datasets Inventory

| # | Topic Directory | Import Name | Observation Period | Granularity | Upstream Source |
|---|---|---|---|---|---|
| 1 | [`brazil_population_by_age_and_sex/`](brazil_population_by_age_and_sex/) | `Brazil_Census_Population_By_Age_And_Sex` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) & Table 1378 |
| 2 | [`brazil_population_by_race/`](brazil_population_by_race/) | `Brazil_Census_Population_By_Race` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9605](https://sidra.ibge.gov.br/tabela/9605) |
| 3 | [`brazil_population_by_religion/`](brazil_population_by_religion/) | `Brazil_Census_Population_By_Religion` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9537](https://sidra.ibge.gov.br/tabela/9537) |
| 4 | [`brazil_population_by_residence/`](brazil_population_by_residence/) | `Brazil_Census_Population_By_Residence` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9923](https://sidra.ibge.gov.br/tabela/9923) & Table 608 |
| 5 | [`brazil_literacy/`](brazil_literacy/) | `Brazil_Census_Literacy` | 1940–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9952](https://sidra.ibge.gov.br/tabela/9952) |
| 6 | [`brazil_education/`](brazil_education/) | `Brazil_Census_Education` | 2000–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 1972](https://sidra.ibge.gov.br/tabela/1972) |
| 7 | [`brazil_total_population/`](brazil_total_population/) | `Brazil_Census_Total_Population` | 1991–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) |

---

## Automation Manifest

The consolidated manifest [`manifest.json`](manifest.json) declares all 7 active Brazil Census topic import specifications and references the shared [`brazil_places_resolved.csv`](brazil_places_resolved.csv).

---

## Unit Testing

To execute all hermetic unit tests across all 7 topic imports:
```bash
python3 -m unittest discover -v -s statvar_imports/brazil_census -p '*_test.py'
```
