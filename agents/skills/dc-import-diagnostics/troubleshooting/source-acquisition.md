# Source acquisition completeness

## Hypothesis index

- [Required request failed but the script continued](#required-request-failed-but-the-script-continued)
- [Required request was not issued](#required-request-was-not-issued)
- [Downloaded file was not retained](#downloaded-file-was-not-retained)

## Scope

- Use this guide when an import may have acquired only part of its required
  source data.
- Check required requests and retained files.
- Do not treat top-level script success as proof that every request succeeded.

## Investigate

- [Read the exact candidate summary](../references/gcs.md#read-one-import-version-summary)
  and use only its recorded Batch job ID for logs.
- Test the strongest plausible hypothesis first. If confirmed, mitigate it and
  stop; if refuted, test the next cause; if evidence is unavailable, report
  `UNKNOWN`.

## Hypotheses

### Required request failed but the script continued

- **Confirm or refute:** Read the downloader code to distinguish required and
  optional requests and identify its failure text. Search that text in
  [bounded logs](../references/batch.md#fetch-bounded-batch-logs). Confirm a
  required failure or skip; refute only with success or optionality evidence.
- **Mitigate:** Report `FAIL` and follow
  [Network failures](network-failures.md) for the specific request.

### Required request was not issued

- **Confirm or refute:** Compare the expected request generation in code and
  configuration with execution evidence. Confirm a required skip or early
  stop; report `UNKNOWN` when the request set cannot be reconstructed.
- **Mitigate:** Recommend correcting the request-generation code or
  configuration and verifying the next run.

### Downloaded file was not retained

- **Confirm or refute:** Compare `source_files/` paths from
  [candidate artifact metadata](../references/gcs.md#list-artifacts-for-one-import-version)
  with the manifest. Confirm a missing or overwritten required path.
- **Mitigate:** Report `FAIL`; recommend correcting the retention pattern or
  path collision and verifying the next run.

## Historical evidence

- Use history only when current evidence is inconclusive or recurrence matters.
- Compare candidate source-file paths and sizes with the
  [accepted version](../references/gcs.md#find-the-last-successful-import-version)
  and, if needed, [up to five recent versions](../references/gcs.md#list-recent-import-versions).
- Treat a file that disappears or shrinks and later returns as possible
  intermittency, not proof. Treat `source_data_size` only as a clue; stable or
  increased total size does not refute a missing-file hypothesis.
- Query historical logs only for an exact past Batch job whose logs are still
  retained.

## Report

- Report `PASS` only when all identifiable required requests succeeded and
  their expected source files were retained.
- Report `FAIL` when a required request or source file failed, was skipped, or
  is missing.
- Report `UNKNOWN` when request coverage, logs, optionality, or retained
  artifacts are insufficient to establish completeness.
- Include the strongest evidence and any unresolved gap.
