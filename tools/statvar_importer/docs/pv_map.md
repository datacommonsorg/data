# PV map guide

A property-value (PV) map tells the StatVar Processor how to turn source text
into Data Commons properties and values. This guide covers everything you need
for most imports. For filters, scaling, aggregation, defaults, and computed
values, see [Advanced processing](advanced_processing.md).

## Format

A PV map is a schema config file, usually CSV (JSON and Python dictionary files
also work; see
[JSON and Python dictionary formats](#json-and-python-dictionary-formats)). Each
row has a key followed by pairs of a property and a value from the Data Commons
schema. Start the file with a `#key` header row so the header doesn't match text
such as `key` in the source:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3
female,gender,Female
total population,value,{Number},populationType,Person,measuredProperty,count
```

The parts of a row are:

- **Key**: text that appears in the source data, either a column header, a cell
  value, or a label row.
- **Property**: a Data Commons property, such as `gender`, or an observation
  property: `observationAbout`, `observationDate`, `value`, `unit`,
  `scalingFactor`, `measurementMethod`, or `observationPeriod`.
- **Value**: a Data Commons value, written without a prefix, such as `Female`.
  The processor adds the namespace.

Quote a key or value that contains a comma, for example `"age, total",age,`.
Without quotes, the CSV reader splits it into extra columns.

Observation properties go into the output CSV. All other properties that start
with a lowercase letter become StatVar properties and are part of the StatVar
DCID.

## Common patterns

Most imports use these four patterns:

| Source                             | PV map row                                                                     | Effect                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| A value column header              | `total population,value,{Number},populationType,Person,measuredProperty,count` | Every number in the column is an observation of this StatVar.                                                       |
| A category value in a label column | `female,gender,Female`                                                         | Adds `gender: Female` to the values in the row.                                                                     |
| A place column                     | `iso3,observationAbout,country/{Data}`                                         | Uses the cell text to build the place DCID.                                                                         |
| A date column                      | `year,observationDate,{Number}`                                                | Uses the cell as the observation date.                                                                              |
| A total in a category column       | `Sex:Total,gender,""`                                                          | Removes `gender`, so the value belongs to the all-persons StatVar; see [Keys for one column](#keys-for-one-column). |

### Mandatory properties

Every StatVar needs `populationType` and `measuredProperty`. `measuredProperty`
defaults to `count` and `statType` to `measuredValue`, so you usually set only
`populationType`. Every SVObs needs `observationAbout`, `observationDate`, and
`value`. The processor drops output without them.

The other schema properties that apply to a value define its StatVar. The
processor generates the StatVar and its DCID for each combination and writes
them to `_stat_vars.mcf`.

## How keys match

The processor looks up keys in this order of scope:

1. **Column headers.** PVs from a header apply to every cell below it.
1. **Cells.** PVs from a label cell apply to the other values in the same row.
1. **Label rows.** A row with a label and no values, such as
   `Count of all Males`, applies its PVs to the rows below it. This works when
   `header_rows` is left unset; otherwise mark the label with `#Header` (see
   [sectioned headers](advanced_processing.md#sectioned-headers)).

Keys match with these rules:

- **Whole words only.** `man` doesn't match `woman`.

- **Longest key first.** When `total` and `total population` both match, the
  processor uses `total population`. Keys that match different parts of the text
  combine: `female` and `total population` both apply to
  `Total Population Female`.

- **Case and order.** For each header or cell, the processor tries these lookups
  in order and uses the first that matches:

  1. The whole text, as written.
  1. The whole text with a column prefix, such as `Sex:Total` (see
     [Keys for one column](#keys-for-one-column)). This lookup is
     case-sensitive.
  1. The whole text in lowercase.
  1. Parts of the text, longest first, each as written and then in lowercase.

  A lowercase key therefore matches text in any case, but a key with capitals
  matches only that exact casing. Prefer lowercase keys when they don't clash
  with other text in the source, so the PV map keeps working if the source
  changes its capitalization.

  Exception: when the text is much longer than the keys, the processor instead
  searches for each key inside the text as written, which is case-sensitive.
  This happens when (words in the text − words in the longest key)² exceeds the
  number of keys, typically for sentence-length indicator names. `pulmonary TB`
  matches `…diagnosed with pulmonary TB…`, but `pulmonary tb` doesn't. Copy the
  source casing for those keys, or turn off `match_substring_word_boundary` (see
  below).

  To make these partial matches ignore case too, turn off
  `match_substring_word_boundary`, for example `match_substring_word_boundary,0`
  in a CSV config. With the setting off, keys also match inside words (for
  example `man` inside `woman`), so use specific keys.

NOTE: Every PV map row counts as a key, including comment rows. Write comments
in the first column only, and keep them to a few words without commas. A comma
starts a new column, which is read as a property or a value. A long first column
changes how keys match.

## References and local variables

A value can refer to the cell being processed or to other properties:

| Reference      | Meaning                       | Example                           |
| -------------- | ----------------------------- | --------------------------------- |
| `{Number}`     | The numeric value of the cell | `value,{Number}`                  |
| `{Data}`       | The text of the cell          | `observationAbout,country/{Data}` |
| `{Key}`        | The PV map key that matched   | `name,"{Key}"`                    |
| `{<Property>}` | The value of another property | `name,"Imports of {ProductName}"` |

A property that starts with a capital letter, such as `ProductName`, is a local
variable. It isn't written to the output. Use it to copy a cell's value into
other properties of the same row, or from a header or label row into the rows
below it:

```csv
#key,property-1,value-1
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
| `<n>Years`               | A single year of age | `20 years,age,20Years`               |
| An empty value           | Removes the property | `Sex:Total,gender,""`                |

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
#key,property-1,value-1,property-2,value-2
Sex:Total,gender,"",measurementMethod,CensusTotal
Age:Total,age,""
```

Here `Total` in the `Sex` column removes `gender`, and `Total` in the `Age`
column removes `age`, so both produce the all-persons StatVar.

Write column-scoped keys as follows:

- **Match the case.** The prefix and the text must match the header and the cell
  exactly, including case. `sex:total` doesn't match `Total` in a `Sex` column.
- **Write an empty value as `""`.** Don't rely on a trailing comma: with `""`,
  you can add more properties after it on the same row, such as
  `measurementMethod` above.
- **Prefix number keys.** A number key such as `2020` also matches any cell with
  that value, including observation values. A count of `2020` gets the key's
  PVs, and the observation is dropped. Prefix it with the column header and set
  the full value in the key, for example `Year:2020,observationDate,2020`. A key
  for the cell replaces the column header's mapping, such as
  `Year,observationDate,{Number}`, so include every property it sets.

Because a colon marks a column-scoped key, avoid colons in other keys. For a
header such as `Projected Population (UOM:Number)`, use part of it without the
colon, such as `projected population`.

## Keys for a cell position

When a cell's text has no key, the processor also tries keys for the cell's
position, in this order: `Cell:<row>:<column>`, `Column:<column>`, and
`Row:<row>`. Rows and columns count from 1, the same as in the `#input` column,
so the first header line is row 1:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3
Cell:1:4,value,{Number},populationType,Person,gender,Female
Column:5,#ignore,skip
Row:3,#ignore,skip
```

In this example:

- `Cell:1:4` maps the header cell in line 1, column 4, for example a header
  that's empty or that repeats in other columns.
- `Column:5,#ignore` skips the cells in column 5.
- `Row:3,#ignore` skips the cells in line 3.

WARNING: A position key replaces the column header's mapping for every cell it
matches, the same as a cell key. `Column:4,measurementMethod,Survey` drops the
values in column 4, because those cells lose `value,{Number}`. Use position keys
for header cells and for `#ignore`, not to add properties to value cells.

## Places

Put place mappings in their own PV map, `<source>_places_pvmap.csv`, so every
table from the same source can reuse it:

```csv
#key,property-1,value-1
# codes
iso3,observationAbout,country/{Data}
# names
kings county ca,observationAbout,geoId/06031
# georgia: US state chosen, the source lists US states
georgia,observationAbout,geoId/13
#georgia,observationAbout,country/GEO
```

The rows follow these rules:

- **Codes:** map the code column with one pattern row.
- **Names:** add one lowercase row per place name.
- **Ambiguous names:** keep the best candidate as the active row. List the other
  candidates as commented rows, with a short note on the choice, so a reviewer
  can check it.

To resolve many names automatically, use the [place tools](../place/README.md).

## Dates

Map the date column directly:

```csv
#key,property-1,value-1
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

- **Skip a column:** leave it out of the PV map, or comment out its row with a
  leading `#`. Commenting removes the mapping, which is also handy for keeping
  alternatives while you test:

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
#key,property-1,value-1
population_2020.csv,observationDate,2020
```

WARNING: Don't use `#Regex` on a file-name key. It runs on every cell's value,
not on the file name, and corrupts the data.

For PVs that apply to all files, see `DEFAULT_PV` in
[Advanced processing](advanced_processing.md#defaults-and-roll-ups).

## JSON and Python dictionary formats

A PV map can also be a JSON file or a Python dictionary file. Each key maps to a
dictionary of properties and values, the same as a CSV row:

```json
{
  "fips code": {"observationAbout": "geoId/{Number}"},
  "year": {"observationDate": "{Number}"},
  "total persons": {"value": "{Number}", "populationType": "Person"}
}
```

Use one of these formats when values contain commas or quotes that are awkward
to escape in CSV. A Python dictionary file can also have comments and trailing
commas; see [`test_data/sample_pv_map.py`](../test_data/sample_pv_map.py). The
processor reads any file that doesn't end in `.csv` as a Python dictionary or as
JSON.
