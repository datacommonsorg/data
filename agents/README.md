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

## Mine import review signals

To collect positive and corrective review signals from merged import pull
requests, use the `dc-import-review-signal-miner` skill through its
[`starter prompt`](prompts/dc-import-review-signal-miner-starter.md). The skill
produces a complete comment audit and a projection containing only strong,
unambiguous signals. It does not update guidelines or create a pull request.

Before running the prompt, ensure the agent has network access to GitHub and
can write to a temporary directory and the selected output directory. Then run
the skill's
[`prerequisite checker`](skills/dc-import-review-signal-miner/scripts/check_prerequisites.sh):

```bash
bash agents/skills/dc-import-review-signal-miner/scripts/check_prerequisites.sh
```

The checker validates `git`, GitHub CLI, authentication, and the exact `gh`
capabilities used by the skill. The mining skill does not require standalone
`jq`, Python, Google Cloud CLI, GCS access, or write access to the Data Commons
repository. Its GitHub commands were tested with GitHub CLI 2.74.2; the checker
reports the installed version without treating 2.74.2 as a minimum.
