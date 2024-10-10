# Import Automation System

The import automation system has three components:
1. [Cloud Build configuration file](cloudbuild/README.md)
2. [Executor](executor/README.md)

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

### Scheduling Updates

1. Push to master of datacommonsorg/data and specify the targets in the commit
   message as described by [Specifying Import Target](#specifying-import-targets)
   but using the SCHEDULES tag instead of IMPORTS.
2. Configure the production pipeline to pick up the data files at some schedule.


## Deployment

1. Check in the `import-automation` directory to the repository.
2. [Configure](executor/README.md#configuring-the-executor) and [deploy](executor/README.md#deploying-on-app-engine) the executor
5. [Create a Cloud Tasks queue](#creating-cloud-task-queue)
6. [Connect the repository to Cloud Build and set up Cloud Build triggers](#setting-up-cloud-build)


### Creating Cloud Task Queue
- See https://cloud.google.com/tasks/docs/creating-queues#creating_a_queue
- It is recommended that `maxAttempts` be set to one. This can be done by `gcloud tasks queues update <QUEUE_ID> --max-attempts=1`


### Setting Up Cloud Build
1. [Connect](https://cloud.google.com/cloud-build/docs/automating-builds/create-manage-triggers#connect_repo) the repository to Cloud Build
2. Create the trigger that runs on pull requests for importing to dev
   - See [this](https://cloud.google.com/cloud-build/docs/automating-builds/create-manage-triggers#build_trigger) for how to create triggers
   - Choose these settings
     - **Event**: `Pull request (GitHub App only)`
     - **Source**
       - **Repository**: Choose the connected repository from the list
       - **Branch**: `^master$`
       - **Comment control**: Choose from one of the three options.
         - `Required except for owners and collaborators`: Pull requests from owners and collaborators would be able to trigger Cloud Build directly. Non-collaborators would need a `/gcbrun` comment from an owner or collaborator in the pull request 
         - `Required`: Every pull request would need a `/gcbrun` comment from an owner or collaborator to run Cloud Build
         - `Not required`: Every pull request can trigger Cloud Build directly.
     - **Build Configuration**
       - **File type**: `Cloud Build configuration file (yaml or json)`
       - **Cloud Build configuration file location**:  `/import-automation/cloudbuild/cloudbuild.yaml`
       - **Substitution variables**
         - **_EMAIL_ACCOUNT**: `<email account used for sending notifications>`;
         - **_EMAIL_TOKEN**: `<password, app password, or access token of the email account>`
         - **_GITHUB_AUTH_USERNAME**: `<GitHub username to authenticate with GitHub API>`
         - **_GITHUB_AUTH_ACCESS_TOKEN**: `<access token of the GitHub account>`
         - **_GITHUB_REPO_NAME**: `<name of the connected repository, e.g., data>`
         - **_GITHUB_REPO_OWNER_USERNAME**: `<username of the owner of the repository, e.g., datacommonsorg>`
         - **_HANDLER_SERVICE**: `<service the executor is deployed to, e.g., default>`
         - **_HANDLER_URI**: `<URI of the executor's endpoint that imports to dev, e.g., />`
         - **_IMPORTER_OAUTH_CLIENT_ID**: `<OAuth client ID used to authenticate with the proxy for the importer>`
         - **_TASK_LOCATION_ID**: `<location ID of the Cloud Tasks queue, e.g., us-central1>` (This can be found by going to the Cloud Tasks control panel and look at the "Location" column.)
         - **_TASK_PROJECT_ID**: `<ID of the Google Cloud project that hosts the task queue, e.g., google.com:datcom-data>`
         - **_TASK_QUEUE_NAME**: `<Name of the task queue>`
3. Create the trigger that runs on pushes to *master* for scheduling updates
   - Copy the dev trigger but add/override these settings
     - **Event**: `Push to a branch`
     - **Build Configuration**
       - **Substitution variables** (keeping the others)
         - **_BASE_BRANCH**: `master`
         - **_HEAD_BRANCH**: `master`
         - **_PR_NUMBER**: `0`
         - **_HANDLER_URI**: `/schedule`
