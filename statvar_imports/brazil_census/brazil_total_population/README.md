# Brazil Census: Total Resident Population

- **Upstream Sources**:
  - [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) (2022 Census resident population by sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 1378](https://sidra.ibge.gov.br/tabela/1378) (2010 Census resident population by sex)
  - [IBGE SIDRA Table 6579](https://sidra.ibge.gov.br/tabela/6579) (2024–2026+ annual EstimaPop resident population estimates across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1991`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_total_population/brazil_total_population_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9514_2022_n6.json`, `sidra_6579_probe.json`, `sidra_6579_estimates_*_n6.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_total_population.csv` (`Ano,Localidade,Sexo,Populacao`) + `history/brazil_total_population_historical.csv` -> `brazil_total_population.csv` & `brazil_total_population.tmcf` (via `brazil_total_population_pvmap.csv` and `brazil_total_population_metadata.csv`)
- **Coverage**: 1991, 2010, 2022, 2024–2026+
