# Rule 13.1: Statvar Name Template

## Requirement
The name assigned to a Statistical Variable (StatVar) must adhere to a specific template format to ensure consistency and readability across the Data Commons Project (DCP).

## Context & Rules
- According to the checklist, the required template for a StatVar name is:
  `"<series name> [<concept name>=<code name>, ...]"`
- This template provides a clear, human-readable summary of the underlying data series and the specific constraint properties (concepts and codes) that define the statistical variable.
- For example, if the series is "Unemployment Rate" and the concepts are "Age" and "Gender" with codes "15-24" and "Female" respectively, the name should be constructed as:
  `"Unemployment Rate [Age=15-24, Gender=Female]"`

## Implementation Logic
1. **Target Files**: Output MCF files where StatVars are defined (e.g., `output_stat_vars.mcf`), and relevant source data/DSD files to fetch names.
2. **Template Validation**:
   - Extract the generated `name` property for each StatVar node.
   - Deconstruct the underlying series name and its associated constraint concepts and codes.
   - Verify that the generated name strictly matches the format: `"<series name> [<concept name>=<code name>, ...]"`
3. **Format Checks**:
   - Ensure the square brackets `[]` are used correctly to enclose the constraints.
   - Ensure a comma and a space `, ` separate multiple concept=code pairs.
   - Ensure an equals sign `=` separates the concept name and the code name.
4. **Error Flagging**:
   - Flag a validation error if a StatVar name does not conform to this template or if the constituent parts (series name, concept name, code name) do not accurately reflect the underlying data definition.

## Implementation Deviations
- **Skipped Execution:** This validation is currently skipped entirely by the script. Because the data pipeline does not reliably generate the `name` property for `StatisticalVariable` nodes (a known missing feature tracked under "Ask Ajai" rules), the script logs a warning and marks the validation as "PASSED (Skipped)".