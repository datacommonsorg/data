### NITIIndiaPopulationProjection Import

- Description: Population projection at India country and state level. Country level data is aggregated from state level through pvmap. The dataset are about total population project at state level and total urban population projection at state level whcih are extended to country level as well.

- Source URL: https://ndap.niti.gov.in/dataset/7208, https://ndap.niti.gov.in/dataset/7209

- Import Type: Manual Refresh

- Data Availability: 2011 to 2026

- Release Frequency: P1Y

### Preprocessing and Data Acquisition

To download the raw input files:

- Click on the provided source url. Login credentials are required to download the data. Create an account if not already created else login and download the data for both the dataset.


### Data Processing

After the files are downloaded, the data is processed using the stat_var_processor.py script. The script uses various command-line arguments to specify the input data, pvmap, configuration file, and output path for each category.

 * India State Population

```bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='{Path to downloaded input state population file}' --pv_map='../../statvar_imports/india_ndap/india_state_population_pvmap.csv' --config_file='../../statvar_imports/india_ndap/india_state_population_metadata.csv' --output_path='../../statvar_imports/india_ndap/output/india_state_population'

```

 * India State UrbanPopulation

```bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='{Path to downloaded input state urban population file}' --pv_map='../../statvar_imports/india_ndap/india_state_urban_population_pvmap.csv' --config_file='../../statvar_imports/india_ndap/india_state_urban_population_metadata.csv' --output_path='../../statvar_imports/india_ndap/output/india_state_urban_population'
```
