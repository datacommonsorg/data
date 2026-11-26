# Brazil Census: Resident Population by Age and Sex

- **Upstream Sources**:
  - [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) (2022 resident population by age and sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 1378](https://sidra.ibge.gov.br/tabela/1378) (2010 resident population by age and sex across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `1991`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_population_by_age_and_sex/brazil_population_by_age_and_sex_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9514_macro.json`, `sidra_9514_muni.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_population_by_age_and_sex.csv` (`Ano,Localidade,Idade,Sexo,Populacao`) + `history/brazil_population_by_age_and_sex_historical.csv` -> `brazil_population_by_age_and_sex.csv` & `brazil_population_by_age_and_sex.tmcf` (via `brazil_population_by_age_and_sex_pvmap.csv` and `brazil_population_by_age_and_sex_metadata.csv`)
- **Coverage**: 1940, 1991, 2000, 2010, 2022+
