# Start Data Commons import review-signal mining

Use the `dc-import-review-signal-miner` skill with these inputs:

- Start time, inclusive: `<START_TIME>` in ISO 8601 UTC.
- End time, exclusive: `<END_TIME>` in ISO 8601 UTC.
- Output directory: `<OUTPUT_DIRECTORY>`.
- Reviewer identities, optional: `<REVIEWERS>` as comma-separated GitHub
  logins, numeric user IDs, or both.

Follow the skill's import-path boundary, conservative signal criteria, output
contracts, and read-only safety rules. Produce only the complete comments
report and the considered-signals projection.
