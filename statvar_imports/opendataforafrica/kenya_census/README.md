# Kenya Census

- source: https://kenya.opendataforafrica.org/

File descriptions:

*_pvmap.csv: StatVar processor schema mappings for a specific source table

*_metadata.csv: StatVar processor configs for a specific source table

*_places_resolved.csv: Mapping from place names in a source table to dcid for StatVar processor

*_indicator.csv: Useful for understanding the columns in the source file when creating PV mappings


- how to download data: 

You can download the input files using the script located at:
data/scripts/opendataafrica/download_folder/download.sh

Run the following command from that directory:

sh download.sh 'kenya' 'dlrrjxg,egdxgkd,emxkej,fwjfdnc,gxbucsd,ixdvqrf,rsfzlbg,srricmg,tdxdksf,vdbvyfd,welrttb,xszlbb' 

- Make sure to run this command from the data/scripts/opendataafrica/download_folder/ directory.

- The output path is optional. If not provided, it defaults to {PWD}/input_files (i.e., an input_files folder in the current working directory).

- If you need to specify a custom path, add it as the third argument to the command.


- type of place: Country and AdministrativeArea1.

- statvars: Demographics, Economy, Education

- years: 2002 to 2023

- place_resolution: Place resolution is performed by the StatVar processor using the places_resolved_csv flag.

### How to run:

`python3 stat_var_processor.py --input_data=/data/statvar_imports/opendataforafrica/kenya_census/test_data/dlrrjxg_input.csv --pv_map=/data/statvar_imports/opendataforafrica/kenya_census/dlrrjxg_pvmap.csv --config=/data/statvar_imports/opendataforafrica/kenya_census/dlrrjxg_metadata.csv --output_path=/data/statvar_imports/opendataforafrica/kenya_census/test_data/dlrrjxg`

## If place resolution is involved,use:
` --places_resolved_csv=data/statvar_imports/opendataforafrica/kenya_census/places_resolved_csv.csv` along with the remaining command.