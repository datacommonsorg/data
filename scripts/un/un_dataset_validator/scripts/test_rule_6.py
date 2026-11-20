"""
VALIDATION RULE:
================
# Rule 6: Dimensions vs. Attributes

## 1. Rule Description
* **Core Rule (6):** All properties defined in the Dataset Definition (DSD) file must be correctly handled as either a **dimension** or an **attribute**. 
* **Dimensions:** Except for specific exemptions (`Geography`, `Time Period`, `OBS_VALUE`, and `SERIES`), any property marked as a "dimension" must be attached to the Statistical Variable (StatVar) as a **constraint property**.
* **Attributes:** Any property marked as an "attribute" must **not** be attached to the Statistical Variable. Instead, it must be included in the output data `.csv` as a separate column.

## 2. Files Involved
* **Input DSD File:** The respective DSD file for the dataset (e.g., an Excel/CSV file containing the `ROLE` column with values "dimension" or "attribute").
* **Input Data File:** The raw `.csv` data.
* **Output Data File:** The generated output `.csv` file.
* **Output MCF File:** The generated `.mcf` file containing the Statistical Variable definitions.

## 3. Concrete Example
* **DSD Definition:** 
  * `PRODUCT` is defined with a `ROLE` of "dimension".
  * `CENSORED_VALUE_TYPE` is defined with a `ROLE` of "attribute".
* **Output Check for Dimension (`PRODUCT`):** 
  * The Statistical Variable node (e.g., `Node: dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_CRL_PUL`) in the `.mcf` file must contain `PRODUCT` as a constraint property (e.g., `product: dcid:UN_PRODUCT-AGG_CRL_PUL`).
* **Output Check for Attribute (`CENSORED_VALUE_TYPE`):** 
  * The StatVar node must **not** contain `CENSORED_VALUE_TYPE`.
  * The output `.csv` file must contain a separate column named `censoredValueType` (or similar mapped name), with values like `UN_CENSORED_VALUE_TYPE-_Z`.


# Rule 6.1: Dimension Mapping to DCP Schema with UN_ Prefix

## Requirement
Each dimension must be mapped to the Data Commons Project (DCP) schema using a common prefix `UN_` without including the specific agency prefix.

## Context & Rules (From Meeting Notes)
- The dataset is processed to create a schema. Any schema generated from the DCP must consistently use the `UN_` prefix for dimensions.
- Every node within the agency-specific schema files follows a "concept_value" structure.
- The mapping must ensure these dimensions correctly represent the concept without introducing agency-specific identifiers in the prefix (e.g., use `UN_` instead of `UN_ECLAC_`).


# Rule 6.2: Dimension Value Mapping

## Objective
Ensure that every value within a dimension column is properly mapped to a generated property value DCID following the exact template: `<prefix>_<CONCEPT>-<CODE>`.

## Context & Rationale
According to the meeting notes and project requirements, any column designated as a "dimension" in the Dataset Definition (DSD) file must have its distinct values transformed into standardized Data Commons Identifiers (DCIDs). The format for these DCIDs consistently incorporates a prefix (typically `UN`), the concept name (derived from the column name), and the specific value code. 

For instance, if the dimension column is `product` and a raw value in the dataset is `CPC2_1_0113`, the mapped value DCID should be formatted as `UN_PRODUCT-CPC2_1_0113`. In the output schema/MCF, this would appear as a property-value pair like `product: dcid:UN_PRODUCT-CPC2_1_0113`.

## Files Involved
*   **DSD File (e.g., `schema.csv` or `DSD.csv`):** Used to identify which columns act as dimensions (where `ROLE` = `Dimension`).
*   **Input Data File (`.csv`):** Provides the raw source values for the identified dimension columns.
*   **Output Files (`.mcf`, `.tmcf`, or processed `.csv`):** Validated to ensure the final output respects the mapped DCID format.

## Verification Logic
1.  **Identify Dimensions:** Read the DSD file and filter for rows where the `ROLE` column is explicitly set to `Dimension` (excluding explicit exceptions like Geography, Time Period, OBS_VALUE, and Series, which have their own rules).
2.  **Extract Concept Names:** Determine the concept name from the dimension's column name. The concept name is generally the uppercase version of the column name (e.g., `product` -> `PRODUCT`).
3.  **Construct Expected DCIDs:** For every row in the input data file, look at the value under the dimension column. Construct the expected DCID using the template:
    *   `Prefix`: `UN` (or derived from the specific dataset configuration).
    *   `Concept`: Capitalized column name.
    *   `Code`: The raw value found in the input data.
    *   **Format:** `<prefix>_<CONCEPT>-<CODE>` (e.g., `UN_PRODUCT-CPC2_1_0113`).
4.  **Validate Output:** Ensure that in the finalized statistical variable mapping or output nodes, the dimension property maps exactly to this constructed DCID (e.g., checking that `product: dcid:UN_PRODUCT-CPC2_1_0113` exists).


"""
import os
import sys
import glob
import csv
import re

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator

def sanitize_for_match(text: str) -> str:
    """Removes underscores and converts to lowercase for column matching."""
    return text.replace("_", "").lower()

