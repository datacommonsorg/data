
# EIA Open Data Import

This folder includes processing scripts for importing datasets from EIA's Open
Data portal: https://www.eia.gov/opendata/qb.php

## Dataset Support

There are two stages of support for a dataset:
1. Raw schema-less stat-vars attached to DC places
2. Stat-vars with full schema definition

For (1), a dataset needs to implement an `extract_place_stat_var` function, like
the one `elec.py`, which takes a `series_id` and returns raw place and
stat-var.

For (2), a dataset needs to implement `generate_schema_statvar`, which takes the
raw stat-vara and generates a fully defined stat-var for it.

### ELEC

Electricity dataset has country, state-level and plant-level information on
electricity generation, consumption, sales etc by energy source and “sectors”
(like residential, commercial, etc.).

Plant-level data has a lot fewer variables than state-level. And where the
stat-type allows, we’ll aggregate plant-level data to zip code level.

## Run

Download and unzip the data files based on the
[manifest](https://api.eia.gov/bulk/manifest.txt).

  TODO: reference download script

To generate CSV, TMCF and stat-var MCF for a supported dataset:

```bash
python3 main.py --data_dir=tmp_raw_data --dataset=ELEC
```

To run tests:

```bash
python3 -m unittest common_test.py
```

