# Brazil Census: Total Resident Population

- **Upstream Sources**:
  - [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) (2022 Census resident population by sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 1378](https://sidra.ibge.gov.br/tabela/1378) (2010 Census resident population by sex)
  - [IBGE SIDRA Table 6579](https://sidra.ibge.gov.br/tabela/6579) (2024–2026+ annual EstimaPop resident population estimates across national, regional, state, and municipal levels)
  - IBGE Historical Census workbooks (1991 POPU state workbooks and 2022 municipal population tables)
- **Raw Downloads**: `raw_files/` (`sidra_9514_2022_n6.json`, `sidra_1378_2010_macro.json`, `sidra_6579_estimates_n6.json`, `Brazil_2022_Muncipal_POP.xlsx`, `POP2022_Brasil_e_UFs.xls`)
- **Processed Input**: `input_files/brazil_total_population.csv` (`Ano,Localidade,Sexo,Populacao`)
- **PV Map**: `brazil_total_population_pvmap.csv`
- **Metadata**: `brazil_total_population_metadata.csv`
- **Coverage**: 1991, 2000, 2010, 2022, 2024–2026+
