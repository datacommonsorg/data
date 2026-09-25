# Summary of `tools/statvar_importer/schema` Directory

This directory contains a suite of Python tools designed for the semi-automated processing, generation, and validation of Data Commons schemas (MCF files). The tools leverage both traditional algorithms (e.g., text matching, graph resolution) and modern Large Language Models (LLMs) to map raw data concepts to the formal Data Commons graph, generate new schema definitions, and ensure quality.

---

## Core Modules

### 1. Data Annotation and PV-Map Generation

These modules are responsible for the initial step of mapping strings from a data source (like CSV headers) to Data Commons Property-Value (PV) pairs.

-   **`data_annotator.py`**:
    -   **Purpose**: The primary tool for annotating raw data strings. It analyzes strings from a CSV and suggests corresponding schema properties and values.
    -   **Key Classes**:
        -   `DataTypeAnnotator`: A rule-based classifier that identifies the type of data in a string (e.g., `DATE`, `PLACE`, `VALUE`) using regular expressions and keyword lists (`words_dates.txt`, `words_place_names.txt`).
        -   `DataAnnotator`: Orchestrates the annotation process for an entire file, using multiple `DataTypeAnnotator` instances to build a "PV Map" (a mapping from source strings to schema PVs).
    -   **Features**: Can optionally integrate with `LLM_PVMapGenerator` to refine its suggestions using an LLM.

-   **`llm_pvmap_generator.py`**:
    -   **Purpose**: Uses an LLM to generate high-quality PV mappings. It's often used as a second pass after `data_annotator.py`.
    -   **Key Classes**: `LLM_PVMapGenerator`.
    -   **Features**:
        -   Constructs a sophisticated prompt using the template from `llm_pvmap_prompt.txt`.
        -   Enriches the prompt with extensive context, including sample PV maps (`sample_pvmap.csv`), example StatVars (`sample_statvars.mcf`), and snippets of the user's data to help the LLM understand the domain.
        -   Parses the structured text output from the LLM back into a machine-readable PV map.

### 2. Schema Generation and Naming

Once a PV map exists, these tools help create the formal schema definitions (new properties, classes, and StatVars) and give them human-readable names.

-   **`schema_generator.py`**:
    -   **Purpose**: Automatically generates new schema nodes (in MCF format) for properties and enumeration values that are present in the data but missing from the existing schema.
    -   **Features**:
        -   If it encounters a new property (e.g., `myCustomProperty`), it creates a `dcs:Property` node, inferring its `domainIncludes` and `rangeIncludes`.
        -   If it encounters a new value for a property (e.g., `myCustomValue` for `myCustomProperty`), it creates a new enumeration member and, if necessary, a new `schema:Class` for the enumeration itself (e.g., `MyCustomPropertyEnum`).
        -   Includes a function (`generate_statvar_name`) to create a descriptive, standardized name for a `StatisticalVariable` based on its properties.

-   **`llm_statvar_name_generator.py`**:
    -   **Purpose**: Uses an LLM to generate or refine the human-readable `name` and `description` for `StatisticalVariable` nodes.
    -   **Key Classes**: `LLM_StatVarNameGenerator`.
    -   **Features**:
        -   Processes StatVars in batches to handle large files efficiently.
        -   Uses the `llm_statvar_name_prompt.txt` template, providing the LLM with examples of well-named StatVars for context.
        -   Can either generate names from scratch or correct grammatical/spelling errors in existing names.

### 3. Schema Matching and Resolution

These modules provide the core lookup capabilities, finding existing schema nodes that correspond to a query.

-   **`schema_matcher.py`**:
    -   **Purpose**: Finds relevant schema nodes (properties or enum values) that match a given text query. This is crucial for bridging the gap between ambiguous source text and the formal schema.
    -   **Key Classes**: `SchemaMatcher`.
    -   **Features**: Employs a hybrid matching strategy:
        1.  **N-gram Matching**: Fast, text-based search for nodes where the `name`, `description`, or `dcid` contains the query terms.
        2.  **Semantic Matching** (optional): Uses ML embeddings to find semantically similar nodes, even if the keywords don't match exactly.

-   **`schema_resolver.py`**:
    -   **Purpose**: Resolves a partially defined node to a complete, existing node in the schema. It acts as a local, offline version of the Data Commons `/resolve` API.
    -   **Key Classes**: `SchemaResolver`.
    -   **Features**:
        -   Builds an in-memory index from unique property-value pairs (e.g., `wikidataId:Q1234`) to a specific node DCID.
        -   For complex nodes like `StatisticalVariable`, it creates a unique "fingerprint" based on the combination of all its defining properties. This allows it to find an exact StatVar match even if the DCID is unknown.

### 4. Schema Quality and Validation

These tools ensure the generated and existing schemas are free of common errors.

-   **`schema_checker.py`**:
    -   **Purpose**: A linter/validator for schema MCF files.
    -   **Features**:
        -   **URL Validation**: Checks that any URL found in a property value is active and returns a successful HTTP status code.
        -   **Spell Checking**: Integrates with the `schema_spell_checker` to find typos.
    -   **Output**: Produces a report of all errors found in the checked files.

-   **`schema_spell_checker.py`**:
    -   **Purpose**: A specialized spell-checker for Data Commons schemas.
    -   **Features**:
        -   Built on the `pyspellchecker` library.
        -   Uses a custom dictionary (`words_allowlist.txt`) to prevent false positives on DC-specific terms (e.g., "dcid", "statvar").
        -   Intelligently extracts words from various formats, including `CamelCase` and `snake_case`.

### 5. Utility and Helper Modules

-   **`genai_helper.py`**:
    -   **Purpose**: A generic wrapper for making calls to a Generative AI model (e.g., Gemini).
    -   **Key Classes**: `GenAIHelper`.
    -   **Features**: Handles API key configuration, prompt formatting with parameters, and the request/response cycle. It includes a dry-run mode for debugging prompts without incurring API costs.

---

## Supporting Files

-   **`*_test.py`**: Unit tests for each of the corresponding modules, ensuring their logic is correct.
-   **`*.txt` Files**:
    -   `llm_*.txt`: Contain the prompt templates that instruct the LLMs on how to perform their tasks.
    -   `words_*.txt`: Contain lists of keywords and allowed terms used by the `data_annotator` and `schema_spell_checker`.
-   **`*.csv` and `*.mcf` Files**:
    -   These are sample data files used for testing the tools and providing few-shot examples to the LLMs (e.g., `sample_pvmap.csv`, `sample_schema.mcf`, `sample_statvars.mcf`).

---

## Overall Workflow

A typical workflow using these tools would be:

1.  **Annotate**: Use `data_annotator.py` on a raw CSV file to get an initial PV map.
2.  **Refine (Optional)**: Use `llm_pvmap_generator.py` to improve the PV map using an LLM.
3.  **Generate Schema**: Feed the PV map and the data into `stat_var_processor.py` (a higher-level tool in the parent directory) which uses `schema_generator.py` to create new StatVar definitions and any other required schema.
4.  **Generate Names**: Use `llm_statvar_name_generator.py` to add high-quality, human-readable names and descriptions to the newly created StatVars.
5.  **Validate**: Run `schema_checker.py` on the final MCF files to check for spelling mistakes and broken URLs before submission.
