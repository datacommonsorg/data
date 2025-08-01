# Waste Water Treatment - OECD Data

- source: https://stats.oecd.org/viewhtml.aspx?datasetcode=WATER_TREAT&lang=en

- how to download data: Manual download from source by clicking the button - `Export`.

- type of place: Country.

- statvars: Environment

- years: 1990 to 2021

- place_resolution: Country places are resolved based on name.

### How to run:

Prerequisite: The below command must be run from a folder that contains stat_var_processor.py script file.

 python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_data.csv'  --pv_map='/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_pvmap.csv'  --places_resolved_csv='/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_places_resolved.csv' --config='/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_metadata.csv'   --output_path="/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_output/WasteWaterTreatment"

