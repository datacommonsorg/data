## Table of Contents

1. [About the Dataset](#about-the-dataset)
2. [Type of place](#about-the-import)
3. [Statvar](#statvar)
4. [Verticals: Demographics]
5. [years]
6. [how to run]

## About the Dataset
Auxílio Brasil is a Brazilian government program that provides financial aid to low-income families.

### How to download data 

### type of place: Municipality
    
### statvars:  Demographics

### years: 2021-2023

### how to run: 
# Step 1.
The Python script 'brazilSplit.py' helps you split large monthly files into smaller files for each municipality. change input_file path in script 'brazilSplit.py' before running the script

The script creates folders for the output files. These folders will have the same names as the corresponding input files. Then places all the generated output files within these newly created folders 

# step 2
place resolve by name:

For place resolving, run the bash script "./municipality_name_correction.sh" Make sure to update the file path within the script itself.
This example demonstrates how to modify a "<file_path>/<file_name.csv>".
	
```
sed -i 's/,CRUZEIRO DO SUL,/,AC CRUZEIRO DO SUL,/g;
s/,RIO BRANCO,/,AC RIO BRANCO,/g' <file_path>/split_data_AC.csv
```

# step 3
How to run: 
python3 stat_var_processor.py --input_data='data/statvar_imports/brazil_dados/Auxilio_Brasil_Pagamentos/test_data/sample_input/auxilio_brazil_pagamentos_data.csv' --pv_map="data/statvar_imports/brazil_dados/Auxilio_Brasil_Pagamentos/auxilio_brazil_pagamentos_pvmap.csv" --output_path='data/statvar_imports/brazil_dados/Auxilio_Brasil_Pagamentos/test_data/sample_output/Auxilio_brazil_pagamentos' --config="data/statvar_imports/brazil_dados/Auxilio_Brasil_Pagamentos/auxilio_brazil_pagamentos_metadata.csv"



The script generates CSV, TMCF, & MCF files.

### Licence
License: Creative Commons Attribution

https://dados.gov.br/dados/conjuntos-dados/auxilio-brasil---pagamentos

