## S0902:Selected Characteristics of the Uninsured in the United States
Data availability: 2011 - 2019
Data Source: [ACS 5Yr Estimates](https://data.census.gov/cedsci/table?q=S0902&g=0100000US.050000&tid=ACSST5Y2019.S0902&hidePreview=true)
Data Granularity: County, State and Country

### About the dataset
The import adds the selected characteristics of the 15 to 19 year old population of the United States. The dataset describes the population’s school enrollment status, marital status, household types where they live and finally about their idleness (whether they are in the labor force or enrolled in school or neither).

**Note:** The data is sparse, in the sense not all counties have data points, we see only 600 of the total 3,200 counties in the US. It is also important to note that among the 600 counties as well, there are counties which have missing points where data is missing for some years causing data holes.

The dataset is based on estimates based on the US 2010 Census and may not accurately capture current, on-ground changes.

The dataset has 108 StatisticalVariable.

### Generating the files for this import (requires modules in Github PRs. #488,
#513 and #515)

**Please run the following command, one directory level above.** 
```shell
 python3 process.py --option=all --table_prefix=S0902_state_county_places --has_percent=True --debug=False --spec_path=s0902/spec_s0902.json --input_path=s0902/s0902_state_county_places.zip --output_dir=s0902/
```
