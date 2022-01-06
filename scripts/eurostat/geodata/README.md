# Eurostat GeoJSON Dataset

This directory contains scripts to turn geojsons from
[Eurostat](https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/nuts)
into MCF suitable for import into Data Commons. This corresponds to NUTS 2016,
which is the version of geos in DC.

We generate three resolutions of the data:
* 1:1 million (`geoJsonCoordinates`)
* 1:10 million (`geoJsonCoordinatesDP1`)
* 1:20 million (`geoJsonCoordinatesDP2`)

## Generation

1. Download and extract the geojsons into `/tmp/eugeos`.

   ```
   ./download.sh
   ```

2. Run the MCF gen script
   ```
   python3 generate_mcf.py
      --input_eu_01m_geojson=/tmp/eugeos/01m \
      --input_eu_10m_geojson=/tmp/eugeos/10m \
      --input_eu_20m_geojson=/tmp/eugeos/20m \
      --output_geojson_dir=/tmp/eugeos/
   ```

## Testing

TODO: implement me

