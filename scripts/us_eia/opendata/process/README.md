
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

* **COAL:** Coal dataset has state and country-level information about coal
  quality, consumption and production.

  Dataset includes some full schema support (2), but mostly (1).

  Ignored for now are coal-mine level information, as well as
  import/export/shipment data involving 2 places.

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

* **NUC_STATUS:** Nuclear outage dataset has nuclear-plant and national data about
  Nuclear energy generation capacity and planned outages.  Dataset has full
  schema support (2).

* **PET:** Petroleum dataset has country and state-level data. This dataset only
  has preliminary support, aka (1).

* **SEDS:** International Energy dataset has US country-level and state-level
  data. This dataset only has preliminary support, aka (1).

* **TOTAL:** Total Energy dataset has US country-level data, and only has
  preliminary support, aka (1).



* Downloading and Processing Data refer README.md (data/scripts/us_eia/opendata/README.md)





