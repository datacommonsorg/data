# Rule 15: Duplicate Properties in Statistical Variables

## Description
This rule ensures that no property or concept code is repeated twice within the same Statistical Variable (StatVar) definition. Duplicating dimension values unnecessarily violates the Data Commons structural requirements and can lead to inconsistent behavior downstream.

## Implementation Details
* **Script:** `scripts/test_rule_15.py`
* **Target:** Parsed `*_stat_vars.mcf` (or `.tmcf`) files located in the `processed_data` directory.
* **Validation Logic:** 
    1. Scan each file for StatVar definitions, identifying blocks that start with `Node: dcid:...`.
    2. Track all property keys defined inside that specific block.
    3. If any key is encountered more than once within the same node, flag it as a violation.

## Remediation
If this rule fails, review the PV map generation logic or custom mapping script. Ensure that dimension-value pairs are properly aggregated and that a single concept/property is only mapped once for a given Statistical Variable.