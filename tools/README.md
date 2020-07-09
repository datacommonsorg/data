# Tools for use in importing data into Data Commons

[TOC]

## Place Name Resolver

Given a CSV with a column called "name" with place names, this tool uses
geocoding to do a best-effort mapping of the names to DCIDs. It produces an
output CSV with two additional columns appended. A "dcid" colummn with the DCID
value and an "errors" column with more information set when the DCID value is
empty.

Optionally, CSVs may include "Node" and "containedInPlace" columns. Where "Node"
defines the local name for the row, and "containedInPlace" columns include local
name references to contained-in places.

For an example, see `sample_resolution_input.csv` and
`sample_resolution_output.csv`.

To run this program:

```
go run place_name_resolver.go --in_csv_path=sample_resolution_input.csv --out_csv_path=sample_resolution_output.csv --maps_api_key=<YOUR_KEY_HERE>
```

