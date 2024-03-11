# Simple Imports

This folder contains configs for imports using [Simple Sttas
Importer](https://github.com/datacommonsorg/import/edit/master/simple/README.md).

## Import config

Each import has a sub-folder with a config file `<import-name>/simple_import.json`.
The parameters for the simple import config file are described in detail 
[here](https://github.com/datacommonsorg/import/blob/master/simple/stats/config.md).

The config has the following parameters:
```
{
  "dataDownloadUrl": ["<GCS path containing input files>"],
  "inputFiles": {
    "<file1.csv>": {
      "importType": "observations",
      "entityType": "Country",
    },
  },
  "provenanceUrl": "<url describing the import source data>",
  "provenanceDescription": "<description including citation for the import source>",
  "cronSchedule": "Cron format <Minute> <Hour> <Day-of-month> <Month> <Day-of-week>"
}
```

Imports with a cronSchedule are processed periodically as a cloud run job by
the [import automation](https://github.com/datacommonsorg/data/tree/master/import-automation).


## Adding a new import

To add a new data source, copy the input files to a GCS bucket that is
read accessible to the service account `965988403328-compute@developer.gserviceaccount.com`.

Then create a sub-folder for the import under `data/simple_imports/<import_name>`.
Add an import config `simple_import.json` with the list of input files to be
processed.
The input files should be in one of the [supported formats](https://github.com/datacommonsorg/import/tree/master/simple#input-files).

