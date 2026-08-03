# Plan: Human-in-the-Loop Schema Generation

This document outlines the plan to integrate human oversight into the schema generation process. The goal is to introduce checkpoints where the user can review, validate, and correct the tool's automated assumptions, thereby improving the quality and accuracy of the final schema.

---

## Guiding Principles

1.  **High-Leverage Checkpoints**: Introduce validation at stages where errors have the most significant downstream impact. The initial Property-Value (PV) map is the most critical of these.
2.  **Clear & Actionable Feedback**: The information presented to the user must be easy to understand, and the mechanism for providing feedback must be straightforward.
3.  **Modular Integration**: The interactive components should be built on top of the existing, non-interactive core libraries. This preserves the reusability of the core logic for fully automated workflows.

---

## Phase 1: Interactive PV-Map Validation

This is the highest-priority phase, as the PV-map is the foundation for all subsequent schema generation.

### 1. New Orchestrator Script: `interactive_schema_builder.py`

-   A new, top-level script will be created to manage the interactive workflow.
-   This script will be responsible for:
    1.  Taking user inputs (e.g., the path to the data file).
    2.  Calling the core library functions in sequence (`data_annotator`, `schema_generator`, etc.).
    3.  Managing the human-in-the-loop interaction points.

### 2. The Interactive Workflow

The script will execute the following steps:

**Step 1: Generate Initial PV-Map**
-   The orchestrator will call `data_annotator.py`'s `generate_pvmap` function.
-   This function will be run on the user-provided data file to produce a candidate PV-map.
-   The orchestrator may optionally call `llm_pvmap_generator.py` to have an LLM refine this initial map.

**Step 2: Present PV-Map for User Review**
-   A new function, `present_pvmap_for_review(pv_map)`, will be created.
-   This function will format the PV-map dictionary into a clean, human-readable markdown table and print it to the console.

    **Example Output:**
    ```
    ============================================================
    Proposed Property-Value Mappings for Review
    ============================================================
    | # | Source String       | Proposed Property | Proposed Value |
    |---|---------------------|-------------------|----------------|
    | 1 | total persons       | populationType    | Person         |
    | 2 | Men                 | gender            | Male           |
    | 3 | Under 5 years       | age               | [- 5 Years]    |
    | 4 | Wommen              | gender            | Female         |
    ------------------------------------------------------------
    ```

**Step 3: Implement the Feedback Loop**
-   After displaying the table, the script will prompt the user for action:
    ```
    Please review the mappings above.
    - To accept all, type 'accept'.
    - To edit, type 'edit'.
    - To quit, type 'quit'.
    Your choice:
    ```
-   **If `accept`**: The script proceeds to the next stage with the validated map.
-   **If `quit`**: The program terminates.
-   **If `edit`**: The script enters an interactive editing mode.

**Step 4: The Editing Mode**
-   The editing mode will allow the user to correct, add, or delete mappings.
-   The interaction will be as follows:
    ```
    Enter the number (#) of the row you want to edit.
    (Type 'add' to create a new mapping, or 'done' to finish editing)
    Your choice: 4

    Editing row #4: "Wommen"
    Current Property: gender
    Enter new Property (or press Enter to keep): gender

    Current Value: Female
    Enter new Value (or press Enter to keep): **Female**  <-- User corrects the typo

    Row #4 updated.
    ```
-   The `add` command will prompt for a new "Source String", "Property", and "Value".
-   The loop continues until the user types `done`, at which point the updated table is displayed for a final review.

**Step 5: Proceed with Validated Map**
-   Once the user accepts the PV-map, the orchestrator will pass this corrected map to the next tools in the pipeline (`schema_generator.py`, `llm_statvar_name_generator.py`, etc.) to complete the schema generation process.

---

## Phase 2: Final Schema Review (Future Enhancement)

After the core PV-map validation is implemented and tested, a second checkpoint can be added.

-   **Checkpoint**: Before writing the final MCF files (`new_schema.mcf`, `new_statvars.mcf`).
-   **Interaction**:
    -   The orchestrator will display a summary of the new schema nodes and StatVars that have been generated.
    -   This will be a simplified view, focusing on the `dcid`, `typeOf`, and `name` of the new nodes.
    -   The user will be given a final chance to `accept` or `quit` before the files are written to disk. This prevents the accidental creation of incorrect schema files.

---

## Required Code Changes

1.  **Create `interactive_schema_builder.py`**: This will be the main entry point for the new feature.
2.  **Create `present_pvmap_for_review()`**: A new utility function for formatting the PV-map.
3.  **Implement the editing logic**: The core loop for handling user input to modify the PV-map.
4.  **Minor modifications to core libraries (if necessary)**: Ensure that functions like `generate_pvmap` can return the map as a dictionary rather than only writing to a file. The goal is to minimize changes to these files.
