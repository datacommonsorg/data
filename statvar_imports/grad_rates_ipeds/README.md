# IPEDS GraduationRates National Dataset
## Overview
This dataset contains national-level graduation rate statistics for students who started as full-time, first-time (FTFT) degree or certificate-seeking undergraduates.
Specifically, it provides graduation rates at three different time intervals: 100%, 150%, and 200% of the "normal time" to completion.
It captures these key metrics:
- 100% Graduation Rate: Students finishing within the standard program length
- 150% Graduation Rate: The standard reporting benchmark (e.g., 6 years for a Bachelor's)
- 200% Graduation Rate: The extended benchmark (e.g., 8 years for a Bachelor's)

type of place: Country.

## Data Source
**Source URL:**
https://nces.ed.gov/ipeds/search/

**Provenance Description:**
The data comes from U.S. Department of Education, National Center for Education Statistics (NCES). Specifically, the data is drawn from the Integrated Postsecondary Education Data System (IPEDS), which is a comprehensive system of interrelated surveys that gathers institutional-level data from colleges, universities, and technical/vocational schools across the United States.

## How To Download Input Data
To download the data, you'll need to use the provided source link. The source link leads to the IPEDS Data Explorer, which is a search tool provided by NCES. Here you need to filter the Graduation Rates as:
- Go to the source link which leads to data explorer
- Under the 'Surveys' dropdown, select 'Graduation Rates 200% (GR200)'
- By default, the data now will be visible for the latest year
- To fetch data for specific years, or all years, select the data year/years from the 'Data Year' dropdown
- Once the table opens, from the page header, select the 'Excel' option, which downloads the data in the .xlsx format
- The downloaded data is now avaialble for processing.

## Processing Instructions
To process the IPEDS Graduation Rate data and generate statistical variables, use the following command from the "data" directory:

**For Data Run**
```bash
python tools/statvar_importer/stat_var_processor.py \
    --input_data='statvar_imports/grad_rates_ipeds/test_data/graduation_rates_ipeds_2022_23.csv' \
    --pv_map='statvar_imports/grad_rates_ipeds/graduation_rates_ipeds_pvmap.csv' \
    --output_path='statvar_imports/grad_rates_ipeds/graduation_rates_ipeds_output' \
    --config_file='statvar_imports/grad_rates_ipeds/graduation_rates_ipeds_metadata.csv' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

This generates the following output files:
- output csv
- output_stat_vars_scehma.mcf
- output_stat_vars.mcf
- output.tmcf

**For Data Quality Checks and validation**
Validation of the data is done using the lint flag in the java tool present.

```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar lint graduation_rates_ipeds_output_stat_vars_schema.mcf graduation_rates_ipeds_output.csv graduation_rates_ipeds_output.tmcf graduation_rates_ipeds_output_stat_vars.mcf  
```

This generates the following output files:
- report.json
- summary_report.csv
- summary_report.html

The report files can be analysed to check for errors and warnings.
Further, Linting is performed on the generated output files using the DataCommons import tool.
