# Rule 11: StatVar DCID Format & Special Characters

## Overview
This rule validates the structural format of the Data Commons Identifier (DCID) generated for each Statistical Variable (StatVar). The DCID must strictly adhere to a specific templated format, and any illegal or special characters within the originating codes must be converted to underscores (`_`) to ensure valid identifier syntax.

## Files Involved
- **Output:** `output_stat_vars.mcf` (Specifically examining the `Node: dcid:...` lines).

## Implementation Details

### 1. DCID Template
The DCID must be constructed using the following template:
`<prefix>/<agency>/<SERIES>[.<CONCEPT>--<CODE>__…]`

Where:
- `<prefix>` is generally `undata`.
- `<agency>` is the agency identifier (e.g., `sdg`).
- `<SERIES>` is the identifier of the series (e.g., `AG_FLS_INDEX`).
- The `[.<CONCEPT>--<CODE>__…]` portion represents the dimensional constraints attached to the StatVar, chained together. 

### 2. Special Character Conversion
Any special characters present in the original `<SERIES>`, `<CONCEPT>`, or `<CODE>` values (such as spaces, dashes, slashes, or parentheses) MUST be converted to underscores (`_`) before being concatenated into the DCID string.

## Example
Given an agency of `sdg`, a series of `AG_FLS_INDEX`, a concept of `PRODUCT`, and a code of `AGG_ANIMAL_PROD`:

**Expected MCF Node Definition:**
```
Node: dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD
```

## Python Implementation Strategy

1. **Parse MCF:** Read the `output_stat_vars.mcf` file and extract all values from the `Node:` property that begin with `dcid:`.
2. **Regex Validation:** Use a regular expression to validate the structural integrity of the extracted DCID against the expected template. A simplified regex structure would look like: `^dcid:undata/[a-z0-9_-]+/[A-Z0-9_-]+(\.[A-Z0-9_-]+--[A-Z0-9_-]+(__[A-Z0-9_-]+--[A-Z0-9_-]+)*)?$`. (Note: The exact regex will need to be refined based on the full scope of allowed characters in standard DCIDs, but it must enforce the template hierarchy).
3. **Character Check:** Independently verify that no spaces or unescaped/unconverted special characters exist within the identifier string after the `dcid:` prefix.
4. **Reconciliation (Advanced):** If the input data is available during this check, independently reconstruct the expected DCID using the input series and dimension codes (applying the underscore conversion logic) and verify it matches the DCID found in the MCF.

## Implementation Deviations
- **Flexible Agency/Prefix:** The implemented regular expression (`^dcid:[a-zA-Z0-9_]+/[a-zA-Z0-9_]+/...`) dynamically accepts any alphanumeric sequence for the prefix and agency, rather than hardcoding `undata`.
- **Hyphens vs. Underscores:** The strict regex implementation exclusively expects underscores (`_`) as word separators in series, concepts, and codes, differing from earlier examples that suggested hyphens (`-`) might be allowed.