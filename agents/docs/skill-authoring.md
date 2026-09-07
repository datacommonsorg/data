# Repository agent skill authoring

Use this guide when adding or reorganizing skills under `agents/`.

## Repository locations

| Content | Location |
|---|---|
| Runtime skill entry point | `agents/skills/<skill>/SKILL.md` |
| Skill-specific references | `agents/skills/<skill>/references/` |
| Shared agent-readable references | `agents/common/references/` |
| Shared configuration | `agents/common/config/` |
| Shared Python helpers and tests | `agents/common/scripts/` |
| Python helper wrapper | `agents/common/run_python.sh` |
| Starter prompts | `agents/prompts/` |
| Human maintenance guidance | `agents/docs/` |
| Golden evaluation queries | `agents/evals/` |

Keep contributor guidance in `agents/docs/`, outside runtime skill
directories.

## Expose skills

- For automatic loading in Antigravity, prefer adding the skill's canonical
  directory path to `.agents/skills.json`.
- Add human entry points, starter prompts, and authoring guides to
  `agents/README.md` when they need to be discoverable.
- Remove obsolete names instead of adding aliases unless compatibility is
  explicitly required.

## Keep ownership clear

- Keep instructions and operations used by one skill inside that skill.
- Move content to `agents/common/` only when it has another real consumer.
- Keep common references consumer-neutral. Skills may link to common
  references; common references must not link into skill directories.
- Keep shared configuration and reusable Python execution helpers in
  `agents/common/`.
- Prefer a service or domain reference over a separate file for every command.
  Do not introduce a recipe hierarchy unless a concrete need emerges.

## Keep runtime guidance focused

- Describe the user problem and the skill's capability, not its file inventory.
- State clear `Use when` and `Do not use for` boundaries.
- Keep scope, safety, and common routes in `SKILL.md`. Link details needed only
  in some cases.
- Write routes using terms users will recognize. Clarify ambiguous terms instead
  of silently choosing a meaning.
- Use source-relative Markdown links. Referenced sections must have unique,
  plain ATX headings; link text does not need to match the heading.

## Document external inputs when useful

- Use `Required inputs` for values needed before work can begin.
- Use `Inputs resolved when needed` for values that only some flows require.
- Place input sections near the top, before safety and workflow instructions.
- Omit empty input sections.
- Prefer values supplied by the user.
- Use stable `<NAME>` placeholders throughout the skill.
- Write unresolved cross-repository paths as inline code rather than Markdown
  links. Use a Markdown link after the destination is resolved.
- Keep resolution and validation instructions together.

For example:

- Unresolved: `<IMPORT_REPO>/docs/usage.md`
- Resolved: [Import tool usage](https://github.com/datacommonsorg/import/blob/master/docs/usage.md)

A table is useful when a skill has multiple inputs:

| Input | Resolution |
|---|---|
| `<INPUT_NAME>` | Describe how to resolve and validate the value. |

## Useful authoring tips

These tips complement the target agent's guidance. Follow client-specific rules
when they differ.

- Use representative user requests to shape triggers, routes, and tests. For
  example, "Why did this import fail?" should route to troubleshooting.
- Focus on repository knowledge, procedures, and non-obvious edge cases. Skip
  background the agent already handles well.
- Use bullet points for distinct constraints and directives: LLMs treat bullet
  items as actionable checklists, whereas rules buried in paragraphs are easily
  overlooked.
- Keep instructions punchy, imperative, and scannable: Short, direct commands
  give rules maximum instruction-following weight.
- Explicitly ban unverified assumptions: Instruct the agent to trace code paths,
  verify edge cases, and ground findings in actual tool/code output rather than
  guessing.
- State the situation and action together. For example, "If no Batch job ID
  exists, inspect Scheduler."
- Use short sentences and consistent terms.
- Prefer one source for detailed information. Repeat small details when useful.
  For example, keep a full Batch command in `batch.md` and a short route to it
  in `SKILL.md`.
- Be prescriptive when mistakes are risky. Allow judgment otherwise.
- Improve skills based on observed failures.

For diagnostics-specific routing and troubleshooting conventions, see
[DC import diagnostics authoring](dc-import-diagnostics-authoring.md).

## Important: Define Python execution

When authoring or updating a skill that runs Python, make its runtime
instructions follow these rules:

- Give a user-provided Python environment highest priority. Otherwise, use the
  repository-local Python virtual environment at `.env/`.
- With the repository environment:
  - Run helper scripts with `./agents/common/run_python.sh`.
  - Run tests with `./run_tests.sh -p <directory>`.
  - Run other Python commands with `.env/bin/python`.
  - If dependencies are missing or stale, run `./run_tests.sh -r`, then retry.
- Ask before other dependency installations.
- Report an unusable environment. Never fall back to global `python` or
  `python3`.

## Validate changes

- Add or update golden queries in `agents/evals/` for important routing
  behavior.
- Keep structural and behavioral assertions in
  `agents/common/scripts/skill_contract_test.py` or the relevant operational
  test.
- Rely on the contract tests for reachable Markdown links, section fragments,
  registered skill paths, and the common-to-skill dependency boundary.
- Avoid contracts for prose wording, document counts, schemas, or deleted
  historical paths.

Run:

```sh
.env/bin/python -m unittest discover -v -s agents/common/scripts -p '*_test.py'
./run_tests.sh -l
git diff --check
```
