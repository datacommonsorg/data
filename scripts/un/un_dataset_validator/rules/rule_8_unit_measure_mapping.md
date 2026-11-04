# Rule 8: UNIT_MEASURE Mapping and Multiplier Logic Integration

## Requirement
`UNIT_MEASURE` must be mapped to a Data Commons Project (DCP) enum using the name from the source dataset. Additionally, validation logic for `UNIT_MEASURE` should be closely integrated with multiplier logic.

## Context & Rules (From Meeting Notes)
- The checklist initially marked this as an "ASK AJAI" item regarding how to map `UNIT_MEASURE` to a DCP enum and what to set in the `shortDisplayName`.
- During the meeting, it was agreed that the mapping for rule number eight involves similar multiplier logic to what is used for applying multipliers (Rule 7).
- The decision was finalized to integrate this mapping and the associated multiplier logic into the existing validation code to ensure consistency when validating how units and multipliers are applied to values.

## Implementation Logic
1. **Target Files**: Source data files (containing `UNIT_MEASURE`), DSD files, and schema mapping files.
2. **Enum Mapping Validation**:
   - Verify that each `UNIT_MEASURE` from the source is correctly mapped to an existing DCP enum.
   - The validation should check that the name used for the enum corresponds to the unit defined in the source data.
3. **Multiplier Logic Integration**:
   - Tie the validation of `UNIT_MEASURE` with the validation of `UNIT_MULTIPLIER`.
   - Ensure the code checks that when a unit is applied, any corresponding multiplier logic (e.g., scaling the value based on the multiplier enum) is also evaluated correctly.
   - Flag any mismatches where a unit measure does not successfully map to a DCP enum or where the integrated multiplier application fails.