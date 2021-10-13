# India GeoJSON Dataset from Datameet

This directory contains scripts to turn geojsons from [Datameet's
repo](https://github.com/datameet/maps) into MCF suitable for import into Data
Commons.

## Generation

1. Convert the State and District Shapefiles into GeoJSONs following
   instructions [here](https://github.com/datameet/maps#note-on-format).

   NOTE: You can install `ogr2ogr` tool as `apt-get install gdal-bin`.


2. Run:

   ```
   cd scripts/
   python3 -m india_datameet.maps.generate_mcf \
      --input_state_geojson=<Path-to-State-GeoJson> \
      --input_district_geojson=<Path-to-District-GeoJson> \
      --output_geojson_dir=/tmp/
   ```
