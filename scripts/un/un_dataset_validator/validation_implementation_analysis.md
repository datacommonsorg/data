# Custom Data Commons (DC) Validation Implementation Analysis

## 1. Executive Summary
This document outlines a detailed and comprehensive strategy for implementing an automated validation script in Python for the Custom Data Commons datasets. The script verifies that the data transformation pipeline correctly converts raw UN dataset inputs into the required Data Commons formats (MCF and CSV). 

*Note: As instructed, all checklist items marked with "Ask Ajai" (Checks 1, 4.1, 6.1, 8, 10.1, and 13) have been explicitly excluded from this analysis.*

---

## 2. Validation Flow and File Definitions

The validation process involves comparing four distinct categories of files. Let's trace the exact flow using the `SDG_q1-2026` dataset (specifically the `AG_FLS_INDEX` series) as an example.

### A. The Input Files (The "Source of Truth")
The raw input dataset for the UN series contains the initial data points. While the raw files might be staged in buckets or upstream folders, we know their structure based on the transcript and the traceback from the generated files.
* **Example Input Source:** `SDG_q1-2026_OBS_AG_FLS_INDEX.csv` (referenced by the `#input` column in the output CSV).
* **Key Columns Expected:** `series`, `geography` (e.g., `D0`), `timePeriod`, `obsValue`, and various dimensions (like `product`) and attributes (like `censoredValueType`).

### B. The Structure Definitions (DSD & Codelists)
The Data Structure Definition (DSD) dictates how each column in the input file should be treated.
* **Flow:** The validation script must read the DSD to classify columns into two buckets: `ROLE="dimension"` (e.g., `series`, `geography`, `timePeriod`, `product`) and `ROLE="Attribute"` (e.g., `censoredValueType`, `unitMultiplier`).

### C. The Property-Value (PV) Maps
These maps provide the exact translation from UN source codes to Data Commons DCIDs.
* **Example File:** `/all_data/pvmap/un_geography_pvmap.csv`. 
* **Flow:** When validating geography, the script cross-references the input `geography` value against this PV map to determine the expected output DCID.

### D. The Output Files (The Data to Validate)
The generated files live in the `processed_data/` directory.
1. **Output CSV (`SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`):** Contains the transcoded data.
   * **Columns generated:** `observationAbout`, `observationDate`, `value`, `variableMeasured` (StatVar DCID), and extra attribute columns like `censoredValueType`.
2. **Output MCF (`SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf`):** Contains the definitions for the Statistical Variables (StatVars).
   * **Example Node:** `Node: dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD`

---

## 3. Implementation Strategy & Flow by Checklist Rule

### Check 2: `SERIES` mapped to `populationType`
* **Flow:** 
  1. Extract the series code from the input (e.g., `AG_FLS_INDEX`).
  2. Locate the corresponding Statistical Variable in the output MCF.
  3. Validate that the `populationType` property exists and is correctly prefixed.
* **SDG Example:** In `SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf`, the node `dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD` must have the property `populationType: dcid:UN_SDG_SERIES-AG_FLS_INDEX`.
* **Validation Logic:** Assert `output_mcf_node['populationType'] == f"dcid:UN_SDG_SERIES-{input_series}"`.

### Check 3: `GEOGRAPHY` mapped to `observationAbout`
* **Flow:**
  1. Read the `geography` column from the input file.
  2. Look up the corresponding Data Commons DCID using `un_geography_pvmap.csv`.
  3. Verify that the expected DCID populates the `observationAbout` column in the output CSV.
* **SDG Example:** If the input geography is `D0` (World), the PV map resolves this to `Earth`. In `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`, the `observationAbout` column must equal `dcid:Earth`.
* **Validation Logic:** If a regional/national geography code fails to resolve via the PV map, the script must flag it and record the unresolved geography code to a separate error log.

### Check 4: `TIME_PERIOD` mapped to `observationDate`
* **Flow:** Compare the time string from the input to the output.
* **SDG Example:** If the input `timePeriod` is `2015`, the output CSV (`SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`) must have `observationDate` = `2015`.
* **Validation Logic:** Assert `input_row['timePeriod'] == output_row['observationDate']`. (Complex un-mappable date formats like `2024-25/P3M` are ignored per "Ask Ajai" rules).

### Check 5: `OBS_VALUE` mapped to `value`
* **Flow:** Ensure numerical fidelity between input and output.
* **SDG Example:** In `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`, a row contains `value: 100`. This must exactly match the `OBS_VALUE` from the corresponding row in the input CSV.
* **Validation Logic:** Use `pandas.to_numeric()` to ensure the generated output `value` is an exact float/int equivalent of the input.

### Check 6: Dimensions as Constraint Properties
* **Flow:** 
  1. The DSD marks specific columns (other than time, geo, value, and series) as dimensions.
  2. These dimensions must appear as properties attached to the StatVar Node in the MCF.
* **SDG Example:** The DSD for `AG_FLS_INDEX` defines `product` as a dimension. In the MCF (`SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf`), the script must find the property attached to the StatVar: `product: dcid:UN_PRODUCT-AGG_ANIMAL_PROD`.
* **Validation Logic:** Assert that the MCF node contains `product` and that its value adheres to the `<prefix>_<CONCEPT>-<CODE>` format (e.g., `UN_PRODUCT-...`).

### Check 7: `UNIT_MULTIPLIER` Application
* **Flow:** If the input data has a multiplier (e.g., Thousands), the output `value` must be pre-calculated.
* **Validation Logic:**
  1. Look up the input's `UNIT_MULTIPLIER` code in `CL_MULT_pvmap_multiply.csv`.
  2. Calculate: `Expected_Value = float(input['OBS_VALUE']) * integer_multiplier`.
  3. Assert `Expected_Value == float(output['value'])`.

### Check 9: `FREQUENCY` to `observationPeriod`
* **Flow:** Ensure the input frequency maps to the correct DC `observationPeriod`.
* **Validation Logic:** Check the PV map (`CL_FREQUENCY_pvmap_obsperiod.csv`). 
* **Important Anomaly Handling:** The Python script must dynamically check the output CSV headers for known typos like `opservationPeriod` (which exists in the current output files). It should fail the validation if the correct `observationPeriod` header is missing, flagging the typo.

### Check 10: Attributes as Output Columns
* **Flow:** 
  1. The DSD dictates which columns are "Attributes" (e.g., not attached to the MCF StatVar, but carried over to the CSV).
  2. The script checks the output CSV headers for these columns.
* **SDG Example:** `censoredValueType` is an attribute. In `SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv`, there is an explicitly generated column named `censoredValueType` containing values like `UN_CENSORED_VALUE_TYPE-_Z`.
* **Validation Logic:** `assert 'censoredValueType' in output_csv.columns`. 

### Check 11: StatVar DCID Format & Special Characters
* **Flow:** The DCID generated for each variable must follow the strict `<prefix>/<agency>/<SERIES>[.<CONCEPT>--<CODE>__…]` template without illegal characters.
* **SDG Example:** The script reads `dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD` from the MCF.
* **Validation Logic:** Regex validation. Ensure that original special characters (e.g., in the product code) were accurately replaced by underscores (`_`).

### Check 12: Name Property Matches DSD/CL
* **Flow:** The generated `name` in the MCF should be human-readable, mapped directly from the Codelist descriptions.
* **Validation Logic:** Cross-reference the dimension codes (e.g., `AGG_ANIMAL_PROD`) against the UN Codelist descriptions. Ensure that these descriptions are concatenated correctly into the `name` property of the StatVar MCF node. (Note: The script should log a warning rather than failing if the name is entirely missing, as this is a known pipeline issue).