# Import Scripts for UN Country Boundaries

### Download URL

From [UN Geodata
Simplified](https://geoportal.un.org/arcgis/apps/sites/#/geohub/datasets/d7caaff3ef4b4f7c82689b7c4694ad92/about),
the UN team got us the BNDA geojson that is checked into `data/`.

### Overview

This script generates both the MCFs as well as the json caches used
in the DC website.

Since Place geos have a single provenance and we want to use these
boundaries only for UN SDG, we add them as a new `geoJsonCoordinatesUN`
property (plus `DPx` suffixes).

The following countries in DC do not have boundaries:
* country/ANT
* country/ATB
* country/ATN
* country/CTE
* country/FXX
* country/IOT
* country/UMI
* country/WLF
* country/XKS
* country/YUG

Among those, the following ones have boundary from World Bank source:
* country/IOT
* country/UMI
* country/WLF


### Scripts

Run the following script to generate Website cache and MCFs ready for import.

```bash
export MIXER_API_KEY=<autopush_api_key>
./run.sh
```

Copy the contents of `output/mcf` over for manifesting.

Copy the contents of `output/cache` to the website repo.
