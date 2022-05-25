# Importing Census ACS5Year Subject Tables

This folder contains a general-purpose script for importing ACS subject tables. It is based off the import for the S2201 table, so might need some tweaks to support additional tables. Please feel free to update the script!

Note: the script currently only supports dcids with the `geoId/` prefix (states, counties, places, etc.).

The script expects the following flags:

* `output`: This is the path to the folder where the TMCF and CSV files will be generated.
* `download_id`: This is a param that is used to fetch the source data from `https://www.census.gov/acs/www/data/data-tables-and-tools/subject-tables/`. To find the `download_id`, select the desired Geos and Years for the table, then click the "Download" button. If you Inspect Network, there should be a request of the form `https://data.census.gov/api/access/table/download?status&download_id=[DOWNLOAD_ID]`.
* `features`: This is the path to a JSON which contains custom mappings used to generate the Statistical Variables for the table and other info for the TMCF. These must be manually curated for each table and are based on the descriptive column names in the source data. Each descriptive column name has various features which are separated by `!!`. (For example, the descriptive column name `Estimate!!Total!!Households` includes the features `Estimate`, `Total`, and `Households`.) The JSON include the following optional maps:
  * `base`: This maps a feature to a "base Statistical Variable" that typically includes the `measuredProperty` and `populationType` and does not include any property values. (For example, the feature `Median income (dollars)` is mapped to the base `Median_Income_Household`, and the Statistical Variable `Count_Household_WithFoodStampsInThePast12Months` has a base of `Count_Household`.) This map should also have a `_DEFAULT` key option, which will be used if no other base is found.
  * `properties`: This maps a feature to a property value. (For example, the feature `Households receiving food stamps` is mapped to the property value `WithFoodStampsInThePast12Months`.)
  * `implied_properties`: This maps a feature to a list of features that imply it. We only use the most specific feature to generate the Statistical Variable. (For example, the feature `Male householder, no spouse present`, which is mapped to the property value `SingleFatherFamilyHousehold`, is only measured for the feature `Other family`, which is mapped to the property value `OtherFamilyHousehold`. However, both values are in the range of the property `householdType`, so we only include the most specific one.)
  * `inferred_properties`: This maps a feature to a feature that is inferred by it, but not explictly listed in the descriptive column name. We add the inferred property value to the Statistical Variable. (For example, the feature `No workers in past 12 months`, which is mapped to the property value `NoWorkersInThePast12Months`, is only measured for the feature `Families`, which is mapped to the property value `FamilyHousehold`, even though `Families` is not part of the descriptive column name. However, these values are in the ranges of different properties, so we should include both.)
  * `units`: This maps a Stastical Variable to a unit, which will be added to the TMCF. (For example, the Statistical Variable `Median_Income_Household_WithFoodStampsInThePast12Months` is mapped to the unit `USDollar`.)
* `stat_vars`: This is the path to a file that contains a list of supported Statistical Variables. When generating new Statiscal Variables from descriptive column names, variables not in this list will be skipped.

See the `s2201` folder for an example of these files.

To run the script, from the parent directory (`subject_tables`), run:

```
python3 common/process.py --output=[OUTPUT] --download_id=[DOWNLOAD_ID] --features=[FEATURES] --stat_vars=[STAT_VARS]
```

This will generate the files `output.tmcf` and `output.csv` in the path specified by the `output` flag.


## Spec Validator

### Description

The validator tool tries to do basic sanity checks on the spec.

The script parses:
- The set of CSV files downloaded from census (Any one)
	- List of CSV file paths
	- List of ZIP file paths
	- JSON file containing list of all columns
- Config Spec JSON file

It tries to identify:
- Tokens appearing in spec but not in any of the CSV files
- Tokens appearing in CSV files but not in spec
- Columns that have no property assignment
- Columns that might possibly be in conflict with ignore and property assignment
- Missing Denominator Total Columns
- Denominator column appearing under multiple totals
- Possible missing EnumSpecialisations
- Multiple measurement assignment
- Multiple population assignment
- Extra inferredSpec

