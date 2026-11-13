# Data sampler

`data_sampler.py` makes a small input file that keeps the variety of a large
one. Use the sample to test a PV map, a config, and place mappings with the
[StatVar Processor](../README.md) (`stat_var_processor.py`) in seconds, before
you process the full input.

A good test sample has every value of the columns that become schema: the
indicator or variable names, category columns such as sex or age group, and the
places. It doesn't need every number or footnote.

Run the commands in this guide from the repository root after
`./run_tests.sh -r`.

## Contents

- [How sampling works](#how-sampling-works)
- [Options](#options)
- [Choose the columns to track](#choose-the-columns-to-track)
- [Recipes](#recipes)
- [Large inputs](#large-inputs)

## How sampling works

The sampler reads the input rows in order and keeps a row when it adds variety.
Each step lists the option that controls it:

1. It copies the header rows to the output. *Option:* `--sampler_header_rows`
   (default `1`); count title lines above the column names too.
1. It keeps a row when one of its tracked cells has a value that the sample
   doesn't have yet, or has fewer than `--sampler_rows_per_key` times (default
   `5`). *Options:* `--sampler_unique_columns` and `--sampler_column_regex`
   choose the tracked cells, `--sampler_row_keys` tracks combinations of
   columns, and `--sampler_column_keys` lists values to keep first.
1. It stops adding rows for a column after that column has
   `--sampler_uniques_per_column` distinct values (default `10`; `-1` for no
   limit).
1. It adds other rows at random, at the rate `--sampler_rate`. By default the
   rate is the output size divided by the input size, so with
   `--sampler_output_rows=-1` it adds no random rows. `0` turns them off.
1. It stops when the output has `--sampler_output_rows` rows, header rows
   included (default `100`; `-1` for no limit).

Tracked cells are the cells in `--sampler_unique_columns`, or in every column if
that option isn't set. A cell is tracked only if its value matches
`--sampler_column_regex`. The default regex, `^[0-9]{4}$|[a-zA-Z-]`, matches
4-digit years and text with a letter or a hyphen. Numbers and numeric codes,
such as FIPS codes, don't match.

NOTE: The `--input_rows` option of `stat_var_processor.py` reads only the first
rows of the input. The sampler picks rows from the whole file, so the sample
includes values that appear only near the end.

## Options

| Option                         | Default                  | Use                                                                                                                                                                       |
| ------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--sampler_input`              | none                     | Input CSV file, as a local path or a `gs://` path. Use a quoted wildcard, such as `'input/*.csv'`, for several files.                                                     |
| `--sampler_output`             | none                     | Output CSV file, as a local path or a `gs://` path.                                                                                                                       |
| `--sampler_output_rows`        | `100`                    | Maximum rows in the output, header rows included. `-1` means no limit.                                                                                                    |
| `--sampler_unique_columns`     | all columns              | Comma-separated header names of the columns to track.                                                                                                                     |
| `--sampler_uniques_per_column` | `10`                     | Maximum distinct values to collect for each column. `-1` collects all of them.                                                                                            |
| `--sampler_rows_per_key`       | `5`                      | Maximum rows for each distinct value.                                                                                                                                     |
| `--sampler_rate`               | output rows ÷ input rows | Rate of extra random rows. `0` turns them off, so the same command gives the same sample. With `--sampler_output_rows=-1`, the default adds none.                         |
| `--sampler_column_regex`       | `^[0-9]{4}$\|[a-zA-Z-]`  | Only values that match are tracked. Use `'.*'` to track every value, including empty cells and numeric codes, or `.` to skip empty cells.                                 |
| `--sampler_row_keys`           | none                     | Combinations of columns to track, such as `Indicator\|Sex\|Age Group,Country`; see [One row for each StatVar](#one-row-for-each-statvar).                                 |
| `--sampler_column_keys`        | none                     | Values that must be in the sample, as `<column>:<file>` pairs; see [Include specific values](#include-specific-values).                                                   |
| `--sampler_header_rows`        | `1`                      | Number of header rows to copy. Include title lines above the column names.                                                                                                |
| `--sampler_input_delimiter`    | detected                 | Delimiter of the input file, such as `;`, `\|`, or `tab`. If set, it's used instead of the detected one; see [Files with other delimiters](#files-with-other-delimiters). |
| `--sampler_output_delimiter`   | same as the input        | Delimiter of the output file.                                                                                                                                             |
| `--sampler_input_encoding`     | `UTF8`                   | Encoding of the input file.                                                                                                                                               |

To call the sampler from Python, pass the same settings as a config dictionary
to `data_sampler.sample_csv_file()`. The keys are the flag names without `--`,
except `header_rows`, `input_delimiter`, `output_delimiter`, and
`input_encoding`, which drop the `sampler_` prefix.

## Choose the columns to track

Track the columns whose values the PV map turns into schema or places:

- **Indicator or variable columns**, such as `Indicator` or `Series name`.
- **Category columns** that map to constraint properties, such as `Sex`,
  `Age Group`, or `Race`.
- **Place columns**, with names or codes, such as `Country` or `FIPS`.
- **Date columns**, only if their formats vary, such as `2020` and `2020-Q1`.

Don't track these columns:

- **Value columns.** The default regex already skips numbers.
- **Free-text and ignored columns**, such as footnotes, notes, flags, and source
  URLs. They can have thousands of distinct values, which fill the sample with
  rows that don't test the PV map.

For a wide table, where the column headers name the variables, the header row
already covers them. Track only the label columns, such as the place column.

For example, take a 6,247-row file with these columns:

```csv
Country,M49 Code,Indicator,Sex,Age Group,Year,Value,Footnote
India,356,Population,Female,0-14,2000,536.3,Revised 375
India,356,Population,Female,15-64,2000,507.9,
Brazil,076,Literacy rate,Male,65+,2000,68.3,Estimated
```

The file has 52 countries and 8 indicators. One indicator appears only in the
last rows, and the `Footnote` column has 862 distinct values. Each command below
is a recipe in the next section:

| Command                                              | Rows | Countries | Indicators |
| ---------------------------------------------------- | ---- | --------- | ---------- |
| Defaults ([Quick sample](#quick-sample))             | 99   | 21 of 52  | 7 of 8     |
| Track the important columns, 100 rows                | 99   | 38 of 52  | 7 of 8     |
| [Every value](#every-value-of-the-important-columns) | 61   | 52 of 52  | 8 of 8     |

## Recipes

Each recipe shows the options to add to this command:

```bash
./agents/common/run_python.sh tools/statvar_importer/data_sampler.py \
  --sampler_input=<import-dir>/input/data.csv \
  --sampler_output=/tmp/sample.csv
```

The input, the output, and the `--sampler_column_keys` files can be local paths
or `gs://` paths. GCS paths need Google Cloud credentials, for example from
`gcloud auth application-default login`.

### Quick sample

Run the command without other options to get up to 100 rows for a first look at
the data. The sample can miss rare values, and footnote columns use up part of
it.

### Every value of the important columns

To test a PV map, get every value of the important columns, with one row each:

```bash
  --sampler_unique_columns="Country,Indicator,Sex,Age Group" \
  --sampler_column_regex='.*' \
  --sampler_uniques_per_column=-1 \
  --sampler_rows_per_key=1 \
  --sampler_output_rows=-1
```

`--sampler_column_regex='.*'` tracks every value in these columns, including
empty cells and values that the default regex skips, such as `65+`. Use `.`
instead to skip rows whose only new value is an empty cell. With no row limit,
the sampler adds no random rows, so the same command gives the same sample. The
sample is small because one row can bring new values for several columns. In the
example, 61 rows cover all 52 countries and 8 indicators. Run
`stat_var_processor.py` on this sample to find missing keys; see
[Test the PV map and places on a sample](advanced_processing.md#test-the-pv-map-and-places-on-a-sample).

### One row for each StatVar

The [every value](#every-value-of-the-important-columns) recipe covers each
value of each column, but not each combination. When a StatVar comes from a
combination of columns, such as `Indicator`, `Sex`, and `Age Group`, the sample
can miss some StatVars. In the example, the input has 64 combinations; the
every-value sample has only 27 of them, and its run produced 22 of the 27
StatVars in the full output.

Track the combinations with `--sampler_row_keys`. A row key is a list of columns
separated by `|`; separate several row keys with commas. The sampler keeps a row
when any row key has a combination of values that the sample doesn't have yet:

```bash
  --sampler_row_keys="Indicator|Sex|Age Group,Country" \
  --sampler_uniques_per_column=-1 \
  --sampler_rows_per_key=1 \
  --sampler_output_rows=-1
```

Here the first row key covers every StatVar, and the second, a single column,
covers every place. In the example, the sample has 104 rows with all 64
combinations and all 52 countries, and it produced the same 27 StatVars as the
full input.

To also cover every observation property for each StatVar, add a row key with
the StatVar columns and the columns that set those properties. For example, add
a `Method` column that maps to `measurementMethod`:

```bash
  --sampler_row_keys="Indicator|Sex|Age Group,Indicator|Sex|Age Group|Method,Country"
```

In a variant of the example with a `Method` column, this gave 218 rows. They
produced all 27 StatVars and all 81 combinations of StatVar and measurement
method in the full output.

Keep these points in mind:

- **Use columns with few values.** Each new combination adds a row. In the
  example, a row key with the free-text `Footnote` column instead of `Method`
  gave 2,183 rows.
- **The regex doesn't apply to row keys.** Row keys track every combination,
  including empty cells and numbers.
- **Column names must match the header** exactly, including case and spaces. If
  a row key names a column that isn't in the header rows, the sampler stops with
  `Missing row key columns in headers` and lists the missing columns. For a file
  with title lines, set `--sampler_header_rows`; see
  [Title lines above the header](#title-lines-above-the-header).
- **Only the row keys are tracked** when you don't set
  `--sampler_unique_columns`. Set both to also track single columns with the
  regex.
- **Wide tables.** When the column headers name the variables, every row already
  has all the header combinations. Use row keys only for the label columns that
  change the StatVar.

### A representative sample for a new import

When you start a new import, you don't have a PV map yet, so you don't know
which columns to track. An AI agent can read a column profile and a few rows,
and pick the columns for you. Follow these steps:

1. Make a quick sample to show the agent:

   ```bash
   ./agents/common/run_python.sh tools/statvar_importer/data_sampler.py \
     --sampler_input=<import-dir>/input_files/data.csv \
     --sampler_output=/tmp/quick_sample.csv \
     --sampler_output_rows=30
   ```

1. Profile every column of the full input. The script counts distinct values,
   filled cells, and numbers, and lists examples:

   ```bash
   python3 - <<'EOF' > /tmp/profile.txt
   import csv, re
   INPUT = '<import-dir>/input_files/data.csv'
   HEADER_ROWS = 1  # Line number of the column names.
   MAX_TRACKED = 1000  # Stop collecting distinct values after this many.
   year = re.compile(r'^(1[89]|20)\d\d$')
   number = re.compile(r'^-?[\d,]*\.?\d+$')
   with open(INPUT, encoding='utf-8', newline='') as f:
       reader = csv.reader(f)
       for _ in range(HEADER_ROWS):
           names = next(reader)
       stats = [{'values': {}, 'filled': 0, 'numeric': 0, 'years': 0,
                 'decimals': 0} for _ in names]
       rows = 0
       for row in reader:
           rows += 1
           for stat, value in zip(stats, row):
               value = value.strip()
               if not value:
                   continue
               stat['filled'] += 1
               stat['numeric'] += bool(number.match(value))
               stat['years'] += bool(year.match(value))
               stat['decimals'] += bool(number.match(value)) and '.' in value
               if len(stat['values']) < MAX_TRACKED:
                   stat['values'][value] = stat['values'].get(value, 0) + 1
   print(f'{rows} rows')
   print('column | distinct | filled | numeric | type | examples')
   for name, stat in zip(names, stats):
       filled = max(stat['filled'], 1)
       distinct = len(stat['values'])
       numeric = stat['numeric'] / filled
       if stat['years'] / filled > 0.9:
           kind = 'date'
       elif numeric > 0.9 and (stat['decimals'] or distinct >= MAX_TRACKED):
           kind = 'value'
       elif numeric > 0.9:
           kind = 'number or code'
       else:
           kind = 'text'
       examples = ', '.join(list(stat['values'])[:5])
       count = f'{MAX_TRACKED}+' if distinct >= MAX_TRACKED else distinct
       print(f'{name} | {count} | {stat["filled"] / max(rows, 1):.0%} | '
             f'{numeric:.0%} | {kind} | {examples}')
   EOF
   ```

1. Give the agent this prompt, followed by the contents of `/tmp/profile.txt`
   and `/tmp/quick_sample.csv`. Use any coding agent or Gemini. The agent sees
   the profile and the sample rows, so share only data you're allowed to share.

   ```text
   I'm starting a Data Commons import with the StatVar Processor. Below are a
   profile of each column in the input file and a sample of its rows. Classify
   each column into exactly one role:

   - place: names or codes of the places that observations are about.
   - statvar: values that change the statistical variable, such as indicator
     names and categories like sex, age group, or race.
   - svobs: values that set other observation properties, such as unit, period,
     measurement method, or scaling factor.
   - date: observation dates.
   - value: the observed numbers.
   - skip: IDs, free-text notes, and columns that don't describe the data.

   If a column has both data values and section labels, choose the role of the
   data values. Reply with only JSON that uses the exact column names:
   {"place": [], "statvar": [], "svobs": [], "date": [], "value": [], "skip": []}
   ```

   For the example file, the agent replied:

   ```json
   {"place": ["Country", "M49 Code"], "statvar": ["Indicator", "Sex", "Age Group"],
    "svobs": [], "date": ["Year"], "value": ["Value"], "skip": ["Footnote"]}
   ```

1. Review the reply, fix any wrong roles, and save it as `/tmp/roles.json`.

1. Turn the roles into row keys: one for the `statvar` columns, one for the
   `statvar` and `svobs` columns together, and one for each `place` column. Then
   sample one row for each combination:

   ```bash
   ROW_KEYS=$(python3 -c "
   import json
   roles = json.load(open('/tmp/roles.json'))
   keys = ['|'.join(roles['statvar']),
           '|'.join(roles['statvar'] + roles['svobs'])] + roles['place']
   print(','.join(dict.fromkeys(key for key in keys if key)))
   ")
   echo "$ROW_KEYS"
   ./agents/common/run_python.sh tools/statvar_importer/data_sampler.py \
     --sampler_input=<import-dir>/input_files/data.csv \
     --sampler_output=<import-dir>/test_data/<name>_input.csv \
     --sampler_header_rows=1 \
     --sampler_row_keys="$ROW_KEYS" \
     --sampler_uniques_per_column=-1 \
     --sampler_rows_per_key=1 \
     --sampler_output_rows=-1
   ```

   For the example roles, the row keys are
   `Indicator|Sex|Age Group,Country,M49 Code`. Set `--sampler_header_rows` to
   the line number of the column names.

In the example, the sample has 104 rows with all 64 combinations and all 52
countries. Once the PV map was written, the sample produced all 27 StatVars of
the full input. In the quick-start input, the sample kept the title lines and
both section label rows, because the label rows are new values of the tracked
`County` column. It produced the same 6 StatVars as the full input.

The agent can only guess which columns become observation properties before the
PV map exists. In the example, it marked `Footnote` as `skip`, but the PV map
later mapped `Estimated` to `measurementMethod`. The sample then had 36 of the
54 combinations of StatVar and measurement method. When the PV map is ready,
make the final test input with the next recipe.

### A test input that covers every StatVar

To create `test_data/<name>_input.csv` for an import, pick input rows from the
output of a full run instead of from the input columns. The sample then makes
`stat_var_processor.py` generate every StatVar in the full output, with every
combination of `unit`, `observationPeriod`, `measurementMethod`, and
`scalingFactor`. This uses the import's own PV map, so you don't need to know
which columns each property comes from. Follow these steps:

1. Copy the import's config, and add an `output_columns` row with the SVObs
   properties and the `#input` column. The last row for a setting wins:

   ```bash
   cp <import-dir>/<Import>_statvar_processor_config.csv /tmp/full_config.csv
   echo >> /tmp/full_config.csv
   echo 'output_columns,"observationAbout,observationDate,variableMeasured,value,unit,observationPeriod,measurementMethod,scalingFactor,#input"' >> /tmp/full_config.csv
   ```

1. Process the full input with the import's PV maps and the new config:

   ```bash
   ./agents/common/run_python.sh tools/statvar_importer/stat_var_processor.py \
     --input_data=<import-dir>/input_files/data.csv \
     --pv_map=<import-dir>/<import>_pvmap.csv \
     --config_file=/tmp/full_config.csv \
     --output_path=/tmp/full_output/<import> \
     --output_counters=/tmp/full_output/counters.csv
   ```

1. Keep the header rows and one input row for each combination of
   `variableMeasured` and the SVObs properties. The `#input` column of each
   output row gives the input file and line:

   ```bash
   python3 -c "
   import csv, os
   OUTPUT = '/tmp/full_output/<import>.csv'
   INPUT = '<import-dir>/input_files/data.csv'
   SAMPLE = '<import-dir>/test_data/<name>_input.csv'
   HEADER_ROWS = 1  # Lines up to and including the column names.
   KEEP_ROWS_WITHOUT_OBS = False  # True keeps section label rows.
   KEY_PROPS = ['variableMeasured', 'unit', 'observationPeriod',
                'measurementMethod', 'scalingFactor']
   seen, rows_with_obs, rows_needed = set(), set(), set()
   with open(OUTPUT, encoding='utf-8') as f:
       for row in csv.DictReader(f):
           file, line, _ = row['#input'].rsplit(':', 2)
           if os.path.basename(file) != os.path.basename(INPUT):
               continue
           rows_with_obs.add(int(line))
           key = tuple(row.get(p, '') for p in KEY_PROPS)
           if key not in seen:
               seen.add(key)
               rows_needed.add(int(line))
   with open(INPUT, encoding='utf-8', newline='') as f, \
        open(SAMPLE, 'w', encoding='utf-8', newline='') as out:
       writer = csv.writer(out)
       for line, row in enumerate(csv.reader(f), start=1):
           if (line <= HEADER_ROWS or line in rows_needed or
                   (KEEP_ROWS_WITHOUT_OBS and line not in rows_with_obs)):
               writer.writerow(row)
   print(f'{len(seen)} combinations from {len(rows_needed)} rows')
   "
   ```

1. Process the sample with the same command, with
   `--input_data=<import-dir>/test_data/<name>_input.csv`, and check that its
   output has the same StatVars and property combinations as the full output.

In the example, 54 rows reproduced all 27 StatVars and 54 combinations of the
full 6,247-row input. Keep these points in mind:

- **Section label rows.** Rows such as `Count of all Males` set properties for
  the rows below them, but produce no observations. Set
  `KEEP_ROWS_WITHOUT_OBS = True` to keep every row without observations. In the
  quick-start input, the sample without them lost `gender` from 4 StatVars, and
  the sample with them matched the full output. The option also keeps rows that
  the processor dropped or ignored, so the sample can be much larger.
- **Title lines.** Count them in `HEADER_ROWS`, for example `3` for the
  quick-start input, which has 2 title lines above the column names.
- **Several input files.** Run the script once for each file, with `INPUT` and
  `SAMPLE` set to that file. It keeps only the rows that came from `INPUT`.
- **Other properties.** Add any other property that varies, such as
  `observationAbout` for one row per place, to `output_columns` and `KEY_PROPS`.

NOTE: If the sample input or its expected output files have more than about
1,000 lines, store them with Git LFS instead of committing them as regular
files. Run `git lfs track "<import-dir>/test_data/*.csv"` from the repository
root, and commit the updated `.gitattributes` with the files. The repository
README lists Git LFS in its one-time setup.

### A few rows for each value

To check values and dates for each indicator and category, keep several rows for
each value:

```bash
  --sampler_unique_columns="Indicator,Sex,Age Group" \
  --sampler_column_regex='.*' \
  --sampler_uniques_per_column=-1 \
  --sampler_rows_per_key=3 \
  --sampler_output_rows=-1
```

In the example, this gives 25 rows with every indicator, sex, and age group.

### Numeric code columns

Codes such as FIPS or M49 codes don't match the default regex, so the sampler
doesn't track them. In the example, tracking only `M49 Code` gives an empty
sample. Add `--sampler_column_regex='.*'` to track any value:

```bash
  --sampler_unique_columns="M49 Code" \
  --sampler_column_regex='.*' \
  --sampler_uniques_per_column=-1 \
  --sampler_rows_per_key=1 \
  --sampler_output_rows=-1
```

This gives one row for each of the 52 codes. The regex applies to every tracked
column, so set `--sampler_unique_columns` too; otherwise the sampler also tracks
the value column.

### Include specific values

To make sure some values are in the sample, such as places with unusual names or
a rare indicator, list them in a CSV file. Give the file a header row, and put
the values in the first column:

```csv
Country
Côte d'Ivoire
"Congo, Dem. Rep."
Bolivia (Plurinational State of)
```

Pass one `<column>:<file>` pair for each column:

```bash
  --sampler_column_keys="Country:/tmp/must_countries.csv,Indicator:/tmp/must_indicators.csv" \
  --sampler_output_rows=-1
```

Each listed value gets up to `--sampler_rows_per_key` rows. Keep these points in
mind:

- **The row limit still applies.** In the example, the rare indicator is in the
  last rows, so it was missing from a 100-row sample. With
  `--sampler_output_rows=-1`, it was included.
- **The regex still applies.** For numeric codes, add
  `--sampler_column_regex='.*'`.
- **A `dcid:` prefix is ignored** when the sampler compares values, so you can
  list DCIDs with or without it.

### Title lines above the header

If the file starts with title lines, count them in `--sampler_header_rows`, for
example `--sampler_header_rows=2` for one title line. The names in
`--sampler_unique_columns` and `--sampler_row_keys` must appear in these header
rows. Otherwise, the sampler stops before it reads the data, with
`Missing unique columns in headers` or `Missing row key columns in headers`, and
writes no output.

### Files with other delimiters

The sampler detects the delimiter from the first rows of the file, and writes
the output with the same delimiter. It tries `,`, tab, `;`, `|`, and `:`, and
uses the first one that appears the same number of times in every row. In a
test, `;`, `|`, and tab versions of the example file gave the same 104-row
sample as the comma file.

Set the delimiter when detection can pick the wrong one. For example, in a `;`
file with decimal commas, such as `India;356;Population;536,3`, every row has
one comma, so the sampler detects `,`:

```bash
  --sampler_input_delimiter=';'
```

Use `tab` for tab-separated files, for example `--sampler_input_delimiter=tab`.
To write the output with another delimiter, set `--sampler_output_delimiter`.

### Several input files

Pass a quoted wildcard to sample several files into one output:

```bash
  --sampler_input='<import-dir>/input/*.csv'
```

The output has the header rows of the first file only, so use this for files
with the same columns. Write this output to a local file: the sampler appends
the rows of each file, and it can't append to a `gs://` file.

### All place names for place resolution

To list every place name, sample only the place column with the
[every value](#every-value-of-the-important-columns) options:

```bash
./agents/common/run_python.sh tools/statvar_importer/data_sampler.py \
  --sampler_input=<import-dir>/input/data.csv \
  --sampler_output=/tmp/places_sample.csv \
  --sampler_unique_columns=Country \
  --sampler_column_regex='.*' \
  --sampler_uniques_per_column=-1 \
  --sampler_rows_per_key=1 \
  --sampler_output_rows=-1
```

Then write the names to a `place_name` column:

```bash
python3 -c "
import csv
rows = csv.DictReader(open('/tmp/places_sample.csv', encoding='utf-8'))
names = sorted({row['Country'] for row in rows if row['Country']})
with open('/tmp/place_names.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['place_name'])
    writer.writerows([name] for name in names)
"
```

Use the list to write a places PV map, or resolve the names with
`place_resolver.py`; see the [place tools guide](../place/README.md).

## Large inputs

The sampler reads the input once, row by row, and doesn't load the file into
memory. Keep these points in mind for large files:

- **It reads the whole file without a row limit.** With
  `--sampler_output_rows=-1`, it reads every row. With a limit, it stops at the
  limit, but random rows are spread across the file, so it usually reads most of
  it anyway. In a test with 2 million rows (127 MB), the default command read
  1.8 million rows, and the every-value recipe read all of them. Both took about
  15 seconds.
- **Memory grows with the distinct values it tracks**, not with the file size.
  The every-value recipe on that file used about 110 MB.
- **Always set `--sampler_unique_columns` when you remove the limits.** Without
  it, the sampler tracks every column. A column with a different value in each
  row, such as an ID or a footnote, then selects every row. On the test file,
  the output was the whole input, and the run took twice as long and used 370
  MB.
- **GCS inputs are copied first.** The sampler downloads a `gs://` input to a
  local temporary file before it reads it. Make sure the machine has disk space
  for the whole file, and expect the download time even for a small sample.
