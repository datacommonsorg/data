# SDMX Metadata Enrichment Pipeline

The enrichment process is organized into three distinct steps: Discovery, Fetching, and Integration.

---

## Step 1: Discovery (`metadata_enricher_find.py`)

**Role**: Analyzes the base SDMX metadata using Gemini CLI to identify codes and concepts that require enrichment. It generates context-aware search queries (`enrichment_query`) for these items while preserving the original dataset structure.

**Command**:
```bash
python tools/agentic_import/sdmx/metadata_enricher_find.py \
  --input_metadata_json="/path/to/metadata.json" \
  --dataset_prefix="oecd_prices" \
  --output_path="/path/to/items_to_enrich.json" \
  --gemini_cli="gemini" \
  --enable_sandboxing
```

**Input**:
- Base SDMX `metadata.json` file.

**Output**:
- `items_to_enrich.json`: A pruned JSON structure containing only selected items with their generated `enrichment_query`.

---

## Step 2: Fetching (`metadata_enricher_fetch.py`)

**Role**: Orchestrates external web searches (via Gemini CLI) to populate detailed descriptions (`enriched_description`) for the items identified in the previous step.

**Command**:
```bash
python tools/agentic_import/sdmx/metadata_enricher_fetch.py \
  --input_items_json="/path/to/items_to_enrich.json" \
  --dataset_prefix="oecd_prices" \
  --output_path="/path/to/enriched_items.json" \
  --gemini_cli="gemini" \
  --enable_sandboxing
```

**Input**:
- `items_to_enrich.json` (from Step 1).

**Output**:
- `enriched_items.json`: A pruned JSON structure with `enriched_description` added for each item.

---

## Step 3: Integration (`metadata_enricher_merge.py`)

**Role**: Merges the fetched descriptions back into the original SDMX metadata JSON, resulting in a complete, enriched metadata file.

**Command**:
```bash
python tools/agentic_import/sdmx/metadata_enricher_merge.py \
  --input_metadata_json="/path/to/metadata.json" \
  --input_enriched_items_json="/path/to/enriched_items.json" \
  --output_path="/path/to/metadata_enriched.json"
```

**Input**:
- Base SDMX `metadata.json`.
- `enriched_items.json` (from Step 2).

**Output**:
- `metadata_enriched.json`: The final, full metadata JSON with `enriched_description` fields merged into the matching codes and concepts.

---

## Full Pipeline Example

To run the entire enrichment pipeline for a dataset:

```bash
# 1. Discover items to enrich
python tools/agentic_import/sdmx/metadata_enricher_find.py \
  --input_metadata_json="metadata.json" \
  --dataset_prefix="my_dataset" \
  --output_path="items_to_enrich.json"

# 2. Fetch enriched descriptions
python tools/agentic_import/sdmx/metadata_enricher_fetch.py \
  --input_items_json="items_to_enrich.json" \
  --dataset_prefix="my_dataset" \
  --output_path="enriched_items.json"

# 3. Merge results into the original metadata
python tools/agentic_import/sdmx/metadata_enricher_merge.py \
  --input_metadata_json="metadata.json" \
  --input_enriched_items_json="enriched_items.json" \
  --output_path="metadata_enriched.json"
```