And creates:
- List and count of all column names
- List and count of all ignored column names
- List and count of all accepted column names

The script generates column and token data file and another file with outcome of results in the output directory

`all` key of dictionary refers to combination across all the files in the input

filename based outcomes can also be found in the output files

When calling functions from another script, following function arguments can be used:

- `filewise` option is generally used for debug purposes only

- `check_metadata` for zip file, `is_metadata`(also a commandline option) for CSV files can be made True if _metadata_ type files need to be processed

### Commandline options
- `spec_path` - path to JSON file containing the spec
- `column_list_path` - path of JSON file containing a list of all columns, present in https://github.com/rbhoot/acs_tables
- `zip_list` - Comma seperated list of paths of zip files fetched from census
- `csv_list` - Comma seperated list of paths of csv files fetched from census
- `tests` - Can take multiple values from:
	- all
	- extra_tokens
	- missing_tokens
	- column_no_pv
	- ignore_conflicts
	- enum_specialisations
	- denominators
	- extra_inferred
	- multiple_measurement
	- multiple_population
- `validator_output` - The output directory for the files generated by the validator. The files generated include:
	- `test_results.json` - Contains output of each test.
	- `columns.json` - Contains the list of columns by year and combined, also has seperate section for ignored columns.

### Commandline invocation examples

To run all tests against zip file:
```
python acs_spec_validator.py --zip_list=~/acs_tables/S0701/S0701_us.zip --spec_path=../spec_dir/S0701_spec.json --validator_output=~/acs_tables/S0701/validator
```
To run all tests against list of columns:
```
python acs_spec_validator.py --column_list_path=~/acs_tables/S0701/all_columns.json --spec_path=../spec_dir/S0701_spec.json --validator_output=~/acs_tables/S0701/validator
```

## Column map validator

### Description

The validator checks the column map generated from `process.py` or `generate_col_map.py`.

Following checks are performed on the column map:
- Presence of extra columns that should have been ignored
- Absence of columns that should not have been ignored
- Count of StatVars of type MarginOfError and not MarginOfError
- Presence of StatVar that has only margin of error
- Different StatVars having same DCID
- Same StatVar being generated multiple times in the same year
- DCID time series holes
- DCIDs unique to particular year
- DCIDs missing in particular year

### Commandline options

- `spec_path` - path to JSON file containing the spec
- `column_map` - path to JSON file containing the column map generated by processing script
- `yearwise_columns` - path of JSON file containing a list of all columns grouped by year, present in https://github.com/rbhoot/acs_tables
- `colmap_validation_output` - path of the directory to write output files 

### Commandline invocation examples
```
python column_map_validator.py --spec_path=../spec_dir/S0701_spec.json --column_map=~/acs_tables/S0701/column_map.json --yearwise_columns=~/acs_tables/S0701/yearwise_columns.json --colmap_validation_output=~/acs_tables/S0701/
```

Common utils has a set of functionalities that can be used for any basic US census file pre-processing.

### common_util.py
It offers following functionalities through similar named functions:
- Get Token List from a ZIP file
- Get list of columns from a csv reader object
- Get list of columns from a csv file path
- Get list of columns from a csv file path list
- Get list of columns from a zip file
- Get python dictionary object from Config Spec JSON path
- Check if column needs to be ignored
- Remove the columns that need to be ignored from a list of columns
- Get a list of ignored columns from a list of columns
- Get a list of tokens from a list of columns
- Find tokens missing in a spec
- Get request a URL and get JSON object from the response body


### Denominator Section Generation Process
Denominator section generation takes as input a config file of the format *denominator_config_sample.json*. 

The script works in 2 major steps:
- Creating a long config file from the config file and inputs linked to in config file. This step generates 2 new files that will be used for the next step:
  - `_long.json`
  - `_long_columns.json`
