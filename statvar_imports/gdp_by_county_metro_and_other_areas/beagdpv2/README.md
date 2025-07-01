# BEAGDPv2

The data set contains GDP by  county, Metro, and Other Areas

Download:
Data download URL : `https://apps.bea.gov/regional/zip/CAGDP9.zip`
Select the CAGDP9: Real GDP in chaied dollars by County & MSA


Processing: 
Earlier code : `https://source.corp.google.com/piper///depot/google3/datacommons/mcf/bea/v2/` ( 2001-2021 data)
Current execution : Using statvarProcessor ( 2001-2023 data).


Check for any additional NAICS to be mapped from source and update the `bea_pv_map.py`
Also any new place mappings has to be updated in the `bea_place_mapping.csv` with corresponding dcid
Used the statvar_remap to map the dcid generated in the format of existing dcid ( The existing statvar has measurement qualifier in the end of statvar whereas the script generates dcid has it in the beginning) 

###Execution steps :

To Download, run:

`python3 bea_download.py`

Note : The downloaded file will be saved as "input_files/CAGDP9__ALL_AREAS_2001_2023.csv"

###How to run:

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/input_files/CAGDP9__ALL_AREAS_*.csv -
-pv_map=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/<filename_of_pvmap> 
--places_resolved_csv=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_place_mapping.csv 
--config_file=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/<filename_of_metadata> 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/output_files/bea_gdp_output
```

If the Statistical Variable (SV) requires remapping, include the flag --statvar_dcid_remap_csv in above command.
`--statvar_dcid_remap_csv=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_statvar_remap.csv`

###Example

To Process the files, Run:

Execute the script inside the folder "/data/tools/statvar_importer/"

```
python3 stat_var_processor.py 
--input_data=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/input_files/CAGDP9__ALL_AREAS_*.csv 
--pv_map=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_pv_map.py 
--places_resolved_csv=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_place_mapping.csv 
--config_file=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_metadata.py 
--statvar_dcid_remap_csv=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/bea_statvar_remap.csv 
--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
--output_path=../../statvar_imports/gdp_by_county_metro_and_other_areas/beagdpv2/output_files/bea_gdp_output
```


