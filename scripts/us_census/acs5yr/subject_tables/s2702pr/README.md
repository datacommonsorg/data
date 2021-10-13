## S2702PR:Selected Characteristics of the Uninsured in the Puerto Rico
Data availability: 2013 - 2019
Data Source: [ACS 5Yr Estimates](https://data.census.gov/cedsci/table?q=S2702PR&g=0100000US.050000&tid=ACSST5Y2019.S2702PR&hidePreview=true)
Data Granularity: County, State and Country

### About the dataset
The dataset describes various characteristics of the population that are uninsured in the Puerto Rico. The dataset is based on estimates based on the US 2010 Census and may not accurately capture current, on-ground changes.

The dataset has 215 StatisticalVariable. In this import, we do not include
StatisticalVariable for Households with Income between $50,000 to $74,999. These
StatisticalVariables will be added when the dataset is refreshed for additional
geos.

### Generating the files for this import (requires modules in Github PRs. #488,
#513 and #515)

**Please run the following command, one directory level above.** 
```shell
 python3 process.py --option=all --table_prefix=S2702PR_state_county_places --has_percent=True --debug=False --spec_path=s2702pr/spec_s2702pr.json --input_path=s2702pr/s2702pr_state_county_places.zip --output_dir=s2702pr/
```
