# SDMX Enrichment Tools

This folder contains three standalone tools for SDMX metadata enrichment.
Each tool supports CLI usage and can be called programmatically.

## 1) metadata_enricher_find.py
Selects which SDMX codes/concepts need enrichment and generates
`enrichment_query` values using full dataset context.

CLI usage:
```
python tools/agentic_import/sdmx/metadata_enricher_find.py \
  --input_metadata_json="/path/to/metadata.json" \
  --dataset_prefix="oecd_prices" \
  --output_path="/path/to/items_to_enrich.json" \
  --gemini_cli="gemini" \
  --enable_sandboxing
```

Output:
- A pruned JSON that preserves the original structure but keeps only selected
  items with `enrichment_query`. Name/description fields are omitted.

## 2) metadata_enricher_fetch.py
Uses Gemini CLI web search to populate `enriched_description` for each selected
item.

CLI usage:
```
python tools/agentic_import/sdmx/metadata_enricher_fetch.py \
  --input_items_json="/path/to/items_to_enrich.json" \
  --dataset_prefix="oecd_prices" \
  --output_path="/path/to/enriched_items.json" \
  --gemini_cli="gemini" \
  --enable_sandboxing
```

Output:
- A pruned JSON in the same structure as the input, with `enriched_description`
  added and `enrichment_query` removed.

## 3) metadata_enricher_merge.py
Merges `enriched_description` into the base metadata JSON.

CLI usage:
```
python tools/agentic_import/sdmx/metadata_enricher_merge.py \
  --input_metadata_json="/path/to/metadata.json" \
  --input_enriched_items_json="/path/to/enriched_items.json" \
  --output_path="/path/to/metadata_enriched.json"
```

Output:
- A full metadata JSON with `enriched_description` merged into the matching
  codes and concepts.
