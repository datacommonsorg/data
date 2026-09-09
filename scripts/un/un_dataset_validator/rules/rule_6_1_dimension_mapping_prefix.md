# Rule 6.1: Dimension Mapping to DCP Schema with UN_ Prefix

## Requirement
Each dimension must be mapped to the Data Commons Project (DCP) schema using a common prefix `UN_` without including the specific agency prefix.

## Context & Rules (From Meeting Notes)
- The dataset is processed to create a schema. Any schema generated from the DCP must consistently use the `UN_` prefix for dimensions.
- Every node within the agency-specific schema files follows a "concept_value" structure.
- The mapping must ensure these dimensions correctly represent the concept without introducing agency-specific identifiers in the prefix (e.g., use `UN_` instead of `UN_ECLAC_`).

## Implementation Logic
1. **Target Files**: Locate and read the generated schema files or the mapping configurations that define how dimensions are output.
2. **Prefix Validation**:
   - For every dimension identified (where the ROLE is 'dimension' in the respective DSD), verify the resulting mapped output.
   - Check that the prefix applied is strictly `UN_`.
   - Flag an error if the prefix contains an agency name (e.g., `UN_ILO_` or `UN_WHO_`) or if the `UN_` prefix is entirely missing.
3. **Scope**: This applies to all datasets processed to create the DCP schema across all agencies.

## Implementation Deviations
- **Temporarily Excluded:** During the June 23rd meeting, it was decided that all validations mapping strictly to the base DCP schema (such as enforcing the `UN_` prefix mapping) are temporarily ignored pending further clarification from AJ. The validation script currently skips this check.