# OECD - OECD_Property_Tax (Tax On Property)

- source: https://www.oecd.org/en/data/indicators/tax-on-property.html

- how to download data: Manual download from source based on filter - `Tax On Property`.

- type of place: Country.

- statvars: Economy

- years: 1965 to 2021

- place_resolution: Resolved manually.

### How to run:

`python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=statvar_imports/oecd/oecd_property_tax/pv_map/<filename>_pvmap.csv --places_resolved_csv=statvar_imports/oecd/oecd_property_tax/Places_Resolved.csv --config=statvar_imports/oecd/oecd_property_tax/metadata.csv --output_path=--output_path=<filepath/filename>`

#### Example
`python3 stat_var_processor.py --input_data=statvar_imports/oecd/oecd_property_tax/test_data/sample_input/oecd_property_tax.csv --pv_map=statvar_imports/oecd/oecd_property_tax/pv_map.csv --places_resolved_csv=statvar_imports/oecd/oecd_property_tax/Places_Resolved.csv --config=statvar_imports/oecd/oecd_property_tax/metadata.csv --output_path=statvar_imports/oecd/oecd_property_tax/test_data/sample_output/oecd_property_tax`
