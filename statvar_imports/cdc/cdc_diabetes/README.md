# CDC US Diabetes Surveillance System (CDCDiabetes) County Import

## Overview

This directory contains the automated import pipeline for the **CDCDiabetes** (`CDC_Diabetes`) dataset from the [CDC United States Diabetes Surveillance System (USDSS)](https://usdss.cdc.gov/diabetes/) (historically hosted at `https://gis.cdc.gov/grasp/diabetes/DiabetesAtlas.html#`).

It produces US county-level (`geoId/<5-digit FIPS>`) age-adjusted prevalence percentages and standard errors (`statType: dcid:stdError`) for adults aged 20+ years across three indicators and three gender breakdowns (18 StatVars total) from **2004 through 2024**:

| Condition | Gender | Measured Value StatVar | Standard Error StatVar (`stdError`) |
| :--- | :--- | :--- | :--- |
| Diagnosed Diabetes | Total | `dcid:Percent_Person_20OrMoreYears_WithDiabetes` | `dcid:dc/d4j16hnl53es2` |
| Diagnosed Diabetes | Male | `dcid:dc/xmpy89x1nh8cg` | `dcid:dc/xwtlmj1vg7618` |
| Diagnosed Diabetes | Female | `dcid:dc/nh3s4skee5483` | `dcid:dc/ryjdx30rfbfbb` |
| Obesity | Total | `dcid:Percent_Person_20OrMoreYears_Obesity` | `dcid:dc/bzfel0wfs6qhf` |
| Obesity | Male | `dcid:dc/x13tvt8jsgrm4` | `dcid:dc/73vt0flpsz26b` |
| Obesity | Female | `dcid:dc/4lvmzr1h1ylk1` | `dcid:dc/h3vxgc4gwl4c7` |
| Physical Inactivity | Total | `dcid:Percent_Person_20OrMoreYears_PhysicalInactivity` | `dcid:dc/1yfe8eezs4jbc` |
| Physical Inactivity | Male | `dcid:dc/ty7pq88d26963` | `dcid:dc/bv6fv4et0d8pd` |
| Physical Inactivity | Female | `dcid:dc/tcqb49dvg7k53` | `dcid:dc/t1hj2ymqdg5s6` |

## Pipeline Architecture

1. **Historical Baseline (2004–2021)**: Loaded from `gs://unresolved_mcf/cdc/diabetes/20240112/` (162 pre-processed CSVs, `1,016,418` observation rows) or a local `--baseline_dir`.
2. **CDC USDSS County API (2022–2024+)**: `download_and_preprocess.py` queries the live CDC USDSS surveillance endpoints:
   - County metadata (`InitAppData_*.json`) and available years (`SurveillanceIndicatorsYearsList_Counties.json`).
   - County estimates via `POST https://usdss.cdc.gov/webapi/Diabetes/AllCountiesDataOneYear` for `IndicatorID` `151` (Diabetes), `201` (Obesity), and `202` (Physical Inactivity), `AgeID=635` (Age-Adjusted), `DatasetID=1044` (Adults Aged 20+ Years), `DataTypeID=1113` (Percentage), and `SexID` `591` (Total), `592` (Male), `593` (Female).
   - Writes raw per-series CSVs to `input_files/DiabetesAtlasCountyData_<condition>_<gender>_<year>.csv`.
3. **Standard Error Calculation**:
   $$\text{stdError} = \text{round}\left(\frac{\text{Upper Limit} - \text{Percentage}}{1.96},\ 5\right)$$
4. **Unified Output**: Combines and deduplicates all rows by `(year, location, variableMeasured)` into `output/cdc_diabetes.csv` and copies `cdc_diabetes.tmcf` to `output/cdc_diabetes.tmcf`.

## Running the Import

```bash
bash statvar_imports/cdc/cdc_diabetes/run.sh
```

## Running Unit Tests

```bash
./run_tests.sh -p statvar_imports/cdc/cdc_diabetes
```
