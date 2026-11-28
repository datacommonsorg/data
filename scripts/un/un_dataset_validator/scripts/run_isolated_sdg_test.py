import os
import sys
import shutil

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    sdg_dir = os.path.join(base_dir, "dcp_data_20260616/20260616/sdg_q1-2026")
    test_data_dir = os.path.join(base_dir, "un_dataset_validator/test_data")
    
    # Target files
    csv_file = os.path.join(test_data_dir, "SDG_q1-2026_OBS_AG_FLS_PCT_data.csv")
    mcf_file = os.path.join(test_data_dir, "SDG_q1-2026_OBS_AG_FLS_PCT_data_stat_vars.mcf")
    
    if not os.path.exists(csv_file) or not os.path.exists(mcf_file):
        print(f"Error: Could not find test files. Ensure you are running this from the workspace root.")
        sys.exit(1)
        
    # Setup isolated test environment
    isolated_dir = os.path.join(base_dir, "un_dataset_validator/isolated_test_env")
    processed_dir = os.path.join(isolated_dir, "processed_data")
    logs_dir = os.path.join(isolated_dir, "isolated_logs")
    
    if os.path.exists(isolated_dir):
        shutil.rmtree(isolated_dir)
        
    os.makedirs(processed_dir)
    os.makedirs(logs_dir)
    
    # Copy targeted test files
    shutil.copy(csv_file, processed_dir)
    shutil.copy(mcf_file, processed_dir)
    
    # Symlink required dependency directories from the actual dataset
    for folder in ["pvmap", "schema", "dc_generated"]:
        src = os.path.join(sdg_dir, folder)
        dst = os.path.join(isolated_dir, folder)
        if os.path.exists(src):
            os.symlink(src, dst)
            
    print(f"✅ Isolated environment created at: {isolated_dir}")
    print(f"✅ Isolated logs will be stored in: {logs_dir}\n")
    
    # Dynamically load the un_dataset_validator rules
    sys.path.append(os.path.join(base_dir, "un_dataset_validator/scripts"))
    
    from test_rule_1 import Rule1Validator
    from test_rule_2 import Rule2Validator
    from test_rule_3 import Rule3Validator
    from test_rule_4 import Rule4Validator
    from test_rule_5_7 import Rule5And7Validator
    from test_rule_6 import Rule6Validator
    from test_rule_9 import Rule9Validator
    from test_rule_10 import Rule10Validator
    from test_rule_11 import Rule11Validator
    from test_rule_12 import Rule12Validator
    from test_rule_13 import Rule13Validator
    from test_rule_8 import Rule8Validator
    from test_rule_14 import Rule14Validator
    
    validators = [
        Rule1Validator, Rule2Validator, Rule3Validator, Rule4Validator,
        Rule5And7Validator, Rule6Validator, Rule8Validator, Rule9Validator, Rule10Validator, Rule11Validator,
        Rule12Validator, Rule13Validator, Rule14Validator
    ]
    
    all_passed = True
    for v_class in validators:
        rule_name = v_class.__name__.replace('Validator', '')
        # Instantiate validator pointing to the isolated directory & custom log folder
        v = v_class("sdg_q1-2026", isolated_dir, log_dir=logs_dir)
        print(f"--- Running {rule_name} ---")
        try:
            passed = v.validate()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"Error executing {rule_name}: {str(e)}")
            all_passed = False
            
    print("\n==============================")
    if all_passed:
        print("✅ All un_dataset_validators PASSED on the isolated test files.")
    else:
        print(f"❌ Some un_dataset_validators FAILED. Please review the specific logs inside:\n   {logs_dir}")
    print("==============================")

if __name__ == "__main__":
    main()