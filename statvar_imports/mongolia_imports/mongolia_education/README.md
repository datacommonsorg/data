## Mongolia_Education Import

This import contains statistical data related to Mongolia's education data at the country level.

-----

### ⚙️ How to Use

The workflow for this data import involves two main steps: downloading the necessary files and then processing them.

#### Step 1: Download the Data

- **Source:** [Mongolia education data](https://www.1212.mn/en/statcate)
- **Description:** The provided URL links to the official website of the National Statistical Office (NSO) of Mongolia. This specific page presents official statistics and data related to the country's population and households.

To get the necessary data files, you'll need to run download script `common_download_script.py`.

All downloaded files will be located into the `mongolia_education/input_files` folder.

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
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/students_of_universities_and_colleges_by_professional_field .csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/students_of_universities_and_colleges_by_professional_field _pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/students_of_universities_and_colleges_by_professional_field _output
--places_resolved_csv=statvar_imports/mongolia_imports/mongolia_education/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/students_in_teritary_educational_institutions_by_sex_and_educational_degree.csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/students_in_teritary_educational_institutions_by_sex_and_educational_degree_pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/students_in_teritary_educational_institutions_by_sex_and_educational_degree_output
--places_resolved_csv=statvar_imports/mongolia_imports/mongolia_education/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/number_of_students_in_universities_and_colleges_by_region.csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/number_of_students_in_universities_and_colleges_by_region_pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/number_of_students_in_universities_and_colleges_by_region_output
--places_resolved_csv=statvar_imports/mongolia_imports/mongolia_education/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/number_of_kindergartens_by_region.csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/number_of_kindergartens_by_region_pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/number_of_kindergartens_by_region_output
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/number_of_full_time_teachers_in_universities_and_colleges_by_sex.csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/number_of_full_time_teachers_in_universities_and_colleges_by_sex_pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/number_of_full_time_teachers_in_universities_and_colleges_by_sex_output 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

```bash
python3 stat_var_processor.py
--input_data=statvar_imports/mongolia_imports/mongolia_education/input_files/graduates_of_universities_and_colleges_by_professional_field.csv
--pv_map=statvar_imports/mongolia_imports/mongolia_education/graduates_of_universities_and_colleges_by_professional_field_pvmap.csv
--config_file=statvar_imports/mongolia_imports/mongolia_education/mongolia_metadata.csv
--output_path=statvar_imports/mongolia_imports/mongolia_education/output_files/graduates_of_universities_and_colleges_by_professional_field_output
--places_resolved_csv=statvar_imports/mongolia_imports/mongolia_education/mongolia_place_resolver.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
