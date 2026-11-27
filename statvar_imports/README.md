# StatVar imports

This folder has the imports that use the
[StatVar processor](../tools/statvar_importer/README.md) to convert source data
into Data Commons StatisticalVariables and observations. An import here is a PV
map and config files for the processor, with a script to download or prepare
the source data if the import needs one. Imports with their own conversion code
are in [`scripts/`](../scripts/README.md).

## Folder layout

Each import has a folder, `<source>/` or `<source>/<import>/` for a source with
several imports. An import folder has these files:

| File                                    | Use                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `manifest.json`                         | Scripts, input and output files, and schedule for automated refresh.                              |
| `<import>_pvmap.csv`                    | PV map from text in the source data to schema properties and values.                              |
| `<import>_statvar_processor_config.csv` | Settings for the processor. Existing imports name this file `*_metadata.csv`.                     |
| `*_places_resolved.csv`                 | Place names and their dcids, for an import that resolves places.                                  |
| Download or run script                  | Fetches or prepares the source data, or runs the processor several times.                         |
| `test_data/`                            | A small input and its expected output.                                                            |
| `statvar_test_config.json`              | Test of the import with the files in `test_data/`.                                                |
| `README.md`                             | Source, license, and how to refresh the import.                                                   |

## Create an import

Follow the [quick reference](../tools/statvar_importer/README.md#quick-reference)
of the StatVar processor guide. In brief:

1. Write the PV map and the config for the source data.
1. Run the processor on a sample, and check the counters and the output.
1. Add the processor command to `manifest.json`; see
   [Add the processor to an import](../tools/statvar_importer/README.md#add-the-processor-to-an-import).
1. Add a test, as described in [Test an import](#test-an-import).

## Test an import

An import test runs the processor on the input in `test_data/` and compares the
output with the expected files. It fails when the output changes or the
processor counts an error. Follow
[Import tests](../tools/statvar_importer/docs/import_tests.md) to create the
test input, the expected output, and `statvar_test_config.json`.

Run the tests from the repository root with the repository environment active:

| Task                                  | Command                                                                |
| ------------------------------------- | ---------------------------------------------------------------------- |
| Run the test of one import or folder  | `python3 statvar_imports/statvar_imports_test.py --test_root=<dir>`    |
| Run all tests in this folder          | `./run_tests.sh -p statvar_imports/`                                   |

[`statvar_imports_test.py`](statvar_imports_test.py) runs the test of every
import with a `statvar_test_config*.json`. The second command also runs the
other `*_test.py` files in this folder, such as tests of download scripts.

## Related docs

| Task                                            | Where                                                                                           |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Write a PV map and a config, run the processor  | [StatVar processor](../tools/statvar_importer/README.md)                                        |
| PV map reference                                | [PV map guide](../tools/statvar_importer/docs/pv_map.md)                                        |
| Make a small test input                         | [Data sampler](../tools/statvar_importer/docs/data_sampler.md)                                  |
| Add or update an import test                    | [Import tests](../tools/statvar_importer/docs/import_tests.md)                                  |
| A run produced fewer rows than expected         | [Troubleshooting](../tools/statvar_importer/docs/troubleshooting.md)                            |
| Fields of `manifest.json`                       | [Manifest reference](../agents/common/references/import-automation/manifest.md)                 |
| Automated refresh of imports                    | [Import automation](../import-automation/README.md)                                             |
| Validation rules for each refresh               | [Import validation](../tools/import_validation/README.md)                                       |
| Generate a PV map automatically                 | [tools/agentic_import](https://github.com/datacommonsorg/data/tree/master/tools/agentic_import) |
| Data model, MCF format, and import workflow     | [Docs](../docs/README.md)                                                                       |
| Review an import change before a pull request   | [dc-import-code-review skill](../agents/skills/dc-import-code-review/SKILL.md)                  |
| Diagnose a failed or changed refresh            | [dc-import-diagnostics skill](../agents/skills/dc-import-diagnostics/SKILL.md)                  |
