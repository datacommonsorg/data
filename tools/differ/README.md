# Dataset Differ

This utility generates a diff (point and series analysis) of two data files of the same dataset for import analysis.

**Usage**
```
python differ.py --currentData=<filepath> --previousData=<filepath>
```

Parameter description
currentDataFile: Location of the current MCF data file
previousDataFile: Location of the previous MCF data file
groupbyColumns: Columns to group data for diff analysis in the order var,place,time etc. Default value: “variableMeasured,observationAbout,observationDate”
valueColumns: Columns with statvar value (unit etc.) for diff analysis. Default value:  "value,unit"

Output generated is of the form below showing counts of differences for each variable.
Detailed diff output is written to a file for further analysis.

variableMeasured   added  deleted  modified  same  total
0   dcid:var1       1      0       0          0     1
1   dcid:var2       0      2       1          1     4
2   dcid:var3       0      0       1          0     1
3   dcid:var4       0      2       0          0     2
