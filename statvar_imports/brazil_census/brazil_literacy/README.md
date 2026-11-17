# Brazil Census: Literacy and Illiteracy

- **Upstream Sources**:
  - [IBGE SIDRA Table 9952](https://sidra.ibge.gov.br/tabela/9952) (2022 literacy and illiteracy counts for ages 15+ by sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 9543](https://sidra.ibge.gov.br/tabela/9543) & [Table 9542](https://sidra.ibge.gov.br/tabela/9542) (2022 literacy and illiteracy rates by age group across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/`)
- **Raw Downloads**: `raw_files/` (`sidra_9952_*.json`, `sidra_9543_rates.json`, `sidra_9542_rates_*.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_literacy.csv` + `history/brazil_literacy_historical.csv` -> `brazil_literacy.csv` & `brazil_literacy.tmcf` (via `brazil_literacy_pvmap.csv` and `brazil_literacy_metadata.csv`)
  - `input_files/brazil_literacy_rates.csv` + `rates/history/brazil_literacy_rates_historical.csv` -> `rates/brazil_literacy_rates.csv` & `rates/brazil_literacy_rates.tmcf` (via `brazil_literacy_rates_pvmap.csv` and `brazil_literacy_rates_metadata.csv` with `unit: dcs:Percent` and `scalingFactor: 100`)
- **Coverage**: 1940, 2000, 2010, 2022+
