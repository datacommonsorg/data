# Tools used in importing data into Data Commons

## Place Name Resolver

Given a CSV with a column called "name" with place name values, this tool uses
the geocoding API to do a best-effort mapping of the names to DCIDs. It produces
an output CSV with two additional columns appended. A "dcid" column with the
corresponding DCID values and an informational "errors" column set when the DCID
value is empty.

Optionally, CSVs can include "Node" and "containedInPlace" columns. Where "Node"
defines the (unique) local-id for the row, and "containedInPlace" column
includes local-id references to contained-in places.

For sample input/output CSVs, see the `.csv` files in `place_name_resolver/testdata` directory.

### Usage

```
go run resolver.go --in_csv_path=testdata/input_basic.csv --out_csv_path=/tmp/output_basic.csv --maps_api_key=<YOUR_KEY_HERE>
```

### Testing

```
go test -v
```

