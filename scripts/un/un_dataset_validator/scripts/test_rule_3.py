"""
VALIDATION RULE:
================
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


"""
import os
import sys
import glob
import random
import csv

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import get_input_file_path

def load_pv_map(pv_map_path):
    geo_map = {}
    if not os.path.exists(pv_map_path):
        return geo_map
    with open(pv_map_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                key_parts = row[0].split(':')
                if len(key_parts) == 2 and key_parts[0] == 'GEOGRAPHY':
                    geo_code = key_parts[1].strip()
                    dcid = row[2].strip()
                    geo_map[geo_code] = dcid
    return geo_map

def load_geo_names(geo_names_path):
    geo_names = {}
    if not os.path.exists(geo_names_path):
        return geo_names
    with open(geo_names_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            geo_code = row.get('CODE', '')
            name = row.get('NAME_EN', '')
            if geo_code:
                geo_names[geo_code] = name
    return geo_names

class Rule3Validator(BaseRuleValidator):
    def validate_file(self, output_csv_path, geo_map, unmapped_geos):
        filename = os.path.basename(output_csv_path)
        
        output_mapping = {}
        with open(output_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if '#input' in row:
                    parts = row['#input'].split(':')
                    if len(parts) >= 2:
                        input_filename = parts[0]
                        try:
                            line_num = int(parts[1])
                            output_mapping[(input_filename, line_num)] = row.get('observationAbout', '')
                        except ValueError:
                            pass
        
        if not output_mapping:
            return {"status": "SKIPPED", "reason": "No #input mapping found in output CSV"}
            
        input_filename = list(output_mapping.keys())[0][0]
        input_csv_path = get_input_file_path(self.dataset_name, input_filename, self.input_data_dir)
        
        if not input_csv_path or not os.path.exists(input_csv_path):
            return {"status": "FAILED", "errors": [f"Input file not found: {input_filename}"]}

        errors = []
        
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for line_idx, row in enumerate(reader, start=2):
                geo_code = None
                if 'GEOGRAPHY' in row:
                    geo_code = row['GEOGRAPHY']
                elif 'geo' in row:
                    geo_code = row['geo']
                elif 'REF_AREA' in row:
                    geo_code = row['REF_AREA']
                elif 'GeoAreaCode' in row:
                    geo_code = row['GeoAreaCode']
                    
                if geo_code is None:
                    continue
                    
                expected_dcid = geo_map.get(geo_code)
                
                mapping_key = (input_filename, line_idx)
                if mapping_key in output_mapping:
                    actual_dcid = output_mapping[mapping_key]
                    if expected_dcid and actual_dcid != expected_dcid:
                        errors.append(f"File {input_filename}, Line {line_idx}: expected observationAbout '{expected_dcid}' for geo '{geo_code}', but got '{actual_dcid}'")
                    elif not expected_dcid:
                        unmapped_geos.add(geo_code)
                        if not actual_dcid.startswith('dcid:'):
                            errors.append(f"File {input_filename}, Line {line_idx}: unresolved geo '{geo_code}' produced invalid observationAbout '{actual_dcid}' (missing dcid: prefix)")
                else:
                    if not expected_dcid:
                        unmapped_geos.add(geo_code)
                        
        if errors:
            return {"status": "FAILED", "errors": errors}
            
        return {"status": "PASSED"}

    def validate(self):
        self.setup_logging("Rule 3 (Geography Mapping)")
        
        pv_map_path = os.path.join(self.pvmap_dir, "un_geography_pvmap.csv")
        # Global geography names
        geo_names_path = os.path.join(os.path.dirname(self.dataset_dir), "un_geography.csv")
        
        self.write_log(f"Loading PV Map from {pv_map_path}...")
        geo_map = load_pv_map(pv_map_path)
        self.write_log(f"Loaded {len(geo_map)} geography mappings.")
        
        self.write_log(f"Loading Geography Names from {geo_names_path}...")
        geo_names = load_geo_names(geo_names_path)
        
        pattern = os.path.join(self.processed_dir, "*_data.csv")
        output_files = glob.glob(pattern)
        
        unmapped_geos = set()
        
        if not output_files:
            self.write_log(f"No *_data.csv files found in {self.processed_dir}")
            print(f"No *_data.csv files found in {self.processed_dir}")
            return False
            
        total = len(output_files)
        passed = 0
        failed = 0
        skipped = 0
        failed_details = []
        
        for filepath in output_files:
            result = self.validate_file(filepath, geo_map, unmapped_geos)
            
            if result["status"] == "PASSED":
                passed += 1
            elif result["status"] == "SKIPPED":
                skipped += 1
            else:
                failed += 1
                failed_details.append({"filename": os.path.basename(filepath), "errors": result["errors"]})

        self.write_log(f"--- Detailed Failure Report ---")
        if failed == 0:
            self.write_log("No validation failures detected (excluding unmapped geos).")
        else:
            for failure in failed_details:
                self.write_log(f"\nFAILED FILE: {failure['filename']}")
                errors = failure['errors']
                self.write_log(f"Total row mismatch errors in this file: {len(errors)}")
                
                sampled_errors = random.sample(errors, min(10, len(errors)))
                self.write_log(f"Sampled mismatch errors (up to 10):")
                for err in sampled_errors:
                    self.write_log(f"  - {err}")

        self.write_log(f"\n--- Unmapped Geographies Report ---")
        if not unmapped_geos:
            self.write_log("No unmapped geographies found.")
        else:
            self.write_log(f"Found {len(unmapped_geos)} unique unmapped geographies that were dropped from the output:")
            for geo in sorted(unmapped_geos):
                name = geo_names.get(geo, "Unknown Name")
                self.write_log(f"  - {geo}: {name}")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")
        self.write_log(f"Skipped: {skipped}")

        print(f"Rule 3 Validation complete. Results written to {self.log_file}")
        return failed == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_3.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule3Validator(sys.argv[1], sys.argv[2])
    validator.validate()