# Stat Var MCF Utilities

Tools and uitlity functions for StatVars and MCF nodes.

## Stat Var Data Processor

A generic script to process csv data files into StatisticalVariables and
StatVarObservations. The script takes as input, data files such as csv or excel, a
config mapping of row/column headers and cell values into DataCommons schema
property-values (PVs) and generates a '.mcf' file with StatisticalVariables
capturing the attributes of the data as well as a '.csv' and '.tmcf' with
statvar observations mapping the data value for a place and time to a StatVar.

The script uses a config dictionary for other parameters controlling the
execution of the script. The configuration parameters can be provided as a
python dictionary of a JSON object as follows:
```
{
   '<parameter>': '<value>'
   ...

}
```
where the '<parameter>' is a one of the supported configuration paramaters.
Some of the parameters can also be specified as a command line flags.

For a full set of configuration parameters, please refer to the file:
`config.py`.

### Property-Value Map for DC Schema
The mapping from data source strings to Data Commons schema is provided as a
dictionary of data source strings to the property:value (PV) dictionary in the
format:
```
{
  <data string> : {
                     '<property>' : '<value>',
                     ...
                  },
   ...
}

for example:
  'Male': { 'age': 'dcs:Male' },
```

The `<value>` in the PV map above can also have a reference to other properties
similar to a python format string, with the the property name enclused in
paranthesis `{<parameter-name>}`.

There are also some default property:values created for each data cell in the
source:
  `Number` refers to a numeric (int or float) value,
  `Data` refers to the string value.

The PV map can be used to specify the property:values that apply to all the
cells in a column or in a row or to a specific cell. Any PVs mapped to the
column header apply to all cells in that column. Similarly, any PV applied to
cell also apply to all others cells in that row.

Any cell that generates the `value` property will result in a
StatVarObservation with all the PVs that apply to StAtVarObservation, such as,
`observationDate`, `observationAbout`, `variableMeasured`, `unit` and
`measurementMethod`. Any remaining PVs mapped to a cell that are not part of a
StatVarObservation are used to create the StatVar for that data.

For example consider the following csv data source table, th name 'census.csv':

| Index | Year | FIPS | Gender | Age   | Total    |
|-------|------|------|--------|-------|----------|
| 1     | 2022 | 06   | Male   | 25 -  | 13100000 |
| 2     | 2019 | 48   | Female | 16 64 |  9110000 |
| ...                                             |


The column headers can be mapped to DC schema property:values as follows:
```
{
  # File level PVs applicable to all data
  'census.csv': {
                   'populationType': 'dcs:Person',
                   'measuredProperty': 'dcs:count',
                },
  # StatVatObs mappings from column headers
  'Year' : { 'observationDate': '{Number}' }
  'FIPS' : { 'observationAbout': 'dcid:geoId/{Number}' }
  'Total': { 'value': '{Number}' }

  # StatVar Constraint Properties
  'Male' : { 'gender' : 'dcs:Male' },
  'Female' : { 'gender' : 'dcs:Female' },

  # StatVar constraing for age group
  'Age': {
           '#Regex': '(?P<StartAge>[0-9-]+) *(?P<EndAge>[0-9-]+)',
           'age': '[ {StartAge} {EndAge} Years]',
         },
}
```

The row with index 1 will be mapped to the following StatVar:
```
# StatVar obervation PVs
observationDate: 2022           <-- from column 'Year'
observationAbout: dcid:geoId/06 <-- from column 'FIPS'
value: 13100000                 <-- from column 'Total'

# StatVar PVs
populationType: dcs:Person      <-- from file name mapping 'census.csv'
measuredProperty: dcs:count     <-- from file name mapping 'census.csv'
gender: dcs:Male                <-- from column 'Gender'
age: [25 - years]               <-- from column 'Age'

# internal PVs not output as they begin with caps and are not valid DC properties
StartAge: 25                    <-- from Regex applied to 'Age'column value
EndAge: '-'
```

A StatVar will be generated for the statvar PVS above wih the dcid from
`stat_var_generator.py:generate_dcid`:
`Node: dcid:Count_Person_25OrMoreYears_Male`. This will be used as the
`variableMeasured` property in the statvar observation.

The script will emit the StatVars with valid observations into the MCF file. For
exmaple:
```
Node: dcid:Count_Person_25OrMoreYears_Male
typeOf: dcs:StatisticalVariable
populationType: dcs:Person
measuredProperty: dcs:count
gender: dcs:Male
age: [25 - years]
statType: dcs:measuredValue
```

The statvar observation will be added to a csv and tmcf file as follows:
`output.csv`
```
observationAbout,observationDate,value,variableMeasured
geoId/06,2022,13100000,dcid:Count_Person_25OrMoreYears_Male
```
`output.tmcf`
```
Node: E:output->E0
observationDate: C:output->observationDate
observationAbout: C:output->observationAbout
value: C:output->value
variableMeasured: C:output->variableMeasured
typeOf: dcs:StatVarObservation
```


#### Properties with special meanings
The following properties have a specific interpretations and are used for
processing only and are not emitetd into the StatVar of the StatVarObservation:
 - 'Number': Captures a numeric value in a cell, if any.
 - 'Data': Captures the value in a cell as a string.
 - '#Regex': A python regular expression with named parameters that become
       further PVs.
       For example the regex: `(?P<StartAge>[0-9-]+) *(?P<EndAge>[0-9-]+)`
       can be applied to parse age group from cell with the sytnax: 'NN MM'
       where NN is anumber or '-'

### Command
To process a file, run the script with the following command:
```
python3 stat_var_processor.py --config=<config-file> --pv_map=<map-file> \
   --input_data=<input-csv-file> --output_path=<output-prefix>
```

For example, to process the `test_data/sample_input.csv`, run the following
command:
```
# Process data in sample_input.csv into statvars sample_output.mcf
# and svobs sample_output.csv and sampe_output.tmcf:
python3 stat_var_processor.py --config=test_data/sample_config.py \
   --pv_map=sample_pv_map.py  \
   --input_data='test_data/sample_input*.csv' \
   --output_path=test_data/sample_output
```

For more examples, please see other pv maps in the folder: `test_data/`.

## MCF file utilities

The following scripts can be used as libraries or standalone command line
utilities to process MCF files with any Nodes.

### MCF File Utils
The script `mcf_file_utils.py` contains functions to read or write MCF nodes in
files.

 - `load_mcf_file()`: Load MCFs nodes from a file into a dictionary keyed by
   dcid
 - `write_mcf_nodes()`: Save a dictionary of MCF nodes into a file.

This script can also be used to merge noded form multiple MCF files into a
single one:
```
python3 mcf_file_util.py --input_mcf=<file1>[,<file2>...] --output_mcf=<file>
```

For example:
```
python3 mcf_file_util.py --input_mcf='test_data/*.mcf' --output_mcf=/tmp/merged.mcf

```

### MCF Diff

### MCF Filter

## Other Utility functions

### DC APi Wrapper