class Rule6Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 6 (Dimension vs Attribute Mapping)")
        
        if not self.dsd_dir or not os.path.exists(self.dsd_dir):
            self.write_log(f"Could not find DSD directory for dataset {self.dataset_name}")
            print(f"Could not find DSD directory for dataset {self.dataset_name}")
            return False
            
        dsd_dir = self.dsd_dir
        dsd_files = glob.glob(os.path.join(dsd_dir, "*.csv"))
        
        if not dsd_files:
            self.write_log(f"No DSD files found in {dsd_dir}")
            return False

        exemptions = ['SERIES', 'GEOGRAPHY', 'TIME_PERIOD', 'OBS_VALUE']
        total_files = len(dsd_files)
        failed_files = 0

        self.write_log(f"DSD Directory: {dsd_dir}")
        self.write_log(f"Output Directory: {self.processed_dir}\n")

        for dsd_path in sorted(dsd_files):
            filename = os.path.basename(dsd_path)
            match = re.search(r'_DSD_(.*?)\.csv', filename)
            if not match:
                continue
            series = match.group(1)

            mcf_pattern = os.path.join(self.processed_dir, f"*_OBS_{series}_data_stat_vars.mcf")
            csv_pattern = os.path.join(self.processed_dir, f"*_OBS_{series}_data.csv")

            mcf_files = glob.glob(mcf_pattern)
            csv_files = glob.glob(csv_pattern)

            if not mcf_files or not csv_files:
                self.write_log(f"[{series}] SKIPPED: Missing corresponding MCF or CSV file.")
                continue

            mcf_path = mcf_files[0]
            csv_path = csv_files[0]

            errors = []

            dimensions = []
            attributes = []
            with open(dsd_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    role = row.get('ROLE', '').strip().lower()
                    concept = row.get('CONCEPT', '').strip()
                    
                    if role == 'dimension':
                        if concept.upper() not in exemptions:
                            dimensions.append(concept)
                    elif role == 'attribute':
                        attributes.append(concept)

            with open(mcf_path, 'r', encoding='utf-8') as f:
                mcf_content = f.read()

            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader, [])
                sanitized_headers = [sanitize_for_match(h) for h in headers]
                
                dim_indices = []
                dim_col_names = []
                for dim in dimensions:
                    expected_col = sanitize_for_match(dim)
                    if expected_col in sanitized_headers:
                        dim_indices.append(sanitized_headers.index(expected_col))
                        dim_col_names.append(dim)
                
                dim_values = {dim: set() for dim in dim_col_names}
                if dim_indices:
                    for row in csv_reader:
                        for idx, dim in zip(dim_indices, dim_col_names):
                            if idx < len(row):
                                val = row[idx].strip()
                                if val:
                                    dim_values[dim].add(val)

            for dim in dimensions:
                dim_upper = dim.upper()
                
                # Rule 6.1: strict UN_ prefix mapping
                expected_prefix = f"dcid:UN_{dim_upper}-"
                if expected_prefix not in mcf_content:
                     # Look for agency-specific prefix violation
                     match = re.search(rf"dcid:(UN_[A-Z0-9]+_{dim_upper}-)", mcf_content)
                     if match:
                          errors.append(f"File {os.path.basename(mcf_path)}: Rule 6.1 Violation - Dimension '{dim}' uses an agency-specific prefix '{match.group(1)}' instead of 'UN_{dim_upper}-'.")
                     else:
                          # It might be present without UN_ or completely missing
                          if f"_{dim_upper}-" in mcf_content:
                               errors.append(f"File {os.path.basename(mcf_path)}: Rule 6.1 Violation - Dimension '{dim}' found but without the required 'UN_' prefix.")
                          else:
                               errors.append(f"File {os.path.basename(mcf_path)}: Dimension '{dim}' not found as a constraint property in MCF.")

                # Rule 6.2: Dimension Value Mapping
                if dim in dim_values:
                    for val in dim_values[dim]:
                        clean_val = re.sub(r'[^a-zA-Z0-9_]', '_', str(val))
                        expected_dcid = f"UN_{dim_upper}-{clean_val}"
                        if expected_dcid not in mcf_content:
                            errors.append(f"File {os.path.basename(mcf_path)}: Rule 6.2 Violation - Dimension '{dim}' value '{val}' missing expected mapped DCID '{expected_dcid}'.")

            attr_column_map = {
                'UNIT_MEASURE': 'unit',
                'FREQUENCY': 'opservationperiod',  # Pipeline typo
                'UNIT_MULT': None,  # Consumed by Rule 7, not in CSV
            }
            
            for attr in attributes:
                attr_upper = attr.upper()
                
                if attr_upper == 'UNIT_MULT' or (attr_column_map.get(attr_upper) is None and attr_upper in attr_column_map):
                    continue
                
                attr_prop_name = attr.lower()
                if re.search(rf'^{attr_prop_name}:\s*dcid:', mcf_content, re.MULTILINE | re.IGNORECASE):
                    errors.append(f"File {os.path.basename(mcf_path)}: Attribute '{attr}' incorrectly attached to a StatVar in the MCF file.")
                if f"UN_{attr_upper}-" in mcf_content:
                     errors.append(f"File {os.path.basename(mcf_path)}: Attribute '{attr}' found with dimension-like DCID 'UN_{attr_upper}-' in MCF.")

                expected_col = attr_column_map.get(attr_upper, sanitize_for_match(attr))
                if expected_col not in sanitized_headers:
                     errors.append(f"File {os.path.basename(csv_path)}: Attribute '{attr}' not found as a separate column in the output CSV. Expected a column matching '{expected_col}'.")

            if errors:
                failed_files += 1
                self.write_log(f"[{series}] FAILED")
                for err in errors:
                    self.write_log(f"  - {err}")
                self.write_log("")
            else:
                self.write_log(f"[{series}] PASSED")

        self.write_log(f"\nSummary:")
        self.write_log(f"Total DSDs Checked: {total_files}")
        self.write_log(f"Passed: {total_files - failed_files}")
        self.write_log(f"Failed: {failed_files}")

        print(f"Rule 6 Validation completed. {failed_files}/{total_files} files failed.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_6.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule6Validator(sys.argv[1], sys.argv[2])
    validator.validate()