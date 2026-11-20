# CDCWonder_NNDSS_InfectiousWeekly

## Overview
Notifiable Infectious Diseases Data: Weekly tables from CDC WONDER containing incident counts of infectious diseases reported by US states, New York City, the District of Columbia, US territories, and US Census divisions.

This unified import preserves the historical 2006–2021 archive from GCS (`gs://unresolved_mcf/cdc/nndss_infectious_diseases_weekly/20250206/cdc_nndss_weekly_tables.csv`) and appends 2022–present `Current week` incident counts streamed from CDC's Socrata endpoint (`x9gk-5huc`).

## Data Sources
- **2022–Present**: `https://data.cdc.gov/api/views/x9gk-5huc/rows.csv?accessType=DOWNLOAD&api_foundry=true`
- **2006–2021 Historical Baseline**: `gs://unresolved_mcf/cdc/nndss_infectious_diseases_weekly/20250206/cdc_nndss_weekly_tables.csv`

## Processing Instructions
Run `preprocess.py` from this directory:

```bash
python3 preprocess.py
```

Outputs are written to `output/cdc_nndss_weekly_tables.csv` and `output/cdc_nndss_weekly_tables.tmcf`.

## Running Unit Tests
```bash
python3 -m unittest preprocess_test.py
```
