# Troubleshooting

Use this guide when a run produces too few rows, wrong values, or lint errors.
Start with the workflow, then find your symptom in the tables.

## Workflow

1. Run on a sample with `--input_rows=100` and
   `--output_counters=counters/<import>_counters.csv`.
1. Read the counters (see [Counters to check](#counters-to-check)).
1. Trace a few output rows to the source with the `#input` column, for example
   `data.csv:4:6`: the file, line 4, and column 6, both counted from 1.
1. Fix the PV map or config and rerun.
1. Lint the output (see [Check the results](../README.md#check-the-results)).

## Counters to check

Some counter names carry a stage prefix, such as
`1:process_input_dropped-svobs-invalid`. Group them by the question they answer:

| Question                   | Counters                                                                                                                                                                                       |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Were all data rows read?   | `input-rows-processed`; `input-rows-ignored-*` counts skipped lines such as titles, footers, and rows with too few columns                                                                     |
| Did the PV map match?      | `warning-missing-property-key` counts lookups without a match. It is high even in good runs because every number is looked up; use it only to compare runs.                                    |
| What was dropped, and why? | `dropped-svobs-unresolved-place`, `dropped-svobs-unresolved-date`, `dropped-svobs-invalid`, `dropped-svobs-with-invalid-statvar`, `filter-dropped-svobs-pvs`, `dropped-statvars-without-svobs` |
| What caused the drops?     | `error-svobs-missing-property`, `error-statvar-missing-property`, `error-statvar-with-dup-svobs`, `error-mismatched-svobs`                                                                     |
| What was written?          | `generated-statvars`, `output-svobs-csv-rows`                                                                                                                                                  |

A counter that is missing from the file is 0. `error-unresolved-place` and
`warning-svobs-missing-place` also count header and label rows, so nonzero
values alone aren't a problem. `input-header-rows` counts header and label rows;
`input-rows-ignored-preprocess` and `input-rows-ignored-too-few-columns` count
blank lines, titles, and footers.

## Common problems

| Symptom                                                                     | Likely cause                                                                                                                            | Fix                                                                                                                                                               |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The run stops with `429 Too Many Requests`, leaving empty or partial output | Without `DC_API_KEY`, the processor uses a shared Data Commons API key that is rate limited                                             | Set `DC_API_KEY` to your own key; see [Setup](../README.md#setup).                                                                                                |
| The CSV has no rows or too few rows                                         | A value column has no `value,{Number}` mapping                                                                                          | Add `value,{Number}` to the value column's header row in the PV map.                                                                                              |
| The CSV has no rows; `warning-svobs-missing-place` is high                  | `header_rows` doesn't point at the header line, or `mapped_columns` is set without `header_rows`                                        | Count `header_rows` from the top of the file, including title lines, or leave both unset.                                                                         |
| `dropped-svobs-unresolved-place`                                            | `observationAbout` is missing or isn't a DCID                                                                                           | Map the place column; see [Map places](../README.md#map-places).                                                                                                  |
| Place names in `--places_resolved_csv` don't resolve                        | A PV map key matches text inside the names, such as `county` in `Kings County CA`                                                       | Use a specific key, such as `county name`; see the [place tools](../place/README.md).                                                                             |
| `error-statvar-missing-property`, `dropped-svobs-with-invalid-statvar`      | A StatVar lacks `populationType` or `measuredProperty`                                                                                  | Add the property to the value column's PV map row.                                                                                                                |
| `error-svobs-missing-property`, `dropped-svobs-invalid`                     | An SVObs lacks `observationDate`, `observationAbout`, or `value`                                                                        | Map the date, place, and value columns.                                                                                                                           |
| `error-statvar-with-dup-svobs`, a StatVar missing                           | Rows produce the same StatVar, place, and date with different values. The StatVar is dropped with all its observations, from every row. | Add the property that tells the rows apart, such as `gender`. If the rows are parts of one total, see [aggregation](advanced_processing.md#aggregate-duplicates). |
| A property is missing from some StatVars                                    | The key doesn't match the source text                                                                                                   | Check the spelling. A key that matches a phrase inside longer text is case-sensitive; copy the source casing. Keep comment rows short.                            |
| A label row such as `Count of all Males` doesn't apply to the rows below    | `header_rows` is set, so label rows are treated as data                                                                                 | Leave `header_rows` and `mapped_columns` unset, or mark the label with `#Header`.                                                                                 |
| A config setting has no effect                                              | The setting name has a typo                                                                                                             | Check the name against [Advanced configuration](config.md).                                                                                                       |
| `#Ignore` or `#header` has no effect                                        | Keywords are case-sensitive                                                                                                             | Write `#ignore` and `#Header`.                                                                                                                                    |
| A computed property is missing                                              | A `#Eval` or `#Filter` expression failed silently                                                                                       | Test it on a few rows with `--debug`; cast strings with `float()` or `int()`.                                                                                     |

## Wrong values

| Symptom                                                      | Likely cause                                                      | Fix                                                                                                                             |
| ------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Numbers with thousands separators are misread                | The source uses a different separator or decimal mark             | Check the input; values such as `1,234` are read as `1234` by default.                                                          |
| Dates are misread, such as `01/02/2020` read as January      | The date is ambiguous                                             | Parse it with an explicit format; see [Dates](advanced_processing.md#dates).                                                    |
| A `UnicodeDecodeError`                                       | The source isn't UTF-8                                            | Set `input_encoding`, for example `latin-1`.                                                                                    |
| Values are 1,000 times too small                             | The source reports values in thousands                            | Add `#Multiply,1000`; see [Scale values](advanced_processing.md#scale-values).                                                  |
| New StatVar DCIDs appear for StatVars that already exist     | `--existing_statvar_mcf` is missing, or a property differs        | Pass `--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`. To force a DCID, use `statvar_dcid_remap_csv`. |
| A file-level date or `DEFAULT_PV` replaces a column's values | `DEFAULT_PV` and file-name keys override other columns in the row | Use them only for properties no column provides.                                                                                |

## Lint errors

`dc-import lint` checks the CSV, TMCF, and MCF files. Errors that come from the
PV map are fixed there:

| Lint error                                                           | Fix in the PV map                                                                                                                                         |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| An undefined property or enum value, such as an unknown `race` value | Use an existing value (find one with `schema_matcher.py`, see [Schema tools](../schema/README.md)), or review the new value in `_stat_vars_schema.mcf`.   |
| A malformed DCID                                                     | Check the place pattern, for example `country/{Data}` needs ISO 3166 alpha-3 codes.                                                                       |
| `existing_statvar_mcf` fails with `403 Forbidden`                    | You don't have access to `gs://unresolved_mcf`; leave the flag out for local tests.                                                                       |
| Lint fails with `ConnectException` and writes no report              | Lint can't reach the Data Commons API. Run it with network access; `-e=false -ep=false` reduces the calls, and `-s=false` crashes in the current release. |
| A value that isn't a number                                          | Check that the `value` column holds numbers and that footers are excluded.                                                                                |
| A date that isn't ISO 8601                                           | Map dates with a format the processor normalizes, or convert them with `#Eval`.                                                                           |

Warnings about empty values in optional columns, such as
`StrSplit_EmptyToken_scalingFactor` for `unit`, `scalingFactor`,
`measurementMethod`, or `observationPeriod`, are expected when only some rows
set the column. Ignore them.

Warnings such as `Existence_FailedDcCall_*` mean that lint couldn't reach the
Data Commons API to check a reference. Rerun with network access before you
treat them as problems.

## Debug a few rows

Run with `--debug` on a small sample and search the log for the source text:

```bash
./agents/common/run_python.sh tools/statvar_importer/stat_var_processor.py \
  --input_data=<input>.csv --pv_map=<import>_pvmap.csv \
  --config_file=<import>_statvar_processor_config.csv \
  --output_path=/tmp/debug/<import> --output_counters=/tmp/debug/counters.csv \
  --input_rows=10 --debug > /tmp/debug/run.log 2>&1
grep -n "Total Persons" /tmp/debug/run.log | head
```

To debug specific rows, set `process_rows` in the config; see
[Advanced configuration](config.md#debug-a-few-rows).

For more detail, use `--log_level` instead of `--debug`:

- `--log_level=2` also logs how references such as `{Number}` and `{Data}` are
  resolved for each cell (`Resolved references`).
- `--log_level=3` also logs every PV map lookup: each text tried as a key, with
  its column prefix (`Search PVs for <column>:<text>`), each partial-match
  fragment, and the keys that matched (`Got PVs for`).

Level 3 writes about ten times as many lookup lines, so combine it with
`--input_rows` or `process_rows`, and search the log for the source text:

```bash
grep -n "Search PVs for.*Total Persons\|Got PVs for" /tmp/debug/run.log | head
```

## Observations dropped between versions

When an automated refresh drops observations, compare the two versions:

1. Download the retained `cleaned_csv` and counters for the current and the
   previous version. Counters are retained only if `counters/*.csv` is in the
   manifest's `source_files`.
1. Compare the counters to find the stage that changed, for example more
   `dropped-svobs-unresolved-place` or fewer `input-rows-processed`. Treat a
   counter difference as a clue, not proof.
1. Group the missing rows by StatVar, place, or date to find a pattern.
1. Trace a few missing rows to the source with `#input`, and check whether the
   source changed: new labels, renamed columns, or new places.
1. Update the PV map; see
   [Write PV maps that survive auto-refresh](pv_map.md#write-pv-maps-that-survive-auto-refresh).

For the full investigation workflow, see the
[deleted observations guide](../../../agents/skills/dc-import-diagnostics/troubleshooting/deleted-observations.md).
