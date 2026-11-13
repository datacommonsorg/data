# Brazil Census: Resident Population by Age and Sex

- **Upstream Sources**:
  - [IBGE SIDRA Table 9514](https://sidra.ibge.gov.br/tabela/9514) (2022 resident population by age and sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 1378](https://sidra.ibge.gov.br/tabela/1378) (2010 resident population by age and sex across national, regional, state, and municipal levels)
  - IBGE Historical Census workbooks (1940, 1991, 2000 age and sex distributions)
- **Raw Downloads**: `raw_files/` (`sidra_9514_*.json`, `sidra_1378_*.json`, `Brazil_1940_age_sex.xls`, `Brazil_2000_age_sex.xls`, `POPU91*.xls`)
- **Processed Input**: `input_files/brazil_population_by_age_and_sex.csv` (`Ano,Localidade,Idade,Sexo,Populacao`)
- **PV Map**: `brazil_population_by_age_and_sex_pvmap.csv`
- **Metadata**: `brazil_population_by_age_and_sex_metadata.csv`
- **Coverage**: 1940, 1991, 2000, 2010, 2022+
