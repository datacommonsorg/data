---
name: dc-import-code-review
description: Reviews staged, unstaged, branch-comparison, or GitHub pull request changes to Data Commons imports under scripts/** and statvar_imports/**. Use when an import author or reviewer asks for an import-specific code review. Do not use for unrelated repository code or deployed-import diagnosis.
---

# Review Data Commons import changes

Review one explicitly selected import change set. Inspect every in-scope changed
hunk, report only supported findings, and leave the repository and GitHub
unchanged.

## Safety and scope

- Resolve the repository root with `git rev-parse --show-toplevel`. From that
  root, verify that `scripts/` and `statvar_imports/` exist, and run Git
  operations using repository-relative paths.
- Treat the repository and GitHub as read-only. Never edit the import, post or
  resolve review comments, approve a pull request, stage files, discard local
  changes, or change the active branch.
- Enumerate every changed path before filtering the review.
- Report findings only for changed files under `scripts/**` and
  `statvar_imports/**`.
- List changed paths outside those directories as skipped. Read unchanged or
  shared code only when needed to understand an in-scope change, and do not
  report unrelated findings from that context.
- Stop and report that there are no import changes when the selected target has
  no changed paths in scope. Do not fall back to a general repository review.

## Resolve the review target

Require exactly one target before reviewing:

| User intent | Change set |
|---|---|
| Staged changes | Index versus `HEAD` |
| Unstaged changes | Working tree versus index, plus untracked files |
| All local changes | Working tree and index versus `HEAD`, plus untracked files |
| Changes against a branch | Merge base of the explicit base ref and `HEAD` through `HEAD` |
| Pull request | Exact pull request diff and head commit |

If the review target is ambiguous, ask whether to review staged, unstaged, all
local, branch-comparison, or pull request changes. If a branch comparison lacks
an exact base ref, ask for it. Do not infer `master`, `main`, a remote, or a
combination of local changes.

Use Git to acquire local targets without changing repository state:

- For staged changes, use `git diff --cached`.
- For unstaged tracked changes, use `git diff`. Enumerate untracked files with
  `git ls-files --others --exclude-standard` and treat their complete contents
  as changed.
- For all local changes, use `git diff HEAD` and include the complete contents
  of untracked files.
- For a branch comparison, resolve `git merge-base <BASE_REF> HEAD` and compare
  that commit through `HEAD`. Exclude staged, unstaged, and untracked work
  unless the user separately selected local changes.

For each target, first collect its complete changed-path list without a
pathspec. Then acquire the in-scope diff for `scripts/` and `statvar_imports/`.
Preserve additions, modifications, deletions, and renames in the coverage
record.

## Review a pull request

Accept a `datacommonsorg/data` pull request number or URL. Use `gh` for every
GitHub operation.

Start with these read-only commands:

```bash
gh pr view <PR> --repo datacommonsorg/data \
  --json number,title,url,baseRefName,baseRefOid,headRefOid,changedFiles,additions,deletions,files
gh pr diff <PR> --repo datacommonsorg/data
```

1. Use the metadata to record the pull request identity, exact base and head
   SHAs, changed-file count, additions, and deletions.
2. Use the pull request diff as the authoritative description of the change
   set when it is complete. Enumerate its changed files before applying the
   import-path filter.
3. Review from the diff when it is complete and contains enough context.
4. Create a detached temporary worktree at the exact head SHA when the diff is
   unavailable or incomplete, a changed file is renamed, binary, or generated,
   behavior crosses files, complete manifest references are needed, or focused
   checks require a checkout.

Never run `gh pr checkout` over the active worktree. When a temporary worktree
is needed:

- Create a unique root with `mktemp -d` and record its resolved path.
- Fetch the pull request head and base from `datacommonsorg/data` without
  switching the active branch.
- Verify the fetched head and base SHAs match `gh pr view` before adding the
  detached worktree.
- Continue to use the pull request diff to identify changed lines when it is
  complete. If it is unavailable or incomplete, compare the verified base and
  head commits locally and report that fallback as a limitation.
- Remove the detached worktree with `git worktree remove` after the review.
  Remove no path that was not created and validated by this run.

If GitHub metadata, the diff, or a required fetch is incomplete, report the
limitation instead of claiming complete coverage.

## Load review guidance

Read [import code review guidelines](references/guidelines.md) for every
review. Follow its links to repository documentation when relevant to the
changed import files. Apply a recommendation only when it is relevant to the
changed behavior.

When any in-scope `manifest.json` changes, also read the current shared
[import manifest reference](../../common/references/import-automation/manifest.md).
Use the shared reference for current fields and requirements; do not
reconstruct the manifest contract from historical guidance.

Apply repository instructions to changed import code without duplicating their
generic language and style rules in the import guidelines.

If documentation conflicts with the current implementation, treat the code as
the implementation truth. Call out the conflict and its implications in the
review; do not resolve it silently.

## Review changed behavior

- Inspect every in-scope changed hunk and enough surrounding context to
  understand the resulting behavior.
- Trace changed manifests to referenced scripts and inputs when those
  relationships are affected.
- Trace downloads and transformations far enough to evaluate completeness,
  failure handling, retries, data loss, mappings, validation, and tests.
- Anchor each finding to a changed line whenever possible. Unchanged context
  may support a finding but may not become an unrelated finding.
- Report only issues introduced or exposed by the selected change set. Do not
  turn pre-existing problems into review findings.
- Run only focused checks useful for the selected import. State exactly what
  ran, what passed or failed, and what could not run.
- Prefer hermetic checks. Do not run tests that call live source, Data Commons,
  or cloud APIs or require credentials unless the user explicitly requests
  them and the prerequisites are available. Bound each check, and stop and
  report a stalled check instead of waiting indefinitely.
- Prefer no finding over a speculative finding. State missing context as a
  limitation.
- Report a positive finding only for a meaningful, reusable import practice.
  Do not praise routine syntax, formatting, or merely the absence of a defect.

## Assign remediation priority

Use priority to describe remediation urgency, not confidence:

| Priority | Meaning |
|---|---|
| P0 | Immediate security issue, broad data corruption, or production emergency |
| P1 | Likely incorrect data, import failure, or serious reliability problem |
| P2 | Realistic validation, testing, maintainability, or operational risk |
| P3 | Minor, localized improvement |

Positive findings are unranked. If there are no actionable findings, say so
directly without claiming correctness beyond the reviewed evidence.

## Report the review

Use this Markdown structure for the review:

```markdown
## Review scope

- Target: <staged | unstaged | all local | branch comparison | PR>
- Reviewed: <in-scope files and changed hunks>
- Skipped: <out-of-scope changed files, if any>

## Findings

### [P1] <Category>

- path/to/file.py:42 - Brief description
  - Finding: What the changed code does incorrectly.
  - Impact: Concrete data, operational, or maintenance consequence.
  - Recommendation: Specific corrective action.

## Positive findings

- path/to/file.py:80 - Meaningful reusable pattern ✓
  - Finding: Good - What was done correctly.

## Coverage

| File | Status | Result |
|---|---|---|
| path/to/file.py | Reviewed | One P1 finding |
| path/to/manifest.json | Reviewed | No findings |

## Verification and limitations

- Checks run: <commands or none>
- Checks not run: <reason>
- Limitations: <missing context or none>
```

Order actionable findings by P0 through P3. Every actionable finding must
include `Finding`, `Impact`, and `Recommendation`. Every positive finding must
include `Finding: Good - <WHAT WAS DONE CORRECTLY>`. Use the exact `File`,
`Status`, and `Result` coverage columns shown above, and include every in-scope
changed file, including files with no findings.
