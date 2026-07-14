"""
VALIDATION RULE:
================
# Rule 10: Attributes as Output Columns

## Description
According to the UN Data Commons mapping rules, every concept defined in the dataset's Data Structure Definition (DSD) file with a `ROLE` of `Attribute` must be present as a separate column in the output `data.csv` file. 

Attributes provide supplementary information (such as footnotes, observation statuses, or flags) about the observation value. Unlike dimensions, attributes must **NOT** be attached as properties to the Statistical Variables.

**Note on Exclusions (Rule 10.1):** Parsing and validating the internal string structures of complex attributes (e.g., verifying comma-separated multiple footnotes inside a single `FOOTNOTE` cell) is marked as an "Ask Ajai" item and is strictly excluded from this validation check. This rule only validates the *presence* of the attribute column in the output.

## Files Involved
- **Input:** Dataset-specific DSD file (e.g., `schema/dsd.csv` or similar file defining `ROLE`).
- **Output:** The generated data CSV file (e.g., `SDG_q1-2026_OBS_AG_FOOD_WST_data.csv`).


# Rule 10.1: Coded Attributes Mapping to Property Enum

## Requirement
All coded attributes within the dataset must be correctly mapped and assigned a `property:enum` value in the Data Commons Project (DCP) schema.

## Context & Rules
- According to Rule 10, all attributes (columns marked as 'Attribute' in the DSD) should become output columns along with the observation.
- For attributes that are specifically *coded* (meaning they pull from a defined codelist or restricted set of values, as opposed to free-text), the schema must reflect this by assigning a `property:enum` mapping.
- This ensures that coded attributes maintain their structural integrity and defined value set in the output DCP schema.


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

class Rule10Validator(BaseRuleValidator):
    def validate(self):
        self.setup_logging("Rule 10 (Attributes as Output Columns)")
        
        if not self.dsd_dir or not os.path.exists(self.dsd_dir):
            self.write_log(f"Could not find DSD directory for dataset {self.dataset_name}")
            print(f"Could not find DSD directory for dataset {self.dataset_name}")
            return False
            
        dsd_dir = self.dsd_dir
        dsd_files = glob.glob(os.path.join(dsd_dir, "*.csv"))
        
        if not dsd_files:
            self.write_log(f"No DSD files found in {dsd_dir}")
            return False

        total_files = len(dsd_files)
        failed_files = 0

        self.write_log(f"DSD Directory: {dsd_dir}")
        self.write_log(f"Output Directory: {self.processed_dir}\n")
        
        # Rule 10.1: Load schema to check Enum mapping
        schema_file = os.path.join(self.dataset_dir, "schema", f"un_codelist_schema_{self.dataset_name}.mcf")
        schema_content = ""
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_content = f.read()

        for dsd_path in sorted(dsd_files):
            filename = os.path.basename(dsd_path)
            match = re.search(r'_DSD_(.*?)\.csv', filename)
            if not match:
                continue
            series = match.group(1)

            csv_pattern = os.path.join(self.processed_dir, f"*_OBS_{series}_data.csv")
            csv_files = glob.glob(csv_pattern)

            if not csv_files:
                self.write_log(f"[{series}] SKIPPED: Missing corresponding CSV file.")
                continue

            csv_path = csv_files[0]
            errors = []
            attributes = []
            coded_attributes = []

            with open(dsd_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    role = row.get('ROLE', '').strip().lower()
                    concept = row.get('CONCEPT', '').strip()
                    repr_type = row.get('REPRESENTATION', '').strip().lower()
                    
                    if role == 'attribute':
                        attributes.append(concept)
                        if repr_type == 'coded':
                            coded_attributes.append(concept)

            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader, [])
                sanitized_headers = [sanitize_for_match(h) for h in headers]

            attr_column_map = {
                'UNIT_MEASURE': 'unit',
                'FREQUENCY': 'opservationperiod',  # Pipeline typo
                'UNIT_MULT': None,  # Consumed by Rule 7, not in CSV
            }
            
            for attr in attributes:
                attr_upper = attr.upper()
                
                # Rule 10.1: Check Enum mapping for coded attributes
                if attr in coded_attributes:
                    if schema_content:
                        # Find the node for this unConcept
                        concept_pattern = rf"Node: dcid:([^\n]+)\n(?:[^\n]+\n)*?unConcept: \"{attr_upper}\"\n"
                        # Wait, the node might have unConcept before or after rangeIncludes
                        # Let's search the whole block
                        block_pattern = rf"Node: dcid:[^\n]+(?:\n(?!\n).*)*unConcept: \"{attr_upper}\"(?:\n(?!\n).*)*"
                        match_block = re.search(block_pattern, schema_content)
                        if match_block:
                            block_text = match_block.group(0)
                            if "rangeIncludes: dcid:" not in block_text:
                                errors.append(f"File {os.path.basename(csv_path)}: Rule 10.1 Violation - Coded attribute '{attr}' does not have a 'rangeIncludes' enum mapping in the schema.")
                        else:
                            # It might be defined differently (e.g. unit)
                            if attr_upper not in ['UNIT_MEASURE', 'UNIT_MULT', 'FREQUENCY']:
                                errors.append(f"File {os.path.basename(csv_path)}: Rule 10.1 Violation - Coded attribute '{attr}' schema definition not found in un_codelist_schema.")
                
                if attr_upper == 'UNIT_MULT' or (attr_column_map.get(attr_upper) is None and attr_upper in attr_column_map):
                    continue

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

        print(f"Rule 10 Validation completed. {failed_files}/{total_files} files failed.")
        print(f"Details saved to {self.log_file}")
        
        return failed_files == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_10.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule10Validator(sys.argv[1], sys.argv[2])
    validator.validate()
