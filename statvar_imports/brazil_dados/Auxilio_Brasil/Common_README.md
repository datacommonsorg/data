###  Open Data MDS Auxilio Brasil

- import_name: "Auxilio_Brasil_Benefits_Program" and "Auxilio_Brasil_Extraordinary_Benefits_Program"

- source: https://www.gov.br/
          https://dados.gov.br/dados/busca?termo=auxilio%2520Brasil
          https://www.gov.br/pt-br/servicos/receber-o-auxilio-brasil-pab
          https://dados.gov.br/dados/conjuntos-dados/familias-por-faixa-de-renda-com-cadastro-atualizado-no-cadastro-unico

- how to download data: Manual download from source based on filter - `Auxilio Brasil Benefits Program and Auxilio Brasil Extraordinary Benefits Program`

- place_resolution: Municipality codes of Brazil. (In place mapping, the municipal codes 293020 & 530010 are not mapped and there is no wikidata id in source)

- statvars: Demographics, Household
  
- years: 2021 to 2023

- type of place: AA,AA2, City. 

### How to run:
`python3 stat_var_processor.py --existing_statvar_mcf='stat_vars.mcf' --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_dados/Auxilio_Brasil/pv_map.csv --places_resolved_csv=statvar_imports/brazil_dados/Auxilio_Brasil/Brazil_MunicipalityCodes_Places_Resolved.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>.csv

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/brazil_dados/Auxilio_Brasil/Auxilio_Brasil_Benefits_Program/test_data/sample_input/Auxilio_Brasil_Benefits_Program_test_data.csv --pv_map=statvar_imports/brazil_dados/Auxilio_Brasil/pv_map.csv --places_resolved_csv=statvar_imports/brazil_dados/Auxilio_Brasil/Brazil_MunicipalityCodes_Places_Resolved.csv --config=statvar_imports/brazil_dados/Auxilio_Brasil/Auxilio_Brasil_Benefits_Program/metadata.csv --output_path=statvar_imports/brazil_dados/Auxilio_Brasil/Auxilio_Brasil_Benefits_Program/test_data/sample_output/Auxilio_Brasil_Benefits_Program`
