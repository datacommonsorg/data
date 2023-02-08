This directory contains scripts to extract gridded data from EarthEngine using
data sets like
[Dynamic
World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1),
and convert them into data files per grid region, such as [S2 cell](https://s2geometry.io/devguide/s2cell_hierarchy), aggregated statvar observations and events.

## Setup

The scripts use [Google Earth Engine](https://earthengine.google.com/)
[Python APIs](https://developers.google.com/earth-engine/guides/python_install)
to extract flooded regions as a [geoTIFF](https://en.wikipedia.org/wiki/GeoTIFF)
file.  These `.tif` files are exported to [Google Cloud
Storage](https://cloud.google.com/storage) (GCS).
The raster files are then copied over using `gsutil` to be processed into `.csv` locally.


The tools can be installed as follows:
### Google Earth Engine Python API

1. Install the API with the command:
```
pip install earthengine-api --upgrade
```

2. Authenticate
Run the following command and follow the instructions to open a URL on a browser
to get an authentication token.
```
earthengine authenticate
```

If this is being executed on a remote computer without browser, run the
following command:
```
earthengine authenticate --quiet
```

### Google Cloud SDK
Install the `gsutil` command to copy files from GCS to the local
machine.

1. Install GCS tools using the command:
```
sudo apt-get install google-cloud-sdk
```

2. Authenticate to GCS project
Authenticate to the Google Cloud service using the following command and follow
the instructions:
```
gcloud auth login
```

3. Create a bucket on Google Cloud Storage (GCS)
To copy files on GCS, create a storage bucket with the following command or on
the cloud console.
```
gsutil mb gs://<GCS-BUCKET-NAME>/
```

## Extract geoTIFF from EarthEngine (EE)
The script `earthengine_image.py` generates geoTIFF raster files from
EarthEngine for selected bands from an image collection from the [EarthEngine data
catelog](https://developers.google.com/earth-engine/datasets).

For example, to extract regions with water from the EarthEngine's [Dynamic
World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) dataset, run the following:
```
# Download monthly images for the last 12 months.
# Project and bucket on Google Could Storage to save the geoTiff from EE
GCS_BUCKET='<YOUR_BUCKET>' 
GCS_FOLDER='earth-engine-exports'
python3 earthengine_image.py  \
   --gcs_bucket="$GCS_BUCKET" \
   --gcs_folder="$GCS_FOLDER" \
   --start_date=2022-01-01 \
   --time_period=P1M  \
   --ee_image_count=12 \
   --ee_mask=land \
   --ee_dataset=dynamic_world \
   --band=water \
   --band_min=0.7 \
   --ee_reducer=max
# Once it it completes, the images would be available on
# gs://<GCS_BUCKET>/<GCS_FOLDER>/*.tif
```

## Process GeoTIFF files into gridded data CSVs
The script `raster_to_csv.py` converts the geoTiff from the previous step into a
CSV file with a row per [S2
cell](https://s2geometry.io/devguide/s2cell_hierarchy) with columns for each of
the band in the geoTiff. The geenrated csv can be processed
using the
[import tool](https://github.com/datacommonsorg/import/blob/master/docs/usage.md) into StatVarObservation MCF nodes.

For example, to extract S2 cells with water from the geoTiff generated 
in the previous step into a StatVarObservation MCF nodes for
[Area_FloodEvent](https://datacommons.org/browser/Area_FloodEvent), run the
following:
```
# Download the geoTiff from GCS
gsutil cp gs://<GCS_BUCKET>/<GCS_FOLDER>/*.tif .
# Convert the geoTiff into raster
python3 raster_to_csv.py \
  --input_geotiff=ee_image_dynamic_world-band_water-r_max-mask_land-s_1000-from_2022-01-01.tif \
  --output_date=2022-01 \
  --output_csv=flood_s2_cells_svobs.csv

# Creates flooded_s2_cells.csv with the following columns:
# area,date,latitude,longitude,s2CellId,s2Level,water
# This can be procesed with s2cells_svobs.tmcf using dc-import
dc-import genmcf flood_s2_cells_svobs.csv s2cell_svobs.tmcf
```

The `raster_to_csv.py` script can also process other csv data files with columns for `latitude,longitude` into CSV for StatVarObservations by S2 cells.
```
python3 raster_to_csv.py \
  --input_csv=<CSV file with a row for each lat/lng> \
  --output_csv=s2_cells_svobs.csv \
```

## Generate events for places
The script `process_events.csv` converts a csv file with observations for a
place, such as an s2 cell, into events aggregated over space and time.

For example, the flood_s2_cells_svobs.csv generated in the earlier step,
can be converted into [FloodEvent](http://daatcommons.org/browser/FloodEvent) nodes
with properties such as `startDate`, `endDate` and `affectedPlaces` using the
following command:
```
# Update the event_config.py with settings for the data set.
python3 process_events.py \
  --config=event_config.py \
  --input_csv=flood_s2_cells_svobs.csv \
  --output_path=flood_ \

# This generates the following files:
# - flood_events.{csv,tmcf}: Event nodes
# - flood_svobs.{csv}: Observations for each event
```


## Testing
To test the scripts in this folder, run the commands:
```
python3 -m unittest earthengine_image.py
python3 -m unittest raster_to_csv.py
python3 -m unittest process_events.py
```
