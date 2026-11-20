# Brazil Census: Population by Race (Cor ou Raça)

- **Upstream Sources**:
  - [IBGE SIDRA Table 9605](https://sidra.ibge.gov.br/tabela/9605) (2022+ resident population by race/color across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_population_by_race/brazil_population_by_race_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9605_probe.json`, `sidra_9605_*_n6.json`, `sidra_9605_macro_all.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_population_by_race.csv` (`Ano,Localidade,Cor,Populacao`) + `history/brazil_population_by_race_historical.csv` -> `brazil_population_by_race.csv` & `brazil_population_by_race.tmcf` (via `brazil_population_by_race_pvmap.csv` and `brazil_population_by_race_metadata.csv`)
- **Coverage**: 1940, 2000, 2010, 2022+
