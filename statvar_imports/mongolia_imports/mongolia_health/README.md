## Mongolia_Demographics Import

This import contains Statistical data related to births and deaths in Mongolia.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [Mongolia population and household data](https://www.1212.mn/en/statcate)
- **Description:** The provided URL links to the official website of the National Statistical Office (NSO) of Mongolia. This specific page presents official statistics and data related to births and deaths in Mongolia.

To get the necessary data files, you'll need to run download script `common_download_script.py`.

All downloaded files will be located into the `mongolia_health/input_files` folder.

This import will be fully refreshed in an automated manner.

-----

#### Step 2: Process the Files

After downloading the files, you can process them to generate the final output. There are two ways to do this:

**Option A: Use the `run.sh` script**

The `run.sh` script automates the processing of all the downloaded files.

**Run the following command:**

```bash
sh run.sh
```

**Option B: Manually Execute the Processing Script**

You can also run the `stat_var_processor.py` script individually for each file. This script is located in the `data/tools/statvar_importer/` directory.

Here are the specific commands for each file:

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/deaths_by_month_and_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/deaths_by_month_and_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/deaths_by_month_and_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_place_resolver.csv 
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/infant_mortality_per_1000_live_births_by_month_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/infant_mortality_per_1000_live_births_by_month_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/infant_mortality_per_1000_live_births_by_month_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_place_resolver.csv 
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/live_births_by_month_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/live_births_by_month_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/live_births_by_month_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_place_resolver.csv 
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/number_of_abortions_by_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/number_of_abortions_by_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/number_of_abortions_by_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_place_resolver.csv 
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/number_of_hospital_beds_by_type.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/number_of_hospital_beds_by_type_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/number_of_hospital_beds_by_type_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
```

```bash
python3 stat_var_processor.py
--input_data=../../statvar_imports/mongolia_imports/mongolia_health/input_files/number_of_mothers_delivered_child_by_month_region.csv
--pv_map=../../statvar_imports/mongolia_imports/mongolia_health/number_of_mothers_delivered_child_by_month_region_pvmap.csv
--config_file=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_metadata.csv
--output_path=../../statvar_imports/mongolia_imports/mongolia_health/output_files/number_of_mothers_delivered_child_by_month_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
--places_resolved_csv=../../statvar_imports/mongolia_imports/mongolia_health/mongolia_place_resolver.csv
```

