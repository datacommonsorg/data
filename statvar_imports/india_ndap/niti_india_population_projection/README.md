### NITIIndiaPopulationProjection Import

- Description: Population projection at India country and state level. Country level data is aggregated from state level through pvmap. The dataset are about total population project at state level and total urban population projection at state level whcih are extended to country level as well.

- Source URL: https://ndap.niti.gov.in/dataset/7208, https://ndap.niti.gov.in/dataset/7209

- Import Type: Automated / Semi-Automated (via GCS-staged NDAP API configuration)

- Data Availability: 2011 to 2026

- Release Frequency: P1Y

### Preprocessing and Data Acquisition

`download_script.py` downloads the raw datasets from the NDAP OpenAPI using a configuration file stored in GCS (`gs://unresolved_mcf/india_ndap/niti_india_population_projection/download_config.json`) so API credentials are not exposed in the repository.

#### GCS Configuration (`download_config.json`)

```json
{
  "state_population_url": "https://loadqa.ndapapi.com/v1/openapi?API_Key=<YOUR_API_KEY>&ind=I7208_4&dim=Country,StateName,StateCode,Year,D7208_3",
  "state_urban_population_url": "https://loadqa.ndapapi.com/v1/openapi?API_Key=<YOUR_API_KEY>&ind=I7209_4&dim=Country,StateName,StateCode,Year,D7209_3",
  "input_files": "input_files/"
}
```

To download the raw input files:

```bash
python3 download_script.py
```

### Data Processing

After the files are downloaded to `input_files/`, the data is processed using `stat_var_processor.py`:

 * India State Population

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --input_data=input_files/india_state_population_input.csv \
  --pv_map=india_state_population_pvmap.csv \
  --config_file=india_state_population_metadata.csv \
  --output_path=output/india_state_population \
  --output_counters=counters/india_state_population_counters.csv
```

 * India State Urban Population

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --input_data=input_files/india_state_urban_population_input.csv \
  --pv_map=india_state_urban_population_pvmap.csv \
  --config_file=india_state_urban_population_metadata.csv \
  --output_path=output/india_state_urban_population \
  --output_counters=counters/india_state_urban_population_counters.csv
```

