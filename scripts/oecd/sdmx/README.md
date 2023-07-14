# OECD Bulk Import

This folder contains scripts for the bulk OECD import. This is currently a schemaless import.

Note: This was a very quick first pass attempt to get some data in, so only contains a few hundred of the OECD datasets that follow a specific format.

TODO(nhdiaz): Add tests / get remaining data.

To download data: 
```
OPENSSL_CONF=openssl.cnf python3 download.py
```

To process data and generate artifacts:
```
python3 process.py
```

## SDMX

OECD uses the SDMX format for their data. We have translated this into the Data Commons data model as follows:

* The LOCATION dimension is used for observationAbout
* The TIME_PERIOD dimension is used for observationDate
* The TIME_FORMAT attribute is used for observationPeriod
* The UNIT attribute is used for unit
* The POWERCODE attribute is used for scalingFactor
* The OBS_STATUS (observation level) attribute is used for measurementMethod
* All other dimensions and attributes are added the stat var definition
* The series is used as the parent SVG