import os
import re
from datetime import datetime

def extract_rule_num(filename):
    # Matches rule1, rule5and7, rule10, etc.
    m = re.match(r'rule(\d+)(?:and(\d+))?', filename)
    if m:
        return (int(m.group(1)), filename)
    return (999, filename)

def generate_summary_md(dataset_name: str, log_dir: str):
    output_path = os.path.join(log_dir, "summary.md")
    
    # Locate all logs for this dataset in log_dir
    files = []
    if os.path.exists(log_dir):
        for f in os.listdir(log_dir):
            if f.endswith(".log") and f.startswith("rule") and f"_{dataset_name}_" in f:
                files.append(f)
                
    files.sort(key=extract_rule_num)
    
    if not files:
        print(f"No validation log files found for dataset '{dataset_name}' in directory '{log_dir}'. Skipping summary.md generation.")
        return
        
    summary_lines = []
    summary_lines.append(f"# Validation Summary: {dataset_name}")
    summary_lines.append("")
    summary_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    summary_lines.append(f"**Log Directory:** `{log_dir}`  ")
    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("")
    
    stats = {
        "PASSED": 0,
        "FAILED": 0,
        "TOTAL": 0
    }
    
    matrix_lines = []
    matrix_lines.append("| Rule | Status | Summary |")
    matrix_lines.append("| :--- | :---: | :--- |")
    
    details_block = []
    
    for filename in files:
        filepath = os.path.join(log_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Determine Rule Title
        rule_header_match = re.search(r'--- (Rule [^ ]+(?: & \d+)?[^\-]+) ---', content)
        if rule_header_match:
            rule_name = rule_header_match.group(1).strip()
        else:
            rule_name = filename.replace(f"_{dataset_name}_validation.log", "").replace("_", " ").title()
            
        # Determine overall Status
        status = "PASSED"
        if "FAILED" in content or "FAILED" in filename or ("errors" in content.lower() and "No violations detected" not in content and "No global 1:1 mapping violations" not in content and "No validation failures detected" not in content):
            if "Overall Status: PASSED" in content:
                status = "PASSED"
            else:
                status = "FAILED"
                
        if "Overall Status: FAILED" in content:
            status = "FAILED"
        elif "Overall Status: PASSED" in content:
            status = "PASSED"
            
        stats[status] += 1
        stats["TOTAL"] += 1
        
        # Extract Summary section
        validation_summary_section = ""
        summary_idx = content.find("--- Validation Summary ---")
        if summary_idx == -1:
            summary_idx = content.find("Summary:")
            
        if summary_idx != -1:
            validation_summary_section = content[summary_idx:].strip()
            # clean up lines
            val_lines = [l.strip() for l in validation_summary_section.split("\n") if l.strip() and not l.startswith("---") and not l.startswith("Summary:")]
            validation_summary_section = " | ".join(val_lines)
        else:
            # Check for Overall Status or fallback
            lines = content.split("\n")
            status_lines = [l.strip() for l in lines if "overall status" in l.lower() or "validation results" in l.lower()]
            if status_lines:
                validation_summary_section = " | ".join(status_lines)
            else:
                validation_summary_section = "Completed validation execution."
                
        # Append to Matrix table
        status_badge = f"**PASSED**" if status == "PASSED" else f"**FAILED**"
        matrix_lines.append(f"| {rule_name} | {status_badge} | {validation_summary_section} |")
        
        # Build Detailed Breakdown
        details_block.append(f"### {rule_name}")
        details_block.append("")
        details_block.append(f"- **Status:** {status_badge}")
        if validation_summary_section:
            details_block.append(f"- **Summary:** {validation_summary_section}")
            
        # Parse failure report details if FAILED
        if status == "FAILED":
            details_block.append("- **Failure Details:**")
            details_block.append("  ```text")
            failure_section_match = re.search(r'--- Detailed Failure Report ---\s*(.*?)(?=\n---|\Z)', content, re.DOTALL)
            if failure_section_match:
                fail_details = failure_section_match.group(1).strip().split("\n")
                # Show up to 15 lines of errors
                for fd in fail_details[:15]:
                    details_block.append(f"  {fd}")
                if len(fail_details) > 15:
                    details_block.append(f"  ... and {len(fail_details) - 15} more lines of errors.")
            else:
                # Fallback: grab some error messages
                lines = content.split("\n")
                error_lines = [l for l in lines if "failed" in l.lower() or "error" in l.lower() or "invalid" in l.lower() or "missing" in l.lower()]
                for el in error_lines[:10]:
                    details_block.append(f"  {el}")
                if len(error_lines) > 10:
                    details_block.append(f"  ... and {len(error_lines) - 10} more errors.")
            details_block.append("  ```")
            
        details_block.append("")
        details_block.append("---")
        details_block.append("")
        
    summary_lines.append("## Overall Status Matrix")
    summary_lines.append("")
    summary_lines.extend(matrix_lines)
    summary_lines.append("")
    summary_lines.append(f"**Total Rules Run:** {stats['TOTAL']} | **Passed:** {stats['PASSED']} | **Failed:** {stats['FAILED']}  ")
    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("")
    summary_lines.append("## Detailed Rule Breakdowns")
    summary_lines.append("")
    summary_lines.extend(details_block)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
        
    print(f"Successfully generated validation summary report at: {output_path}")
