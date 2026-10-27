# NOAA GPCC Standardized Precipitation Index (SPI) Import

## Overview

This directory contains the unified Data Commons import pipeline for the **NOAA Global Precipitation Climatology Centre (GPCC) Standardized Precipitation Index (SPI)** dataset (`import_name`: `NOAA_GPCC_StandardardizedPrecipitationIndex`).

The pipeline downloads monthly GPCC precipitation NetCDF files (`1.0° x 1.0°` resolution), computes Standardized Precipitation Index (SPI) values using the Pearson Type III distribution across 6 accumulation periods (`1`, `3`, `6`, `9`, `36`, and `72` months), aggregates grid observations to administrative places, and extracts polygon-merged `DroughtEvent` entities and event observations from the 9-month SPI series (`SPI <= -2.0`).

It produces 5 Data Commons import inputs (`input0` through `input4` in `manifest.json`):

1. **`input0` (`gpcc_spi.tmcf`)**: `1.0° x 1.0°` `Grid_1` SPI observations (`StandardizedPrecipitationIndex_Atmosphere_{1,3,6,9,36,72}MonthPeriod`).
2. **`input1` (`gpcc_spi_aggregation.tmcf`)**: Place-aggregated SPI observations for countries and administrative levels (`[dcAggregate/GridWeightedPearson]`).
3. **`input2` (`drought_spi_9m_polygon_place_svobs.tmcf`)**: Place-level `DroughtEvent` summary observations (`Area_DroughtEvent`, `Count_DroughtEvent`).
4. **`input3` (`drought_spi_9m_polygon_events.tmcf`)**: `DroughtEvent` entity nodes (`dc/base/NOAA_GPCC_StandardardizedPrecipitationIndex_Event`).
5. **`input4` (`drought_spi_9m_polygon_svobs.tmcf` + `drought_event_nodes.mcf`)**: Per-event `DroughtEvent` `StatVarObservation` nodes (`Area_DroughtEvent`, `standardizedPrecipitationIndex`, `dc/base/NOAA_GPCC_StandardardizedPrecipitationIndex_Event_Observations`).

## Pipeline Architecture & Scripts

- `run.sh`: End-to-end orchestration script invoked by the import automation executor:
  1. Runs `download.py` to fetch GPCC monitoring (`1982`–present) and full data (`1891`–`2019`) NetCDF files into `source_files/raw_data/`.
  2. Runs `climate_indices` (`process_climate_indices`) in parallel by longitude slice to compute Pearson SPI (`1`, `3`, `6`, `9`, `36`, `72` months).
  3. Runs `preprocess_gpcc_spi.py` to convert NetCDF SPI outputs into `Grid_1` CSVs (`output_files/gpcc_spi_pearson_*.csv`).
  4. Runs `gpcc_spi_aggregation.py` to aggregate `Grid_1` SPI values to administrative places (`output_files/agg_gpcc_spi_pearson_*.csv`).
  5. Runs `../../earthengine/process_events.py` per year (`2010`–present) with `events_drought_gpcc_spi_9m_polygon.py` to detect and polygon-merge `DroughtEvent`s, then concatenates per-year CSV outputs into `drought_spi_9m_polygon_{events,svobs,place_svobs}.csv`.
  6. Runs `postprocess_events.py` to deduplicate cross-year boundary `(dcid, observationDate)` rows in `drought_spi_9m_polygon_svobs.csv` (keeping `max(area)` and `min(standardizedPrecipitationIndex)`) and generate `output_files/events_spi_9m_polygon/events/drought_event_nodes.mcf` (`Node: dcid:<dcid>`, `typeOf: dcs:DroughtEvent`) so `dc-import` resolves `observationAbout` references when validating `input4` independently.

## Running Tests

From the repository root:

```bash
./run_tests.sh -p scripts/noaa/gpcc_spi
```

Or run individual unit tests directly:

```bash
python3 scripts/noaa/gpcc_spi/preprocess_gpcc_spi_test.py
python3 scripts/noaa/gpcc_spi/gpcc_spi_aggregation_test.py
python3 scripts/noaa/gpcc_spi/postprocess_events_test.py
```
