# Processing GeoJSON files

The directory contains script to process GeoJSON files.

## Generate GeoJSON from Shape file.
GeoJSON files can be downloaded from source or generated from shape fles.
To extract geoJSON from a shape file (.shp), run the following command:

```
ogr2ogr -f GeoJSON <output.geojson> <input.shp>
```

Note that the remainign scripts assume geoJSON contains coordinates with
Latitude/Longitude. In case, the shape file contains other coordinates, such as
EPSG:27700, convert it to lat/long coordinates (EPSG:4326) using additional
arguments for coordinates:
```
ogr2ogr -f GeoJSON -s_srs EPSG:27700 -t_srs EPSG:4326 <output.geojson> <input.shp>
```

## Resolve places
If the dcid for the place can't be extracted from the geoJSON features
extract the places and the properties in the geoJSON into a csv
with a row per feature using the following command:
```
python3 process_geojson.py --input_geojson=<input.gsojson> --output_csv=<place_properties.csv>
```
Then add a 'dcid' column with the resolved place using other tools such as the
[place_name_resolver](https://github.com/datacommonsorg/data/tree/master/tools/place_name_resolver).

Pass the csv with resolved places to the next step to generated MCFs with the
flag --places_csv.


## Generate MCFs with geoJsonCoordinates
Run the `process_geojson.py` script to generate MCF files with the
geoJsonCoordinate property containing the boundary polygons. One MCF file is
generated for each polygon simplification level with the suffix DP<N> where
N is a simplification level.

```
# Create output_geojson.mcf with Nodes for each feature in the input geoJSON
python $GEO_DIR/process_geojson.py --input_geojson=<input.geojson> \
  --output_mcf_prefix=output_geojson 
```


The script supports additional arguments:
```
  --place_name_properties: list of properties used to create the name of the
    place. The name is looked up in the places_csv for the place dcid.
  
  --places_csv: csv file with dcid for resolved places.
    If should contain the columns: 'place_name' with the name of the place
    and 'dcid' with the resolved dcid.

  --new_dcid_template: Format string used to generate the dcid for places that
    can't be resolved using the places_csv.
    It can refer to the geoJSON features. For example: 'geoID/{FIPS}' where 'FIPS'
    is a feature in the geoJSON.

  --output_mcf_pvs: Comma separated list of property:value to be added to the
    output MCF. The value can be a python format string with reference to other
    properties. For example: "location: [LatLong {LAT} {LONG}]"
    where 'LAT' and 'LONG' are features in the geoJSON.
    These property:values are added to the first output MCF without the
    simplified polygons.
    Some common properties to add to the output:
      'typeOf: dcid:AdministrativeArea1,location: [LatLong {latitude} {longitude}],containedInPlace: dcid:country/AUS,name: "{place_name}"'

    The value can also be a python expression prefixed with '='.
    For example:
       'typeOf: ="AdministrativeArea1" if len(dcid) <= 8 else "AdministrativeArea2"'

```