- Creating the denominators section using the long config file generated from previous step.

The long config file generated in the 1st step can be used to check and modify the denominator section generation process.

### Config File Options

- `spec_path` - The path to the JSON spec
- `us_data_zip` - The zip file containing **ONLY US level** data downloaded from census.
- `update_spec` - Boolean value. If set to `true` the spec pointed by `spec_path` will be modified and the denominator section will be added/overwritten in the file.
- `ignore_tokens` - List of tokens which will dicard the column if any of the token appears even as substring of token. This is useful if some values behave like percentage but are true values and need not be considered for denominator section. Minimum list: ['Mean', 'Median']

**NOTE: The substring listed in this(ignore_tokens) section will be matched against entire column name, not just entire tokens. This can lead to token substring match too.**
- `census_columns` - The list of top level columns in census tables. Refer to sample file for example. This is used for finding the index of the token representing the census column name within the column name. NOTE: Do not add same column names suffixed by MOE. e.g. *Total* and *Total MOE*.
- `used_columns` - Subset of `census_columns` that are being used in the import. Most of the cases will have the 2 sections same. NOTE: **Do not** add same column names suffixed by MOE. e.g. *Total* and *Total MOE*.
- `year_list` - List of years for which denominator computation will be required.

### Long Config File Options
- `column_tok_index` - This contains the index of the token representing the census column name for each year.
- `denominator_method` - The method to be used for generating denominator section. It can be either of the following:
  - `token_replace` - This method is used when entire census column is a percentage value and the total is present in some other census column. This relationship is represented by:
    - `token_map` - The census column name containing percentage values and the corresponding census column containing it's total.
  - `prefix` - This method is used when each census column contains mixed values, percentage and totals both. The usual representation method is such that the column name containing the total value is present as a prefix in the column name containing percentage. **NOTE: If this convention is not followed, the generated denominators section will be incomplete. Warnings will be raised about such columns and they need to handled manually.**
    - `reference_column` - This is the census column used as refernce and all the totals appearing for this column will be replicated for all census columns under `used_columns`.
    - `totals` - Yearwise list of column names containing total values and hence the list of prefix matching used. The same will be used for other census columns listed under `used_columns`. It is a good idea to check this list against actual table, and tally the number of entries against it.

**NOTE: `prefix` method might fail if census doesn't use a prefix in the column name and mentions just the entity.**
**NOTE: `prefix` method might generate wrong associations if the column sequence is not maintained in the source file.**
**NOTE: known caveat for `prefix` method: If multiple totlas are followed by percentages and 1st total is to be used, generator will wrongly associate the percentages to the last total.**
    
### Common Guidelines For Using Denominator Generator
- Sometimes using a subset of years would lead to change in `denominator_method`. This might be the case when table format changes across years.
- Changing long config manually is an option and might be useful in certain scenarios like:
  - Table having multiple census columns representing totals. In such a case the first one is always picked. Changing the `token_map` section would be necessary to map the columns correctly.
  - Some prefix might have been missed, and might need to be added manually.
- In case wrong `denominator_method` is generated, please file a bug, the code logic might need some change.

### Command Line Invocations
#### common_util.py
Use one of the following 3 flags to provide input csv files:
- `zip_path`
- `csv_path`
- `csv_list`

use `spec_path` flag to input the JSON spec

functionality flags:

- `get_tokens`: this flag produces the list of all unique tokens in the dataset

- `get_columns`: this flag produces all the unique columns in the dataset

- `get_ignored_columns`: this flag produces a list of all columns that were ignored according to the ignoreColumns section of the spec. NOTE: spec_path flag is necessary for this to work

- `ignore_columns`: this flag allows restricting the outputs to have values only from the columns that were not ignored.  NOTE: spec_path flag is necessary for this to work

