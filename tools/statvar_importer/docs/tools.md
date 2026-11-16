# Tools

These helper scripts support the StatVar Processor. You don't need them for
basic processing. Run them from the repository root with
`./agents/common/run_python.sh <script> <flags>` after `./run_tests.sh -r`. Each
script's docstring has its full usage; run it with `--helpfull` to list every
flag.

Some of them already run inside `stat_var_processor.py`: schema reconciliation,
spell checks, schema generation, and place resolution.

## Utilities

Scripts in `tools/statvar_importer/`:

| Tool                      | When to use it                                                                                                                                                                  | Minimal command                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `mcf_file_util.py`        | Merge MCF files, for example from [parallel shards](advanced_processing.md#process-large-inputs-in-parallel), or convert MCF to CSV for inspection (`--output_mcf=<file>.csv`). | `--input_mcf='tmp_output/*_stat_vars.mcf' --output_mcf=output/<import>_stat_vars.mcf`        |
| `mcf_diff.py`             | Compare two MCF files, for example `_stat_vars.mcf` before and after a refresh.                                                                                                 | `--mcf1=old.mcf --mcf2=new.mcf`                                                              |
| `data_sampler.py`         | Make a small, representative sample of a large input for test runs. See the [data sampler guide](data_sampler.md).                                                              | `--sampler_input=data.csv --sampler_output=sample.csv`                                       |
| `mcf_filter.py`           | Remove MCF nodes that already exist in Data Commons or in another MCF file.                                                                                                     | `--input_mcf=new.mcf --ignore_existing_nodes --output_mcf=filtered.mcf`                      |
| `filter_data_outliers.py` | Remove outlier observations from an output CSV.                                                                                                                                 | `--filter_data_input=output.csv --filter_data_output=filtered.csv --filter_data_min_value=0` |
| `process_spreadsheet.py`  | Process data and configs kept in Google Sheets. Needs `gspread` credentials.                                                                                                    | `--input_sheet=<sheet-url> --output_prefix=<prefix> --credentials=<credentials.json>`        |
| `json_to_csv.py`          | Convert a JSON file to CSV before processing.                                                                                                                                   | `--input_json=data.json --csv_output=data.csv`                                               |

## Schema tools

Scripts in `tools/statvar_importer/schema/` find existing schema for source
labels, draft PV maps, generate StatVar names, and check or reconcile MCF nodes.
See the [schema tools guide](../schema/README.md) for the list and usage.

## Place tools

Scripts in `tools/statvar_importer/place/`. See the
[place tools guide](../place/README.md) for usage.

| Tool                     | When to use it                                                         | Minimal command                                                                                                       |
| ------------------------ | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `place_resolver.py`      | Resolve many place names to DCIDs with the Data Commons and Maps APIs. | `--resolve_input_csv=names.csv --resolve_output_csv=resolved.csv --place_resolver_cache=<import>_places_resolved.csv` |
| `place_name_matcher.py`  | Match place names offline against a CSV of known places.               | `--place_csv=places.csv --lookup_names="Kings County"`                                                                |
| `wiki_place_resolver.py` | Find Wikidata IDs for place names with Google Custom Search.           | `--wiki_place_input_csv=names.csv --wiki_place_output_csv=wiki.csv --custom_search_key=<key>`                         |
