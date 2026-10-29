# Deleted observation debugging

Use this guide to debug deleted observations or when a `FAILED` validation rule maps to `DELETED_RECORDS_COUNT` or `DELETED_RECORDS_PERCENT`. The failed rule confirms that deletions exceeded the configured threshold; it does not identify the cause.

## Hypothesis index

- [Source acquisition was incomplete](#source-acquisition-was-incomplete)
- [Retained source no longer contains the data](#retained-source-no-longer-contains-the-data)
- [StatVar Processor changed or dropped observations](#statvar-processor-changed-or-dropped-observations)
- [Other transformation code changed or dropped observations](#other-transformation-code-changed-or-dropped-observations)

## Understand what was deleted

- Use available evidence to understand the scale and pattern of the deletion
  before investigating its cause.
- **Current version:** The version being investigated.
- **Baseline version:** The previous version used by Import Differ and recorded
  in `differ_summary.json`.

| Investigation question | Evidence that may help | What it can show |
| --- | --- | --- |
| How large was the deletion? | `validation_output.csv` and `differ_summary.json` | The failed threshold and overall counts of deleted, added, and modified observations. |
| Which observations were deleted? | `nodes-deleted.mcf`, or a comparison of the complete observation outputs from both versions | The observations that existed in the baseline version but are absent from the current version. |
| Does the deletion have a recognizable pattern? | Deleted observations, or the complete observation outputs from both versions | Whether the deletion is concentrated around particular StatisticalVariables, places, StatVar-place combinations, dates, or facets. |
| Did the overall output shape change? | The current and baseline `summary_report.csv` files | Changes in observation, StatisticalVariable, place, date-range, and facet counts. |

- Look for concentrations in the deleted data to help identify the boundary of
  the problem.
- When relevant, group or filter by StatisticalVariable
  (`variableMeasured`), place (`observationAbout`), StatVar-place combination,
  date, or facet. Treat these as examples rather than required checks.
- Use the most suitable complete observation artifact retained for both
  versions.
  - For StatVar Processor imports, prefer `cleaned_csv` when it is available.
    See the [StatVar Processor](../../../../tools/statvar_importer/README.md)
    for output and source-mapping semantics.
  - For other imports, generated MCF may be the available complete output.
- Use [Query import artifacts](../references/querying-artifacts.md) to choose an
  approach based on the available format and size.
- Use [List artifacts for one import version](../references/gcs.md#list-artifacts-for-one-import-version)
  for each version whose files are needed.
- See the
  [artifact layout](../../../common/references/import-automation/artifact-layout.md)
  and [Import Differ](../../../../tools/import_differ/README.md) for artifact
  locations and semantics.
- Do not expect Import Differ to persist deletion summaries by StatVar, place,
  or StatVar-place.

## Hypotheses

For each plausible hypothesis:

- Try to confirm or refute it from retained evidence.
- Record one status:
  - **CONFIRMED:** Direct evidence supports the proposed cause.
  - **REFUTED:** Direct evidence contradicts the proposed cause.
  - **UNKNOWN:** Required evidence is unavailable or inconclusive.

- Treat a missing artifact as unavailable evidence, not as proof that the whole
  hypothesis is unknown.
- Continue with other available evidence.
- Use `UNKNOWN` when the remaining evidence cannot decide the hypothesis.

### Source acquisition was incomplete

- **Confirm or refute:** Follow
  [Source acquisition completeness](source-acquisition.md).
- **Mitigate:** Address a confirmed acquisition failure before investigating
  downstream processing.

### Retained source no longer contains the data

- **Confirm or refute — StatVar Processor imports:**
  - Use `#input` when available to trace an observation to its source context.
  - Otherwise use the processor output, PV map, and configuration to determine
    which source columns and values could produce the observation.
  - Check whether the corresponding source data is still present.
  - See the [StatVar Processor](../../../../tools/statvar_importer/README.md)
    for source-mapping semantics.
- **Confirm or refute — other imports:**
  - Use the transformation code and retained intermediate outputs to map the
    observation back to its source data.
  - Check whether the corresponding source data is still present.
- **Mitigate:** Identify the source, endpoint, or query change when the rows are
  absent.

### StatVar Processor changed or dropped observations

- **Confirm or refute:**
  - Use the
    [manifest reference](../../../common/references/import-automation/manifest.md)
    to determine whether processor outputs and counters were configured for
    upload.
  - Use [List artifacts for one import version](../references/gcs.md#list-artifacts-for-one-import-version)
    to confirm which artifacts are retained for the current and baseline
    versions.
  - Compare the current and baseline `cleaned_csv` files when both are
    available.
  - Compare retained counters to identify changes in input, ignored, dropped,
    generated, or output observation counts.
  - Treat counter differences as clues rather than proof of the deletion's
    cause.
  - Use `#input`, when available, to trace representative observations to their
    source context.
  - Inspect the PV map and processor configuration for the affected rows.
  - See the [StatVar Processor](../../../../tools/statvar_importer/README.md)
    for output, source-mapping, and counter semantics.
- **Mitigate:** Correct the mapping, configuration, or processing condition. If
  the observation identity changed intentionally, report a replacement rather
  than a true deletion.

### Other transformation code changed or dropped observations

- **Confirm or refute:**
  - Compare the current and baseline CSV when a complete final CSV is retained.
  - Otherwise compare the generated MCF under each version's
    `input<N>/genmcf/` directory.
  - Trace representative deletions through the transformation code.
  - Compare `nodes-added.mcf` when the change may be a delete-plus-add
    replacement.
- **Mitigate:** Correct the transformation or mapping. If the observation
  identity changed intentionally, report a replacement rather than a true
  deletion.

## Classify the impact

- Use StatVar-place grouping for a compact impact view.
- Treat a series as StatVar, place, and observation facet. Dates are points
  within the series.
- Claim whole-series deletion only when the current generated data contains no
  point for the same facet-aware series.

## Report

- State the likely cause and strongest supporting evidence.
- Distinguish deleted points, whole-series deletion, and replacement.
- State unresolved gaps and the next useful check.
