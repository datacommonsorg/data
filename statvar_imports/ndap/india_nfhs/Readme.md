# National Family Health Survey - India

## About
The National Family Health Survey (NFHS) is a large-scale, multi-round survey conducted in a representative sample of households throughout India. National Family Health Survey (NFH) provides information on fertility, infant and child mortality, the practice of family planning, maternal and child health, reproductive health, nutrition, anaemia, utilization and quality of health and family planning services in a state as well as pan India level. The specific goal of the National Family Health Survey (NFHS) are a) to provide essential data on health and family welfare for policy and programme purposes, and b) to provide information on important emerging health and family welfare issues. Besides providing evidence for the effectiveness of ongoing programs, the National Family Health Survey (NFHS-5) data helps identify the need for new programmes with an area-specific focus and identifying groups that are most in need of essential services.

## NDAP Data Portal
There are 3 datasets available for National Family Health Survey:-
1) [National Family Health Survey - 4 & 5: State](https://ndap.niti.gov.in/dataset/6821)
2) [National Family Health Survey - 4 : District](https://ndap.niti.gov.in/dataset/7034)
3) [National Family Health Survey - 5 : District](https://ndap.niti.gov.in/dataset/6822)

## Dataset in this directory
This import directory has National Family Health Survey data for all Indian states and districts for year 2015-2016 and 2019-2020.

type of place: State and District level.

- statvars: Demographics, Health, Education, Housing

- place_resolution: Places resolved based on lgd Codes - https://docs.google.com/spreadsheets/d/1jxQscXvh_vUECyd3vrFyEOdeZNeJyQm4QEAB4WJmml8/edit?gid=1457132370#gid=1457132370 

## Running the import code
To generate CSV, MCF and TMCF for the state and district level data, run the following command:

python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/<data_filename.csv>'  --pv_map='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/7034_source_data-pvmap.csv' --config='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/<metadata_filename.csv>' --output_path='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/nfhs_7034_out'

for eg:
python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/<data_filename.csv>'  --pv_map='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/<pvmap_filename.csv>' --config='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_input/<metadata_filename.csv>' --output_path='/usr/local/google/home/vishnuns/NFHS_PR/data/statvar_imports/ndap/india_nfhs/test_data/sample_output/<filename>'

