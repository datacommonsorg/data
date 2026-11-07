# USGS Water Use

## Raw Data

The raw data (in TSV) can be downloaded from
[this link](https://waterdata.usgs.gov/usa/nwis/wu). The data starts from 1985,
released every 5 years. Each state has a separate table for all its counties.
There are in total 53 data files, for the 50 states, and D.C., Puerto Rico, US
Virgin Islands.

NOTE:

-   There are lots of missing cells in the file, they are represented by "-".
-   The comment lines start with "#", except the first two lines of each file.

## Run

To run the program:

```bash
go run main.go -input_dir=<input_dir> -output_dir=<output_dir>
```
