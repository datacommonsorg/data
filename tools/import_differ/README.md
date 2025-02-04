# Import Differ

This utility generates a diff (point and series analysis) of two versions of the same dataset for import analysis.

**Usage**
```
python import_differ.py --current_data=<path> --previous_data=<path>
```

Parameter description:
- current\_data: Path to the current MCF data (single mcf file or wildcard on local/GCS supported).
- previous\_data: Path to the previous MCF data (single mcf file or wildcard on local/GCS supported).
- output\_location: Path to the output data folder. Default value: results.
- groupby\_columns: Columns to group data for diff analysis in the order var,place,time etc. Default value: “variableMeasured,observationAbout,observationDate,measureMethod,unit”.
- value\_columns: Columns with statvar value for diff analysis. Default value: "value,scalingFactor".

**Output**

Summary output generated is of the form below showing counts of differences for each variable.

| |variableMeasured|added|deleted|modified|same|total|
|---|---|---|---|---|---|---|
|0|dcid:var1|1|0|0|0|1|
|1|dcid:var2|0|2|1|1|4|
|2|dcid:var3|0|0|1|0|1|
|3|dcid:var4|0|2|0|0|2|

Detailed diff output is written to files for further analysis. Sample result files can be found under folder 'test/results'.
- point\_analysis\_summary.csv: diff summry for point analysis
- point\_analysis\_results.csv: detailed results for point analysis
- series\_analysis\_summary.csv: diff summry for series analysis
- series\_analysis\_results.csv: detailed results for series analysis
