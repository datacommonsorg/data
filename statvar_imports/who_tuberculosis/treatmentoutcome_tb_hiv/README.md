# WHO Treatment Outcome for TB and HIV

- source: https://data.who.int/indicators/i/DCDC2EB/625E736

- description: Percentage of people with TB/HIV who started dug-susceptible tuberculosis treatment and whose treatment outcome was recorded as treatment success (cured or treatment completed), treatment failed, died, lost to follow-up, or not evaluated, within the reporting period.
    
- type of place: Country Data

- statvars: Health

- years: 2012 to 2023

- place_resolution: manually.

### Release Frequency: P1Y

### How to run:

- To download the input file

   `python3 tb_data_download_who.py`

- To process the input file

    `python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/Tuberculosis_outcome_TB_HIV.csv --pv_map=tuberculosis_outcome_pvmap.csv --config_file=metadata.csv --output_path=output/tuberculosis_output --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf `
    
#### Refresh type: Fully Autorefresh 

