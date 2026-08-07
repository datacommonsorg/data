# Agents

This directory contains repository-owned agent skills, shared references,
recipes, configuration, and support scripts.

For local tools, Python dependencies, Google Cloud authentication, and the
optional sibling checkout, see [dependency setup](dependency-setup.md).

## Inspect imports

For read-only ET import information, use the
[`dc-import-info` starter prompt](prompts/dc-import-info-starter.md). Copy the
prompt into the agent conversation and append the specific import question.
The prompt routes the request through the repository-owned `dc-import-info`
skill and its bounded recipes.
