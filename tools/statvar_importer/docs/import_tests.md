# Import tests

An import test runs `stat_var_processor.py` with an import's PV map and config
on a small input, and compares the output with expected files in `test_data/`.
Use this guide to add a test to an import under `statvar_imports/`, or to update
a test after the PV map, the config, or the processor changes.

A passing test shows that the output is unchanged. It doesn't show that the
output is correct. Review the expected files before you commit them.

## Contents

- [Add a test](#add-a-test)
- [Update a test](#update-a-test)
- [Run the tests](#run-the-tests)
- [Test config reference](#test-config-reference)
- [Keep test data small](#keep-test-data-small)
- [Limits](#limits)

## Add a test

Run the commands from the repository root with the repository environment
active (`source .env/bin/activate`). In the commands, `<import-dir>` is the
import's folder, such as `statvar_imports/uae_bayanat/uae_population`, and
`<output>` is the file name in the import's `--output_path`, such as
`uae_population_output`.

Follow these steps. Each step ends with a check that tells you it is done:

1. **Create the test input.** Follow
   [A test input that covers every StatVar](data_sampler.md#a-test-input-that-covers-every-statvar)
   and save the sample in `<import-dir>/test_data/`. An import that runs the
   processor several times needs one input for each command. *Done when* the
   sample's output has the same StatVars and property combinations as the full
   output, and the sample meets the limit in
   [Keep test data small](#keep-test-data-small).

1. **Write the test config.** Create `<import-dir>/statvar_test_config.json`
   with one entry for each `stat_var_processor.py` command in the import's
   `manifest.json` or run script. Copy the flags of the command, with the
   changes in [Processor arguments](#processor-arguments). *Done when* every PV
   map and config file that the import passes to the processor is in an entry.

1. **Generate the expected output.** Run the test and keep its output:

   ```bash
   python3 tools/statvar_importer/stat_var_test_runner.py \
     --test_config=<import-dir>/statvar_test_config.json \
     --quiet --keep_temp_dir --test_output=/tmp/<output>_test.json
   ```

   This first run exits with code 1 and status `MISSING_EXPECTED`, because the
   expected files don't exist yet. The `temp_dir` value in
   `/tmp/<output>_test.json` is the folder with the output. Copy the output
   files into `test_data/`:

   ```bash
   cp <temp_dir>/<test_name>/output/<output>* <import-dir>/test_data/
   ```

   *Done when* every `expected_output_file` in the test config exists.

1. **Review the expected output.** Apply the
   [success checks](../README.md#check-the-results) to the files you copied.
   *Done when* every check holds.

1. **Run the test.** Run it two times, because the processor can write rows in
   a different order on each run:

   ```bash
   python3 statvar_imports/statvar_imports_test.py --test_root=<import-dir>
   ```

   *Done when* both runs print `OK` and `git status` shows only the test config
   and the files in `test_data/` as new.

## Update a test

A test fails when the output differs from the expected files. To find the
difference, run the command of step 3 in [Add a test](#add-a-test) and read
`/tmp/<output>_test.json`. Each output has a `diff_status` from
[Diff status](#diff-status) and a `diff_sample`. The full difference is in
`<temp_dir>/<test_name>/output/<output_name>.diff`.

Then take one of these actions:

- **You intended the change.** Repeat steps 3 to 5 of
  [Add a test](#add-a-test), and review the difference in the expected files
  with `git diff` before you commit them.
- **You didn't intend the change.** Fix the PV map, the config, or the code
  until the test passes with the expected files unchanged.

## Run the tests

Use the command for the task:

| Task                                    | Command                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Run one test config and show its log    | `python3 tools/statvar_importer/stat_var_test_runner.py --test_config=<import-dir>/statvar_test_config.json` |
| Run the tests of one import or folder   | `python3 statvar_imports/statvar_imports_test.py --test_root=<dir>`                                          |
| Run the tests of all imports            | `./run_tests.sh -p statvar_imports/`                                                                         |

`statvar_imports_test.py` runs every `statvar_test_config*.json` under the
folder, each in its own process. It also fails a test that leaves new files in
the import folder.

`stat_var_test_runner.py` exits with code 0 only when every output matches. It
has these options:

- `--quiet` hides the processor's log.
- `--keep_temp_dir` keeps the output, the counters, and the processor's logs
  after the run, and prints the folder.
- `--test_output=<file>` saves the result as JSON.

## Test config reference

The test config is a JSON list with one entry for each processor command. Name
the file `statvar_test_config.json`. For a second config in the same folder,
add a suffix, such as `statvar_test_config_states.json`.

This example is from
[`uae_population`](../../../statvar_imports/uae_bayanat/uae_population/statvar_test_config.json),
with an entry added for the StatVar MCF:

```json
[
  {
    "test_name": "Test_UAE_population",
    "statvar_processor_args": {
      "pv_map": "uae_population_pvmap.csv",
      "config_file": "uae_population_metadata.csv",
      "places_resolved_csv": "uae_population_places_resolved_csv.csv",
      "input_data": "test_data/uae_populationbyemiratesnationalityandgender.xlsx",
      "output_path": "output/uae_population_output"
    },
    "statvar_processor_outputs": [
      {
        "output_name": "UAE_population_output_csv",
        "output_file": "output/uae_population_output.csv",
        "expected_output_file": "test_data/uae_population_output.csv",
        "diff_config": {
          "fingerprint_dcid": 1
        }
      },
      {
        "output_name": "UAE_population_output_tmcf",
        "output_file": "output/uae_population_output.tmcf",
        "expected_output_file": "test_data/uae_population_output.tmcf"
      },
      {
        "output_name": "UAE_population_output_stat_vars",
        "output_file": "output/uae_population_output_stat_vars.mcf",
        "expected_output_file": "test_data/uae_population_output_stat_vars.mcf"
      }
    ]
  }
]
```

Each entry has these keys:

| Key                         | Required | Use                                                                                                                   |
| --------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------- |
| `test_name`                 | Yes      | Name of the test and of its output folder. Use letters, digits, and underscores.                                      |
| `statvar_processor_args`    | Yes      | Command line flags of the processor; see [Processor arguments](#processor-arguments).                                 |
| `statvar_processor_outputs` | Yes      | Output files to compare; see [Outputs](#outputs).                                                                     |
| `statvar_processor_config`  | No       | Processor settings that replace the test defaults; see [Processor settings for tests](#processor-settings-for-tests). |
| `expected_error_counters`   | No       | Error counters that the test allows; see [Error counters](#error-counters).                                           |
| `env_file`                  | No       | File with environment variables for the processor.                                                                    |

### Processor arguments

`statvar_processor_args` maps each processor flag to its value, without the
leading `--`. The test runs the processor in the import folder, so write paths
relative to that folder. Copy the flags from the import's command, with these
changes:

- **`input_data`.** Use the test input in `test_data/`. An Excel file works.
  The test writes the CSV files converted from it outside the import folder.
- **`output_path`.** Keep the relative value of the import's command, such as
  `output/<output>`. The test writes the output to a temporary folder. It uses
  an absolute path or a `gs://` path as given, so keep the path relative.
- **`existing_statvar_mcf`.** Leave out a `gs://` path. A test reads only
  files in the repository.
- **`output_counters`.** Leave it out. The test saves the counters in the
  temporary folder.

Keep every other flag, such as `pv_map`, `config_file`, `places_resolved_csv`,
and `statvar_dcid_remap_csv`.

### Outputs

Each item of `statvar_processor_outputs` compares one output file with its
expected file:

| Key                    | Use                                                                                         |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| `output_name`          | Name of the comparison in the result.                                                       |
| `output_file`          | File that the processor writes, as the `output_path` value followed by the file's ending.   |
| `expected_output_file` | Expected file in `test_data/`.                                                              |
| `diff_config`          | Settings for the comparison.                                                                |

Compare the CSV, the TMCF, and the StatVar MCF. The comparison reads each file
as a set of nodes and ignores the order of nodes and properties.

Set `"fingerprint_dcid": 1` in the `diff_config` of a CSV output. The
comparison then pairs each row with the expected row that has the same
properties other than `value`. Without the setting, it pairs rows by row
number, and the test fails when the row order changes.

To ignore a property, list it in `"ignore_property"`. `diff_mcf_files()` in
[`mcf_diff.py`](../mcf_diff.py) lists the other settings.

### Diff status

The result of a comparison has one of these statuses, or several joined with
`|`, such as `ADDED|DELETED`:

| Status             | Meaning                                                           |
| ------------------ | ----------------------------------------------------------------- |
| `MATCHED`          | The output is the same as the expected file.                      |
| `ADDED`            | The output has nodes that the expected file doesn't have.         |
| `DELETED`          | The expected file has nodes that the output doesn't have.         |
| `MODIFIED`         | A node has different properties, such as a different `value`.     |
| `MISSING_EXPECTED` | The expected file doesn't exist.                                  |
| `MISSING_ACTUAL`   | The processor didn't write the output file.                       |

A test passes only when every output is `MATCHED`.

### Error counters

The processor counts problems that it continues past in counters named
`error-*`, such as `error-unresolved-place`. A test fails when a run has an
error counter above 0, even if every output matches. The result lists the
counters in `error_counters`.

Fix the PV map or the config to remove the error. If the import produces the
error on purpose, list the counter in `expected_error_counters` of the entry,
without the stage prefix that the counters file adds:

```json
"expected_error_counters": ["error-unresolved-place"]
```

### Processor settings for tests

A test runs the processor without lookups in the Data Commons API, so that the
result is the same on every run. The test sets these processor settings to
false, whatever the import's config file has:

| Setting                    | Effect of false in a test                                                         |
| -------------------------- | --------------------------------------------------------------------------------- |
| `reconcile_nodes`          | Keeps generated nodes as they are, without a schema lookup.                       |
| `recon_lookup_api`         | Skips the API lookup for replaced schema.                                         |
| `resolve_places`           | Resolves places only with the import's `places_resolved_csv`.                     |
| `output_only_new_statvars` | Writes every generated StatVar to `_stat_vars.mcf`, without an API lookup.        |
| `generate_schema_mcf`      | Writes no schema MCF.                                                             |

The test also removes `DC_API_KEY` and `MAPS_API_KEY` from the processor's
environment. The processor then leaves a place that isn't in
`places_resolved_csv` unresolved.

To turn a setting back on for one test, set it in `statvar_processor_config`:

```json
"statvar_processor_config": {
  "reconcile_nodes": true
}
```

A test with a setting turned on depends on the network and on the data in the
API. Turn a setting on only when the import's output is wrong without it.

## Keep test data small

Keep each file in `test_data/` under about 1,000 lines. Most existing test
inputs have about 100 lines or fewer.

If the sample that covers every StatVar is larger, split the import's commands
into separate entries, each with its own input. If a file is still larger, say
why in the pull request.

Commit test files as regular Git files. The repository stores other large files
with Git LFS, and nobody has checked that the CI checkout fetches them.

## Limits

- **Location.** `statvar_imports_test.py` finds test configs only under
  `statvar_imports/`.
- **Expected files.** No command rewrites the expected files. Repeat steps 3 to
  5 of [Add a test](#add-a-test).
- **Counters.** A test fails on an error counter; see
  [Error counters](#error-counters). It doesn't check other counters, such as
  `dropped-*` and `warning-*`, so read `statvar_counters.csv` in the temporary
  folder when you review the output.
- **Existing StatVars.** Without `existing_statvar_mcf`, the test output may
  have generated dcids for StatVars that the production run reuses.
- **API lookups.** The settings in
  [Processor settings for tests](#processor-settings-for-tests) were checked on
  one import. If a test fails with `429 Too Many Requests` or a network error,
  the processor reached a lookup that those settings don't turn off. Report the
  lookup instead of adding an API key.
