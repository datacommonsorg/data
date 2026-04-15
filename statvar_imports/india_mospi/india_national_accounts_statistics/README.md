### India_NationalAccountsStatistics.

- Description: India economic statistics at country and state level.

- Source URL: https://esankhyiki.mospi.gov.in/macroindicators?product=nas

- Import Type: Manual Refresh

- Data Availability: 2012 to 2026

- Release Frequency: P1Y

### Preprocessing and Data Acquisition

To download the raw input files:

# From indicator select:
- Gross Value Added
- Gross Domestic Product
- Gross State Domestic Product from https://esankhyiki.mospi.gov.in/catalogue-main/catalogue?page=0&search=

# From Year select:
- Select all the years

# From Revision select:
- For Gross Domestic Product select Second Revised Estimates and First Advance Estimates.
- For Gross Value Added select Second Revised Estimates, First Advance Estimates, Provisional Estimates, Second Advance Estimates and Third Advance Estimate.


### Data Processing
 
After the files are downloaded, the data is processed using the stat_var_processor.py script. The script uses various command-line arguments to specify the input data, pvmap, configuration file, and output path for each category.

 * Sample command

```bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='{Downloaded input file path}' --pv_map='../../statvar_imports/india_mospi/india_national_accounts_statistics/{CorrespondingFile}_pvmap.csv' --config_file='../../statvar_imports/india_mospi/india_national_accounts_statistics/{CorrespondingFile}_metadata.csv' --output_path='../../statvar_imports/india_mospi/india_national_accounts_statistics/output/{CorrespondingFile}
```
 * Example
```bash
    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='{Downloaded input file path}' --pv_map='../../statvar_imports/india_mospi/india_national_accounts_statistics/GVA_SecondAdvanceEstimates_pvmap.csv' --config_file='../../statvar_imports/india_mospi/india_national_accounts_statistics/GVA_SecondAdvanceEstimates_metadata.csv' --output_path='../../statvar_imports/india_mospi/india_national_accounts_statistics/output/GVA_SecondAdvanceEstimates
```
