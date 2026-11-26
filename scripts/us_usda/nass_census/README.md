# US Census of Agriculture Import

The Census of Agriculture, taken once every five years (`2002`, `2007`, `2012`, `2017`, `2022`, and subsequent 5-year cycles), covers land use and ownership, operator characteristics, production practices, income, and expenditures for the United States, states, and counties (`NATIONAL`, `STATE`, and `COUNTY` aggregation levels).

This import extracts Census observations (`SOURCE_DESC = "CENSUS"`) from tables 1 and 48-54 across all published 5-year Censuses from 2002 onward:

* 1 - County Summary Highlights
* 48 - Hispanic, Latino, or Spanish Origin Producers
* 49 - American Indian or Alaska Native Producers
* 50 - Asian Producers
* 51 - Black or African American Producers
* 52 - Native Hawaiian or Other Pacific Islander Producers
* 53 - White Producers
* 54 - Producers Reporting More Than One Race

## Source

* Census overview: https://www.nass.usda.gov/publications/agcensus
* Bulk Quick Stats datasets page: https://www.nass.usda.gov/datasets

## Prerequisites & Working Directory

Install the repository Python virtual environment (`.env`) from the `data` repository root:

```bash
./run_tests.sh -r
```

`process.py` resolves its default `statvars`, `input/`, and `output/` paths relative to `scripts/us_usda/nass_census/`, so it can be run either from the `data` repository root or from `scripts/us_usda/nass_census/`.

## Download, Processing, and Pre-Ingestion Checks

1. **Discovery & Download**: `process.py` fetches `https://www.nass.usda.gov/datasets`, discovers the five Quick Stats bulk sector `.txt.gz` archives (`qs.animals_products_*.txt.gz`, `qs.crops_*.txt.gz`, `qs.demographics_*.txt.gz`, `qs.economics_*.txt.gz`, `qs.environmental_*.txt.gz`), downloads them with HTTP `Range` resume support into `input/`, and removes stale archives from prior runs.
2. **Pre-Ingestion Runtime Checks**: Before MCF generation, `process.py` verifies that all five expected sector archives are listed on `/datasets`, validates `Content-Length` and gzip magic headers (`\x1f\x8b`) to catch truncated transfers or HTML soft-404 responses, checks required TSV columns, and raises an error if zero Census observations are produced.
3. **Streaming Transformation**: Streams each `.txt.gz` archive directly without retaining uncompressed `.txt` duplicates, filters `SOURCE_DESC == "CENSUS"` and 5-year Census years (`>= 2002`), skips NASS suppression codes (`(D)`, `(Z)`, `(NA)`, `(X)`, `(S)`), writes per-year `output/agriculture_{year}.csv` files atomically, and merges them into `output/agriculture.csv`.

## Execution & Refresh Procedure

Auto-refresh runs weekly via `manifest.json` (`scripts: ["process.py"]`, `cron_schedule: "30 0 * * 5"`). For manual or local runs:

* **Download and process (default)**:
  ```bash
  .env/bin/python scripts/us_usda/nass_census/process.py
  ```
* **Download only** (saves raw `.txt.gz` files in `input/`):
  ```bash
  .env/bin/python scripts/us_usda/nass_census/process.py --mode=download
  ```
* **Process only** (streams existing `.txt.gz` or `.txt` files in `input/` and writes CSVs in `output/`):
  ```bash
  .env/bin/python scripts/us_usda/nass_census/process.py --mode=process
  ```

## Important Files

* `manifest.json`: Auto-refresh import specification (`USDA_AgricultureCensus`), inputs, and `source_files`.
* `process.py`: Dataset discovery, resumable `.txt.gz` downloader, and streaming TSV-to-CSV processor.
* `statvars`: Mapping from Quick Stats `SHORT_DESC[%%DOMAINCAT_DESC]` keys to Data Commons `StatisticalVariable` and unit DCIDs.
* `agriculture.tmcf`: Template MCF mapping `output/agriculture.csv` columns with `observationPeriod: "P5Y"`.
* `process_test.py` and `testdata/`: Unit tests and paired input/output fixtures (`ag_census_input.txt`, `ag_census_output.csv`).

## Testing

From the `data` repository root:

```bash
./run_tests.sh -p scripts/us_usda/nass_census
./run_tests.sh -l
```
