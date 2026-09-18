# Importing CDC 500 STATES Data

Author: Padma Gundapaneni @padma-g

## Table of Contents
1. [About the Dataset](#about-the-dataset)
    1. [Overview](#overview)
    2. [Data Sources and Tables](#data-sources-and-tables)
    3. [Aggregation Methodology](#aggregation-methodology)
2. [About the Import](#about-the-import)
    1. [Artifacts](#artifacts)
    2. [Import Procedure](#import-procedure)
    3. [Troubleshooting](#troubleshooting)

## About the Dataset

### Overview
The state-level dataset calculates aggregated health indicator prevalence estimates for US states from the city-level CDC 500 Cities (`CDC500`) project data, weighted by corresponding Census ACS 5-Year population counts.

CDC PLACES (Population Level Analysis and Community Estimates) is the official successor program to the original CDC 500 Cities project, expanding health estimates across all US counties, places, and census tracts. In Data Commons, city-level data from both the historical CDC 500 Cities project (2016–2019) and ongoing CDC PLACES releases (2020–present) are ingested under provenance `dc/base/CDC500`.

### Data Sources and Tables

The aggregation script queries Google Cloud BigQuery graph tables in dataset `datcom-store.spanner_dc_graph_prod_DEFAULT`:

1. **`TimeSeries`**:
   - **CDC 500 Series**: Identifies CDC 500 Statistical Variables (`provenance = 'dc/base/CDC500'` and `variable_measured LIKE 'Percent_%'`) and extracts their measurement methods (`measurement_method`). It maps each percentage health metric to its appropriate denominator demographic cohort StatVar (e.g., `Count_Person_18OrMoreYears`, `Count_Person_18To64Years`, `Count_Person_65OrMoreYears`, `Count_Person`, etc.).
   - **Census ACS 5-Year Series**: Filters and joins population counts from Census ACS 5-Year Survey (`provenance = 'dc/base/CensusACS5YearSurvey'`).

2. **`Observation`**:
   - **Health Indicator Percentages**: Fetches city-level percentage values (`value AS percent`), observation dates (`date`), and city geoIds (`entity1 LIKE 'geoId/%'`) for CDC 500 StatVars. To prevent double-counting Oahu/Honolulu County population in years where 13-character Census Designated Places (`geoId/15XXXXX`) are published (2017–2022), `geoId/15003` is explicitly filtered in the `WHERE` clause to include only years `<= '2016'` and `'2017'` county-only indicators (excluding the four 2017 blood pressure and cholesterol indicators that also have 13-character CDP data).
   - **City Cohort Populations**: Fetches city-level population counts (`value AS population`) for the corresponding demographic cohort StatVars.

### Aggregation Methodology

For each state, indicator StatVar, and observation date:
- City observations are joined with their corresponding demographic population counts.
- City geoIds (`geoId/XXXXXXX`) are mapped to state geoIds (`geoId/XX`) using the first 8 characters (including the prefix).
- State-level prevalence percentages are computed as a population-weighted average:

$$\text{State Percent} = \frac{\sum (\text{City Population} \times \text{City Percent})}{\sum \text{City Population}}$$

The output measurement method is prefixed with `dcAggregate/` (e.g., `dcAggregate/CrudePrevalence`).

*Note on Demographic Cohorts:* Several adult health indicators (such as `Percent_Person_Smoking`, `Percent_Person_Obesity`, `Percent_Person_WithDiabetes`) lack explicit age tokens in their DCID and intentionally fall back to `Count_Person` weighting to preserve bitwise parity with existing Data Commons baseline observations.

#### Excluded Indicators

The following age-bracketed cancer screening indicators are omitted from state-level aggregation:
- `Percent_Person_50To74Years_Female_ReceivedMammography`
- `Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening`
- `Percent_Person_21To65Years_Female_ReceivedPapSmearTest`
- `Percent_Person_50To75Years_ReceivedColorectalCancerScreening`

**Rationale**: The Census ACS 5-Year Survey does not publish single composite population StatVars for these non-standard multi-year age brackets (`50To74Years`, `21To65Years`, `50To75Years`). Rather than applying arbitrary proxy weights or risking silent row omission, these indicators are explicitly excluded from state aggregation.

## About the Import

### Artifacts

#### Scripts
[`process.py`](process.py)

#### Unit Tests
[`process_test.py`](process_test.py)

#### tMCF Template
[`cdc500_state.tmcf`](cdc500_state.tmcf)

#### Validation Config
[`validation_config.json`](validation_config.json)

#### Manifest
[`manifest.json`](manifest.json)

### Import Procedure

#### Prerequisites

Ensure Google Cloud authentication is configured with access to BigQuery dataset `datcom-store.spanner_dc_graph_prod_DEFAULT`:

```bash
$ gcloud auth application-default login
```

#### Running the Script

To run the BigQuery aggregation and write the output CSV to the default output directory (`scripts/us_cdc/cdc500_state/CDC500State_Output/CDC500State_Output.csv` when run from repository root):

```bash
$ python3 scripts/us_cdc/cdc500_state/process.py
```

To specify a custom output directory:

```bash
$ python3 scripts/us_cdc/cdc500_state/process.py --output_dir=/path/to/output
```

To specify a GCP project and timeout (in seconds) for BigQuery jobs (if not set in ambient environment):

```bash
$ python3 scripts/us_cdc/cdc500_state/process.py --project=my-gcp-project --timeout=600
```

#### Running Unit Tests

Run the test suite using Python's `unittest` runner from the repository root:

```bash
$ python3 -m unittest scripts.us_cdc.cdc500_state.process_test
```

#### Automation

This import is automated via Data Commons Import Automation and scheduled to run weekly via Cloud Batch every Monday at 01:00 UTC (`cron_schedule: "0 1 * * 1"` in `manifest.json`).

- **Import Type**: Automated (weekly Cloud Batch cron: `0 1 * * 1`)
- **Production GCS Path**: `gs://datcom-prod-imports/scripts/us_cdc/cdc500_state/CDC500_States/`
- **Test GCS Path**: `gs://datcom-import-test/scripts/us_cdc/cdc500_state/CDC500_States/`

### Troubleshooting

- **`RuntimeError: BigQuery query returned 0 rows`**: Verify ADC authentication (`gcloud auth application-default login`) and ensure read permissions on `datcom-store.spanner_dc_graph_prod_DEFAULT`. Pass `--project=<gcp_project_id>` if running outside the default project.
- **`check_statvar_max_dates` validation failure**: When CDC PLACES (the official successor program to CDC 500 Cities) publishes a new release year, update the `CASE` statement in `validation_config.json` (`check_statvar_max_dates`) to reflect the new expected vintage years per cohort.
