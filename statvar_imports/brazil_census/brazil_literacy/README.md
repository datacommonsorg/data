# Brazil Census: Literacy and Illiteracy

- **Upstream Sources**:
  - [IBGE SIDRA Table 9952](https://sidra.ibge.gov.br/tabela/9952) (2022 literacy and illiteracy counts for ages 15+ by sex across national, regional, state, and municipal levels)
  - [IBGE SIDRA Table 9543](https://sidra.ibge.gov.br/tabela/9543) & [Table 9542](https://sidra.ibge.gov.br/tabela/9542) (2022 literacy and illiteracy rates by age group across national, regional, state, and municipal levels)
  - IBGE Historical Census workbooks (1940, 2000, and 2010 literacy counts and rates)
- **Raw Downloads**: `raw_files/` (`sidra_9952_*.json`, `sidra_9543_rates.json`, `sidra_9542_rates_*.json`, `Brazil_1940_Literate.xls`, `Brazil_2010_llliterate_race.xls`, `Brazil_2000_2010_Illiterate_age.csv`, `Brazil_2000_literate.csv`)
- **Processed Inputs & Outputs**:
  - `input_files/brazil_literacy.csv` -> `brazil_literacy.csv` & `brazil_literacy.tmcf` (via `brazil_literacy_pvmap.csv` and `brazil_literacy_metadata.csv`)
  - `brazil_literacy_rates.csv` & `brazil_literacy_rates.tmcf` (direct fractional literacy/illiteracy rate observations with `unit: dcs:Percent` and `scalingFactor: 100`)
- **Coverage**: 1940, 2000, 2010, 2022+
