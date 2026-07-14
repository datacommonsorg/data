# UN Dataset Validation Rules Consolidated Guide

This document consolidates all dataset validation rules used by the UN Data Commons validator. It serves as a single, cohesive, and readable reference for the schema mapping, format requirements, and validation checks enforced across datasets from various agencies (e.g., SDG, ILO, UNICEF).

---

## Rule 1: 1:1 Mapping Validation (PV Maps)

### Requirement
Ensure all UN concepts and codes have a strict 1:1 mapping with the agency-specific Data Commons Project (DCP) schema.

### Core Explanation
* **No Duplicate Properties:** There must be no duplicate properties assigned to a single concept.
* **Property-Value (PV) Alignment:** Within the PV maps, the `event code` column must align perfectly with the `constraint property` column. For example, if the concept is "age" or "poverty status", the `event code` must be "age" or "poverty status" exactly, maintaining consistency across the file.
* **Scope:** This rule applies strictly to the agency-specific schema rather than the base Data Commons mapping.

### Implementation & Verification Logic
1. **Target Files:** Locate and parse PV map files (e.g., `CL_*.csv` or other PV maps in the agency's schema folder).
2. **Canonical Matching:** The validation script uses a canonical format helper (stripping spaces, underscores, and standardizing case) to match `event code` (UnConcept) to `constraint property` (ConstraintProp) instead of requiring exact string equality.
3. **Core Exemptions:** The core concepts `series`, `geography`, `timeperiod`, and `obsvalue` are explicitly skipped during this 1:1 mapping check.

---

## Rule 2: SERIES Mapping to `populationType`

### Requirement
The `series` identifier from the input file must be mapped to the `populationType` property on the generated Statistical Variable nodes in the output `.mcf` file, prefixed with the responsible agency's identifier.

### Core Explanation
* **Series Source:** The series identifier is derived from the input filename (e.g., `AG_FLS_INDEX` from `SDG_..._AG_FLS_INDEX_data.csv`) or an explicit column within the input CSV.
* **Agency-Specific Prefix:** The series code in the `populationType` must be formatted as: `UN_<AGENCY_NAME>_SERIES-<SERIES_CODE>`.
  * *Example:* `populationType: dcid:UN_SDG_SERIES-AG_FLS_INDEX`
* **Case Sensitivity:** Convert the agency name to uppercase (e.g., `sdg` -> `SDG`) before forming the expected DCID.

### Implementation & Verification Logic
1. **Determine Context:** Identify the agency name (e.g., `SDG`, `ILO`, `UNICEF`) based on the root directory of the dataset.
2. **Validate MCF Nodes:** Iterate through all parsed nodes in the output MCF where `typeOf: dcid:StatisticalVariable`.
3. **Assert Property:** Ensure `populationType` exists and is equal to `dcid:UN_<AGENCY>_SERIES-<SERIES_CODE>`. Skip non-StatVar nodes to prevent false positives.

---

## Rule 3: GEOGRAPHY Mapping to `observationAbout`

### Requirement
The geographical identifiers found in the input dataset's geography columns must be mapped to the `observationAbout` column in the generated output `.csv` file. Geographical entities at the "Country" level or above must be successfully resolved to a Data Commons identifier (DCID).

### Core Explanation
* **Geography PV Map:** UN geographical codes are translated into valid DCIDs via the central mapping file `/all_data/pvmap/un_geography_pvmap.csv`.
* **Unresolved National Geographies (Rule 3.1):** If a geography code representing a country-level or higher place (e.g., countries, continents, global regions, Earth) cannot be resolved (or is marked as `#ignore`/`unmapped place`), it must be logged in an explicit error report (`missing_national_geographies.log`).

### Implementation & Verification Logic
1. **Load Reference Files:** Load `un_geography_pvmap.csv` for DCID lookup and `/all_data/un_geography.csv` to understand geographical hierarchies and names.
2. **Column Matching:** Validate that geography codes in the input column (e.g., `geo`, `REF_AREA`) match the expected DCID in the output CSV's `observationAbout` column.
3. **Row Alignment:** Use the output CSV's `#input` lineage column rather than raw indices to safely join and align rows between input and output files.

---

## Rule 4: Time Period to observationDate

### Requirement
Ensure that the `TIME_PERIOD` (or `timePeriod`) column in the source data accurately maps to the Data Commons `observationDate` property in the output CSV, utilizing conversion rules for complex or non-standard formats.

### Core Explanation
The data pipeline standardizes non-standard date formats into correct observation dates based on three validation levels:
1. **YYYY Format:** If the source matches a standard year, the validation checks if the `observationDate` matches the first 4 characters (YYYY) of the input.
2. **Interval Start Date Extraction:** If the input time format is an ISO-8601 interval (e.g., `2014-01/P3M`), the pipeline extracts the start date component (`2014-01`) as the `observationDate`.
3. **Fallback Passthrough:** If conversion checks fail, the value is passed through unaltered, and validation asserts exact string equivalence.

---

## Rule 5: OBS_VALUE Mapping to `value`

### Requirement
The observation value (`OBS_VALUE` column) from the input data must be mapped to the `value` property in the output CSV as a valid number (`value.number`).

### Core Explanation
* **Format Requirements:** The final value in the output must be formatted as a clean numeric value (e.g., `"1,000.50"` becomes `1000.50`) and must be parseable as a float.
* **Empty/Missing Values:** Missing or empty observation entries are mapped to empty/missing in the output rather than failing the numeric check.
* **Multiplier Interaction:** The final value in the output may be adjusted if unit multipliers apply (see Rule 7), but the requirement that the resulting value is a valid `{Number}` remains absolute.

---

## Rule 6: Dimensions vs. Attributes

### Requirement
All properties defined in the Dataset Definition (DSD) file must be correctly handled as either a **dimension** or an **attribute**.

### Core Explanation
* **Dimensions:** Except for specific exemptions (`Geography`, `Time Period`, `OBS_VALUE`, and `SERIES`), any property marked as a "dimension" must be attached to the Statistical Variable (StatVar) in the `.mcf` file as a **constraint property** (e.g., `product: dcid:UN_PRODUCT-X`).
* **Attributes:** Any property marked as an "attribute" (e.g., `CENSORED_VALUE_TYPE`, `FOOTNOTE`) must **NOT** be attached to the Statistical Variable. Instead, they must be included in the output data `.csv` file as separate columns (e.g., `censoredValueType`).

### Implementation & Verification Logic
1. **Parse DSD:** Load the DSD file and separate concepts by their `ROLE` column (dimension vs. attribute), ignoring the standard exemptions.
2. **Verify CSV Columns:** Ensure all attribute concepts appear as separate columns in the output CSV, and do not exist as properties inside MCF nodes.
3. **Verify MCF Constraints:** Ensure all non-exempt dimensions are attached to the corresponding Statistical Variable nodes as constraints.

---

## Rule 6.1: Dimension Mapping to DCP Schema with UN_ Prefix

### Requirement
Each dimension must be mapped to the Data Commons Project (DCP) schema using a common prefix `UN_` without including agency-specific prefixes.

### Core Explanation
* **Consistency:** Any schema generated from the DCP must consistently use the `UN_` prefix (e.g., `UN_PRODUCT-...`) instead of introducing agency-specific identifiers in the prefix (e.g., `UN_ECLAC_` or `UN_ILO_`).
* **Status:** This validation check is **temporarily ignored/skipped** in the validator scripts pending further clarification.

---

## Rule 6.2: Dimension Value Mapping

### Requirement
Every value within a dimension column must be properly mapped to a generated property value DCID following the exact template: `<prefix>_<CONCEPT>-<CODE>`.

### Core Explanation
* **Template Structure:** The expected format is `<prefix>_<CONCEPT>-<CODE>`, where:
  * `<prefix>` is typically `UN` (or configured per dataset).
  * `<CONCEPT>` is the capitalized dimension column name (e.g., `PRODUCT`).
  * `<CODE>` is the raw value from the input.
  * *Example:* `UN_PRODUCT-CPC2_1_0113`
* **Special Character Handling:** Any special characters or spaces in the raw value must be converted to underscores (`_`) before constructing the DCID.
* **Null Safety:** Missing or null values are ignored to prevent invalid strings (like `UN_PRODUCT-nan`).

---

## Rule 7: UNIT_MULTIPLIER Application

### Requirement
The observation value must be scaled and verified in the output dataset using the specified unit multiplier factor.

### Core Explanation
* **Lookup Factor:** The validator uses the common PV map `all_data/pvmap/CL_MULT_pvmap_multiply.csv` to resolve the numeric multiplication factor associated with the multiplier code (e.g., code `-15` maps to `1.00E-15`).
* **Multiplication Logic:** The expected output value is calculated as:
  `Expected_Value = float(Raw_OBS_VALUE) * float(Multiplier_Factor)`
* **Validation Check:** Assert that the calculated `Expected_Value` matches the `value` column in the output CSV, allowing for minor floating-point drift.

---

## Rule 8: UNIT_MEASURE Mapping and Multiplier Logic Integration

### Requirement
`UNIT_MEASURE` must be mapped to an existing Data Commons Project (DCP) enum using the name from the source dataset, and its validation must be closely integrated with the multiplier logic.

### Core Explanation
* **Enum Mapping:** Verify that each `UNIT_MEASURE` from the source maps correctly to a valid DCP enum corresponding to the unit defined in the source data.
* **Multiplier Integration:** Connect the validation of unit measures with unit multipliers to check that when a unit is applied, any corresponding multiplier scaling (e.g., scaling the value based on the multiplier enum) is also evaluated and applied correctly.

---

## Rule 9: Frequency to observationPeriod

### Requirement
Ensure that the `FREQUENCY` column in the source data correctly maps to the Data Commons `observationPeriod` property in the output CSV, according to the common Property-Value (PV) map.

### Core Explanation
* **Lookup Logic:** Cross-reference the input frequency code (e.g., `A` for Annual, `M` for Monthly, `Q` for Quarterly) with the `UnCode` column in `CL_FREQUENCY_pvmap_obsperiod.csv` to find the mapped observation period (e.g., `P1Y` for Annual).
* **Verification:** Verify that the resolved observation period is present in the `observationPeriod` column of the corresponding output CSV row.
* **Header Typo Handling:** The pipeline has been known to generate files with the header `opservationPeriod` instead of `observationPeriod`. The validator dynamically checks for this typo, logs it, and flags it as a failure if the correct header is missing.

---

## Rule 10: Attributes as Output Columns

### Requirement
Every concept defined in the dataset's Data Structure Definition (DSD) file with a `ROLE` of `Attribute` must be present as a separate column in the output `data.csv` file.

### Core Explanation
* **Supplementary Data:** Attributes provide metadata (such as footnotes, observation statuses, or flags) and must NOT be attached to the Statistical Variables in the MCF.
* **Validation:** Filter the DSD for `ROLE='Attribute'`, extract their identifiers (e.g., `OBS_STATUS`, `FOOTNOTE`), and verify they exist as distinct columns in the output CSV header.
* **Exclusions (Rule 10.1):** Parsing and validating the internal string structures of complex attributes (e.g., verifying multiple comma-separated footnotes inside a single `FOOTNOTE` cell) is excluded from this validation check.

---

## Rule 10.1: Coded Attributes Mapping to Property Enum

### Requirement
All coded attributes within the dataset (attributes that reference a Code List / CL file) must be correctly mapped and assigned a `property:enum` value in the Data Commons Project (DCP) schema.

### Core Explanation
* **Schema Integrity:** Coded attributes pulling from a restricted set of values must reflect this in the schema by assigning a `property:enum` mapping to maintain structural integrity.
* **Status:** This validation check is **temporarily ignored/skipped** in the validator scripts pending further discussion.

---

## Rule 11: StatVar DCID Format & Special Characters

### Requirement
Validates that the Data Commons Identifier (DCID) generated for each Statistical Variable (StatVar) in the output `.mcf` matches the expected hierarchical template, and any illegal or special characters within the originating codes are converted to underscores (`_`).

### Core Explanation
* **DCID Template:** `<prefix>/<agency>/<SERIES>[.<CONCEPT>--<CODE>__…]`
  * *Example:* `dcid:undata/sdg/AG_FLS_INDEX.PRODUCT--AGG_ANIMAL_PROD`
* **Special Character Conversion:** Any spaces, dashes, slashes, or parentheses in the original series, concept, or code must be converted to underscores (`_`) before constructing the DCID string.
* **Regex Verification:** The validator applies a regular expression to enforce template structural integrity. It is flexible on the prefix and agency and expects underscores (`_`) as word separators rather than hyphens.

---

## Rule 12: Names (alternateName, Value names, nameWithLanguage)

### Requirement
Ensure that names for properties and values generated in the schema accurately reflect their source definitions in the DSD and Codelist files.

### Core Explanation
* **Validation Checks:**
  * **Rule 12.1 (Property Names):** A property's `alternateName` must match the corresponding name defined in the DSD file.
  * **Rule 12.2 (Value Names):** A value's name must match the name defined in the specific concept's codelist (`CL` file).
  * **Rule 12.3 (Multi-lingual Names):** Translations available in other languages must be added to the `nameWithLanguage` property.
* **String Normalization:** To prevent false mismatches from spacing or punctuation quirks, a `normalize_name()` function strips all punctuation, converts strings to lowercase, and normalizes spacing before comparison.
* **Omissions:** Due to a pipeline issue where `name` properties are omitted from `StatisticalVariable` nodes, the validator currently logs a warning rather than a failure for missing StatVar names.

---

## Rule 13.1: Statvar Name Template

### Requirement
The name assigned to a Statistical Variable (StatVar) must adhere to a specific template format to ensure consistency and readability.

### Core Explanation
* **Template Structure:** `"<series name> [<concept name>=<code name>, ...]"`
  * *Example:* `"Unemployment Rate [Age=15-24, Gender=Female]"`
* **Formatting Rules:** Uses square brackets to enclose constraints, comma-space to separate multiple pairs, and equals sign to separate concept and code names.
* **Status:** This validation is **currently skipped (passed with warnings)** because the pipeline does not reliably generate the `name` property for `StatisticalVariable` nodes.

---

## Rule 15: Duplicate Properties in Statistical Variables

### Requirement
No property key or concept code is allowed to be repeated twice within the same Statistical Variable (StatVar) definition.

### Core Explanation
* **Structural Consistency:** Duplicating dimension values violates the Data Commons structural requirements and can lead to inconsistent behavior downstream.
* **Validation Logic:** The script scans `.mcf` (or `.tmcf`) files for `Node: dcid:...` blocks, tracks all property keys defined inside each block, and flags an error if any property key is defined more than once in the same node.

---

## Rule 16: Observation Completeness (#input tracking)

### Requirement
Guarantees that no non-empty observations are improperly dropped during processing by tracing every valid input cell to an `#input` cell lineage reference in the output files.

### Core Explanation
* **Lineage Tracking:** The output CSV files contain an `#input` column in the format `filename:row:col` tracking the origin of each data point.
* **Validation Logic:**
  1. Parse and collect all `#input` cell references from generated output CSV files.
  2. Scan every raw input CSV file to identify cells containing non-empty observation values (e.g., in `OBS_VALUE`).
  3. Ensure that every identified valid input cell coordinates exist within the collected `#input` references.

---

## Rule 17: Name Constraints (Bracket and Code Prohibitions)

### Requirement
Ensures that the generated `name` properties in the dataset's schemas are human-readable, descriptive, properly formatted, and free of technical prefixes, file identifiers, or template artifacts.

### Core Explanation
* **Bracket Check (Rule 17.1):** A node's name must not start with a bracket `[` (ignoring leading whitespace), ensuring names are not raw template indicators.
* **Code Concept Check (Rule 17.2):** A node's name must not contain technical identifier codes, file prefixes (such as `CL_`, `DSD_`, `FSP`, `TFT`), or uppercase technical values containing underscores (e.g., `ISCED11_02`, `AGG_ANIMAL_PROD`).
* **Exemptions & Safeguards:**
  * Skipping name checks for `StatVarGroup` nodes since their names naturally contain taxonomic labels.
  * Protecting descriptive acronyms (e.g., `GDP`, `FDI`, `UNCLOS`, `CO2`, `ISIC4`, `MGCI`) from triggering false positives.

---

## Rule 18: Single-DCID Node Declarations and MCF Comma Prevention

### Requirement
Every `Node:` statement in MCF files must declare exactly one valid Data Commons Identifier (DCID) and must **never** contain commas (`,`). When representing hierarchical links or relationships using properties like `specializationOf:` or `memberOf:`, they must reference the correct consolidated parent DCID (using double-underscore `__` joiners) instead of incorrectly separating them with commas.

### Core Explanation
* **Origin & Context:** This issue was first identified in `SDG_statvars_groups.mcf` but can occur in similar MCF schema or StatVar group files across any other dataset. It usually stems from automated pipeline scripts incorrectly joining multiple concepts.
* **No Commas in Node Declarations:** Commas are invalid in a `Node:` line because each node definition block represents exactly one entity. Commas (such as `,dcid:`) in a `Node:` statement will crash MCF parsers.
* **Consolidated DCID Joiner (`__`):** Multidimensional or combined keys must use double underscores (`__`) to join constituent DCIDs within a single identifier rather than commas.
  * *Example (Invalid Node):* `Node: dcid:A,dcid:B,dcid:C`
  * *Example (Valid Node):* `Node: dcid:A__B__C`
* **Hierarchy Link Alignment (`specializationOf:` / `memberOf:`):** While commas are technically syntactically valid in `specializationOf:` or `memberOf:` properties to specify multiple distinct parent references, they must not be used to reference parts of a consolidated parent.
  * If a parent is defined as `dcid:A__B__C`, the child node's relationship must refer to `specializationOf: dcid:A__B__C`.
  * If the relationship is defined with commas as `specializationOf: dcid:A,dcid:B,dcid:C`, the parser will interpret it as three separate references to individual nodes (`dcid:A`, `dcid:B`, and `dcid:C`), none of which match the consolidated parent `dcid:A__B__C`, breaking the hierarchy link.

### Implementation & Verification Logic
1. **Assert No Commas in Node Values:** The validator scans every MCF file, identifies all lines beginning with `Node:`, and ensures no comma `,` is present in the DCID value string.
   * *Validation assertion:* `assert ',' not in node_dcid_str, f'Malformed Node name with "," at line {line_num}'`
2. **Synchronized Parent-Child Check:** Ensure that any `specializationOf:` or `memberOf:` lines referencing consolidated parents use double underscores `__` to match the corrected parent node's consolidated DCID.
