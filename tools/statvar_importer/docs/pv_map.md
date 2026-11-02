# PV map guide

A property-value (PV) map tells the StatVar Processor how to turn source text
into Data Commons properties and values. This guide covers everything you need
for most imports. For filters, scaling, aggregation, defaults, and computed
values, see [Advanced processing](advanced_processing.md).

## Format

A PV map is a CSV file. Each row has a key followed by property and value pairs:

```csv
key,p1,v1,p2,v2,p3,v3
female,gender,Female
total population,value,{Number},populationType,Person,measuredProperty,count
```

- **Key**: text that appears in the source data, either a column header, a cell
  value, or a label row.
- **Property**: a Data Commons property, such as `gender`, or an observation
  property: `observationAbout`, `observationDate`, `value`, `unit`,
  `scalingFactor`, `measurementMethod`, or `observationPeriod`.
- **Value**: a Data Commons value, written without a prefix, such as `Female`.
  The processor adds the namespace.

Observation properties go into the output CSV. All other properties that start
with a lowercase letter become StatVar properties and are part of the StatVar
DCID.

## Common patterns

Most imports use these four patterns:

| Source                             | PV map row                                                                     | Effect                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| A value column header              | `total population,value,{Number},populationType,Person,measuredProperty,count` | Every number in the column is an observation of this StatVar. |
| A category value in a label column | `female,gender,Female`                                                         | Adds `gender: Female` to the values in the row.               |
| A place column                     | `iso3,observationAbout,country/{Data}`                                         | Uses the cell text to build the place DCID.                   |
| A date column                      | `year,observationDate,{Number}`                                                | Uses the cell as the observation date.                        |

### Mandatory properties

Every StatVar needs `populationType` and `measuredProperty`. Every SVObs needs
`observationAbout`, `observationDate`, and `value`. The processor drops output
without them. `statType` defaults to `measuredValue`.

## How keys match

The processor looks up keys in this order of scope:

1. **Column headers.** PVs from a header apply to every cell below it.
1. **Cells.** PVs from a label cell apply to the other values in the same row.
1. **Label rows.** A row with a label and no values, such as
   `Count of all Males`, applies its PVs to the rows below it.

Keys match with these rules:

- **Whole words only.** `man` doesn't match `woman`.
- **Longest key first.** When `total` and `total population` both match, the
  processor uses `total population`. Keys that match different parts of the text
  combine: `female` and `total population` both apply to
  `Total Population Female`.
- **Case.** A lowercase key matches whole-cell text in any case: `female`
  matches `Female` and `FEMALE`. A key that matches a phrase *inside* longer
  text is case-sensitive. For example, `pulmonary TB` matches
  `…diagnosed with pulmonary TB…`, but `pulmonary tb` doesn't. Copy the source
  casing for phrase keys.

NOTE: Every PV map row counts as a key, including comment rows. Keep comment
rows to a few words: long comments change how keys match and can stop keys from
matching at all.

## References and local variables

A value can refer to the cell being processed or to other properties:

| Reference      | Meaning                       | Example                           |
| -------------- | ----------------------------- | --------------------------------- |
| `{Number}`     | The numeric value of the cell | `value,{Number}`                  |
| `{Data}`       | The text of the cell          | `observationAbout,country/{Data}` |
| `{Key}`        | The PV map key that matched   | `name,"{Key}"`                    |
| `{<Property>}` | The value of another property | `name,"Imports of {ProductName}"` |

A property that starts with a capital letter, such as `ProductName`, is a local
variable. It isn't written to the output. Use it to build other values:

```csv
key,p1,v1
product,ProductName,{Data}
code,name,"""Total imports of {ProductName} (code: {Data})"""
```

A property whose reference can't be resolved is dropped from the output.

## Values

Write values without a namespace prefix. These forms have special meaning:

| Form                     | Meaning              | Example                              |
| ------------------------ | -------------------- | ------------------------------------ |
| `[<start> <end> <unit>]` | A range              | `25 to 29 years,age,[25 29 Years]`   |
| `[- <end> <unit>]`       | Up to a value        | `under 5 years,age,[- 5 Years]`      |
| `[<start> - <unit>]`     | A value and above    | `85 years and over,age,[85 - Years]` |
| An empty value           | Removes the property | `sex:total,gender,`                  |

## Several PVs from one cell

A single source cell can produce several properties, or several observations:

- **One key, several properties:** list them all on one row, for example
  `female 15-19,gender,Female,age,[15 19 Years]`.

