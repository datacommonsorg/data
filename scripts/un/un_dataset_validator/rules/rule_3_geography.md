# Rule 3: GEOGRAPHY Mapping to `observationAbout`

## 1. Rule Description
* **Core Rule (3):** The geographical identifiers found in the input dataset's geography columns must be mapped to the `observationAbout` column in the generated output `.csv` file. This mapping is performed using a central Property-Value (PV) map.
* **Sub-rule (3.1):** Any place in the input geography column that represents a geographical entity at the "Country" level or above (e.g., continents, global regions, Earth) *must* be successfully resolved to a Data Commons identifier (DCID). If it cannot be resolved, this failure must be explicitly recorded.

## 2. Files Involved
* **Input Dataset:** The raw data containing a geography column (e.g., `REF_AREA` or `geo`).
* **Geography PV Map:** `/all_data/pvmap/un_geography_pvmap.csv`. This file acts as the dictionary, translating UN geographical codes to valid DCIDs for output creation.
* **Event Geography CSV:** `/all_data/un_geography.csv`. According to the implementation meeting notes, this file should be referred to for the full geographical hierarchy to determine if a missing/unresolved geography code represents a country-level or higher entity.
* **Output CSV File:** The generated data file (e.g., `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`), which must contain the `observationAbout` column.

## 3. Concrete Example (SDG Dataset)
* **Input Dataset:** A row in the input CSV has a geography code: `G00000020`.
* **PV Map Lookup:** The script looks up `GEOGRAPHY:G00000020` in `un_geography_pvmap.csv` and finds the mapping to the DCID `dcid:country/AFG`.
* **Output Check:** In the corresponding row of the generated `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`, the `observationAbout` column must contain the value `dcid:country/AFG`.

## 4. Validation Logic & Flow
1. **Load the References:** 
   * Read `un_geography_pvmap.csv` into a Python dictionary to know the expected resolved DCIDs.
   * Read `un_geography.csv` into a dictionary/dataframe to understand the geography names and their hierarchy levels (to identify if a code is a country, continent, etc.).
2. **Identify Target Columns:** 
   * Locate the geography column in the input CSV.
   * Locate the `observationAbout` column in the output CSV.
3. **Iterate and Compare:** 
   * Read the geography code from the input row.
   * Format it to match the PV map key (e.g., prepend `GEOGRAPHY:`).
   * Lookup the expected DCID in the PV map.
   * Verify that the actual value in the output CSV's `observationAbout` column matches the expected DCID.
4. **Handle Unresolved Geographies (Rule 3.1):** 
   * If a geography code is *not* found in the PV map (or maps to an `#ignore` / unmapped place), it is unresolved.
   * Look up this unresolved code in the `un_geography.csv` file. 
   * If the entity represents a country-level or higher place (e.g., 'Earth', 'Asia', 'Country'), record the code and its name to an explicit error log (e.g., `missing_national_geographies.log`).

## 5. Python Implementation Strategy

```python
import pandas as pd

def validate_rule_3(input_csv_path: str, output_csv_path: str, pv_map_path: str, un_geo_csv_path: str, geo_input_col_name: str = 'geo') -> dict:
    """
    Validates Rule 3 & 3.1: Geography mapping and logging unresolved national/higher entities.
    """
    # 1. Load PV Map
    pv_df = pd.read_csv(pv_map_path, comment='#', names=['GeoCode', 'Prop', 'Value'])
    geo_map = dict(zip(pv_df['GeoCode'].astype(str), pv_df['Value'].astype(str)))
    
    # 2. Load Event Geography CSV (Hierarchy Info)
    # Allows us to check if an unresolved code is Country level or above
    un_geo_df = pd.read_csv(un_geo_csv_path)
    # Creating a dictionary for fast lookup: Code -> Name
    un_geo_names = dict(zip(un_geo_df['CODE'].astype(str), un_geo_df['NAME_EN'].astype(str)))
    
    # 3. Load Input and Output data
    input_df = pd.read_csv(input_csv_path)
    output_df = pd.read_csv(output_csv_path)
    
    if geo_input_col_name not in input_df.columns:
        return {"status": "FAILED", "errors": [f"Input column '{geo_input_col_name}' not found."]}
    if 'observationAbout' not in output_df.columns:
        return {"status": "FAILED", "errors": ["Output column 'observationAbout' not found."]}

    errors = []
    unresolved_high_level_geos = set()
    
    # Using the #input tracker is highly recommended to safely join the data, 
    # but for simplicity, assuming a row-by-row mapping here:
    for idx in range(min(len(input_df), len(output_df))):
        raw_code = str(input_df[geo_input_col_name].iloc[idx]).strip()
        pv_lookup_code = f"GEOGRAPHY:{raw_code}"
        
        actual_output = str(output_df['observationAbout'].iloc[idx]).strip()
        expected_output = geo_map.get(pv_lookup_code)
        
        # Rule 3.1: Capture missing national or higher places
        is_unresolved = (not expected_output) or (expected_output == 'unmapped place')
        
        if is_unresolved:
            geo_name = un_geo_names.get(raw_code, "Unknown Name")
            
            # Placeholder check for "country level or above". 
            # In production, this would use a more robust check based on hierarchy / dc_parent_id in un_geography.csv
            # For now, flag it for recording.
            unresolved_high_level_geos.add(f"{raw_code} ({geo_name})")
            
        elif actual_output != expected_output:
            errors.append(f"Row {idx}: Geo mismatch. Input '{raw_code}' -> Expected '{expected_output}', Got '{actual_output}'")

    response = {"status": "PASSED" if not errors else "FAILED"}
    if errors:
        response["errors"] = errors
    if unresolved_high_level_geos:
        # Rule 3.1 mandates recording these
        response["unresolved_high_level_places"] = list(unresolved_high_level_geos)
        
    return response
```

## 6. Edge Cases & Considerations
* **Hierarchy Resolution:** `un_geography.csv` might not have an explicit "level" column (like "country", "continent"). The script might need to infer level based on DCID structure (e.g., `country/XXX` vs `Earth`) or by resolving parents recursively using the `PARENT` column until it reaches a known global root.
* **Row Alignment with `#input`:** Instead of relying on index matching (`idx`), it is much safer to join the generated `SDG_..._data.csv` to the source input CSV using the `#input` column present in the output file, avoiding mismatch errors caused by dropped rows.