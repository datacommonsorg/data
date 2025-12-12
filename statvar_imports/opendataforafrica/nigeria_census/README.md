# NigeriaStatistics

- source:  "https://nigeria.opendataforafrica.org,"

- You can download the input files using the script located at:
  data/scripts/opendataafrica/download_folder/download.sh

- type of place: Country.

- statvars: Education, Health, Economy 

- years: 1960 to 2023.

- place_resolution:Places are resolved based on region ID.[data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv]

## Dataset Descriptions

The following datasets are included in this import:

| Dataset ID | Topic | Description |
| :--- | :--- | :--- |

| **gdcmcbg** | Economic Outlook | **Economic Outlook for Nigeria (2011-2019).** Covers general economic trends, specifically focusing on GDP and related economic indicators within the 2011 to 2019 timeframe. |

| **jgngifg** | Health Sector | **Health Workforce.** Statistics on the medical workforce, including a breakdown of practitioners (Medical, Dental, Veterinary) by nationality and Nursing/Midwifery professionals by specialization. |

| **NGNBSNCPIR2017** | Inflation | **CPI and Inflation Report.** Tracks the Consumer Price Index (CPI) and inflation rates to measure changes in the price level of consumer goods and services. |

| **ufceqi** | Historical GDP | **New GDP at Current Basic Prices.** A historical financial dataset tracking Nigeria's Gross Domestic Product (GDP) in Millions of Naira from 1960 to 2017. |

| **wdidshd** | Labor Force | **Nigeria Labour Force Survey.** Data on labor market participation, employment, and unemployment rates. Disaggregates the population by Age, Education, and Residence (Urban/Rural). |

| **uopetnd** | Education | **Graduate Output.** Statistics on the number of graduates across various disciplines, ranging from Engineering Technology and Built Environment to Business and Arts/Design. |

### How to run:

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/testdata/jgngifg_input.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/jgngifg_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/jgngifg_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/testdata/jgngifg_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/testdata/uopetnd_input.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/uopetnd_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/uopetnd_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/testdata/uopetnd_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/input_files/nigeria/ngnbsncpir2017.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_pvmap.csv' --places_resolved_csv='/data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/output/ngnbsncpir2017_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/input_files/nigeria/wdidshd.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/wdidshd_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/wdidshd_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/output/wdidshd_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/input_files/nigeria/gdcmcbg.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/gdcmcbg_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/gdcmcbg_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/output/gdcmcbg_output`

`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='/data/statvar_imports/opendataforafrica/nigeria_census/input_files/nigeria/ufceqi.csv' --pv_map='/data/statvar_imports/opendataforafrica/nigeria_census/ufceqi_pvmap.csv' --config='/data/statvar_imports/opendataforafrica/nigeria_census/ufceqi_metadata.csv' --output_path=/data/statvar_imports/opendataforafrica/nigeria_census/output/ufceqi_output`

-- Add inputfile.csv and pvmap and metadata accordingly and run like above.

## If place resolution is involved,use:
` --places_resolved_csv=data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv` along with the remaining command.


#### Processing
`python3 stat_var_processor.py --existing_statvar_mcf=stat_vars.mcf --input_data='data/statvar_imports/opendataforafrica/nigeria_census/testdata/ngnbsncpir2017_input.csv' --pv_map='data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_pvmap.csv' --places_resolved_csv='data/statvar_imports/opendataforafrica/nigeria_census/places_resolved_csv.csv' --config='data/statvar_imports/opendataforafrica/nigeria_census/ngnbsncpir2017_metadata.csv' --output_path=data/statvar_imports/opendataforafrica/nigeria_census/output/ngnbsncpir2017_output`


