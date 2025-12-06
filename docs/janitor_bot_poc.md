# Janitor Bot: AI-Powered Code Health Automation (Proof of Concept)

## Problem Definition
As the Data Commons codebase grows, maintaining high standards for code health—specifically documentation, type safety, and code cleanliness—becomes increasingly challenging. Engineering resources are often prioritized for critical feature work, leading to the accumulation of low-risk technical debt such as:
- Missing or incomplete docstrings.
- Lack of type hints (annotations).
- Unused imports and dead code.
- Outdated syntax.

This "bit rot" reduces code readability, increases the learning curve for new contributors, and hampers static analysis tools.

## Proposed Solution: The Janitor Bot
A "Janitor Bot" that incrementally improves code health using Large Language Models (LLMs) like Gemini via Vertex AI. This bot identifies specific code health issues and submits high-precision changes for human review.

### Key Personas (Capabilities)
For this Proof of Concept, we will focus on the following personas:

1.  **The Librarian (Primary Focus):**
    *   **Goal:** Improve code documentation.
    *   **Action:** Identifies functions and classes missing docstrings in utility folders. Generates Google-style docstrings based on the function's logic and signature.

2.  **The Janitor (Secondary Focus):**
    *   **Goal:** Cleanup code.
    *   **Action:** Detects and removes unused imports and dead code paths.

    3.  **The Typer:**
        *   **Goal:** Improve type safety.
        *   **Action:** Adds PEP 484 type hints to function signatures and includes necessary imports.

## Proof of Concept Scope

*   **Target Directory:** `tools/statvar_importer` (Contains a mix of utilities and logic suitable for testing).
*   **Infrastructure:** 
    *   Local Python script execution via `tools/janitor_bot/` package.
    *   Google Cloud Vertex AI (Gemini models) for code generation and analysis.
    *   GCP Project: `stuniki-runtimes-dev`
*   **Workflow:**
    1.  **The Librarian:**
        ```bash
        python3 -m tools.janitor_bot.main --mode librarian --target tools/statvar_importer --apply
        ```
    2.  **The Import Cleaner:**
        ```bash
        python3 -m tools.janitor_bot.main --mode import_cleaner --target tools/statvar_importer/some_file.py --apply
        ```
    3.  **The Dead Code Remover:**
        ```bash
        python3 -m tools.janitor_bot.main --mode dead_code_remover --target tools/statvar_importer/some_file.py --apply
        ```
    4.  **The Typer:**
        ```bash
        python3 -m tools.janitor_bot.main --mode typer --target tools/statvar_importer/some_file.py --apply
        ```

## Future Vision
*   Integration as a GitHub Action triggering on schedule.
*   Expansion to other personas (The Modernizer, The Refactorer, etc.).
*   Automatic Pull Request creation.
