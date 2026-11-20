# Rule 10.1: Coded Attributes Mapping to Property Enum

## Requirement
All coded attributes within the dataset must be correctly mapped and assigned a `property:enum` value in the Data Commons Project (DCP) schema.

## Context & Rules
- According to Rule 10, all attributes (columns marked as 'Attribute' in the DSD) should become output columns along with the observation.
- For attributes that are specifically *coded* (meaning they pull from a defined codelist or restricted set of values, as opposed to free-text), the schema must reflect this by assigning a `property:enum` mapping.
- This ensures that coded attributes maintain their structural integrity and defined value set in the output DCP schema.

## Implementation Logic
1. **Target Files**: Data Structure Definition (DSD) files, source data files, and schema mapping files.
2. **Identification of Coded Attributes**:
   - Parse the DSD file to identify columns where the ROLE is defined as 'Attribute'.
   - Determine which of these attributes are "coded" (i.e., they reference a Code List / CL file).
3. **Enum Mapping Validation**:
   - Verify that for every coded attribute identified, the resulting schema generation logic assigns it a `property:enum` value mapping.
   - Check the output files to ensure that the schema correctly reflects the enum type for these specific attributes, while leaving text attributes as raw values.
4. **Error Flagging**:
   - If a coded attribute is found that is NOT mapped to a `property:enum` in the schema (e.g., if it is mapped as a plain text string), flag this as a validation error.

## Implementation Deviations
- **Temporarily Excluded:** During the June 23rd meeting, it was explicitly decided that all validations enforcing base DCP schema mappings are to be temporarily ignored pending further discussion with AJ. The validation script currently skips this check to align with this decision.