- **Several keys in one cell:** keys that match different words of the cell text
  combine. `Total!!Female!!Under 5 years` gets `gender` from `female` and `age`
  from `under 5 years`. When the source joins words with a character other than
  a space, set it in the config, for example `word_delimiter,!!`.

- **Several values for one property:** quote a comma-separated list, and list
  the property in `multi_value_properties`. The processor writes one observation
  per value:

  ```csv
  key,p1,v1
  fips,observationAbout,"geoId/{Data},geoId/06"
  ```

  With `multi_value_properties,observationAbout`, each county value is also
  written for `geoId/06`. Add `#Aggregate,sum` to the value column to total
  them; see
  [roll-ups](advanced_processing.md#roll-ups-with-multi-value-properties).

## Keys for one column

The same text can mean different things in different columns, such as `Total` in
a `Sex` column and in an `Age` column. Prefix the key with the column header and
a colon to apply it only in that column:

```csv
key,p1,v1
sex:total,gender,
age:total,age,
```

Here `Total` in the `Sex` column removes `gender`, and `Total` in the `Age`
column removes `age`, so both produce the all-persons StatVar.

## Places

Put place mappings in their own PV map, `<source>_places_pvmap.csv`, so every
table from the same source can reuse it:

```csv
key,p1,v1
# codes
iso3,observationAbout,country/{Data}
# names
kings county ca,observationAbout,geoId/06031
# georgia: US state chosen, the source lists US states
georgia,observationAbout,geoId/13
#georgia,observationAbout,country/GEO
```

- **Codes:** map the code column with one pattern row.
- **Names:** add one lowercase row per place name.
- **Ambiguous names:** keep the best candidate as the active row. List the other
  candidates as commented rows, with a short note on the choice, so a reviewer
  can check it.

To resolve many names automatically, use the [place tools](../place/README.md).

## Dates

Map the date column directly:

```csv
key,p1,v1
year,observationDate,{Number}
date,observationDate,{Data}
```

The processor normalizes common formats, such as `Jan 2020` or `2020/01/15`, to
ISO 8601: `YYYY`, `YYYY-MM`, or `YYYY-MM-DD`. For quarters, fiscal years, or
other derived dates, see [Advanced processing](advanced_processing.md#dates).

## Drop rows and columns

- **Drop a whole row:** map a label in the row to `#ignore` with a reason:

  ```csv
  tot,#ignore,total is computed in Data Commons
  ```

  Every value in a row that contains the label is dropped. Write `#ignore` in
  lowercase; `#Ignore` has no effect.

- **Drop a column:** comment out the column's row with a leading `#` and add a
  short reason above it:

  ```csv
  # moe not imported
  #margin of error,value,{Number},statType,marginOfError
  ```

  A column without a `value` mapping produces no observations.

## Write PV maps that survive auto-refresh

Imports refresh when the source publishes new data. Follow these practices so
new releases process without edits:

1. **Lowercase keys for whole-cell text.** `total population` keeps matching if
   the source changes `Total Population` to `TOTAL POPULATION`. Keep the source
   casing for phrase keys (see [How keys match](#how-keys-match)).
1. **A reason for every `#ignore`.** Reviewers can then tell intentional drops
   from mistakes.
1. **Future keys up front.** If years or places are keys, add the upcoming years
   and the places likely to appear.
1. **Reusable files.** Keep places, and other mappings shared by several tables,
   in separate PV maps.
1. **Explicit filters and date ranges.** Don't hard-code a future-year cutoff.

## Use several PV maps

Pass a comma-separated list of PV maps:

```bash
--pv_map=<source>_places_pvmap.csv,<table>_pvmap.csv
```

To apply a PV map only to one column, prefix it with the column header and a
colon:

```bash
--pv_map=<table>_pvmap.csv,country:<source>_places_pvmap.csv
```

## Apply PVs to a whole file

A key that equals the input file name applies its PVs to every row of that file.
Use it for a value that varies by file but appears nowhere in the data:

```csv
key,p1,v1
population_2020.csv,observationDate,2020
```

WARNING: Don't use `#Regex` on a file-name key. It runs on every cell's value,
not on the file name, and corrupts the data.

For PVs that apply to all files, see `DEFAULT_PV` in
[Advanced processing](advanced_processing.md#defaults-overrides-and-roll-ups).

## Python dictionary format

A PV map can also be a Python dictionary file, as in
[`test_data/sample_pv_map.py`](../test_data/sample_pv_map.py). Use CSV for new
imports.
