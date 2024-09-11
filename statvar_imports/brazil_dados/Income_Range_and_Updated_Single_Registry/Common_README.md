###  Brazil Income Range And Updated Single Registry

- import_name: "Brazil_Income_Range_And_Updated_Single_Registry"

- source: https://www.gov.br/
          https://dados.gov.br/dados/busca?termo=auxilio%2520Brasil
          https://www.gov.br/pt-br/servicos/receber-o-auxilio-brasil-pab
          https://dados.gov.br/dados/conjuntos-dados/familias-por-faixa-de-renda-com-cadastro-atualizado-no-cadastro-unico

- how to download data: Manual download from source based on filter - `Brazil Income Range and Updated Single Registry`

- place_resolution: Municipality codes of Brazil. (In place mapping, the municipal codes 293020 & 530010 are not mapped and there is no wikidata id in source)

- statvars: Demographics, Household
  
- years: Updated Single Registry - 2015 to 2023 (2016 & 2020 data is not available)
         Income Range Single Registry - 2012 to 2023
(Separate dataset is downloaded for each year and here only 2023 dataset is taken as example)

- type of place: AA,AA2, City. 

### How to run:
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_dados/<filepath>/pv_map.csv --places_resolved_csv=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Brazil_MunicipalityCodes_Places_Resolved.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Income_Range_Single_Registry_Families/test_data/sample_input/Income_Range_Single_Registry_Families_test_data.csv --pv_map=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Income_Range_Single_Registry_Families/pv_map.csv --places_resolved_csv=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Brazil_MunicipalityCodes_Places_Resolved.csv --config=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Income_Range_Single_Registry_Families/metadata.csv --output_path=statvar_imports/brazil_dados/Income_Range_and_Updated_Single_Registry/Income_Range_Single_Registry_Families/test_data/sample_output/Income_Range_Single_Registry_Families`
