# Brazil Census: Population by Religion

- **Upstream Source**: [IBGE SIDRA Table 9537](https://sidra.ibge.gov.br/tabela/9537)
- **Raw Input**: `input_files/brazil_population_by_religion.csv` (`Ano,Localidade,Religiao,Populacao`)
- **PV Map**: `brazil_population_by_religion_pvmap.csv`
- **Metadata**: `brazil_population_by_religion_metadata.csv`
- **Coverage**: 1940, 2000, 2022+
- **Methodology Note**: Historical census religion tables (1940 and 2000) report religion across the total resident population (all ages), whereas the 2022 IBGE Census (SIDRA Table 9537) reports religion for residents aged 10 years and older (`10 anos ou mais`). To maintain series continuity across census waves while avoiding overwriting the all-ages `Count_Person` total in 2022, the 2022 `Total` row from Table 9537 is excluded and religious denomination series continue under `Count_Person_<Religion>`.
