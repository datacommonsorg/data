# Brazil Census: Literacy and Illiteracy Counts

- **Upstream Sources**:
  - [IBGE SIDRA Table 9952](https://sidra.ibge.gov.br/tabela/9952) (2022+ literacy and illiteracy counts for ages 15+ by sex across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_literacy/brazil_literacy_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9952_*.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_literacy.csv` + `history/brazil_literacy_historical.csv` -> `brazil_literacy.csv` & `brazil_literacy.tmcf` (via `brazil_literacy_pvmap.csv` and `brazil_literacy_metadata.csv`)
  - Literacy & illiteracy rates live in [`../brazil_literacy_rates/`](../brazil_literacy_rates/)
- **Coverage**: 1940, 2000, 2010, 2022+
