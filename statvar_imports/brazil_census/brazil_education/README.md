# Brazil Census: Education and School Attendance

- **Upstream Sources**:
  - [IBGE SIDRA Table 1972](https://sidra.ibge.gov.br/tabela/1972) (2000, 2010 school & daycare attendance by level and administrative network)
  - [IBGE SIDRA Table 10057](https://sidra.ibge.gov.br/tabela/10057) (2022 Census student attendance, age 0 to 5)
  - [IBGE SIDRA Table 10058](https://sidra.ibge.gov.br/tabela/10058) (2022 Census student attendance, age 6 to 17)
  - [IBGE SIDRA Table 10059](https://sidra.ibge.gov.br/tabela/10059) (2022 Census student attendance, age 18+)
  - IBGE Historical Census baselines (`2000`, `2010` synced from `gs://unresolved_mcf/country/brazil/history/brazil_education/brazil_education_historical.csv`)
- **Raw Downloads**: `raw_files/` (`sidra_1972_*.json`, `sidra_10057_*.json`, `sidra_10058_*.json`, `sidra_10059_*.json`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_education.csv` (`Ano,Localidade,RedeEnsino,NivelEnsino,Estudantes`) + `history/brazil_education_historical.csv` -> `brazil_education.csv` & `brazil_education.tmcf` (via `brazil_education_pvmap.csv` and `brazil_education_metadata.csv`)
- **Coverage**: 2000, 2010, 2022+
