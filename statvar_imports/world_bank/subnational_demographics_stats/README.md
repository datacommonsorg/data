# Subnational_Demographics_Stats

Sub-national Demographic data - Worldbank Population for Country and States.
The data presented on this page originates from The World Bank Group. It is made available through their DataBank platform, which provides access to a wide range of global data.

- source:  `https://databank.worldbank.org/source/subnational-population`

- how to download data:
    Run the download script, `download_data.py`. It automatically creates the `input_files` folder and downloads, extracts, and preprocesses `input_files/wb_subnational_input.csv`.

### How to run:

#### Download the data:

To download and preprocess the source data, run from `statvar_imports/world_bank/subnational_demographics_stats/`:
```bash
python3 download_data.py
```

Notes:
- Files are downloaded inside the `input_files` folder (`input_files/P_Data_Extract_From_Subnational_Population.zip`).
- After extracting and preprocessing the data, the final input file is `input_files/wb_subnational_input.csv`.

#### Process the data:

Execute from `statvar_imports/world_bank/subnational_demographics_stats/`:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/wb_subnational_input.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --pv_map=wb_subnational_pvmap.csv \
  --config_file=wb_subnational_metadata.csv \
  --places_resolved_csv=wb_subnational_place_resolution.csv \
  --output_path=output_files/wb_subnational_output \
  --output_counters=counters/wb_subnational_counters.csv \
  --log_level=-2 \
  --log_every_n=1000
```

#### Run tests:

```bash
python3 download_data_test.py
```
