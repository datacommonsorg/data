# Wildland Fire Interagency Geospatial Services (WFIGS)
[The Wildland Fire Interagency Geospatial Services (WFIGS)](https://data-nifc.opendata.arcgis.com/pages/wfigs-page) Group provides authoritative geospatial data products under the interagency Wildland Fire Data Program

## About the Dataset
This dataset report locations for fires in the United states since 2019. The source provides APIs to get historical and Year to date(YTD) data.

## Instructions

We use the WFIGS API to get data for US fires.

To explore the API, use the [API Explorer](https://data-nifc.opendata.arcgis.com/datasets/nifc::wfigs-wildland-fire-locations-full-history/api).

Sample call: https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Fire_History_Locations_Public/FeatureServer/0/query?where=1%3D1&outFields=InitialLatitude,InitialLongitude,InitialResponseAcres,InitialResponseDateTime,UniqueFireIdentifier,IncidentName,IncidentTypeCategory,IrwinID,FireCauseSpecific,FireCauseGeneral,FireCause,FireDiscoveryDateTime,ContainmentDateTime,ControlDateTime,IsCpxChild,CpxID,DiscoveryAcres,DailyAcres,POOFips,POOState,EstimatedCostToDate,TotalIncidentPersonnel,UniqueFireIdentifier&outSR=4326&orderByFields=FireDiscoveryDateTime&f=json&resultType=standard

This will return paged fire records, and we need to iterate through these pages to get the full output.

### Downloading and Processing Data

To download and process WFIGS fire location data, run
```
python3 wfigs_data.py
```

Running this command generates the 'processed_data.csv' file.

### TMCF

'wfigs.tmcf' has the [tmcf](https://github.com/datacommonsorg/data/blob/master/docs/mcf_format.md#template-mcf) used to convert the data into nodes.
