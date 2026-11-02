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
key,p1,v1,p2,v2,p3,v3,p4,v4
population,value,{Number},populationType,Person,measuredProperty,count,#Filter,"Allow=float(value) >= 0"
```

- Property values are strings, so cast them: `float(value)` or `int(value)`.
- The counter `filter-dropped-svobs-pvs` counts dropped observations.
- Keep filters explicit and testable. Don't hard-code a future-year cutoff, such
  as `int(observationDate) <= 2024`; it silently drops new data after a refresh.

## Scale values

Use `#Multiply` when the source reports values in units of N, such as "in
thousands". The processor stores the actual value:

```csv
key,p1,v1,p2,v2,p3,v3,p4,v4
population (thousands),value,{Number},populationType,Person,measuredProperty,count,#Multiply,1000
```

A source value of `1.5` becomes `1500`.

For percentages, keep the source number and add `scalingFactor,100` together
with a denominator, as in the example in
[Derived denominators](#derived-denominators). Don't combine `#Multiply` and
`scalingFactor` for the same value.

## Skip whole rows

`#ignore` drops the observations in a row. To skip a row before any processing,
for example rows marked as provisional, use `#IgnoreRow,True`:

```csv
key,p1,v1
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
  `datetime`, `datetime_strptime`, `relativedelta`, `re`, and `re_sub`.

Pad a code with zeros:

```csv
key,p1,v1
fips,#Eval,"observationAbout=f'geoId/{int(Number):02d}'"
```

Use `#Regex` to extract parts of a cell into local variables with named groups,
and `#Format` for simple string templates:

```csv
key,p1,v1
state,#Format,observationAbout=geoId/{Data:0>2}
```

WARNING: A failed `#Eval` or `#Filter` expression doesn't raise an error. The
property is silently missing. Test new expressions on a few rows with `--debug`
(see [Advanced configuration](config.md#debug-a-few-rows)).

## Dates

The processor normalizes common date formats automatically (see the
[PV map guide](pv_map.md#dates)). Use these patterns for other dates.

**Quarters:** extract the year and quarter with `#Regex`, compute the first
month with `#Eval`, and set `observationPeriod`:

```csv
key,p1,v1,p2,v2,p3,v3
quarter,#Regex,^(?P<Year>[0-9]{4})-Q(?P<Quarter>[1-4])$,#Eval,"observationDate=f'{Year}-{int(Quarter)*3-2:02d}'",observationPeriod,P3M
```

`2020-Q3` becomes `observationDate: 2020-07` with `observationPeriod: P3M`.

**Free-form dates:** use `format_date`, which returns `YYYY-MM-DD`:

```csv
key,p1,v1
date,#Eval,observationDate=format_date(Data)
```

`Thu Nov 16 2023` becomes `2023-11-16`.

**Ambiguous dates:** a date such as `01/02/2020` can be read as January or
February. Parse it with an explicit format:

```csv
key,p1,v1
date,#Eval,"observationDate=datetime_strptime(Data, '%d/%m/%Y').strftime('%Y-%m-%d')"
```

Set `observationPeriod` (for example `P1M` or `P1Y`) when observations cover a
period, and add it to `output_columns`.

## Sectioned headers

Some sheets repeat header rows inside the data, for example one block for men
and one for women. Mark the header text with `#Header` and list the properties
that apply down the columns:

```csv
key,p1,v1,p2,v2
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

When a header cell is blank, the processor copies the PVs of the header to its
left, as for a merged cell that spans two columns. In a sheet whose blank header
cells are separate columns, that creates duplicate StatVars. Stop the copying
with `#MergedCell,0`:

```csv
key,p1,v1,p2,v2,p3,v3
male,gender,Male,#MergedCell,0,value,{Number}
```

## Derived denominators

For a share of a total, set `measurementDenominator` to the current StatVar's
properties minus the ones that define the share. Prefix each removed property
with `-`:

```csv
key,p1,v1,p2,v2,p3,v3,p4,v4,p5,v5
female,gender,Female
share,value,{Number},populationType,Person,measuredProperty,count,measurementDenominator,-gender,scalingFactor,100
```

A `Female` share of `48.5` becomes an observation of
`Count_Person_Female_AsAFractionOf_Count_Person` with `scalingFactor: 100`.

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

**Remap a generated DCID.** When a generated StatVar DCID must match an existing
StatVar, list it in a CSV with a `key` column of generated DCIDs and a `dcid`
column of the DCIDs to use, and set `statvar_dcid_remap_csv` (or the
`--statvar_dcid_remap_csv` flag):

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
[tip in Tools](tools.md#tip-generate-readable-statvar-names).

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

## Defaults, overrides, and roll-ups

### Defaults

The config sets default StatVar and SVObs properties. They apply only when no PV
map sets the property:

- `default_statvar_pvs`: `measuredProperty: count` and `statType: measuredValue`
  by default.
- `default_svobs_pvs`: properties added to every SVObs.

A PV map row with the key `DEFAULT_PV` applies its PVs to every cell of every
input file:

```csv
key,p1,v1,p2,v2
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
```

```csv
key,p1,v1,p2,v2,p3,v3,p4,v4
fips,observationAbout,geoId/{Data}
year,observationDate,{Number}
total population,value,{Number},populationType,Person,measuredProperty,count,#Aggregate,sum
DEFAULT_PV,observationAbout,geoId/06
```

For counties `06001` (100) and `06003` (50) in 2020, the output has both county
rows and `geoId/06, 2020, 150` with `measurementMethod: DataCommonsAggregate`.

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
`statType: meanValue`.

## Process large inputs in parallel

For inputs too large for one run, split them into shards, process the shards in
parallel, and merge the outputs. Run these steps from the import's folder with
the repository environment active:

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
   (identical across shards because `output_columns` is fixed), and merge the
   StatVar MCF files:

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
