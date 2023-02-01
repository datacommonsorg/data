# Floods
This directory contains scripts to extract flood data from EarthEngine using
data sets like
[Dynamic
World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1) 
and generate data files statvar observations on monthly flooded areas
aggregated to different levels of S2 cells.

## Setup

The scripts use [Google Earth Engine](https://earthengine.google.com/)
[Python APIs](https://developers.google.com/earth-engine/guides/python_install)
to extract flooded regions as a [geoTIFF](https://en.wikipedia.org/wiki/GeoTIFF)
file.  These `.tif` files are exported to Google Cloud Storage (GCS).
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
The scripts use the `gsutil` command to copy files form GCS to the local
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
Run the following command to extract flood regions as a `.tif` file from
EarthEngine into GCS, replacing `<GCS-PROJECT>` with the GCS project
authenticated to earlier, `<GCS-BUCKET-NAME>` with the GCS bucket created in
the step above. The `<GCS-DIRECTORY>` will be created if it doesn't already
exist.
```
./run.sh -g <GCS-PROJECT> -b <GCS-BUCKET-NAME> -d <GCS-DIRECTORY>
```

This invokes the script `earthengine_image.py` to extract the raster image and
`raster_to_csv.py` to process the image into data CSVs.
The earth engine export tasks can be viewed on [Earth Engine Task
manager](https://code.earthengine.google.com/tasks) and may take some time (over
30 mins) to complete.

For more options, such as extracting images for multiple months or
processing images from past EE export tasks, please use `./run.sh -h`.


## Testing

```
python3 -m unittest earthengine_image.py
python3 -m unittest raster_to_csv.py
```
