# Brazil Census: Population by Residence (Urban/Rural)

- **Upstream Sources**:
  - [IBGE SIDRA Table 9923](https://sidra.ibge.gov.br/tabela/9923) (2022 resident population by urban/rural situation across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 608](https://sidra.ibge.gov.br/tabela/608) (2010 resident population by urban/rural situation and sex across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `1991`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_population_by_residence/brazil_population_by_residence_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9923_2022_n6.json`, `sidra_608_*.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_population_by_residence.csv` (`Ano,Localidade,Situacao,Sexo,Populacao`) + `history/brazil_population_by_residence_historical.csv` -> `brazil_population_by_residence.csv` & `brazil_population_by_residence.tmcf` (via `brazil_population_by_residence_pvmap.csv` and `brazil_population_by_residence_metadata.csv`)
- **Coverage**: 1940, 1991, 2000, 2010, 2022+
