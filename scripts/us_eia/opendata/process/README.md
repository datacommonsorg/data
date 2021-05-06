
# US EIA Open Data Import Processor

This folder includes processing scripts for importing datasets from EIA's Open
Data portal: https://www.eia.gov/opendata/qb.php

## Dataset Support

There are two stages of support for a dataset:
1. Raw schema-less stat-vars attached to DC places
2. Stat-vars with full schema definition

For (1), a dataset needs to implement an `extract_place_statvar` function, like
the one `elec.py`, which takes a `series_id` and returns raw place and stat-var.

For (2), a dataset needs to implement `generate_statvar_schema` function, which
takes a raw stat-var and generates a fully defined stat-var for it.

### Datasets

* **ELEC:** Electricity dataset has country, state-level and plant-level
  information on electricity generation, consumption, sales etc by energy source
  and “sectors” (like residential, commercial, etc.).

  Plant-level data has a lot fewer variables than state-level. And where the
  stat-type allows, we’ll aggregate plant-level data to zip code level.

  Dataset includes full schema support, aka (2).

* **INTL:** International Energy dataset has country, continent and world-level
  data. This dataset only has preliminary support, aka (1).

* **NG:** Natural gas dataset has country and state-level data. This dataset
  only has preliminary support, aka (1).

* **PET:** Petroleum dataset has country and state-level data. This dataset only
  has preliminary support, aka (1).

* **SEDS:** International Energy dataset has US country-level and state-level
  data. This dataset only has preliminary support, aka (1).

* **TOTAL:** Total Energy dataset has US country-level data, and only has
  preliminary support, aka (1).

## Run

Download and unzip the data files based on the
[manifest](https://api.eia.gov/bulk/manifest.txt) by running the
[`download_bulk.py`](https://github.com/datacommonsorg/data/blob/master/scripts/us_eia/opendata/download_bulk.py)
script.

To generate CSV, TMCF and stat-var MCF for a supported dataset:

```bash
python3 main.py --data_dir=tmp_raw_data/ELEC --dataset=ELEC
```

Replace `ELEC` with any of the other dataset codes listed above.

To run tests:

```bash
python3 -m unittest common_test.py
```

To download and generate all supported datasets:

```bash
./generate.sh all
```
