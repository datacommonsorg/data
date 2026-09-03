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
   - **CDC 500 Series**: Identifies CDC 500 Statistical Variables (`provenance = 'dc/base/CDC500'` and `variable_measured LIKE 'Percent_%'`) and extracts their measurement methods (`measurement_method`). It maps each percentage health metric to its appropriate denominator demographic cohort StatVar (e.g., `Count_Person_18OrMoreYears`, `Count_Person_Female_50To74Years`, `Count_Person_Female_21To65Years`, `Count_Person_65OrMoreYears`, etc.).
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

#### Data Download and Processing Steps

To run the BigQuery aggregation and generate the output CSV:

```bash
$ python3 process.py
```
