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

## About the Dataset

### Overview
The state-level dataset calculates aggregated health indicator prevalence estimates for US states from the city-level CDC 500 Cities (`CDC500`) project data, weighted by corresponding Census ACS 5-Year population counts.

### Data Sources and Tables

The aggregation script queries Google Cloud BigQuery graph tables in dataset `datcom-store.spanner_dc_graph_prod_DEFAULT`:

1. **`TimeSeries`**:
   - **CDC 500 Series**: Identifies CDC 500 Statistical Variables (`provenance = 'dc/base/CDC500'` and `variable_measured LIKE 'Percent_%'`) and extracts their measurement methods (`measurement_method`). It maps each percentage health metric to its appropriate denominator demographic cohort StatVar (e.g., `Count_Person_18OrMoreYears`, `Count_Person_18To64Years`, `Count_Person_65OrMoreYears`, `Count_Person`, etc.).
   - **Census ACS 5-Year Series**: Filters and joins population counts from Census ACS 5-Year Survey (`provenance = 'dc/base/CensusACS5YearSurvey'`).

2. **`Observation`**:
   - **Health Indicator Percentages**: Fetches city-level percentage values (`value AS percent`), observation dates (`date`), and city geoIds (`entity1 LIKE 'geoId/%' AND LENGTH(entity1) = 13`) for CDC 500 StatVars.
   - **City Cohort Populations**: Fetches city-level population counts (`value AS population`) for the corresponding demographic cohort StatVars.

### Aggregation Methodology

For each state, indicator StatVar, and observation date:
- City observations are joined with their corresponding demographic population counts.
- City geoIds (`geoId/XXXXXXX`) are mapped to state geoIds (`geoId/XX`) using the first 8 characters (including the prefix).
- State-level prevalence percentages are computed as a population-weighted average:

$$\text{State Percent} = \frac{\sum (\text{City Population} \times \text{City Percent})}{\sum \text{City Population}}$$

The output measurement method is prefixed with `dcAggregate/` (e.g., `dcAggregate/CrudePrevalence`).

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
[`process.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/cdc500_state/process.py)

#### Unit Tests
[`process_test.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/cdc500_state/process_test.py)

#### tMCF Template
[`cdc500_state.tmcf`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/cdc500_state/cdc500_state.tmcf)

#### Validation Config
[`validation_config.json`](https://github.com/datacommonsorg/data/blob/master/scripts/us_cdc/cdc500_state/validation_config.json)

### Import Procedure

#### Prerequisites

Ensure Google Cloud authentication is configured with access to BigQuery dataset `datcom-store.spanner_dc_graph_prod_DEFAULT`:

```bash
$ gcloud auth application-default login
```

#### Running the Script

To run the BigQuery aggregation and write the output CSV to the default output directory (`CDC500State_Output/CDC500State_Output.csv`):

```bash
$ python3 scripts/us_cdc/cdc500_state/process.py
```

To specify a custom output directory:

```bash
$ python3 scripts/us_cdc/cdc500_state/process.py --output_dir=/path/to/output
```

#### Running Unit Tests

Run the test suite using Python's `unittest` runner from the repository root:

```bash
$ python3 -m unittest scripts.us_cdc.cdc500_state.process_test
```

#### Automation

This import is automated via Data Commons Import Automation and scheduled to run weekly via Cloud Batch every Monday at 01:00 UTC (`cron_schedule: "0 1 * * 1"` in `manifest.json`).

