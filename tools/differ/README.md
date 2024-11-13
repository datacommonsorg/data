# Dataset Differ

This utility generates a diff (point and series analysis) of two versions of the same dataset for import analysis.

**Usage**
```
python differ.py --current_data=<path> --previous_data=<path>
```

Parameter description
current_data: Path to the current MCF data (single mcf file or folder/* supported).
previous_data: Path to the previous MCF data (single mcf file or folder/* supported).
output_location: Path to the output data folder.
groupby_columns: Columns to group data for diff analysis in the order var,place,time etc. Default value: “variableMeasured,observationAbout,observationDate”
value_columns: Columns with statvar value (unit etc.) for diff analysis. Default value:  "value,unit"

Summary output generated is of the form below showing counts of differences for each variable.

variableMeasured   added  deleted  modified  same  total
0   dcid:var1       1      0       0          0     1
1   dcid:var2       0      2       1          1     4
2   dcid:var3       0      0       1          0     1
3   dcid:var4       0      2       0          0     2

Detailed diff output is written to files for further analysis.
- point-analysis-summary.csv: diff summry for point analysis
- point-analysis-results.csv: detailed results for point analysis
- series-analysis-summary.csv: diff summry for series analysis
- series-analysis-results.csv: detailed results for series analysis