# Brazil Census (Censo Demográfico) Data Commons Imports

## Overview

This directory contains automated Data Commons import pipelines for demographic, socioeconomic, education, and literacy datasets from the **Instituto Brasileiro de Geografia e Estatística (IBGE)** Census of Brazil (*Censo Demográfico*).

All imports are organized into dedicated, year-agnostic topic folders. Each topic pipeline dynamically fetches past, present (2010, 2022), and future census releases from official IBGE SIDRA REST APIs, merges historical census baselines, and generates clean tabular input datasets.

Each subfolder contains:
- `download.py`: Automated multi-year extraction script (queries official IBGE SIDRA REST API and merges historical census baselines)
- `download_test.py`: Hermetic unit tests
- `manifest.json`: Data Commons import specification
- `validation_config.json`: Strict validation rules (threshold $\le 0.1\%$ deletions, zero lint errors, zero missing references)
- `<topic>.csv`: Cleaned observations CSV
- `<topic>.tmcf`: Template MCF mapping data columns to Data Commons schema
- `<topic>_pvmap.csv`: Property-value mapping definition
- `<topic>_metadata.csv`: Configuration parameters for `stat_var_processor.py`
- `brazil_places_resolved.csv`: Entity mapping to Wikidata and Data Commons DCIDs
- `input_files/<topic>.csv`: Raw tabular source data (`Ano,Localidade,...`)
- `counters/<topic>_counters.csv`: Processing counters and metrics
- `README.md`: Dataset documentation and provenance

---

## Datasets Inventory

| # | Topic Directory | Import Name | Observation Period | Granularity | Upstream Source |
|---|---|---|---|---|---|
| 1 | [`brazil_population_by_age_and_sex/`](brazil_population_by_age_and_sex/) | `Brazil_Census_Population_By_Age_And_Sex` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) & Table 1378 |
| 2 | [`brazil_population_by_race/`](brazil_population_by_race/) | `Brazil_Census_Population_By_Race` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9605](https://sidra.ibge.gov.br/tabela/9605) |
| 3 | [`brazil_population_by_religion/`](brazil_population_by_religion/) | `Brazil_Census_Population_By_Religion` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9537](https://sidra.ibge.gov.br/tabela/9537) |
| 4 | [`brazil_population_by_residence/`](brazil_population_by_residence/) | `Brazil_Census_Population_By_Residence` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9923](https://sidra.ibge.gov.br/tabela/9923) & Table 608 |
| 5 | [`brazil_literacy/`](brazil_literacy/) | `Brazil_Census_Literacy` | 1940–2022+ | Country, 5 Regions, 27 States (33 places) | [IBGE SIDRA Table 9543](https://sidra.ibge.gov.br/tabela/9543) & Table 1383 |
| 6 | [`brazil_education/`](brazil_education/) | `Brazil_Census_Education` | 2000–2022+ | Municipalities and States | [IBGE SIDRA Table 3987](https://sidra.ibge.gov.br/tabela/3987) |
| 7 | [`brazil_total_population/`](brazil_total_population/) | `Brazil_Census_Total_Population` | 1991–2022+ | Country, 5 Regions, 27 States, Municipalities | [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) |

---

## Automation Manifest

The repository-level manifest [`manifest.json`](manifest.json) declares all 7 active Brazil Census topic import specifications. Each individual subdirectory also includes its own `manifest.json` for isolated modular execution.

---

## Unit Testing

To execute all hermetic unit tests across all 7 topic imports:
```bash
for d in statvar_imports/brazil_census/*/; do
  if [ -f "$d/download_test.py" ]; then
    (cd "$d" && python3 -m unittest download_test.py)
  fi
done
```
