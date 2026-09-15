# Merge mined import review signals

Apply strong recommendations produced by `dc-import-review-signal-miner` to
the Data Commons import code-review guidelines.

## Inputs

- Signal output directory: `<SIGNAL_OUTPUT_DIRECTORY>`
- Data repository path: `<DATA_REPOSITORY_PATH>`

Ask for either input if it is missing. Do not guess it.

## Check the repository

Resolve the repository root from `<DATA_REPOSITORY_PATH>`. Require a named
current branch and a clean checkout, including staged, unstaged, and untracked
files. If it is not clean, stop and list the dirty paths. Never stash, reset,
discard, or overwrite existing work.

Apply changes to the current branch. Do not fetch, switch, create, or delete a
branch. Do not stage, commit, push, or create a pull request.

Modify only
`agents/skills/dc-import-code-review/references/guidelines.md` in the data
repository.

## Select the signals

Require exactly one `import-review-signals-*.md` file in
`<SIGNAL_OUTPUT_DIRECTORY>`. If none or more than one exists, stop and ask the
user to disambiguate.

Treat each recommendation section in that projection as one signal. Use the
matching `import-review-comments-*.md` report only when more source context is
needed. Do not process comments marked `Not considered`, reclassify comments,
or modify either miner report.

## Merge the signals

Compare each signal semantically with the existing guidelines and current
repository implementation. Assign one disposition:

- `Added`: The recommendation is strong, general, new, and non-conflicting.
  Add one concise, neutral recommendation bullet under the best existing
  heading. Add a heading only when no existing heading fits.
- `Already covered`: An existing guideline expresses the same desired
  behavior. Do not replace, rewrite, or duplicate it.
- `Conflict`: The recommendation contradicts existing guidance or current
  implementation. Do not change the guidelines.
- `Skipped`: The recommendation is ambiguous, too specific, unsupported, or
  cannot be merged safely. Do not change the guidelines.

If several signals support the same new guideline, add it once and report a
decision for every signal. If a signal contains a clearly separable new point,
add only that point. Otherwise prefer no change.

Keep the guidelines simple:

- Phrase positive and corrective signals as neutral recommendations.
- Preserve existing recommendations and organization.
- Do not add guideline IDs, severity, confidence, evidence metadata, dates,
  reviewer identities, or source links.
- Do not duplicate generic repository language or style guidance.

## Write the merge report

Write
`<SIGNAL_OUTPUT_DIRECTORY>/import-review-signal-merge-<YYYYMMDD-HHMMSS>.md`
using the current UTC time. Do not overwrite an existing report.

Include a summary with the projection path, repository root, current branch,
HEAD commit, and disposition counts. Then include every signal using:

```markdown
### <SIGNAL RECOMMENDATION>

- Disposition: Added | Already covered | Conflict | Skipped
- Source comments: <URLS FROM THE PROJECTION>
- Existing guidance: <MATCHING OR CONFLICTING GUIDELINE> | None
- Change: <ADDED GUIDELINE BULLET> | None
- Rationale: <SPECIFIC REASON FOR THE DECISION>
```

End the report with checks run, checks not run, changed repository paths, and
explicit statements that changes were not staged, committed, pushed, or used
to create a pull request.

## Verify and finish

- Inspect the final diff and confirm no existing guideline was replaced.
- Confirm the only intended repository edit is `guidelines.md`. If the signal
  output directory is inside the repository, treat the merge report as an
  output artifact and never stage it.
- Run `git diff --check`.
- Run `python3 -m unittest agents.common.scripts.skill_contract_test` with the
  repository's configured Python environment when available. Do not install
  dependencies solely for this run; record unavailable checks in the report.
- Leave all changes unstaged and uncommitted on the current branch.
- Return the merge-report path, disposition counts, and verification results.
