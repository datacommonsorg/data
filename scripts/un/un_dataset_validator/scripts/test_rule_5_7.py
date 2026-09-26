"""
VALIDATION RULE:
================
# Rule 5: OBS_VALUE Mapping to `value`

## 1. Rule Description
* **Core Rule (5):** The observation value (`OBS_VALUE` column) from the input data must be mapped to the `value` property in the output CSV.
* **Format Check:** As per the meeting notes, observation values are required to map to `value.number`. This means the resulting `value` must be a valid number (`{Number}`). This validation check must be performed using the property-value (PV) map.

## 2. Files Involved
* **Input Dataset:** The raw input `.csv` data files containing the `OBS_VALUE` column.
* **Output Data File:** The generated output `.csv` file.
* **Property Value Map (PV Map):** Specifically, the `common_pvmap_obs.csv` file which defines the mapping rule: `OBS_VALUE,value,{Number},...`

## 3. Concrete Example
* **Input Data Row:** Contains an `OBS_VALUE` of `594982.4482`.
* **Output Check:** The output `.csv` file should contain a column named `value`, and the corresponding row must contain `594982.4482` (or potentially a multiplied value if unit multipliers apply, see Rule 10, but inherently it must be numeric).


# Rule 7: UNIT_MULTIPLIER Application

## Context from Meeting Notes
During the meeting, Harish Chandrashekar explicitly stated: "Wherever unit multiplier is there it whatever multiplication factor it has it should be multiplied with the value. Every multiplier should be multiplied with H value." (00:24:26)

This means that if a dataset contains a unit multiplier column (e.g., indicating the values are in thousands or millions), the raw observation value (`OBS_VALUE`) must be multiplied by this factor before being written to the output Data Commons CSV.

## Mapping Logic
1. **Identify Multiplier Attribute:** Identify the column representing the unit multiplier in the raw input data (often named `UNIT_MULT`, `UNIT_MULTIPLIER`, etc., depending on the DSD).
2. **Lookup Factor:** Use the common PV map `all_data/pvmap/CL_MULT_pvmap_multiply.csv` to resolve the multiplication factor. The PV map links the multiplier code to a float value (e.g., `1.00E-15` for -15).
3. **Apply Factor:** The expected value in the Data Commons output CSV should be:
   `Expected_Value = float(Raw_OBS_VALUE) * float(Multiplier_Factor)`
4. **Compare:** Assert that `Expected_Value` matches the `value` column in the processed output CSV.

## Relevant Files
- **Raw Input Data:** Varies per dataset (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv`).
- **PV Map for Multipliers:** `all_data/pvmap/CL_MULT_pvmap_multiply.csv`.
- **Processed Output Data:** Varies per dataset (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv` in `processed_data/`).


"""
import os
import sys
import glob
import csv
import math

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import load_multipliers, get_input_file_path

class Rule5And7Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 5 & 7 (OBS_VALUE mapping & Unit Multipliers)")
        
        multipliers = load_multipliers(self.pvmap_dir)
        
        pattern = os.path.join(self.processed_dir, "*_data.csv")
        output_files = glob.glob(pattern)
        
        if not output_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            print(f"No *_data.csv files found in {self.processed_dir}")
            return False

        total_files = len(output_files)
        total_rows_checked = 0
        total_errors = 0
        file_errors_map = {}
        
        input_file_cache = {}
        
        for filepath in output_files:
            filename = os.path.basename(filepath)
            file_errors = []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if 'value' not in reader.fieldnames or '#input' not in reader.fieldnames:
                    file_errors.append(f"Missing required columns ('value' or '#input') in output.")
                    file_errors_map[filename] = file_errors
                    total_errors += 1
                    continue
                
                for output_row_num, row in enumerate(reader, start=2):
                    input_lineage = row.get('#input', '')
                    if not input_lineage:
                        continue
                        
                    parts = input_lineage.split(':')
                    if len(parts) < 2:
                        continue
                        
                    input_filename = parts[0]
                    try:
                        input_row_idx = int(parts[1])
                    except ValueError:
                        continue
                        
                    if input_filename not in input_file_cache:
                        in_path = get_input_file_path(self.dataset_name, input_filename, self.input_data_dir)
                        if not in_path:
                            file_errors.append(f"Could not find input file: {input_filename}")
                            input_file_cache[input_filename] = None
                            continue
                            
                        rows_dict = {}
                        try:
                            with open(in_path, 'r', encoding='utf-8') as in_f:
                                in_reader = csv.DictReader(in_f)
                                for idx, in_row in enumerate(in_reader, start=2):
                                    rows_dict[idx] = in_row
                            input_file_cache[input_filename] = rows_dict
                        except Exception as e:
                            file_errors.append(f"Failed to read input file {input_filename}: {e}")
                            input_file_cache[input_filename] = None
                            
                    input_data = input_file_cache.get(input_filename)
                    if not input_data:
                        continue
                        
                    in_row = input_data.get(input_row_idx)
                    if not in_row:
                        file_errors.append(f"Row {input_row_idx} not found in input file {input_filename}")
                        continue
                        
                    obs_value_str = in_row.get('OBS_VALUE')
                    unit_mult_code = in_row.get('UNIT_MULT')
                    output_value_str = row.get('value')
                    
                    if obs_value_str is None or output_value_str is None:
                        continue
                        
                    total_rows_checked += 1
                    
                    try:
                        out_val = float(output_value_str)
                    except ValueError:
                        file_errors.append(f"Output row {output_row_num}: 'value' is not numeric ('{output_value_str}')")
                        continue
                        
                    try:
                        clean_obs = obs_value_str.replace(',', '')
                        in_val = float(clean_obs)
                    except ValueError:
                        file_errors.append(f"Input row {input_row_idx}: OBS_VALUE is not numeric ('{obs_value_str}') but output is '{out_val}'")
                        continue

                    mult = 1.0
                    if unit_mult_code and str(unit_mult_code) in multipliers:
                        mult = multipliers[str(unit_mult_code)]
                        
                    expected_val = in_val * mult
                    
                    if not math.isclose(expected_val, out_val, rel_tol=1e-4, abs_tol=1e-4):
                        file_errors.append(f"Row {output_row_num} lineage {input_lineage}: Value mismatch. Expected {in_val} * {mult} = {expected_val}, got {out_val}")

            if file_errors:
                file_errors_map[filename] = file_errors
                total_errors += len(file_errors)

        self.write_log(f"--- File-Specific Violations ---")
        if not file_errors_map:
            self.write_log("No violations detected.")
        else:
            for filename, errors in file_errors_map.items():
                self.write_log(f"\nFAILED FILE: {filename}")
                for err in errors[:20]:
                    self.write_log(f"  - {err}")
                if len(errors) > 20:
                     self.write_log(f"  ... and {len(errors) - 20} more errors.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total output files processed: {total_files}")
        self.write_log(f"Total rows checked: {total_rows_checked}")
        self.write_log(f"Total errors: {total_errors}")
        
        status = "PASSED" if total_errors == 0 else "FAILED"
        self.write_log(f"Overall Status: {status}")

        print(f"Rule 5 & 7 Validation complete. Checked {total_rows_checked} rows. Results written to {self.log_file}")
        return total_errors == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_5_7.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule5And7Validator(sys.argv[1], sys.argv[2])
    validator.validate()