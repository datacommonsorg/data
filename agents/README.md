# Agents

This directory contains repository-owned agent skills, references,
configuration, and support scripts.

For local tools, Python dependencies, Google Cloud authentication, and the
optional sibling checkout, see [dependency setup](dependency-setup.md).

## Inspect or diagnose imports

For read-only ET import information or diagnosis, use the
[`dc-import-diagnostics` starter prompt](prompts/dc-import-diagnostics-starter.md).
Copy the prompt into the agent conversation and append the specific import
question. The prompt routes the request through the repository-owned
`dc-import-diagnostics` skill and its bounded operational references.
