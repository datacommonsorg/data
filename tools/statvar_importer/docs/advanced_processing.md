# Advanced processing

These PV map keywords and settings handle data that the
[basic guide](../README.md) doesn't cover. Each section shows when to use the
feature, a tested example, and its pitfalls.

Keywords start with `#` and are case-sensitive: write them exactly as shown.

## Filter values

Use `#Filter` to drop observations that fail a condition. The condition is a
Python expression of the form `<name>=<expression>`. When it evaluates to
`False`, the observation is dropped:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3,property-4,value-4
population,value,{Number},populationType,Person,measuredProperty,count,#Filter,"Allow=float(value) >= 0"
```

Keep these points in mind:

- Property values are strings, so cast them: `float(value)` or `int(value)`.

- The counter `filter-dropped-svobs-pvs` counts dropped observations.

- Keep filters explicit and testable. Don't hard-code a year cutoff, such as
  `int(observationDate) <= 2024`; it silently drops new data after a refresh.
  Compute it from the current date instead, for example to keep only the last
  two years:

  ```csv
  population,value,{Number},populationType,Person,#Filter,"Allow=int(observationDate[:4]) >= datetime.now().year - 2"
  ```

## Scale values

Use `#Multiply` when the source reports values in units of N, such as "in
thousands". The processor stores the actual value:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3,property-4,value-4
population (thousands),value,{Number},populationType,Person,measuredProperty,count,#Multiply,1000
```

A source value of `1.5` becomes `1500`. Imports most often key this on the unit
word in a header: `thousand` (`#Multiply,1000`), `lakh` (`#Multiply,100000`), or
`crore` (`#Multiply,10000000`).

