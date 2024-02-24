## Importing American Community Survey (ACS) Subject Tables

This directory has the files and code used for importing ACS Subject Tables into DataCommons.

Note: Before running the scripts here ensure the packages specified in `data/requirements_all.txt` is installed.

### Getting Started
Before, getting started with an import of an ACS Subject Table, it is important to ensure the following are available:
1. [**JSON Specification**](jsonSpec.md) describing the values that are applicable for a property based on a token (substring or part) of the column name.

The JSON Specification also defines the default defintions, and other properties for a statistical variable. The [jsonSpec.md](jsonSpec.md) has a detailed description of how to define a new JSON specification.

2. Running the script:
```shell
  python3 process.py <args>
```

We have a unified script that can be used to generate either the column map
or process data or doing both the steps. The mode at which the script is run is
set by command-line args. The following are the command line flags supported:
```
Generic proces module to generate the csv/tmcf and csv
flags:

process.py:
  --[no]debug: [for processing]set the flag to add additional columns to debug
    (default: 'false')
  --[no]has_percent: [for processing]Specify the datasets has percentage values that needs to be convered to counts
    (default: 'false')
  --input_path: Path to input directory with (current support only for zip files)
  --option: Specify how to run the process, colmap -- generates column map, process -- runs processing, all -- runs colmap first and then proessing
    (default: 'all')
  --output_dir: Path to the output directory
    (default: './')
  --spec_path: Path to the JSON spec [mandatory]
    (default: './common/testdata/spec.json')
  --table_prefix: [for processing]Subject Table ID as a prefix for output files, eg: S2702
    (default: 'S2702')
```
**NOTE: We support only zip files through this script, we will be adding support
to use csv file (standalone) or a directory of data files in the upcoming
commits.**

