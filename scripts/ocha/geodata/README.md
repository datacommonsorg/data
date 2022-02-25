# OCHA Geodata

This directory contains scripts to turn shapefiles from UN OCHA
(https://data.humdata.org) into MCF suitable for import into Data Commons.

This includes geojsons for the following countries:
* [Nepal](https://data.humdata.org/dataset/administrative-bounadries-of-nepal)
* [Pakistan](https://data.humdata.org/dataset/pakistan-administrative-level-0-1-2-and-3-boundary-polygons-lines-and-central-places)
* [Bangladesh](https://data.humdata.org/dataset/administrative-boundaries-of-bangladesh-as-of-2015#)
* [China](https://data.humdata.org/dataset/cod-ab-chn)

## Generation

1. Download and prepare geojsons.  This depends on `ogr2ogr` tool.

   ```
   export COUNTRY=CN   # Options are: BG, CN, NP, PK
   ./download.sh $COUNTRY
   ```

2. Generate ID maps.

    ```
    export OUTDIR=scratch/$COUNTRY/output
    mkdir -p "$OUTDIR"
    python3 generate_mcf.py \
      --ocha_input_geojson_pattern=scratch/$COUNTRY/*.geojson \
      --ocha_output_dir="$OUTDIR" \
      --ocha_generate_id_map=True
    ```

3. Resolve the names using Place Name Resolver.

   ```
   go run ../../../tools/place_name_resolver/resolver.go \
     --in_csv_path="$OUTDIR/id_map.csv" \
     --out_csv_path="$OUTDIR/resolved_id_map.csv" \
     --maps_api_key=<KEY>
   ```

4. Manually validate and fix-up the `resolved_id_map.csv`

5. Generate the MCFs

   ```
   python3 generate_mcf.py \
      --ocha_input_geojson_pattern="scratch/$COUNTRY/*.geojson" \
      --ocha_output_dir="$OUTDIR" \
      --ocha_resolved_id_map="$OUTDIR"/resolved_id_map.csv
   ```

## Testing

TODO: implement me
