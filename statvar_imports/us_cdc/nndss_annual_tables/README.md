# CDCWonder NNDSS InfectiousAnnual Import

## About the Dataset
Notifiable Infectious Diseases Data: Annual tables from CDC WONDER which has the incident counts of different infectious diseases per year and are aggregated based on demographic factors. The statistics are reported by the 50 states, New York City, the District of Columbia, and the U.S. territories

### Download URL

Source URL {https://wonder.cdc.gov/nndss/nndss_annual_tables_menu.asp}.


To download the latest versions of ALL datasets available, run the following command. Files will be downloaded and extracted to a nndss_Annual_data folder.

### License

This dataset is available for public use, license is available at https://www.cdc.gov/other/agencymaterials.html


### Downloading and Processing Data


   To download the data follow the below steps

```
	1.  Select the radio button for the category.
   2.  Select all locations, all years, and all diseases.
   3.  Save your selections.
   4.  The corresponding table will become visible.
   5.  To download the data, click on "Export."
```

   To execute the data run the below command, keep chaning the config

```bash
   python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data='input_files/region_state/NNDSS_Annual_Summary_Data_2023.csv' --pv_map=regional_state_pvmap.csv --config_file=common_metadata.csv --output_path=output/nndss_regional_state --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf |& tee check.log
``` 

```bash
   python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data='input_files/{age,race etc}/NNDSS_Annual_Summary_Data_2023.csv' --pv_map=measles_pvmap.csv --config_file=common_metadata.csv --output_path=output/nndss_measles_{age,raceetc} --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf |& tee check.log
```
