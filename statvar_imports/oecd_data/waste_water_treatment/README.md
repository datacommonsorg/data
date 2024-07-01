# Waste Water Treatment - OECD Data

- source: https://stats.oecd.org/viewhtml.aspx?datasetcode=WATER_TREAT&lang=en

- how to download data: Manual download from source by clicking the button - `Export`.

- type of place: Country.

- statvars: Environment

- years: 1990 to 2021

- place_resolution: Country places are resolved based on name.

### How to run:

 python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/usr/local/google/home/kuru/DC_13_june/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_data.csv'  --pv_map='/usr/local/google/home/kuru/DC_13_june/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_pvmap.csv'  --places_resolved_csv='/usr/local/google/home/kuru/DC_13_june/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_places_resolved.csv' --config='/usr/local/google/home/kuru/DC_13_june/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_input/Wastewater_treatment_metadata.csv'   --output_path="/usr/local/google/home/kuru/DC_13_june/data/statvar_imports/oecd_data/waste_water_treatment/testdata/sample_output/WasteWaterTreatment"

