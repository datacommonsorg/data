# Import Automation System

The import automation system has three components:
1. [Cloud Build configuration file](cloudbuild/README.md)
2. [Executor](executor/README.md)
3. Import Progress Dashboard
   - [Import Progress Dashboard API](import-progress-dashboard-api/README.md)
   - [Import Progress Dashboard Frontend](import-progress-dashboard-frontend/README.md)

## User Manual

### Specifying Import Targets
Import targets are specified in the commit message using the IMPORTS tag.
The system accepts one or two of the following formats depending on the files
affected by the commit.

1. Absolute import name:
   {path to the directory containing the manifest file}:{import name in the manifest}
2. Relative import name: {import name in the manifest}

In the commit message, use IMPORTS={comma separated list of import names
without spaces between the elements} to specify import targets.
The commit message may contain more than just the tag and list.

A commit can modify files in multiple directories that contain manifest files.
The system will detect the affected directories based on paths of changed files.
If only one directory is affected, both absolute and relative import names
are accepted. If multiple directories are affected, absolute import names must
be used. You can also use IMPORTS=all to ask the system to run all affected
imports and use IMPORTS={path to the directory containing the manifest file}:all
to run all imports in that directory, but they are discouraged as they are not
explicit.


### Example Commit Messages

Assuming the following directory structure:
```
.
└── data
    └── scripts
        └── us_bls
            ├── cpi
            │   ├── README.md
            │   ├── c_cpi_u_1999_2020.csv
            │   ├── c_cpi_u_1999_2020.mcf
            │   ├── c_cpi_u_1999_2020.tmcf
            │   ├── c_cpi_u_1999_2020_import_config.txt
            │   ├── cpi_u_1913_2020.csv
            │   ├── cpi_u_1913_2020.tmcf
            │   ├── cpi_u_1913_2020_import_config.txt
            │   ├── cpi_w_1913_2020.csv
            │   ├── cpi_w_1913_2020.mcf
            │   ├── cpi_w_1913_2020.tmcf
            │   ├── cpi_w_1913_2020_import_config.txt
            │   ├── generate_csv.py
            │   └── manifest.json
            └── jolts
                ├── BLSJolts.csv
                ├── BLSJolts.tmcf
                ├── BLSJolts_StatisticalVariables.mcf
                ├── README.md
                ├── __init__.py
                ├── bls_jolts.py
                ├── import.config
                └── manifest.json
```

Assuming scripts/us_bls/cpi/manifest.json has
```json
{
    "import_specifications": [
        {
            "import_name": "USBLS_CPIAllItemsAverage",
            ...
        }
    ]
}
```

Assuming scripts/us_bls/jolts/manifest.json has
```json
{
    "import_specifications": [
        {
            "import_name": "BLS_JOLTS",
            ...
        }
    ]
}
```

If the commit only changes files in scripts/us_bls/cpi:
- To import USBLS_CPIAllItemsAverage:
  - "fix syntax error IMPORTS=scripts/us_bls/cpi:USBLS_CPIAllItemsAverage" or
  - "IMPORTS=USBLS_CPIAllItemsAverage fix memory leak"
- To import BLS_JOLTS
  - "nice day IMPORTS=scripts/us_bls/jolts:BLS_JOLTS"
- To import both USBLS_CPIAllItemsAverage and BLS_JOLTS
  - "update README IMPORTS=scripts/us_bls/cpi:USBLS_CPIAllItemsAverage,scripts/us_bls/jolts:BLS_JOLTS" or
  - "IMPORTS=USBLS_CPIAllItemsAverage,scripts/us_bls/jolts:BLS_JOLTS hope they succeed"

If the commit changes files in both scripts/us_bls/cpi and scripts/us_bls/jolts
directories:
- To import USBLS_CPIAllItemsAverage:
  - "fix syntax error IMPORTS=scripts/us_bls/cpi:USBLS_CPIAllItemsAverage"
- To import BLS_JOLTS
  - "nice day IMPORTS=scripts/us_bls/jolts:BLS_JOLTS" or
  - "good try IMPORTS=BLS_JOLTS"
- To import both USBLS_CPIAllItemsAverage and BLS_JOLTS
  - "update README IMPORTS=scripts/us_bls/cpi:USBLS_CPIAllItemsAverage,scripts/us_bls/jolts:BLS_JOLTS" or
  - "IMPORTS=scripts/us_bls/cpi:USBLS_CPIAllItemsAverage,BLS_JOLTS hope they succeed"

### Importing to Dev Graph

1. Fork datacommonsorg/data
2. Create a new branch in the fork
3. Create a pull request from the new branch to master of datacommonsorg/data
4. Push commits to the branch. If you want a commit to execute some imports,
   specify the import targets in the commit message
   (see [Specifying Import Targets](#specifying-import-targets)). If no tag
   is found, no imports will be executed.
5. Check the [Import Progress Dashboard](https://dashboard-frontend-dot-datcom-data.uc.r.appspot.com/)

### Scheduling Updates

1. Push to master of datacommonsorg/data and specify the targets in the commit
   message as described by [Specifying Import Target](#specifying-import-targets)
   but using the SCHEDULES tag instead of IMPORTS.
2. Configure the production pipeline to pick up the data files at some schedule.


## Deployment

TODO(intrepiditee): Finish.
