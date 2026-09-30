import argparse
import sys
import os

# Ensure the scripts directory is in sys.path
sys.path.append(os.path.dirname(__file__))

from test_rule_1 import Rule1Validator
from test_rule_2 import Rule2Validator
from test_rule_3 import Rule3Validator
from test_rule_4 import Rule4Validator
from test_rule_5_7 import Rule5And7Validator
from test_rule_6 import Rule6Validator
from test_rule_8 import Rule8Validator
from test_rule_9 import Rule9Validator
from test_rule_10 import Rule10Validator
from test_rule_11 import Rule11Validator
from test_rule_12 import Rule12Validator
from test_rule_13 import Rule13Validator
from test_rule_14 import Rule14Validator
from test_rule_15 import Rule15Validator
from test_rule_16 import Rule16Validator
from test_rule_17 import Rule17Validator
from summary_generator import generate_summary_md

def main():
    parser = argparse.ArgumentParser(description="UN Data Commons Validation Runner")
    parser.add_argument("--dataset", required=True, help="Dataset name, e.g., sdg_q1-2026")
    parser.add_argument("--dataset_dir", required=True, help="Dataset directory, e.g., dcp_data_20260616/20260616/sdg_q1-2026")
    parser.add_argument("--input_data_dir", required=True, help="Path to raw input DATA directory")
    parser.add_argument("--dsd_dir", required=True, help="Path to DSD schemas directory")
    parser.add_argument("--rule", required=True, help="Rule to run (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, or all)")
    parser.add_argument("--log_dir", default="un_dataset_validator/logs", help="Directory to save logs")
    args = parser.parse_args()

    validators = {
        "1": Rule1Validator,
        "2": Rule2Validator,
        "3": Rule3Validator,
        "4": Rule4Validator,
        "5": Rule5And7Validator,
        "7": Rule5And7Validator, # Support calling rule 7 individually as alias
        "6": Rule6Validator,
        "8": Rule8Validator,
        "9": Rule9Validator,
        "10": Rule10Validator,
        "11": Rule11Validator,
        "12": Rule12Validator,
        "13": Rule13Validator,
        "14": Rule14Validator,
        "15": Rule15Validator,
        "16": Rule16Validator,
        "17": Rule17Validator,
    }

    if args.rule.lower() == "all":
        # Run rules 1–6, 8–17 in order (6.1, 10.1, 13.1 sub-rules are temporarily excluded)
        rules_to_run = ["1", "2", "3", "4", "5", "6", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17"]
    else:
        rules_to_run = [r.strip() for r in args.rule.split(",")]

    all_passed = True
    for rule in rules_to_run:
        if rule not in validators:
            print(f"Unknown rule: {rule}")
            sys.exit(1)
            
        validator_class = validators[rule]
        validator = validator_class(args.dataset, args.dataset_dir, input_data_dir=args.input_data_dir, dsd_dir=args.dsd_dir, log_dir=args.log_dir)
        print(f"--- Running Rule {rule} ---")
        passed = validator.validate()
        if not passed:
            all_passed = False

    if args.rule.lower() == "all":
        try:
            generate_summary_md(args.dataset, args.log_dir)
        except Exception as e:
            print(f"Error generating summary.md: {e}")

    if not all_passed:
        print("\nSome validations FAILED. Check logs for details.")
        sys.exit(1)
    else:
        print("\nAll validations PASSED.")

if __name__ == "__main__":
    main()