For percentages, keep the source number and add `scalingFactor,100` together
with a denominator, as in the example in
[Derived denominators](#derived-denominators). Don't combine `#Multiply` and
`scalingFactor` for the same value.

## Skip whole rows

`#ignore` drops the observations in a row. To skip a row before any processing,
for example rows marked as provisional, use `#IgnoreRow,True`:

```csv
#key,property-1,value-1
provisional,#IgnoreRow,True
```

The counter `input-rows-ignored` counts skipped rows. To skip rows by line
number, set `ignore_rows` in the config, for example `ignore_rows,"[1,5]"`.

## Compute values

Use `#Eval` to compute a property with a Python expression of the form
`<property>=<expression>`. The expression can use these values:

- Cell values: `Data` (text) and `Number`.
- Any other property or local variable in the same row, such as `Year`.
- These functions: `format_date`, `str_to_camel_case`, `dateutil_parser_parse`,
  `datetime`, `datetime_strptime`, `relativedelta`, `re` (for example `re.sub`),
  and `re_sub`.
- Python built-ins such as `int`, `float`, and `str`, and string methods on text
  values, such as `zfill`, `split`, `replace`, and `lower`.

**Clean up text.** String methods and `re.sub` handle codes and labels that need
small fixes:

```csv
#key,property-1,value-1
fips,#Eval,"observationAbout='geoId/' + Data.zfill(5)"
year,#Eval,"observationDate=re.sub(r'[^0-9]', '', Data)"
```

`6001` becomes `geoId/06001`, and `Y2020` becomes `2020`. Similarly,
`Data.split('-')[0].replace('FY ', '')` turns `FY 2020-21` into `2020`.

**Generate schema values from the source.** When a column holds category names,
such as products, `str_to_camel_case` turns each name into an enum value. You
don't need one PV map row per name:

```csv
#key,property-1,value-1,property-2,value-2
product,#Eval,"ProductEnum=str_to_camel_case(Data)",productType,{ProductEnum}
```

`Crude oil` and `Natural Gas (LNG)` become `productType: CrudeOil` and
`productType: NaturalGasLNG`, in the StatVars `Amount_EnergyImport_CrudeOil` and
`Amount_EnergyImport_NaturalGasLNG`. Values that aren't in the Data Commons
schema yet go to `_stat_vars_schema.mcf` as provisional enum values. Review that
file, because each new spelling in the source creates a new value.

Pad a code with zeros. `Number` and `Data` are both stored as text, so pad
`Data` with a string format:

```csv
#key,property-1,value-1
fips,#Eval,"observationAbout=f'geoId/{Data:0>2}'"
```

`6` becomes `geoId/06`. To compute with a number, cast it first, for example
`int(Number) * 2`.

Use `#Regex` to extract parts of a cell into local variables with named groups.
For example, to turn `Age: 10 - 20` into an age range:

```csv
#key,property-1,value-1,property-2,value-2
age group,#Regex,(?P<StartAge>[0-9]+) *- *(?P<EndAge>[0-9]+),age,[{StartAge} {EndAge} Years]
```

`Age: 10 - 20` and `Age: 21-30` become `age: [10 20 Years]` and
`age: [21 30 Years]` (StatVars `..._10To20Years` and `..._21To30Years`). The
pattern can match anywhere in the cell.

Use `#Format` for simple string templates:

```csv
#key,property-1,value-1
state,#Format,observationAbout=geoId/{Data:0>2}
```

Every `#` directive on a column header key, such as `#Eval`, `#Regex`,
`#Format`, or `#Filter`, runs for each value in that column. It also runs on the
header cell itself, where `Number` isn't set. The resulting `Failed to evaluate`
log lines and `warning-unresolved-value-ref` counts are expected when the output
is right.

WARNING: A failed `#Eval` or `#Filter` expression doesn't raise an error. The
property is silently missing. Test new expressions on a few rows with `--debug`
(see [Advanced configuration](config.md#debug-a-few-rows)).

## Dates

The processor normalizes common date formats automatically (see the
[PV map guide](pv_map.md#dates)). Use these patterns for other dates.

**Quarters:** `observationDate` is the end of the period: `YYYY` stands for the
whole year, and a quarter uses its last month. Extract the year and quarter with
`#Regex`, compute the last month with `#Eval`, and set `observationPeriod`:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3
quarter,#Regex,^(?P<Year>[0-9]{4})-Q(?P<Quarter>[1-4])$,#Eval,"observationDate=f'{Year}-{int(Quarter)*3:02d}'",observationPeriod,P3M
```

`2020-Q1` becomes `observationDate: 2020-03` and `2020-Q3` becomes `2020-09`,
with `observationPeriod: P3M`.

Cells that don't match a `#Regex` keep their other PVs.

**A year inside text:** use `#Regex` alone. Name the group after the property to
set it directly:

```csv
#key,property-1,value-1
year,#Regex,(?P<observationDate>[0-9]{4})
```

`Calendar Year (Jan - Dec), 2026` becomes `observationDate: 2026`. You can also
name the group `Year` and use `{Year}` in another value.

**Free-form dates:** use `format_date`, which returns `YYYY-MM-DD`:

```csv
#key,property-1,value-1
date,#Eval,observationDate=format_date(Data)
```

`Thu Nov 16 2023` becomes `2023-11-16`.

### Parse dates

Use these `#Eval` functions to parse and format dates. Each example parses
`15/02/2022`:

| Expression                                                                                          | Result       | Use                                         |
| --------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------- |
| `observationDate=format_date(Data)`                                                                 | `2022-02-15` | Free-form dates, output as `YYYY-MM-DD`     |
| `observationDate=format_date(Data, '%Y-%m')`                                                        | `2022-02`    | The same, with an output format             |
| `observationDate=dateutil_parser_parse(Data, dayfirst=True).strftime('%Y-%m-%d')`                   | `2022-02-15` | Day-first dates                             |
| `observationDate=datetime_strptime(Data, '%d/%m/%Y').strftime('%Y-%m-%d')`                          | `2022-02-15` | An exact input format                       |
| `observationDate=(datetime_strptime(Data, '%d/%m/%Y') - relativedelta(months=1)).strftime('%Y-%m')` | `2022-01`    | Date arithmetic, such as the previous month |

Quote the expression in the CSV because it contains commas, for example
`date,#Eval,"observationDate=format_date(Data, '%Y-%m')"`. You can also assign
the result to a local variable and use it, as in
`date,#Eval,"Date=format_date(Data)",observationDate,{Date}`.

**Ambiguous dates:** a date such as `01/02/2020` can be read as January or
February. Parse it with an explicit format:

```csv
#key,property-1,value-1
date,#Eval,"observationDate=datetime_strptime(Data, '%d/%m/%Y').strftime('%Y-%m-%d')"
```

Set `observationPeriod` (for example `P1M` or `P1Y`) when observations cover a
period, and add it to `output_columns`.

## Sectioned headers

Some sheets repeat header rows inside the data, for example one block for men
and one for women. Mark the header text with `#Header` and list the properties
that apply down the columns:

```csv
#key,property-1,value-1,property-2,value-2
male,gender,Male,#Header,gender
female,gender,Female,#Header,gender
```

With this input, the row `,Male,Female` sets `gender` for each column in the
rows below it:

```csv
year,a,b
,Male,Female
2020,10,11
2021,12,13
```

A later header row adds to the column properties from earlier header rows rather
than replacing them. Repeat every property that changes in each header row.

## Merged header cells

A header that spans several columns, as a merged cell does, leaves the cells to
its right blank. `#MergedCell,<N>` copies the header's PVs to the next `N` blank
header cells and no further:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3
male,gender,Male,#MergedCell,2,value,{Number},populationType,Person
```

With the headers `year,male,,,female`, `male` applies to its own column and the
next 2 blank columns; `female` starts a new header. Without `#MergedCell`, a
header copies into every blank header cell to its right. Use `#MergedCell,0` to
stop the copying when blank header cells are separate columns.

## Derived denominators

For a share of a total, set `measurementDenominator` to the current StatVar's
properties minus the ones that define the share. Prefix each removed property
with `-`:

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3,property-4,value-4,property-5,value-5
female,gender,Female
share,value,{Number},populationType,Person,measuredProperty,count,measurementDenominator,-gender,scalingFactor,100
```

A `Female` share of `48.5` becomes an observation of
`Count_Person_Female_AsAFractionOf_Count_Person` with `scalingFactor: 100`.

To remove several properties, quote the list, for example
`measurementDenominator,"-age,-race,-gender"` for a share of all persons. You
can also name the denominator StatVar directly, for example
`measurementDenominator,Count_Person`.

## Number formats

For sources that write `1.234,5` for 1234.5, set the decimal mark and the
thousands separators in the config:

```csv
parameter,value
number_decimal,","
number_separator,". "
```

`number_separator` lists every character to strip, here a period and a space.

## StatVar DCIDs and names

**Remap a generated DCID.** Use a remap file when a generated StatVar DCID must
match an existing StatVar. List generated DCIDs in a `key` column and the DCIDs
to use in a `dcid` column, then set `statvar_dcid_remap_csv` or the
`--statvar_dcid_remap_csv` flag:

```csv
key,dcid
Count_Person_Female,Count_Person_Female_Remapped
```

The counter `remapped-statvar-dcid` counts remapped StatVars.

**Leave default values out of the DCID.** `statvar_dcid_ignore_values` lists
values of default StatVar properties, such as `statType`, to leave out of the
generated DCID. The default is `measuredValue,StatisticalVariable`.

**Generate names.** Set `generate_statvar_name,True` to add a `name` built from
the StatVar properties, or `llm_generate_statvar_name,True` with
`--google_genai_key` to generate names with Gemini. To name StatVars after
processing instead, see the
[tip in Schema tools](../schema/README.md#generate-readable-statvar-names).

**Schemaless StatVars.** With `schemaless,True`, properties that start with a
capital letter and aren't in the Data Commons schema are allowed. They are used
in the DCID and written as comments in the StatVar MCF. See
`test_data/sample_schemaless_pv_map.py` for an example.

## Other settings used by imports

| Setting                   | Use                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `observation_date_format` | Output format for `observationDate`, as a `strftime` pattern, for example `%Y-%m-%dT%H:%M:%S` for hourly data. |
| `data_url`                | Download the input from a URL when `--input_data` doesn't exist locally.                                       |
| `spell_check`             | Set to `False` to skip spell checks of the generated StatVars.                                                 |
| `spell_allow_words`       | Words the spell check accepts, for example `"prediabetes,sigmoidoscopy"`.                                      |

## Defaults and roll-ups

### Defaults

The config sets default StatVar and SVObs properties. They apply only when no PV
map sets the property:

- `default_statvar_pvs`: `measuredProperty: count` and `statType: measuredValue`
  by default.
- `default_svobs_pvs`: properties added to every SVObs.

A PV map row with the key `DEFAULT_PV` applies its PVs to every cell of every
input file:

```csv
#key,property-1,value-1,property-2,value-2
DEFAULT_PV,measurementMethod,CensusEstimate
```

`DEFAULT_PV` and [file-name keys](pv_map.md#apply-pvs-to-a-whole-file) take
priority over values that come from other columns in the same row. For example,
`DEFAULT_PV,observationDate,2019` replaces the dates from a year column. The
value column's own header PVs still override them. Use `DEFAULT_PV` only for
properties that no column provides.

### Roll-ups with multi-value properties

Normally a later value replaces an earlier one for the same property. A property
listed in `multi_value_properties` keeps every value instead, and the processor
writes one observation per value. Combine this with `#Aggregate` to roll county
values up to a state total:

```csv
parameter,value
multi_value_properties,observationAbout
output_columns,"observationAbout,observationDate,variableMeasured,value,measurementMethod"
```

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3,property-4,value-4
fips,observationAbout,geoId/{Data}
year,observationDate,{Number}
total population,value,{Number},populationType,Person,measuredProperty,count,#Aggregate,sum
DEFAULT_PV,observationAbout,geoId/06
```

For counties `06001` (100) and `06003` (50) in 2020, the output has both county
rows and `geoId/06, 2020, 150` with `measurementMethod: DataCommonsAggregate`.

NOTE: List `measurementMethod` in `output_columns` when you aggregate. Without
`output_columns`, the output drops the `DataCommonsAggregate` method.

**Roll up a constraint property to a total.** The same pattern gives totals
across a constraint property, such as `gender`. Give each gender value a second,
empty value with a trailing comma, so each cell produces one observation with
the gender and one without it. `#Aggregate` sums the observations without a
gender into the total:

```csv
parameter,value
multi_value_properties,gender
output_columns,"observationAbout,observationDate,variableMeasured,value,measurementMethod"
```

```csv
#key,property-1,value-1,property-2,value-2,property-3,value-3,property-4,value-4
fips,observationAbout,geoId/{Data}
year,observationDate,{Number}
male,gender,"Male,",value,{Number},populationType,Person,#Aggregate,sum
female,gender,"Female,",value,{Number},populationType,Person,#Aggregate,sum
```

For this input:

```csv
fips,year,male,female
06001,2020,60,40
06003,2020,30,20
```

The output has `Count_Person_Male` and `Count_Person_Female` for each county,
plus `Count_Person` with `100` for `06001` and `50` for `06003`, with
`measurementMethod: DataCommonsAggregate`. A `DEFAULT_PV` row with an empty
`gender` doesn't work for this; it produces no totals.

### Aggregate duplicates

When several rows produce the same StatVar, place, and date, the processor drops
the StatVar unless you aggregate them. First check whether the rows differ in a
property that's missing from the PV map, such as `gender`; add it if so. If the
rows are parts of one total, aggregate them:

- Per key: `#Aggregate,<type>` in the value column's PV map row.
- For all StatVars: `aggregate_duplicate_svobs,<type>` in the config.

The types are `sum`, `min`, `max`, `mean`, `list`, `first`, and `last`. All
except `first` and `last` set `measurementMethod` to `DataCommonsAggregate`, or
prefix an existing method with `dcAggregate/`. `mean` also sets
`statType: meanValue`. The generated TMCF can include an `#Aggregate` line; lint
accepts it.

## Test the PV map and places on a sample

Make a sample with every value of the important columns; see the
[data sampler guide](data_sampler.md#every-value-of-the-important-columns). Run
`stat_var_processor.py` on the sample with `--debug`, so the counters name the
values that failed:

```bash
./agents/common/run_python.sh tools/statvar_importer/stat_var_processor.py \
  --input_data=/tmp/sample.csv \
  --pv_map=<import-dir>/<import>_pvmap.csv,<import-dir>/<source>_places_pvmap.csv \
  --config_file=<import-dir>/<Import>_statvar_processor_config.csv \
  --output_path=/tmp/sample_output/<import> \
  --output_counters=/tmp/sample_output/counters.csv \
  --debug
```

Then check these counters:

| Counter                                                    | Meaning                                                                                        | Fix                                                                                  |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `warning-missing-property-key_<column>:<text>`             | No key matches the whole text of a cell in that column, for example `Indicator:Literacy rate`. | Add a key, unless a partial key already maps the text.                               |
| `dropped-svobs-unresolved-place`, `error-unresolved-place` | Some places didn't resolve to DCIDs.                                                           | Add the names to the places PV map or to `places_resolved_csv`.                      |
| `error-statvar-missing-property`                           | Some StatVars lack a required property, such as `populationType`.                              | Usually an indicator without a key; see the `warning-missing-property-key` counters. |

To list the texts without keys in one column:

```bash
grep 'warning-missing-property-key_Indicator:' /tmp/sample_output/counters.csv
```

After the counters are clean on the sample, process the full input; see
[Check the results](../README.md#check-the-results).

## Speed up processing

Before you process a large input, estimate the run time and remove work the
processor doesn't need to do:

1. **Estimate the time for the full input.** Process the first rows with
   `--input_rows=5000`, then read `process_remaining_time` in the counters file
   (`1:process_input_process_remaining_time`). It's the estimated number of
   seconds for the rest of the input, from the rate so far and the row count of
   the input files. For example, 5,000 rows of a 60,000-row file took 9 seconds,
   with 113 seconds remaining. Long runs also log it with the other counters
   periodically.
1. **Look up only label cells.** Set `header_rows` and `mapped_columns`, so the
   processor looks up only the header rows and the label columns instead of
   every cell; see [Input layout](config.md#input-layout). In a table with two
   label columns and two value columns, this halved the PV map lookups.
1. **Resolve places ahead of time.** Map every place to a DCID in the PV map,
   for example `fips,observationAbout,geoId/{Data}` or a places PV map, or list
   every name in `places_resolved_csv`. A place that's still a name after the PV
   map lookup is sent to the place resolver, which calls the Data Commons or
   Maps API for each observation. The processor turns this resolution on
   whenever `places_resolved_csv`, `places_csv`, `dc_api_key`, or `maps_api_key`
   is set, and `resolve_places,0` doesn't turn it off.
1. **Split the input.** If the run is still too slow, process shards in
   parallel, as described in the next section.

## Process large inputs in parallel

For inputs too large for one run, split them into shards, process the shards in
parallel, and merge the outputs. Run these steps from the import's folder with
the repository environment active:

1. **Fix the output columns.** Set `output_columns` in the config, for example
   `observationAbout,observationDate,variableMeasured,value,measurementMethod`.
   Then every shard writes the same columns in the same order, and all the shard
   CSVs can use one TMCF. Without it, each shard picks its own columns: a
   property with one value in a shard, such as a single date, moves from the CSV
   into the TMCF.

1. **Shard by a column.** Choose a column such that rows that aggregate
   together, with the same StatVar, place, and date, land in the same shard, for
   example the place column. Splitting by line count can give partial sums.

   ```bash
   mkdir -p shards
   python3 -c "
   import pandas as pd
   df = pd.read_csv('input_files/data.csv', dtype=str, keep_default_na=False)
   for key, rows in df.groupby('iso3'):
       rows.to_csv(f'shards/{key}.csv', index=False)
   "
   ```

1. **Process the shards in parallel.** Write shard outputs to a temporary folder
   outside `output/`:

   ```bash
   mkdir -p tmp_output counters
   ls shards/*.csv | xargs -P 8 -I{} sh -c '
     n=$(basename {} .csv)
     python3 ../../tools/statvar_importer/stat_var_processor.py \
       --input_data={} --pv_map=<import>_pvmap.csv \
       --config_file=<import>_statvar_processor_config.csv \
       --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
       --output_path=tmp_output/$n \
       --output_counters=counters/${n}_counters.csv'
   ```

1. **Merge the outputs.** Concatenate the CSVs with one header, reuse one TMCF
   (identical across shards because of step 1), and merge the StatVar MCF files:

   ```bash
   mkdir -p output
   first=$(ls tmp_output/*.csv | head -1)
   head -1 "$first" > output/<import>.csv
   for f in tmp_output/*.csv; do tail -n +2 "$f" >> output/<import>.csv; done
   cp "${first%.csv}.tmcf" output/<import>.tmcf
   python3 ../../tools/statvar_importer/mcf_file_util.py \
     --input_mcf='tmp_output/*_stat_vars.mcf' \
     --output_mcf=output/<import>_stat_vars.mcf
   ```

   Merge `tmp_output/*_stat_vars_schema.mcf` the same way if the shards produced
   schema.
