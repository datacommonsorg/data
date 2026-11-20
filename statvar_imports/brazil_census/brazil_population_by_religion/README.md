# Brazil Census: Population by Religion

- **Upstream Sources**:
  - [IBGE SIDRA Table 9537](https://sidra.ibge.gov.br/tabela/9537) (2022 resident population aged 10+ by religion across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 2094](https://sidra.ibge.gov.br/tabela/2094) (2010 resident population of all ages by religion across national, regional, state, and municipal levels)
  - IBGE Historical Census baselines (`1940`, `2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_population_by_religion/brazil_population_by_religion_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_9537_2022_n6.json`, `sidra_2094_2010_n6.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_population_by_religion.csv` (`Ano,Localidade,Religiao,Populacao`) + `history/brazil_population_by_religion_historical.csv` -> `brazil_population_by_religion.csv` & `brazil_population_by_religion.tmcf` (via `brazil_population_by_religion_pvmap.csv` and `brazil_population_by_religion_metadata.csv`)
- **Coverage**: 1940, 2000, 2010, 2022+
- **Methodology Note**: Historical census religion tables (1940, 2000, and 2010 via SIDRA Table 2094) report religion across the total resident population (all ages), whereas the 2022 IBGE Census (SIDRA Table 9537) reports religion for residents aged 10 years and older (`10 anos ou mais`). To accurately reflect the 2022 universe while avoiding overwriting the all-ages `Count_Person` total in 2022, the 2022 `Total` row from Table 9537 is excluded and 2022 religious denomination series are emitted under age-qualified `Count_Person_10OrMoreYears_<Religion>` StatVars (`age: [10 - Years]`).
