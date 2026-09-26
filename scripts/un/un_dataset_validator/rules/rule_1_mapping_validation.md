# Rule 1: 1:1 Mapping Validation (PV Maps)

## Requirement
Ensure all UN concepts and codes have a strict 1:1 mapping with the agency-specific DCP schema.

## Context & Rules (From Meeting Notes)
- There must be no duplicate properties assigned to a single concept.
- Within the Property-Value (PV) maps, the `event code` column must align perfectly with the `constraint property`.
- For example, if the concept is "age" or "poverty status", the `event code` must be "age" or "poverty status" exactly, maintaining consistency across the file.
- This rule applies strictly to the agency-specific schema rather than the base Data Commons mapping.

## Implementation Logic
1. **Target Files**: Locate and read PV map files (e.g., `CL_*.csv` or other common PV maps within an agency's schema folder).
2. **Column Validation**:
   - Verify the existence of the `event code` and `constraint property` columns.
   - For every row, ensure the value in the `event code` column exactly matches the value in the `constraint property` column.
3. **1:1 Mapping Enforcement**:
   - Validate that each concept has exactly one unique property assigned to it.
   - Flag any duplicate properties assigned to a single concept as a validation error.
4. **Scope**: Apply these checks within the context of the respective agency's schema files.

## Implementation Deviations
- **Canonical Formatting:** The Python script uses a `to_canonical_format` helper (which strips spaces, underscores, and standardizes case) to match `event code` (UnConcept) to `constraint property` (ConstraintProp), rather than requiring exact string equality.
- **Skipped Concepts:** The core concepts `series`, `geography`, `timeperiod`, and `obsvalue` are explicitly skipped during this 1:1 validation check.
