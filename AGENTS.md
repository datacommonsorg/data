# Data Commons data imports

Scripts, configs, and tools that bring external datasets into the Data Commons
knowledge graph.

## Folders

Read a folder's README before working in it.

- [`agents/`](agents/README.md): agent skills, starter prompts, and evals for
  import diagnostics and review.
- [`docs/`](docs/README.md): adding a dataset to Data Commons: data model, MCF
  format, workflow.
- [`import-automation/`](import-automation/README.md): scheduled import jobs
  (Cloud Batch executor) and the ingestion pipeline.
- [`scripts/`](scripts/README.md): per-source import scripts that convert raw
  data to MCF or TMCF + CSV.
- [`simple_imports/`](simple_imports/README.md): config-only imports for the
  Simple Stats Importer.
- `statvar_imports/`: per-source imports built with the StatVar Processor (PV
  maps and configs).
- [`tools/`](tools/README.md): shared import tools: StatVar Processor, place
  resolution, validation, differ.
- [`util/`](util/README.md): Python and Go libraries for writing MCF and testing
  imports.

## Imports

Imports live in `scripts/` and `statvar_imports/`. Imports on auto-refresh also
have a `manifest.json`; read the
[manifest reference](agents/common/references/import-automation/manifest.md)
before interpreting or editing one.

- Diagnose an import (config, schedule, status, output, failures): follow
  [`dc-import-diagnostics`](agents/skills/dc-import-diagnostics/SKILL.md).
- Review import changes: follow
  [`dc-import-code-review`](agents/skills/dc-import-code-review/SKILL.md).

## Python environment

From the repo root, `./run_tests.sh -r` creates `.env` and installs
`requirements_all.txt`. Run Python with `.env` activated.

## Tests and lint

- Test a folder: `./run_tests.sh -p <folder>`, e.g.
  `./run_tests.sh -p tools/statvar_importer/`.
- Tests are `*_test.py` files. Discovery needs an `__init__.py` in the test's
  directory and every parent up to the top-level folder.
- Lint check: `./run_tests.sh -l`. Fix: `./run_tests.sh -f`.
