# Tools

These helper scripts support the StatVar Processor. You don't need them for
basic processing. Run them from the repository root with
`./agents/common/run_python.sh <script> <flags>` after `./run_tests.sh -r`. Each
script's docstring has its full usage; run it with `--helpfull` to list every
flag.

Some of them already run inside `stat_var_processor.py`: schema reconciliation,
spell checks, schema generation, and place resolution.

## Schema tools

Scripts in `tools/statvar_importer/schema/`:

| Tool                            | When to use it                                                                                                                                                          | Minimal command                                                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `schema_matcher.py`             | Find existing properties and values for source labels while you write a PV map by hand.                                                                                 | `--input_file=labels.txt --schema_matcher_mcf=<schema>.mcf --schema_output_csv=matches.csv`                                    |
| `data_annotator.py`             | Draft a PV map for a CSV, optionally with Gemini. Sends data to the Gemini API when `--llm_data_annotation` is on.                                                      | `--data_annotator_input=data.csv --annotator_output_pv_map=draft_pvmap.csv --google_api_key=<key>`                             |
| `llm_pvmap_generator.py`        | Draft PV map rows for a list of strings with Gemini. Sends the strings to the Gemini API.                                                                               | `--llm_pvmap_input=strings.csv --llm_pvmap_output=draft_pvmap.csv --google_api_key=<key>`                                      |
| `llm_statvar_name_generator.py` | Generate readable StatVar names with Gemini. Sends the StatVar definitions to the Gemini API. See the [tip](#tip-generate-readable-statvar-names) for the full command. | `--llm_statvar_input=output/<import>_stat_vars.mcf --llm_statvar_output=/tmp/<import>_stat_vars_named.mcf --llm_api_key=<key>` |
| `schema_generator.py`           | Generate schema nodes for new properties and enum values used in an MCF file.                                                                                           | `--input_nodes=<statvars>.mcf --schema_mcf=<schema>.mcf --generated_mcf=new_schema.mcf`                                        |
| `schema_checker.py`             | Check names, descriptions, and URLs in MCF nodes.                                                                                                                       | `--schema_input_mcf=<file>.mcf --schema_check_output=errors.csv`                                                               |
| `schema_spell_checker.py`       | Spell-check MCF nodes.                                                                                                                                                  | `--spell_input_mcf=<file>.mcf --spell_error_output=errors.csv`                                                                 |
| `schema_reconciler.py`          | Replace superseded nodes with their successors.                                                                                                                         | `--recon_input=<file>.mcf --recon_output=reconciled.mcf`                                                                       |
| `schema_resolver.py`            | Look up schema nodes by their properties.                                                                                                                               | `--input_schema_mcf=<schema>.mcf --resolve_mcf=<nodes>.mcf --resolve_output_path=resolved.mcf`                                 |
| `genai_helper.py`               | Run a Gemini prompt from the command line.                                                                                                                              | `--genai_input=prompt.txt --genai_output=response.txt --genai_api_key=<key>`                                                   |

For end-to-end automated PV map generation, see
[tools/agentic_import](../../agentic_import/README.md).

### Tip: generate readable StatVar names

Generated StatVars have DCIDs but often no readable `name`. After processing,
generate names, review them, and replace the original file:

```bash
PYTHONPATH=util:tools/statvar_importer \
./agents/common/run_python.sh tools/statvar_importer/schema/llm_statvar_name_generator.py \
  --llm_statvar_input=<import-dir>/output/<import>_stat_vars.mcf \
  --llm_statvar_output=/tmp/<import>_stat_vars_named.mcf \
  --llm_api_key=<gemini-api-key>
```

This script needs `util/` and `tools/statvar_importer/` on `PYTHONPATH`, as
shown. The tool sends the StatVar definitions to the Gemini API. To generate
names during processing instead, pass `--llm_generate_statvar_name` with
`--google_genai_key=<key>` to `stat_var_processor.py`.

## Place tools

Scripts in `tools/statvar_importer/place/`. See the
[place tools guide](../place/README.md) for usage.

| Tool                     | When to use it                                                         | Minimal command                                                                                                       |
| ------------------------ | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `place_resolver.py`      | Resolve many place names to DCIDs with the Data Commons and Maps APIs. | `--resolve_input_csv=names.csv --resolve_output_csv=resolved.csv --place_resolver_cache=<import>_places_resolved.csv` |
| `place_name_matcher.py`  | Match place names offline against a CSV of known places.               | `--place_csv=places.csv --lookup_names="Kings County"`                                                                |
| `wiki_place_resolver.py` | Find Wikidata IDs for place names with Google Custom Search.           | `--wiki_place_input_csv=names.csv --wiki_place_output_csv=wiki.csv --custom_search_key=<key>`                         |

## Utilities

Scripts in `tools/statvar_importer/`:

| Tool                      | When to use it                                                                                                                                                                  | Minimal command                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `mcf_file_util.py`        | Merge MCF files, for example from [parallel shards](advanced_processing.md#process-large-inputs-in-parallel), or convert MCF to CSV for inspection (`--output_mcf=<file>.csv`). | `--input_mcf='tmp_output/*_stat_vars.mcf' --output_mcf=output/<import>_stat_vars.mcf`        |
| `mcf_diff.py`             | Compare two MCF files, for example `_stat_vars.mcf` before and after a refresh.                                                                                                 | `--mcf1=old.mcf --mcf2=new.mcf`                                                              |
| `data_sampler.py`         | Make a small, representative sample of a large input for test runs.                                                                                                             | `--sampler_input=data.csv --sampler_output=sample.csv`                                       |
| `mcf_filter.py`           | Remove MCF nodes that already exist in Data Commons or in another MCF file.                                                                                                     | `--input_mcf=new.mcf --ignore_existing_nodes --output_mcf=filtered.mcf`                      |
| `filter_data_outliers.py` | Remove outlier observations from an output CSV.                                                                                                                                 | `--filter_data_input=output.csv --filter_data_output=filtered.csv --filter_data_min_value=0` |
| `process_spreadsheet.py`  | Process data and configs kept in Google Sheets. Needs `gspread` credentials.                                                                                                    | `--input_sheet=<sheet-url> --output_prefix=<prefix> --credentials=<credentials.json>`        |
| `json_to_csv.py`          | Convert a JSON file to CSV before processing.                                                                                                                                   | `--input_json=data.json --csv_output=data.csv`                                               |