#### Example snippets:
1. To run the column map generation alone:
```shell
python3 process.py --option=colmap --spec_path=common/testdata/spec_s2702.json --input_path=common/testdata/s2702_alabama.zip --output_dir=.
```
After the script runs, you will find a file named `column_map.json` in the
specified output directory path. In the case of the above command, you would see
the file in `./column_map.json`. [Click here](https://00f74ba44b3b48571f4dfe2bc5089ebcc85138f7fc-apidata.googleusercontent.com/download/storage/v1/b/unresolved_mcf/o/us_census%2Facs5yr_subject_tables%2Fs2702%2Ftest_s2702%2Fcolumn_map.json?jk=AFshE3W8bI4n9bgvFIYtp2qhUVmLJzJ2GTd41za3zmiK05y3jUzhnmwyhgjhESCZgSIpVdZbSpVrpA1CMmsBWyayRRxuoO5KalN75QLQIoHlWKyKbYs3pffNod4SDdvDuw_ZKXFUGDRuelXzgiGP2sV6neg-DI1rdEO409tWdck9hJrJYYuPN4r_146r9CVBPWzOAxoB_-LWn6N_huSr6K8rPI0nLmtZMRBTOyMsOhW2BpiFPxAMjMor3uNIJfn8dGSnsnlCzhAqE0SkMABlic82lJuaktz83dobYMvrmTABinNmy15paEPJAyzMhE3vsQyG9fipeCnfdpmsXKzvI_Du_nqcb2e2oPdWrvN5x9st1QJxMcMdX4hW2nceRh0py6ZRQnVoCM6SkGz-Utbcbcpge9zrCreJVK9Mwm91U7zzGkJYaeXu1IwN_yU-ebJNhY1Vli98xlU_Wn5UczRSQWyh54LZJFAThxvqABNxTiBy3te0zQAAxYVSdf8qw4T617qclzUf_g6CouSUlZLwgUtijuy-P9wIxRa-n_0sE5yWQkjWFzGXAiGNo9e_bMWBAyczEX-7L6bag0bEoway8Dln3d-EHDWNt7b5pFgDt35qJqtwfAvXpd-dR1pStJqFPd-ms2Gy4oYRmMgMfJO8kdo_gpP-eChd-uV9LRoPctJaOBK5NH-_YtTCE1QExYZLIO9aE9TC3fp8IAhMkvV06grUUNppPDEzdLoRs_fwRnSYH2vSsuQKilCwTTHYMz1e21mfQ1FuRagYtmZynrqb93dUgoSpYoS5EdSYhqeDm4-24Hs0scLqiMEMxUSgwtfvLzkMdO8etXAW-U67dd_bXfGuo-A2YkFTsmsd5ao94RB1OzZDMOqGJFUqOeX9Uv8pr8p1QV5VL4WCHgLnxebDiWyVjN_6WTG0xwWz9TxNioqw_KH1aAcfVH1WYB-MmOAwGfG1gw3yDfW25tC6grZwRAfSZFPLk1c-7Nb_fi6ALRAXrp9ovZFajJ3elVMph2FVQDIqi7Fc2SZYW2Ceu_1AOWXdtXaIpMQsATLmPQr4Aw&isca=1) to view a sample
`column_map.json` file which was generated for the Subject Table [S2702](https://data.census.gov/cedsci/table?q=S2702&tid=ACSST1Y2019.S2702)


2. To run an end-to-end workflow:
```shell
python3 process.py --option=all --table_prefix=test_s2702 --has_percent=True --debug=False --spec_path=common/testdata/spec_s2702.json --input_path=common/testdata/s2702_alabama.zip --output_dir=.
```
This command does two steps: (1) generation of `column_map.json` file to the
specified output directory and (2) generation of the processed csv with
StatVarObservations and the corresponding template MCF file in the output
directory.

If the example command is run, you will find the following files in the current
directory, since the output path is `./`:
```shell
column_map.json   # for each-year, the file maps a column to a generated
stat_var node
test_s2702_cleaned.csv # csv file with StatVarObservations i.e. quantity
measured for a stat_var at a particular place and date. It also has additional
columns like units, and scalingFactor if they are specified in the JSON spec.
test_s2702_output.mcf # file in mcf format with all the StatVars generated in
the column map
test_s2702_output.tmcf # template mcf file used in combination with the csv file
for data import
test_s2702_summary.json # summary stats of data processing year-wise
```

If `debug=True` is used as the option, the following additional files will be written to the output directory
```shell
column_to_dcid.csv #maps the stat var dcid associated to each column of the data file
column_to_statvar_map.json #a json file with column mapped to the complete stat-var node
```
And `test_s2702_cleaned.csv` will have an additional column that will contain the name of column in the dataset for which each StatVarObservation was recorded


3. To run data processing step alone:
**NOTE:** Please ensure that the column map for the input is available
```shell
python3 process.py --option=process --table_prefix=test_s2702 --has_percent=True --debug=False --spec_path=common/testdata/spec_s2702.json --input_path=common/testdata/s2702_alabama.zip --output_dir=.
```
This command is similar to the previous command but it expects that the
`column_map.json` is file already present in the output directory. This function
will have the following output.
```shell
column_map.json (this was generated a-priroi using the colmap option)
test_s2702_cleaned.csv # csv file with StatVarObservations i.e. quantity
measured for a stat_var at a particular place and date. It also has additional
columns like units, and scalingFactor if they are specified in the JSON spec.
test_s2702_output.mcf # file in mcf format with all the StatVars generated in
the column map
test_s2702_output.tmcf # template mcf file used in combination with the csv file
for data import
test_s2702_summary.json # summary stats of data processing year-wise
```

### Example Use cases:
- Using the code module as-is : [S2702 import](s2702/)
- Over-riding methods of the module to customize for specific tables [S1702
  import](s1702/)

## Resolving Census Place GeoID strings to DataCommons dcids
There are different census summary levels at which subject table data are available. We use the [resolve_geo_id.py](common/resolve_geo_id.py) module to resolve the place dcids from the US census GeoID strings using the FIPS code.

The summary levels that are now supported by the module include:
|Summary level code|Summary level name|
|--------------------|---------------------|
|010|US Country-level|
|040|State-level|
|050|County-level|
|060|State-County-County Subdivision|
|140|Census tract|
|150|Block group|
|160|City/ Places|
|500|Congressional district [111th]|
|860|ZCTA|
|950,960,970|School districts|

The summary levels that are not mentioned in this table are currently not supported. In case, you come across more summary-levels to be added, please file an issue.
