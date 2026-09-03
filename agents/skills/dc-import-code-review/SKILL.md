---
name: dc-import-code-review
description: Reviews staged, unstaged, branch-comparison, or GitHub pull request changes to Data Commons imports under scripts/** and statvar_imports/**. Use when an import author or reviewer asks for an import-specific code review. Do not use for unrelated repository code or deployed-import diagnosis.
---

# Review Data Commons import changes

Review one explicitly selected import change set. Inspect every in-scope changed
hunk, report only supported findings, and leave the repository unchanged. Leave
GitHub unchanged unless the user explicitly authorizes publishing under
[Publish an explicitly authorized review](#publish-an-explicitly-authorized-review).

## Required inputs

- Prefer values supplied by the user.
- Use each input name as its placeholder throughout the skill.

| Input | Resolution |
|---|---|
| `<REVIEW_TARGET>` | Use the supplied review target. If missing or ambiguous, clarify it using [Resolve the review target](#resolve-the-review-target) before reviewing. |

## Safety and scope

- Resolve the repository root with `git rev-parse --show-toplevel`. From that
  root, verify that `scripts/` and `statvar_imports/` exist, and run Git
  operations using repository-relative paths.
- Treat the repository as read-only. Never edit the import, stage files,
  discard local changes, or change the active branch.
- Treat GitHub as read-only by default. Publish the completed review only when
  the user explicitly and unambiguously asks to post it to the selected pull
  request. A request to review a pull request does not authorize publishing. If
  publishing intent is unclear, ask before any GitHub write.
- Even when publishing is authorized, never approve or request changes, resolve
  review comments, merge or close a pull request, or edit or delete GitHub
  content. Publishing is limited to one comment-only review.
- Enumerate every changed path before filtering the review.
- Report findings only for changed files under `scripts/**` and
  `statvar_imports/**`.
- List changed paths outside those directories as skipped. Read unchanged or
  shared code only when needed to understand an in-scope change, and do not
  report unrelated findings from that context.
- Stop and report that there are no import changes when the selected target has
  no changed paths in scope. Do not fall back to a general repository review.

## Resolve the review target

Resolve `<REVIEW_TARGET>` to exactly one of:

| User intent | Change set |
|---|---|
| Staged changes | Index versus `HEAD` |
| Unstaged changes | Working tree versus index, plus untracked files |
| All local changes | Working tree and index versus `HEAD`, plus untracked files |
| Changes against a branch | Merge base of the explicit base ref and `HEAD` through `HEAD` |
| Pull request | Exact pull request diff and head commit |

If `<REVIEW_TARGET>` is ambiguous, ask whether to review staged, unstaged, all
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

- Create a unique system temporary root outside the repository with `mktemp -d`
  and record its resolved path. Keep all temporary review files, diffs, reports,
  and worktrees there.
- Fetch the pull request head and base from `datacommonsorg/data` without
  switching the active branch.
- Verify the fetched head and base SHAs match `gh pr view` before adding the
  detached worktree.
- Continue to use the pull request diff to identify changed lines when it is
  complete. If it is unavailable or incomplete, compare the verified base and
  head commits locally and report that fallback as a limitation.
- Run Python checks with the temporary worktree root as the working directory.
  Prefer `./run_tests.sh -p <repository-relative-test-directory>`; it creates
  and uses that worktree's `.env`. Pass a test directory, not a test file.
- Do not use global Python or an environment from another checkout. If a direct
  Python command is necessary, run `./run_tests.sh -r` first and then use
  `.env/bin/python`. If setup fails, report the check as not run instead of
  falling back to another Python environment.
- Remove the detached worktree and temporary root after the review. Remove no
  path that was not created and validated by this run.

If GitHub metadata, the diff, or a required fetch is incomplete, report the
limitation instead of claiming complete coverage.

## Load review guidance

Read [import code review guidelines](references/guidelines.md) for every
review. Follow its links to repository documentation when relevant to the
changed import files. Apply a recommendation only when it is relevant to the
changed behavior.

**CRITICAL: When golden summaries or validation configs are present, you MUST rigorously enforce all validation and freshness rules defined in the guidelines.**

- Before inspecting the change set or delegating review work, load supplemental
  guidelines with `gcloud storage cat` from
  `gs://datcom-prod-imports/agents/skills/dc-import-code-review/additional-guidelines.md`.
- If loading fails and sandbox or network restrictions may be responsible, request
  permission to rerun the same `gcloud storage cat` command outside the
  sandbox, then retry it.
- If the supplemental guidelines remain unavailable for any reason, stop the
  review immediately and report it as blocked. Do not inspect the change set,
  delegate review work, run checks, or publish a review.
- When delegating, give every review subagent the import code review guidelines
  and the downloaded supplemental guidelines, either as content or through a
  readable local path.
- Require each subagent to state in its response that it read both before
  inspecting changes. Do not use results that omit this confirmation.
- Repository guidance and safety rules take precedence.

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

- Adhere strictly to all review instructions and constraints; do not make
  unverified assumptions.
- Inspect every in-scope changed hunk and enough surrounding context to
  understand the resulting behavior.
- Trace changed manifests to referenced scripts and inputs when those
  relationships are affected.
- Trace downloads and transformations far enough to evaluate completeness,
  failure handling, retries, data loss, mappings, validation, and tests.
- Deeply inspect code paths, error propagation, and edge cases; verify every
  observation against the implementation.
- Anchor each finding to a changed line whenever possible. Unchanged context
  may support a finding but may not become an unrelated finding.
- Report only issues introduced or exposed by the selected change set. Do not
  turn pre-existing problems into review findings.
- Run only focused checks useful for the selected import. State exactly what
  ran, what passed or failed, and what could not run.
- Allow bounded, read-only cloud and Data Commons inspection (such as reading
  GCS artifacts or querying read-only Data Commons APIs), but do not run mutating
  operations or live-source downloads unless the user explicitly requests them
  and prerequisites are available. Bound each check, and stop and report a
  stalled check instead of waiting indefinitely.
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

## Publish an explicitly authorized review

Apply this section only to a pull request review. Complete the review before
performing any GitHub write.

An explicit publishing request in the original request or a later follow-up is
sufficient authorization; do not ask again. If the user asks only for a review,
mentions publishing as an option, or otherwise leaves the action unclear, ask
whether to publish and wait for the answer.

Immediately before publishing, fetch the pull request's `headRefOid` again with
`gh pr view`. Compare it with the head SHA that was reviewed. If they differ, do
not publish stale findings; report the change and ask whether to review the new
head.

Prepare one comment-only review:

- Post actionable findings inline only when they can be anchored to a changed
  line in the current pull request diff.
- Put unanchored findings, positive findings, coverage, verification, and
  limitations in the review body. Do not post positive findings inline.
- Use repository-relative paths, the verified head SHA as `commit_id`, and
  `line` with `side`: `RIGHT` for an added line and `LEFT` for a deleted line.
- Use `event: COMMENT`. Never use `APPROVE` or `REQUEST_CHANGES`.

Create a single review so its body and inline comments are submitted together:

```bash
gh api --method POST \
  repos/datacommonsorg/data/pulls/<PR_NUMBER>/reviews \
  --input <PAYLOAD_FILE> \
  --jq '{id, state, html_url, commit_id}'
```

Use this payload shape. Omit `comments` when there are no inline findings.

```json
{
  "commit_id": "<VERIFIED_HEAD_SHA>",
  "event": "COMMENT",
  "body": "<REVIEW_SUMMARY>",
  "comments": [
    {
      "path": "scripts/source/import/process.py",
      "line": 42,
      "side": "RIGHT",
      "body": "**[P1] Finding title**\n\nFinding: ...\n\nImpact: ...\n\nRecommendation: ..."
    }
  ]
}
```

If the execution environment requires approval for the GitHub write, request
it. If approval is denied or authentication lacks write permission, report that
nothing was published. After a successful response, report the review URL and
the number of inline comments. If the result is uncertain, inspect existing
reviews for the verified head before retrying so the review is not duplicated.