additional flags for parsing configuration:
- `delimiter`: By default this is set tp '!!'
- `is_metadata`: this flag can be used to process only metadata files in case the data files are big

### helper_functions.py
- `denominator_config`: The config file created by user using the sample file.
- `denominator_long_config`: The long config file generated from the confing file at the end of the first step, usually the same as first `denominator_config` with `_long` suffix in filename.

## Command Line Examples
### common_util.py
To get list of all tokens:
```
python common_util.py --get_tokens --zip_path=../sample_data/s1810.zip
```

To get list of all tokens after ignored columns have been removed:
```
python common_util.py --get_tokens --ignore_columns --zip_path=../sample_data/s1810.zip --spec_path=../spec_dir/S1810_spec.json
```
Replace get_tokens with get_columns to get list of columns

To get the list of ignored columns:
```
python common_util.py --get_ignored_columns --zip_path=../sample_data/s1810.zip --spec_path=../spec_dir/S1810_spec.json
```

### helper_functions.py

This file can be used from command line to generate denominator section. The file also contains related functions which might be used elsewhere.

To excute the 1st step of the denominator section generation:
```
python helper_functions.py --denominator_config=~/acs_tables/S0701/denominator_config.json
```
The above command generates 2 files in the same directory as config file that would be used by the 2nd step:
- long config file with filename suffixed with `_long`
- a column grouping json file with siffix `_long_columns`

To execute the 2nd step of denominator generation:
```
python helper_functions.py --denominator_long_config=~/acs_tables/S0701/denominator_config_long.json
```
The above command would create a denominators.json in the same directory as config file. If the flag has been set in config, the spec will be updated with generate4d denominators section.

In case no modification is needed in long config file:
```
python helper_functions.py --denominator_config=~/acs_tables/S0701/denominator_config.json --denominator_long_config=~/acs_tables/S0701/denominator_config_long.json
```
The above command will execute both the steps and create denominators.json file in the directory with config file.

**WARNING:**
Save a copy of the generated spec if it is modified. Running the script again will overwrite the changes

Check the missing_report.json file for list of columns that need attention

The script creates a 'compiled spec' which contains everything from all the specs present in the spec_dir

It then proceeds to split 'compiled spec' in 2 parts:
- keeping the parts where token match occours
- storing the discarded parts in other similar spec for reference in case of similar token

## Command Line Invocations

To generate a guess spec:
```
python acs_spec_generator.py --guess_new_spec --zip_list=../sample_data/s1810.zip
```
NOTE: This command creates following important files to lookout for:
- generate_spec.json: This is the guessed spec for the input file
- missing_report.json: This file contains:
	- List of tokens present in the dataset but not in the spec
	- List of columns that were not assigned any propery and value
- union_spec.json: This is the union of all the 
- discarded_spec_parts.json: This contains parts of the union spec that were not used in the output spec

NOTE: acs_spec_generator.py caches properties and types under `data/scripts/us_census/acs5yr/subject_tables/common/datacommons_api_wrappers/prefetched_outputs`. As new properties and enums are constantly added into DC, this needs to be refreshed regularly. This can be done by deleting the prefetch folder. Once this is done, the script will automatically make calls to the DC REST API and refresh the files during the next guess spec run.

To generate a guess spec with expected properties or population types:
```
python acs_spec_generator.py --guess_new_spec --zip_list=../sample_data/s1810.zip --expected_populations=Person,Household --expected_properties=occupancyTenure
```
This will look for properties on DataCommons API and add placeholders for available enum values


To create a union of all specs:
```
python acs_spec_generator.py --create_union_spec
```
NOTE: The output is also stored in file 'union_spec.json'

If the specs are present in some other directory:
```
python acs_spec_generator.py --create_union_spec --spec_dir=<path to dir>
```

To get a list of properties available in the union of all specs:
```
python acs_spec_generator.py --get_combined_property_list
```
Other available flags from common_utils:
- is_metadata
- delimiter
