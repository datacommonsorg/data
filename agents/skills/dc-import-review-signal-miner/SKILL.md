---
name: dc-import-review-signal-miner
description: >-
  Collects and classifies review comments from merged datacommonsorg/data pull
  requests that touch scripts/** or statvar_imports/**. Use when bootstrapping
  or incrementally mining strong positive and corrective import-review signals,
  optionally limited to specified GitHub reviewers. Do not use to review a
  single change or to update import-review guidelines.
---

# Mine Data Commons import review signals

Collect review comments from merged pull requests in `datacommonsorg/data`,
identify strong import-review signals, and write the two Markdown reports
defined below. Do not update guidelines, upload artifacts, or create a pull
request.

## Inputs

- Start time, inclusive: `<START_TIME>` in ISO 8601 UTC.
- End time, exclusive: `<END_TIME>` in ISO 8601 UTC.
- Output directory: `<OUTPUT_DIRECTORY>`.
- Reviewer identities, optional: `<REVIEWERS>` as comma-separated GitHub
  logins, numeric user IDs, or both.

If a required input is unresolved, ask for it before collecting data. If
`REVIEWERS` is omitted or empty, consider comments from every human reviewer.
Strip a leading `@` from logins and match logins case-insensitively. Match
numeric IDs exactly. Use `datacommonsorg/data` as the repository and `master`
as its current-code reference.

## Check prerequisites

From the Data Commons data repository root, run the skill-owned checker once
before creating temporary files or calling GitHub:

```bash
bash agents/skills/dc-import-review-signal-miner/scripts/check_prerequisites.sh
```

Stop if it exits nonzero. The checker verifies `git`, `gh`, GitHub CLI
authentication, and the exact `gh api` and `gh search prs` options used below.
It reports the detected `gh` version for provenance. It does not require the
standalone `jq` program because `gh --jq` provides the required filtering.

## Scope and safety

- Use `gh` for every GitHub operation.
- Process only pull requests whose `merged_at` value is within the requested
  half-open interval and whose final changed-file list contains at least one
  path under `scripts/**` or `statvar_imports/**`.
- Collect all non-empty inline review comments, submitted review bodies, and
  pull request conversation comments from each eligible pull request.
- If `REVIEWERS` is provided, allow only comments authored by a matching
  reviewer to have disposition `Considered`. Keep other comments in the
  complete report as context and mark them `Not considered`. Author replies
  and comments from other reviewers may still provide outcome evidence.
- Use comments on out-of-scope files only as surrounding evidence. Never
  promote them as import-guideline signals.
- Treat the Data Commons checkout as read-only.
- Do not modify `guidelines.md`, upload files, post comments, or create or
  update pull requests.
- Prefer skipping a possible signal over promoting an ambiguous signal.
- Do not expose credentials or authentication output in either report.

## Prepare current master

Use a current `master` snapshot only to verify that a candidate still matches
the repository. Do not create a checkout for each pull request.

If a suitable local clone is available, fetch `master` and create one detached
temporary worktree at the fetched commit. Do not change the active worktree.

Otherwise, create one temporary clone with `gh repo clone`. Make it shallow,
partial, and sparse:

```bash
gh repo clone datacommonsorg/data <TEMP_DIRECTORY>/data -- \
  --depth=1 --filter=blob:none --sparse
git -C <TEMP_DIRECTORY>/data sparse-checkout set scripts statvar_imports
```

Create the temporary root with `mktemp -d` and record its resolved path before
using it. When using a worktree, remove it with `git worktree remove`. Never
remove an unverified path or the active repository.

Verify that the snapshot resolves to the fetched `master` commit. A worktree
provides isolation; the shallow, partial, and sparse options reduce downloaded
data. Remove only temporary paths created by this run after both reports have
been written successfully.

## Collect pull requests and comments

Use GitHub REST API version `2026-03-10`. Do not silently fall back to an
unversioned request. If GitHub returns `410 Gone` for this version, stop and
report that the skill's API contract needs updating.

After the prerequisite checker passes, use `--method GET` whenever passing
`-f` or `-F` query parameters; otherwise `gh api` changes the request to
`POST`. Use `--paginate --jq`, not `--paginate --slurp --jq`; the tested GitHub
CLI rejects the latter combination.

Set task-specific shell variables before calling GitHub:

```bash
DC_REPO='datacommonsorg/data'
GITHUB_API_VERSION='2026-03-10'
DC_SEARCH_START_DATE='<UTC DATE FROM START_TIME: YYYY-MM-DD>'
DC_SEARCH_END_DATE='<UTC DATE FROM END_TIME: YYYY-MM-DD>'
DC_RUN_DIR='<TEMP_DIRECTORY>/github'
DC_CANDIDATES_FILE="${DC_RUN_DIR}/candidate-prs.jsonl"
mkdir -p "${DC_RUN_DIR}"
: > "${DC_CANDIDATES_FILE}"
```

### Discover merged pull requests

Count the coarse date-range search before retrieving candidates:

```bash
DC_SEARCH_QUERY="repo:${DC_REPO} is:pr is:merged merged:${DC_SEARCH_START_DATE}..${DC_SEARCH_END_DATE}"
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  /search/issues \
  -f q="${DC_SEARCH_QUERY}" \
  -F per_page=1 \
  --jq '.total_count'
```

If the count exceeds 1,000, split the UTC date range into smaller ranges and
repeat. GitHub Search exposes at most 1,000 results for one query. Its date
range is inclusive, so deduplicate pull request numbers when coarse ranges
share a boundary date.

For each range whose count is at most 1,000, collect candidates:

```bash
gh search prs \
  --repo "${DC_REPO}" \
  --merged \
  --merged-at "${DC_SEARCH_START_DATE}..${DC_SEARCH_END_DATE}" \
  --limit 1000 \
  --json number,title,url \
  --jq '.[]' >> "${DC_CANDIDATES_FILE}"
```

After deduplication, retrieve authoritative metadata for every candidate:

```bash
DC_PR_NUMBER='<PULL REQUEST NUMBER>'
DC_PR_DIR="${DC_RUN_DIR}/pr-${DC_PR_NUMBER}"
mkdir -p "${DC_PR_DIR}"

gh pr view "${DC_PR_NUMBER}" \
  --repo "${DC_REPO}" \
  --json number,title,url,mergedAt,mergeCommit,headRefOid,baseRefOid,author,changedFiles \
  --jq '{number,title,url,mergedAt,
         merge_commit_sha:(.mergeCommit.oid // null),
         head_sha:.headRefOid,
         base_sha:.baseRefOid,
         author_login:.author.login,
         changed_files:.changedFiles}' \
  > "${DC_PR_DIR}/metadata.json"
```

Retain only metadata satisfying `START_TIME <= mergedAt < END_TIME`. The search
date range is only a coarse candidate filter; never use it as the final time
test.

### Fetch changed files

Fetch the complete changed-file list before collecting comments:

```bash
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  "/repos/${DC_REPO}/pulls/${DC_PR_NUMBER}/files" \
  -F per_page=100 \
  --paginate \
  --jq '.[]' > "${DC_PR_DIR}/files.jsonl"
```

Retain the pull request only when `filename` or `previous_filename` begins with
`scripts/` or `statvar_imports/`. Compare the number of file records with
`changed_files` from `metadata.json`. The REST endpoint returns at most 3,000
files. If the counts differ or `changed_files` exceeds 3,000, do not consider
signals from that pull request and record the collection limitation.

### Fetch the three comment sources

Fetch all inline review comments and their replies:

```bash
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  "/repos/${DC_REPO}/pulls/${DC_PR_NUMBER}/comments" \
  -F per_page=100 \
  --paginate \
  --jq '.[]' > "${DC_PR_DIR}/review-comments.jsonl"
```

Fetch submitted review bodies. Exclude empty bodies, but retain every review
state, including `APPROVED`, `CHANGES_REQUESTED`, `COMMENTED`, and `DISMISSED`:

```bash
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  "/repos/${DC_REPO}/pulls/${DC_PR_NUMBER}/reviews" \
  -F per_page=100 \
  --paginate \
  --jq '.[] | select((.body // "") != "")' \
  > "${DC_PR_DIR}/reviews.jsonl"
```

Fetch non-empty pull request conversation comments. GitHub exposes these
through the issue-comments endpoint because every pull request is also an
issue:

```bash
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  "/repos/${DC_REPO}/issues/${DC_PR_NUMBER}/comments" \
  -F per_page=100 \
  --paginate \
  --jq '.[] | select((.body // "") != "")' \
  > "${DC_PR_DIR}/conversation-comments.jsonl"
```

The three files above are the complete comment sources for this workflow.
Standalone commit comments are out of scope. Fetch pull request commits and
the final diff only when needed to verify a possible signal:

```bash
gh api --method GET \
  -H 'Accept: application/vnd.github+json' \
  -H "X-GitHub-Api-Version: ${GITHUB_API_VERSION}" \
  "/repos/${DC_REPO}/pulls/${DC_PR_NUMBER}/commits" \
  -F per_page=100 \
  --paginate \
  --jq '.[]' > "${DC_PR_DIR}/commits.jsonl"

gh pr diff "${DC_PR_NUMBER}" \
  --repo "${DC_REPO}" \
  > "${DC_PR_DIR}/final.diff"
```

The pull-request commits endpoint returns at most 250 commits. Do not use an
apparently complete `commits.jsonl` as proof when the outcome depends on older
commits that may be omitted.

If exact outcome evidence remains unavailable, mark the possible signal `Not
considered`. Do not broaden to undocumented endpoints or browser scraping.

### Normalize collected records

Use these fields from the downloaded JSON records:

- Match reviewer filters against `user.login` and `user.id`. Use `user.type`
  to exclude bots from considered signals.
- Link inline threads with `pull_request_review_id` and `in_reply_to_id`.
- Preserve `path`, `line`, `original_line`, `side`, `original_side`,
  `diff_hunk`, `commit_id`, and `original_commit_id` when present.
- Preserve `body`, `created_at`, `updated_at`, `html_url`, and
  `author_association` for every comment.
- Use the PR author's login from `metadata.json` to distinguish author replies
  from reviewer-authored signal sources.

Deduplicate by comment source and numeric `id`. Do not collapse distinct
comments with identical text. If any paginated command exits nonzero, stop and
report the incomplete endpoint instead of producing a successful run.

The fixed endpoint contract is documented by GitHub's
[API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions),
[search](https://docs.github.com/en/rest/search/search),
[pull request](https://docs.github.com/en/rest/pulls/pulls),
[review comment](https://docs.github.com/en/rest/pulls/comments),
[review](https://docs.github.com/en/rest/pulls/reviews), and
[issue comment](https://docs.github.com/en/rest/issues/comments) references.

## Classify every collected comment

Classify each comment as one of:

- `Positive signal`: it explicitly endorses a concrete import practice.
- `Corrective signal`: it explicitly requests or explains a concrete import
  correction.
- `No signal`: it does not express a reusable import practice.

Then assign one disposition:

- `Considered`: strong enough to appear in the considered-signals projection.
- `Not considered`: insufficient for guideline consideration.

Mark a signal `Considered` only when all of the following are established:

- The signal concerns code under `scripts/**` or `statvar_imports/**`.
- The comment author matches `REVIEWERS` when that filter is provided.
- The desired behavior is clear and actionable.
- The practice applies to more than the source, dataset, or temporary
  situation in that pull request.
- The pull request outcome supports the signal. For a corrective signal, the
  requested behavior was implemented and merged. For a positive signal, the
  endorsed behavior was retained in the merged result.
- The current `master` snapshot contains supporting code or documentation and
  does not contradict the practice.
- The signal can be restated as a concise recommendation without guessing at
  the reviewer's intent.

Mark a comment `Not considered` when it is a question, generic approval,
automated message, personal style preference, one-off detail, unresolved
discussion, unimplemented suggestion, out-of-scope observation, obsolete
practice, or otherwise ambiguous. State the concrete reason. Do not invent
missing rationale.

Treat reviewer comments as evidence rather than authority. A merged pull
request alone does not prove that every comment in it is valid. Use the comment
thread, resulting change, merged state, and current `master` together.
If current `master` cannot be verified, mark possible signals `Not considered`
and state that current validation was unavailable.

## Phrase considered recommendations

For every considered signal, write one short recommendation describing the
desired behavior. Phrase positive and corrective signals in the same neutral
form.

Do not assign guideline IDs, severity, confidence scores, or mandatory rule
metadata. Do not combine unrelated signals. Preserve separate source comments
when several comments support the same recommendation.

## Write the complete comments report

Write
`<OUTPUT_DIRECTORY>/import-review-comments-<START_DATE>-<END_DATE>.md`.
Include every collected comment from every eligible pull request, including
comments marked `Not considered`.
Create the output directory if needed, but do not create other persistent
files.

Use this structure:

```markdown
# Import review comments

## Collection summary

- Repository: datacommonsorg/data
- Interval: <START_TIME> to <END_TIME>
- Reviewer filter: All human reviewers | <NORMALIZED REVIEWER IDENTITIES>
- Current-code reference: <MASTER_SHA>
- Merged pull requests discovered: <COUNT>
- Eligible pull requests: <COUNT>
- Comments collected: <COUNT>
- Considered positive signals: <COUNT>
- Considered corrective signals: <COUNT>
- Comments not considered: <COUNT>
- Collection limitations: None | <DESCRIPTION>

## PR <NUMBER> - <TITLE>

- Pull request: <URL>
- Merged at: <TIMESTAMP>
- Merge commit: <SHA> | Unavailable
- Pull request head commit: <SHA>
- In-scope changed paths: <PATHS>

### Comment <COMMENT_URL>

- Type: Inline review comment | Review body | Conversation comment
- Author: <LOGIN> (<NUMERIC USER ID>)
- Created at: <TIMESTAMP>
- Location: <PATH:LINE> | Pull request level
- Scope: Import path | Outside import path | Pull request level
- Signal: Positive signal | Corrective signal | No signal
- Disposition: Considered | Not considered
- Reason: <ONE CONCRETE SENTENCE>
- Proposed recommendation: <TEXT> | Not applicable
- Outcome evidence: <LINKS OR CURRENT MASTER PATHS> | None

#### Comment text

<VERBATIM COMMENT BODY>
```

Order pull requests by merge time and number. Within each pull request, order
comments by creation time, comment type, and numeric ID so repeated runs are
stable.

## Write the considered-signals projection

Write
`<OUTPUT_DIRECTORY>/import-review-signals-<START_DATE>-<END_DATE>.md`.
Derive this file from the completed comments report rather than classifying the
comments again. Include only entries whose disposition is `Considered`.

Group entries with the same proposed recommendation when the evidence supports
the same general practice. Preserve every supporting comment URL and whether
each source was positive or corrective.

Use this structure:

```markdown
# Considered import review signals

## Summary

- Repository: datacommonsorg/data
- Interval: <START_TIME> to <END_TIME>
- Reviewer filter: All human reviewers | <NORMALIZED REVIEWER IDENTITIES>
- Current-code reference: <MASTER_SHA>
- Recommendations: <COUNT>
- Positive source comments: <COUNT>
- Corrective source comments: <COUNT>

## <CONCISE RECOMMENDATION>

- Recommendation: <DESIRED BEHAVIOR>
- Signal types: Positive | Corrective | Positive and corrective
- Why it is generalizable: <ONE OR TWO SENTENCES>
- Pull request outcome: <MERGED BEHAVIOR AND SUPPORTING LINKS>
- Current master evidence: <PATHS AND RELEVANT LINES OR SYMBOLS>
- Source comments:
  - <POSITIVE OR CORRECTIVE> - <COMMENT URL> - <SHORT CONTEXT>
```

If there are no considered signals, still write the projection with a zero
count and the statement `No strong import-review signals were found.`

## Validate and report completion

Before finishing:

- Confirm every retained pull request touches an import path.
- Confirm all paginated comment sources were exhausted.
- Confirm every considered source comment matches the reviewer filter when one
  was provided.
- Confirm every comment in the projection exists in the complete report and is
  marked `Considered`.
- Confirm the summary counts match the report contents.
- Confirm ambiguous signals were not promoted.
- Confirm only the two requested Markdown reports were created outside the
  temporary checkout.

Return the two output paths and the collection summary. Clearly report any
collection limitation; do not describe an incomplete run as successful.
