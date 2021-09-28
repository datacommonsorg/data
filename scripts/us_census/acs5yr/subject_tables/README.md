## Importing American Community Survey (ACS) Subject Tables

This directory has the files and code used for importing ACS Subject Tables into DataCommons.

Note: Before running the scripts here ensure the packages specified in `data/requirements.txt` is installed.

### Getting Started
Before, getting started with an import of an ACS Subject Table, it is important to ensure the following are available:
1. [**JSON Specification**](jsonSpec.md) describing the values that are applicable for a property based on a token (substring or part) of the column name.

The JSON Specification also defines the default defintions, and other properties for a statistical variable. The [jsonSpec.md](jsonSpec.md) has a detailed description of how to defined a new JSON specification.

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

2. To run an end-to-end workflow:
```shell
python3 process.py --option=all --table_prefix=test_s2702 --has_percent=True --debug=False --spec_path=common/testdata/spec_s2702.json --input_path=common/testdata/s2702_alabama.zip --output_dir=.
```

3. To run data processing step alone:
**NOTE:** Please ensure that the column map for the input is available
```shell
python3 process.py --option=process --table_prefix=test_s2702 --has_percent=True --debug=False --spec_path=common/testdata/spec_s2702.json --input_path=common/testdata/s2702_alabama.zip --output_dir=.
```

### Example Use cases:
- Using the code module as-is : [S2702 import]()
- Over-riding methods of the module to customize for specific tables [S1702
  import]()
