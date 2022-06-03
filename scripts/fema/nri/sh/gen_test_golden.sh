head source_data/NRIDataDictionary.csv -n 70 > test_data/test_data_dictionary.csv
head source_data/NRI_Table_Counties.csv -n 10 > test_data/test_data_county.csv
head source_data/NRI_Table_CensusTracts.csv -n 10 > test_data/test_data_tract.csv

python3 -c "import generate_schema_and_tmcf;generate_schema_and_tmcf.generate_schema_and_tmcf_from_file('test_data/test_data_dictionary.csv','test_data/expected_data_schema.mcf','test_data/expected_data_tmcf.mcf','test_data/test_csv_columns.json')"
python3 -c "import process_data;process_data.process_csv('test_data/test_data_county.csv','test_data/expected_data_county.csv','test_data/test_csv_columns.json')"
python3 -c "import process_data;process_data.process_csv('test_data/test_data_tract.csv','test_data/expected_data_tract.csv','test_data/test_csv_columns.json')"
