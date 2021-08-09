# Importing World Bank Official Boundaries into Data Commons

Author: beets

### Download URL

[World Boundaries GeoJSON - Very High Resolution](https://datacatalog.worldbank.org/dataset/world-bank-official-boundaries)

### Overview

Country-level boundary information as recognized by the World Bank. This import does not include disputed areas or entities not already included in Data Commons. Both high-resolution and simplified geojson's are included.  Geojson's are simplified using [`geopandas.GeoSeries.simplified`](https://geopandas.readthedocs.io/en/latest/docs/reference/api/geopandas.GeoSeries.simplify.html).

See the [accompanying Python notebook](country_boundaries_exploration.ipynb) for more exploration on the dataset.

### Notes and caveats

- DC entities of type 'Country' without 'country/' prefixes were ignored
- World Bank codes were preferred, where dependent areas are separate entities e.g. [Tokelau](https://datacommons.org/browser/country/TKL) is kept separate from [New Zealand](https://datacommons.org/browser/country/NZL).
- Not all DC countries have data for this import.

### License

This dataset is licensed under CC-BY 4.0

### Artifacts

Generated MCF's are stored [in this gcs bucket](https://pantheon.corp.google.com/storage/browser/unresolved_mcf/template_mcf_imports/WorldBankBoundaries/mcfs/coords_only).

### Scripts

Run the following script to download and generate MCFs ready for import.

```bash
python3 country_boundaries_mcf_generator.py
```