# Simple Imports

This folder contains configs for imports using [Simple Stats
Importer](https://github.com/datacommonsorg/import/edit/master/simple/README.md).

## Import config

Each import has a sub-folder with a config file `<import-name>/import_config.json`.
The parameters for the simple import config file are described in detail 
[here](https://github.com/datacommonsorg/import/blob/master/simple/stats/config.md).
If there are multiple imports per source, each import can be in a sub-folder
with a source specific folder, such as, `<source>/<import>/import_config.json`.

The config has the following parameters for automated updates:
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
  "cronSchedule": "<Minute> <Hour> <Day-of-month> <Month> <Day-of-week>"
}
```

Imports with a `cronSchedule` are processed periodically as a cloud run job by
the [import automation](https://github.com/datacommonsorg/data/tree/master/import-automation).


## Adding a new import

To add a new data source:
1. Copy the input files to a GCS bucket that is allows objects and metadata read
   access for the service account `965988403328-compute@developer.gserviceaccount.com`
   that runs the import automation for Data Commons.
   Note: Grant access to the bucket containing the input files
   for the roles `Storage Legacy Bucket Reader` and
   `Storage Legacy Object Reader` following the steps described
   [here](https://cloud.google.com/storage/docs/access-control/using-iam-permissions#console).

2. Create a sub-folder for the import under `data/simple_imports/<import_name>`.
3. Add an import config `import_config.json` with the list of input files
 and / or folders to be processed.
The input files should be in one of the [supported formats](https://github.com/datacommonsorg/import/tree/master/simple#input-files).

