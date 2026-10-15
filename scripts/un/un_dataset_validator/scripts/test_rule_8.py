"""
VALIDATION RULE:
================
# Rule 8: UNIT_MEASURE Mapping and Multiplier Logic Integration

## Requirement
`UNIT_MEASURE` must be mapped to a Data Commons Project (DCP) enum using the name from the source dataset. Additionally, validation logic for `UNIT_MEASURE` should be closely integrated with multiplier logic.

## Context & Rules (From Meeting Notes)
- The checklist initially marked this as an "ASK AJAI" item regarding how to map `UNIT_MEASURE` to a DCP enum and what to set in the `shortDisplayName`.
- During the meeting, it was agreed that the mapping for rule number eight involves similar multiplier logic to what is used for applying multipliers (Rule 7).
- The decision was finalized to integrate this mapping and the associated multiplier logic into the existing validation code to ensure consistency when validating how units and multipliers are applied to values.


"""
import os
import sys
import glob
import csv

# We add the current directory to sys.path so we can import modules
sys.path.append(os.path.dirname(__file__))

from base_validator import BaseRuleValidator
from validator_utils import get_input_file_path

def load_unit_measure_map(pvmap_dir: str) -> dict:
    """Load UNIT_MEASURE -> DCP enum mappings from the PV map file."""
    candidates = [
        os.path.join(pvmap_dir, "CL_UNIT_MEASURE_pvmap.csv"),
        os.path.join(pvmap_dir, "common_pvmap_obs.csv"),
    ]
    # Also search global pvmap directory
    global_pvmap = os.path.join(
        os.path.dirname(os.path.dirname(pvmap_dir)), "pvmap"
    )
    candidates += [
        os.path.join(global_pvmap, "CL_UNIT_MEASURE_pvmap.csv"),
        os.path.join(global_pvmap, "common_pvmap_obs.csv"),
    ]

    for path in candidates:
        if not os.path.exists(path):
            continue
        unit_map = {}
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support two common PV map schemas
                un_code = (row.get('UnCode') or row.get('UnCodeKey') or '').strip().strip('"')
                prop_val = (row.get('ConstraintPropValue') or row.get('val') or '').strip()
                prop = (row.get('prop') or row.get('ConstraintProp') or '').strip()

                # Only capture rows that map UNIT_MEASURE codes (not multipliers)
                if un_code and prop_val and 'MULT' not in un_code.upper() and 'FREQ' not in un_code.upper():
                    unit_map[un_code] = prop_val
        if unit_map:
            return unit_map

    return {}


