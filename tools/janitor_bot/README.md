# Janitor Bot: AI-Powered Code Health

Janitor Bot is a CLI tool that uses Google Cloud Vertex AI (Gemini models) to automatically improve code health. It acts as a collection of specialized "personas," each dedicated to a specific maintenance task.

## Personas

1.  **The Librarian:** Adds missing Google-style docstrings to functions.
2.  **The Import Cleaner:** Removes unused import statements.
3.  **The Dead Code Remover:** Identifies and deletes unreachable code.
4.  **The Typer:** Adds PEP 484 type hints to function signatures.

## Prerequisites

1.  **Python 3.10+**
2.  **Google Cloud Project** with Vertex AI API enabled.
3.  **Authentication:** `gcloud auth application-default login` or a Service Account key.

## Installation

The bot is part of the `tools` package. Ensure you are in the project root and have the virtual environment activated.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install google-cloud-aiplatform
```

## Usage

Run the bot as a module using `python3 -m tools.janitor_bot.main`.

### Common Arguments

*   `--mode`: The persona to run (`librarian`, `import_cleaner`, `dead_code_remover`, `typer`).
*   `--target`: File or directory to scan.
*   `--apply`: If set, changes are written to disk. If omitted, runs in **Dry Run** mode (prints preview).
*   `--project`: GCP Project ID (default: `stuniki-runtimes-dev`).
*   `--verify / --no-verify`: Enable/disable syntax checking before saving (default: True).

### Examples

#### 1. Generate Docstrings (The Librarian)
Scans a file and adds docstrings to functions that lack them.

```bash
python3 -m tools.janitor_bot.main \
  --mode librarian \
  --target tools/statvar_importer/utils.py \
  --apply
```

#### 2. Clean Unused Imports
Scans a directory and removes unused imports from all Python files.

```bash
python3 -m tools.janitor_bot.main \
  --mode import_cleaner \
  --target tools/statvar_importer \
  --apply
```

#### 3. Remove Dead Code
Identifies unreachable code (e.g., code after a return statement).

```bash
python3 -m tools.janitor_bot.main \
  --mode dead_code_remover \
  --target tools/statvar_importer/legacy.py \
  --apply
```

#### 4. Add Type Hints (The Typer)
Infers and adds type annotations to function signatures.

```bash
python3 -m tools.janitor_bot.main \
  --mode typer \
  --target tools/statvar_importer/utils.py \
  --apply
```

## Safety Net

The bot includes a built-in **Safety Net** (`tools/janitor_bot/runner.py`) that prevents it from breaking your code.

1.  **Backup:** The file content is read into memory.
2.  **Transform:** The AI persona generates the new code.
3.  **Verify:** The Runner compiles the generated code in a temporary file to check for **Syntax Errors**.
4.  **Apply:**
    *   If Syntax Check **Passes**: The changes are written to disk.
    *   If Syntax Check **Fails**: The changes are discarded, and an error is logged.

To disable this feature (use with caution), pass `--no-verify`.

```