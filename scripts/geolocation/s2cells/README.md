`s2_mapper` tool maps any CSV that identifies the {lat, lng, date, value} into
S2 cells of a chosen levels and aggregates the values (per the chosen aggregate
function).

The input is a CSV and a dict of params:

```
{
  # Specifies S2 level
  "s2lvls": [10],
  # Specifies the aggregation function to use
  "aggrfunc": "sum" | "mean" | "max" | "min",
  # Specifies the column names for lat, lng, date, val
  "latcol": <col-name>,
  "lngcol": <col-name>,
  "datecol": <col-name>,
  "valcol": <col-name>,
  # Specifies the output date format. Input should be a valid ISO 8601 format.
  "datefmt": "YYYY-mm-dd" | "YYYY-mm" | "YYYY"  #  Optional
}
```

Run it as:

```
python3 s2_mapper.py --in_params=<json> --in_csv=<csv> --out_dir=scratch/
