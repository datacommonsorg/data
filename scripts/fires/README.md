# Wildland Fire Interagency Geospatial Services (WFIGS)
[The Wildland Fire Interagency Geospatial Services (WFIGS)](https://data-nifc.opendata.arcgis.com/pages/wfigs-page) Group provides authoritative geospatial data products under the interagency Wildland Fire Data Program

## About the Dataset
This dataset report locations for fires in the United states since 2019. The source provides APIs to get historical and Year to date(YTD) data.

## Instructions

### Downloading and Processing Data

To download and process WFIGS fire location data, run
```
python3 wfigs_data.py
```

Running this command generates the 'processed_data.csv' file.

### TMCF

'wfigs.tmcf' has the [tmcf](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf) used to convert the data into nodes.
