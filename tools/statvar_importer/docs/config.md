# Advanced configuration

Most imports need only the settings in the
[basic guide](../README.md#write-a-config). This page lists the other settings
that imports use, grouped by topic. Each table shows the default and when to
change it. Set them in `<import>_statvar_processor_config.csv` as
`parameter,value` rows, and quote values that contain commas.

For every setting and its default, see
[`get_default_config`](../config_flags.py) in the Python source.

## How settings combine

Settings come from three places. A later source overrides an earlier one:

1. Command-line flags, such as `--input_rows`, and their defaults.
1. The config file passed with `--config_file`.
1. PV map rows whose key is a config setting name, for example
   `mapped_columns,3` inside a PV map.

### PV maps with the same key

You can pass several PV maps with `--pv_map=a.csv,b.csv`. When both map the same
key, the file loaded last wins for each property. Properties that only the
earlier file sets are kept. For example, if `a.csv` has `wh,race,WhiteAlone` and
`b.csv` has `wh,race,BlackOrAfricanAmericanAlone`, the output uses
`BlackOrAfricanAmericanAlone`.

### On and off values

In a CSV config, write on/off settings as `1` and `0`. `True`, `False`, `yes`,
`no`, `on`, and `off` also work, in any case. An empty value means off:

```csv
parameter,value
reconcile_nodes,0
match_substring_word_boundary,0
```

The processor converts the value to the type of the setting's default. A setting
without a default in `config_flags.py` keeps the text as is.

WARNING: The processor accepts any setting name without checking it, so a typo
such as `mapped_coloumns` is silently ignored. Copy names from this page or from
`get_default_config`.

## Input layout

| Setting          | Default                              | When to change it                                                                                                                                                                 |
| ---------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `header_rows`    | `-1` (detect headers and label rows) | Set to the line number of the last header row, counted from the top of the file including title lines. Leave unset when rows with only a label must apply to the rows below them. |
| `mapped_columns` | not set                              | Set to the number of label columns at the left, such as `3`. Only those cells, plus headers, are looked up. Set it only together with `header_rows`.                              |
| `mapped_rows`    | not set                              | Set to the number of label rows at the top of a wide sheet, where categories run across the columns.                                                                              |
| `header_columns` | `-1`                                 | Set to the number of label columns in a transposed sheet whose headers run down the left side.                                                                                    |
| `input_columns`  | all                                  | Process only the first N columns.                                                                                                                                                 |
| `input_rows`     | all                                  | Process only the first N rows, for sample runs.                                                                                                                                   |
| `input_encoding` | `utf-8`                              | Set for sources in another encoding, such as `latin-1`.                                                                                                                           |
| `ignore_rows`    | none                                 | Skip the listed line numbers, such as `"[1,5]"`.                                                                                                                                  |
| `data_url`       | not set                              | Download the input from a URL when `--input_data` doesn't exist locally.                                                                                                          |
| `process_rows`   | all                                  | Process only the listed line numbers, such as `"1,2,15"`. Include the header line. Use it to debug a few rows.                                                                    |

When neither `mapped_columns` nor `mapped_rows` is set, every cell is looked up
in the PV map. That is slower and can match numbers by accident.

## Key matching

| Setting                              | Default      | When to change it                                                                                                                                                                                                                |
| ------------------------------------ | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `word_delimiter`                     | space        | Set when the source joins words with another character, for example `!!` in US Census headers (`Total!!Male!!Under 5 years`), so keys can match each part; see [several PVs from one cell](pv_map.md#several-pvs-from-one-cell). |
| `match_substring_word_boundary`      | on           | Turn off to let lowercase keys match inside long text in any case; see [How keys match](pv_map.md#how-keys-match). Keys then also match inside words.                                                                            |
| `number_decimal`, `number_separator` | `.` and `, ` | Set for sources such as `1.234,5`; see [number formats](advanced_processing.md#number-formats).                                                                                                                                  |

## StatVars

| Setting                                              | Default                                              | When to change it                                                                                                                                                                           |
| ---------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `drop_statvars_without_svobs`                        | `1` (drop)                                           | Set to `0` to keep StatVars that have no observations, such as denominators.                                                                                                                |
| `multi_value_properties`                             | `name,alternateName,measurementDenominator`          | List properties that keep every value instead of the last one; see [roll-ups](advanced_processing.md#roll-ups-with-multi-value-properties).                                                 |
| `statvar_dcid_remap_csv`                             | not set                                              | Point to a CSV with a key column of generated DCIDs and a `dcid` column of the DCIDs to use instead. Use it when a generated DCID must match an existing StatVar. Also available as a flag. |
| `default_statvar_pvs`, `default_svobs_pvs`           | `measuredProperty: count`, `statType: measuredValue` | Change the properties applied when the PV map doesn't set them; see [defaults](advanced_processing.md#defaults).                                                                            |
| `statvar_dcid_ignore_values`                         | `measuredValue,StatisticalVariable`                  | Values of default properties to leave out of generated DCIDs.                                                                                                                               |
| `generate_statvar_name`, `llm_generate_statvar_name` | `False`                                              | Generate StatVar names; see [StatVar DCIDs and names](advanced_processing.md#statvar-dcids-and-names).                                                                                      |
| `schemaless`                                         | `False`                                              | Allow StatVar properties that aren't in the schema; see [StatVar DCIDs and names](advanced_processing.md#statvar-dcids-and-names).                                                          |
| `generate_schema_mcf`                                | `True`                                               | Set to `False` to skip writing `_stat_vars_schema.mcf`.                                                                                                                                     |
| `reconcile_nodes`                                    | `True`                                               | Turn off to skip replacing superseded StatVars and values with their successors.                                                                                                            |
| `aggregate_duplicate_svobs`                          | not set                                              | Aggregate duplicate observations for all StatVars; see [aggregation](advanced_processing.md#aggregate-duplicates).                                                                          |

## Place resolution

The [basic guide](../README.md#map-places) maps places with a places PV map. For
automatic resolution of place names, use these settings and see the
[place tools](../place/README.md):

| Setting               | Default | When to change it                                                                             |
| --------------------- | ------- | --------------------------------------------------------------------------------------------- |
| `places_resolved_csv` | not set | A reviewed CSV of `place_name,dcid` rows. Also available as the `--places_resolved_csv` flag. |
| `places_within`       | not set | Limit name resolution to places within these DCIDs, such as `country/IND`.                    |
| `place_type`          | not set | Limit name resolution to these place types, such as `State,AdministrativeArea1`.              |

NOTE: Setting the `DC_API_KEY` environment variable also turns on automatic
place-name resolution.

## Run control

| Setting                            | Default                       | When to change it                                                 |
| ---------------------------------- | ----------------------------- | ----------------------------------------------------------------- |
| `--log_level`                      | `0` (INFO)                    | Set to `1` for debug messages from every module.                  |
| `--log_every_n`                    | `1`                           | Log one in N repeated messages to shorten logs.                   |
| `debug`                            | `False`                       | Turn on detailed processing logs; see below.                      |
| `dc_api_root`                      | `https://api.datacommons.org` | Point to another Data Commons API instance.                       |
| `observation_date_format`          | detected                      | Output format for `observationDate`, such as `%Y-%m-%dT%H:%M:%S`. |
| `spell_check`, `spell_allow_words` | `True`, none                  | Turn off spell checks, or allow specific words.                   |

### Debug a few rows

`--debug` logs every lookup and merge, which is too much for a full input.
Always combine it with a small sample:

```bash
./agents/common/run_python.sh tools/statvar_importer/stat_var_processor.py \
  --input_data=<input>.csv --pv_map=<import>_pvmap.csv \
  --config_file=<import>_statvar_processor_config.csv \
  --output_path=/tmp/debug/<import> --output_counters=/tmp/debug/counters.csv \
  --input_rows=10 --debug > /tmp/debug/run.log 2>&1
```

To debug specific rows, set `process_rows` in the config instead of
`--input_rows`. Search the log for the source text of a key to see which PVs it
matched.
