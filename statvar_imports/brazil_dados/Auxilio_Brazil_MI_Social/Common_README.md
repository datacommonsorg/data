###  Auxilio Brazil Mi Social

- import_name: "Auxilio_Brazil_Benefits_Program" and "Auxilio_Brazil_Extraordinary_Benefits_Program"

- source: https://www.gov.br/
          https://dados.gov.br/dados/busca?termo=auxilio%2520Brasil
          https://www.gov.br/pt-br/servicos/receber-o-auxilio-brasil-pab
          https://dados.gov.br/dados/conjuntos-dados/familias-por-faixa-de-renda-com-cadastro-atualizado-no-cadastro-unico---mi-social

- how to download data: Manual download from source based on filter - `Auxilio Brazil Benefits Program and Auxilio Brazil Extraordinary Benefits Program`

- place_resolution: Municipality codes of Brazil. (In place mapping, the municipal codes 293020 & 530010 are not mapped and there is no wikidata id in source)

- statvars: Demographics, Household
  
- years: 2021 to 2023

- type of place: AA,AA2, City. 

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data=<input_file>.csv --pv_map=statvar_imports/brazil_dados/Auxilio_Brazil_MI_Social/pv_map.csv --places_resolved_csv=statvar_imports/brazil_dados/Auxilio_Brazil_MI_Social/Brazil_MunicipalityCodes_Places_Resolved.csv --config=<filepath/filename>.csv --output_path=<filepath/filename>

