# Strategy for Generating Property-Value (PV) Maps

This document outlines the strategy for mapping UN Data files to Data Commons Property-Value (DCPV) pairs using the reviewed codelists and specialized metadata dictionaries.

## 1. Core Mapping Logic

To avoid ambiguity, we use a **"Concept:Code"** notation as the primary key for all mappings.
- **Concept**: The ID of the dimension or attribute (e.g., `AGE`, `SEX`).
- **Code**: The specific value found in the data file (e.g., `Y15T19`, `F`). 

## 2. Per-File Metadata Dictionaries

For each data file in `undata/data/`, a corresponding metadata dictionary has been generated in `undata/metadata/{filename}_metadata.csv`. 

### Format of `{filename}_metadata.csv`:
- `column_name`: The data column header.
- `value`: The unique code found in that column.
- `dc_pv_pair`: The mapped Data Commons property-value string.

## 3. Automation Script

The script `undata/generate_metadata.py` automates the creation of these dictionaries by:
1. Pre-loading master codelists from `undata/cl_reviewed/`.
2. Scanning data files in `undata/data/` for unique values.
3. Exporting a targeted CSV for each data file.

## 4. Integration with Agentic Import

When invoking `pvmap_generator.py`, use the following command structure:

```bash
python tools/agentic_import/pvmap_generator.py \
  --input_data="undata/data/DATA_FILE.csv" \
  --input_metadata="undata/metadata/DATA_FILE_metadata.csv" \
  --output_path="output/DATA_FILE"
```

## 5. Workflow

1. **Step 1**: Run `python3 undata/generate_metadata.py`.
2. **Step 2**: Process files one-by-one using `pvmap_generator.py`, passing the corresponding `_metadata.csv` file.
3. **Step 3**: The resulting `pvmap.csv` will be generated with 100% accuracy relative to the reviewed codelists.
