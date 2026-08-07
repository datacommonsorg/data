"""
VALIDATION RULE:
================
# Rule 16: Observation Completeness (#input tracking)

## Requirement
Verify that no non-empty observations are improperly dropped during processing. The generated `#input` column tracks the origin of each data point, so every valid observation cell in the source data should have a corresponding `#input` reference in the output.

## Context & Rules
- For every `*_data.csv` in the output directory, collect all the `#input` coordinates.
- For every `.csv` in the input data directory, parse the data.
- Identify cells that should have been processed (non-empty data points).
- Ensure that the generated output tracks these cells.
"""

import os
import glob
import sys
import pandas as pd

# Ensure the scripts directory is in sys.path
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator

class Rule16Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 16 (Observation Completeness)")
        
        if not self.input_data_dir:
            self.write_log("Error: input_data_dir is required for Rule 16.")
            print(f"Error: input_data_dir is required for Rule 16. Log written to {self.log_file}")
            return False

        # 1. Collect all `#input` references from output files
        out_pattern = os.path.join(self.processed_dir, "*_data.csv")
        out_csv_files = glob.glob(out_pattern)
        
        if not out_csv_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            return False

        actual_inputs = set()
        for out_file in out_csv_files:
            try:
                # Read output CSV safely
                df = pd.read_csv(out_file, dtype=str)
                if '#input' in df.columns:
                    # Dropna and strip to be safe
                    inputs = df['#input'].dropna().str.strip()
                    for item in inputs:
                        if item:
                            actual_inputs.add(item)
            except Exception as e:
                self.write_log(f"Error reading output file {out_file}: {e}")

        self.write_log(f"Extracted {len(actual_inputs)} unique #input references from output data.")

        # 2. Iterate through input files and check if non-empty observations exist in actual_inputs
        in_pattern = os.path.join(self.input_data_dir, "*.csv")
        in_csv_files = glob.glob(in_pattern)
        
        if not in_csv_files:
            self.write_log(f"No input .csv files found in {self.input_data_dir}")
            return False

        failed_files = 0
        total_missing = 0
        
        for in_file in in_csv_files:
            filename = os.path.basename(in_file)
            file_errors = []
            
            try:
                # Read input CSV
                # Use string type to avoid parsing issues and correctly identify empty strings vs NaNs
                df_in = pd.read_csv(in_file, dtype=str)
                
                # Determine which columns might contain observations.
                # A simple heuristic: columns named OBS_VALUE or similar.
                # If the dataset has a specific structure, this might need refinement.
                obs_columns = [col for col in df_in.columns if col.upper() in ['OBS_VALUE', 'VALUE', 'OBS']]
                
                if not obs_columns:
                    self.write_log(f"File {filename}: No clear observation value column found (e.g., OBS_VALUE). Skipping.")
                    continue
                
                # For each observation column, iterate over rows
                # Pandas iterrows is 0-indexed, meaning row 0 corresponds to line 2 in CSV (line 1 is header).
                # But we should use the exact coordinate system used by the generator.
                # Typically, `#input` uses format `filename:row:col` (1-based row, 1-based col, or similar).
                # Wait, looking at SDG_q1-2026_OBS_AG_FLS_PCT.csv:2:4
                # 2 is the 1-based data row (which is index 0 in pandas, line 2 in the text file).
                # Let's parse the exact format from actual_inputs for this file.
                
                for idx, row in df_in.iterrows():
                    csv_row_num = idx + 2 # Header is line 1, first data row is line 2
                    
                    for col_name in obs_columns:
                        val = row[col_name]
                        
                        # Check if it's non-empty (not NaN and not empty string)
                        if pd.notna(val) and str(val).strip() != "":
                            # Try to find the coordinate
                            col_idx = df_in.columns.get_loc(col_name) # 0-based column index
                            
                            # Construct expected coordinate
                            coord = f"{filename}:{csv_row_num}:{col_idx}"
                            
                            if coord not in actual_inputs:
                                file_errors.append(f"Missing mapped input: {coord} (Value: {val})")
                                total_missing += 1
                                
            except Exception as e:
                file_errors.append(f"Error processing input file {filename}: {e}")
                
            if file_errors:
                failed_files += 1
                self.write_log(f"\nFAILED FILE: {filename}")
                for err in file_errors[:20]:
                    self.write_log(f"  - {err}")
                if len(file_errors) > 20:
                    self.write_log(f"  ... and {len(file_errors) - 20} more missed observations.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total input files processed: {len(in_csv_files)}")
        self.write_log(f"Input files with missing observations: {failed_files}")
        self.write_log(f"Total missing observations: {total_missing}")
        
        status = "PASSED" if failed_files == 0 else "FAILED"
        self.write_log(f"Overall Status: {status}")

        print(f"Rule 16 Validation completed. {failed_files}/{len(in_csv_files)} files failed.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Rule 16 Validation (Observation Completeness)")
    parser.add_argument("--dataset", required=True, help="Dataset name (e.g., sdg_q1-2026)")
    parser.add_argument("--dataset_dir", required=True, help="Path to the dataset directory")
    parser.add_argument("--input_data_dir", required=True, help="Path to raw input DATA directory")
    args = parser.parse_args()
    
    validator = Rule16Validator(args.dataset, args.dataset_dir, input_data_dir=args.input_data_dir)
    validator.validate()
