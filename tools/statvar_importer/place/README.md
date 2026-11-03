# Place tools

Use these tools to resolve many place names to Data Commons DCIDs. For most
imports, a hand-written places PV map is simpler; see
[Map places](../README.md#map-places).

## Resolve place names

Give the processor a reviewed CSV of place names and DCIDs with
`--places_resolved_csv`. You can write the file by hand or generate it with
`place_resolver.py`.

### Use a reviewed places file

The file needs a `place_name` column with the names exactly as they appear in
the source and a `dcid` column:

```csv
place_name,dcid
Kings County CA,geoId/06031
Orange County CA,geoId/06059
```

Map the place column to `observationAbout,{Data}` in the PV map and pass the
file:

```bash
--places_resolved_csv=<import>_places_resolved.csv
```

The processor replaces each place name with its DCID without calling an API.
List the file in the manifest's `source_files`.

WARNING: Make sure no PV map key matches text inside the place names. For
example, the key `county` matches inside `Kings County CA` and stops the name
from resolving. Use a specific key, such as `county name`.

### Generate the file with `place_resolver.py`

WARNING: In testing, `place_resolver.py` resolved no names, even with a valid
API key and with `--resolve_api_url=https://api.datacommons.org/v2/resolve` (the
default is the `autopush` endpoint). Check the output, and fall back to a
hand-written places PV map if names come back empty.

To look up DCIDs for many names, generate the file and review it:

1. Create a CSV with the names in a `place_name` column. Quote names that
   contain commas:

   ```csv
   place_name
   "Kings County, CA"
   "Orange County, CA"
   ```

1. Resolve the names. Run from the repository root:

   ```bash
   ./agents/common/run_python.sh tools/statvar_importer/place/place_resolver.py \
     --resolve_input_csv=<import-dir>/place_names.csv \
     --resolve_output_csv=/tmp/places_output.csv \
     --place_resolver_cache=<import-dir>/<import>_places_resolved.csv \
     --place_names_within=country/USA \
     --place_types=County
   ```

   The tool needs a Data Commons API key in `DC_API_KEY` (or
   `--resolve_api_key`); without one, it resolves nothing.
   `--place_names_within` and `--place_types` narrow the matches.

1. Review `<import>_places_resolved.csv` and fix wrong DCIDs by hand. Check
   candidates in the output CSV, which can list more than one DCID per name.

1. Pass the reviewed file with `--places_resolved_csv`, as described above.

You can also copy reviewed rows into the places PV map as
`<name>,observationAbout,<dcid>`.

## Advanced options

### Resolution inside the processor

The processor resolves place names itself when one of these settings is set:
`places_resolved_csv`, `places_csv`, `dc_api_key`, or `maps_api_key`. Narrow the
matches with these config settings:

| Setting         | Purpose                                                      |
| --------------- | ------------------------------------------------------------ |
| `places_within` | Only places within these DCIDs, such as `country/IND`.       |
| `place_type`    | Only these place types, such as `State,AdministrativeArea1`. |

NOTE: The `DC_API_KEY` environment variable sets `dc_api_key`, so it turns on
automatic place resolution even without other settings. Review new names in the
counters and in the output.

### Lookup services

`place_resolver.py` tries these sources in order:

1. The cache file (`--place_resolver_cache`, the same file as
   `--places_resolved_csv`).
1. The Data Commons resolve API (`--resolve_api_key`, default `DC_API_KEY`).
1. The Google Maps Places API (`--maps_key`, default `MAPS_API_KEY`).

For Wikidata IDs, use `wiki_place_resolver.py` (below).

### Offline name matching

`place_name_matcher.py` matches names against a CSV of known places with partial
and fuzzy matching, without API calls:

```bash
./agents/common/run_python.sh tools/statvar_importer/place/place_name_matcher.py \
  --place_csv=places.csv --lookup_names="Kings County"
```

The places CSV needs `dcid` and `name` columns. The script's docstring shows a
BigQuery export of all Data Commons places.

### Wikidata IDs

`wiki_place_resolver.py` finds Wikidata IDs for names with Google Custom Search:

```bash
./agents/common/run_python.sh tools/statvar_importer/place/wiki_place_resolver.py \
  --wiki_place_input_csv=names.csv --wiki_place_output_csv=wiki.csv \
  --custom_search_key=<key>
```

### Flag names across tools

The tools use different flag names for the same setting:

| Setting              | `stat_var_processor.py` | `place_resolver.py`      |
| -------------------- | ----------------------- | ------------------------ |
| Resolved names file  | `--places_resolved_csv` | `--place_resolver_cache` |
| Known places file    | `--places_csv`          | `--place_names_csv`      |
| Places within        | `--places_within`       | `--place_names_within`   |
| Place types          | `--place_type`          | `--place_types`          |
| Maps API key         | `--maps_api_key`        | `--maps_key`             |
| Data Commons API key | `--dc_api_key`          | `--resolve_api_key`      |