class Rule8Validator(BaseRuleValidator):
    def validate_file(self, output_csv_path: str, unit_map: dict) -> dict:
        output_mapping = {}  # (input_filename, line_num) -> unit_value
        typo_col = None

        with open(output_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if '#input' not in (reader.fieldnames or []):
                return {"status": "SKIPPED", "reason": "No #input column in output CSV"}

            # Locate the unit column (allow for casing variants)
            unit_col = next(
                (c for c in (reader.fieldnames or []) if c.lower() == 'unit'),
                None
            )
            if not unit_col:
                return {"status": "FAILED", "errors": ["Output CSV missing 'unit' column for UNIT_MEASURE."]}

            for row in reader:
                parts = row.get('#input', '').split(':')
                if len(parts) >= 2:
                    try:
                        line_num = int(parts[1])
                        output_mapping[(parts[0], line_num)] = row.get(unit_col, '').strip()
                    except ValueError:
                        pass

        if not output_mapping:
            return {"status": "SKIPPED", "reason": "No valid #input rows parsed"}

        input_filename = list(output_mapping.keys())[0][0]
        input_csv_path = get_input_file_path(self.dataset_name, input_filename, self.input_data_dir)
        if not input_csv_path or not os.path.exists(input_csv_path):
            return {"status": "FAILED", "errors": [f"Input file not found: {input_filename}"]}

        errors = []
        unmapped_codes = set()

        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fields_upper = {c.upper(): c for c in (reader.fieldnames or [])}

            unit_measure_col = (
                fields_upper.get('UNIT_MEASURE') or
                fields_upper.get('UNIT_MSR') or
                fields_upper.get('MEASURE')
            )
            if not unit_measure_col:
                return {"status": "SKIPPED", "reason": "No UNIT_MEASURE column in input CSV"}

            for line_idx, row in enumerate(reader, start=2):
                raw_code = row.get(unit_measure_col, '').strip()
                if not raw_code:
                    continue

                mapping_key = (input_filename, line_idx)
                if mapping_key not in output_mapping:
                    continue

                actual_unit = output_mapping[mapping_key]

                if not unit_map:
                    # No PV map loaded — just verify the unit column is non-empty
                    if not actual_unit:
                        errors.append(
                            f"File {input_filename}, Line {line_idx}: UNIT_MEASURE '{raw_code}' present in input "
                            f"but 'unit' column is empty in output."
                        )
                    continue

                expected_unit = unit_map.get(raw_code)
                if not expected_unit:
                    unmapped_codes.add(raw_code)
                    continue

                if actual_unit != expected_unit:
                    errors.append(
                        f"File {input_filename}, Line {line_idx}: UNIT_MEASURE '{raw_code}' -> "
                        f"expected '{expected_unit}', got '{actual_unit}'."
                    )

        if unmapped_codes:
            errors.append(
                f"UNIT_MEASURE codes not found in PV map (no expected value to verify): "
                f"{sorted(unmapped_codes)}"
            )

        if errors:
            return {"status": "FAILED", "errors": errors}
        return {"status": "PASSED"}

    def validate(self):
        self.setup_logging("Rule 8 (UNIT_MEASURE Mapping)")

        unit_map = load_unit_measure_map(self.pvmap_dir)
        if not unit_map:
            self.write_log(
                "WARNING: No UNIT_MEASURE PV map found. Validation will only check "
                "that the 'unit' column is non-empty when UNIT_MEASURE is present."
            )
        else:
            self.write_log(f"Loaded {len(unit_map)} UNIT_MEASURE mappings.")

        pattern = os.path.join(self.processed_dir, "*_data.csv")
        output_files = glob.glob(pattern)

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
            result = self.validate_file(filepath, unit_map)

            if result["status"] == "PASSED":
                passed += 1
            elif result["status"] == "SKIPPED":
                skipped += 1
                self.write_log(f"SKIPPED: {os.path.basename(filepath)} — {result.get('reason', '')}")
            else:
                failed += 1
                failed_details.append({
                    "filename": os.path.basename(filepath),
                    "errors": result["errors"],
                })

        self.write_log(f"\n--- Detailed Failure Report ---")
        if failed == 0:
            self.write_log("No validation failures detected.")
        else:
            for failure in failed_details:
                self.write_log(f"\nFAILED FILE: {failure['filename']}")
                errors = failure['errors']
                self.write_log(f"Total errors: {len(errors)}")
                for err in errors[:20]:
                    self.write_log(f"  - {err}")
                if len(errors) > 20:
                    self.write_log(f"  ... and {len(errors) - 20} more errors.")

        self.write_log(f"\n--- Validation Summary ---")
        self.write_log(f"Total files processed: {total}")
        self.write_log(f"Passed: {passed}")
        self.write_log(f"Failed: {failed}")
        self.write_log(f"Skipped: {skipped}")

        status_passed = failed == 0
        self.write_log(f"Overall Status: {'PASSED' if status_passed else 'FAILED'}")
        print(f"Rule 8 Validation complete. Results written to {self.log_file}")
        return status_passed


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_rule_8.py <dataset_name> <dataset_dir>")
        sys.exit(1)
    validator = Rule8Validator(sys.argv[1], sys.argv[2])
    validator.validate()
