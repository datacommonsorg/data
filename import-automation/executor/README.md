# Import Automation Executor

This directory contains code for the executor of the import automation system,
which runs user scripts, generates CSVs and MCFs, and imports them to the Data
Commons knowledge graph using the importer.

## Running locally

Authenticate with GCP first: `gcloud auth application-default login`

### Scheduling or Updating An Import Locally

You can schedule (on the GCP Cloud Scheduler) or execute an import job from your local machine.

Ensure this script is executed from the directory which contains `schedule_update_import.sh`, i.e. from `/data/import-automation/executor`. Configs (`<repo_root>/import-automation/executor/app/configs.py`) are loaded from GCS. To override any configs locally, set them in the file `<repo_root>/import-automation/executor/config_override.json`. note that the config fields must belong to `<repo_root>/import-automation/executor/app/configs.py`, else the update will produce an Exception. Note that the `user_script_args` field in configs can also be set in the config file.

Note: any local changes to the `<repo_root>/import-automation/executor/config_override.json` file are ignored by git. This was done using:

```
Run git update-index --skip-worktree <repo_root>/import-automation/executor/config_override.json
```

To start tracking changes to this file, execute the following:
```
Run git update-index --no-skip-worktree <repo_root>/import-automation/executor/config_override.json
```

To get a list of files that are skipped when checking for changes, execute:

```
Run git ls-files -v . | grep ^S
```

### Usage

Run `./schedule_update_import.sh --help` for usage.


#### Schedule an Import:
To schedule an import to run as a cron job on the GCP Cloud Scheduler, do the following:

```
Run `./schedule_update_import.sh -s <project_id> <path_to_import>`
```

`<project_id>` is the GCP project id where the import executer is run from e.g. `datcom-import-automation-prod`.
`<path_to_import>` is the path to the import (relative to the root directory of the `data` repo), with the name of the import provided with a colon, e.g. `scripts/us_usda/quickstats:UsdaAgSurvey`.

Example invocation:

```
Run `./schedule_update_import.sh -s datcom-import-automation-prod scripts/us_usda/quickstats:UsdaAgSurvey`
```

The script will log the name of the Cloud Scheduler job and a url for all the jobs on the scheduler. Please verify that all the job metadata was updated as expected.

### Using git commits
Imports can also be scheduled by specifying a git commit message. Import targets are specified in the commit message using the IMPORTS tag. The system accepts one or two of the following formats depending on the files affected by the commit.

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
   (see [Using git commits](#using-git-commits)). If no tag
   is found, no imports will be executed.

### Scheduling Updates

1. Push to master of datacommonsorg/data and specify the targets in the commit
   message as described by [using git commits](#using-git-commits)
   but using the SCHEDULES tag instead of IMPORTS.
2. Configure the production pipeline to pick up the data files at some schedule.


## Deployment

1. Check in the `import-automation` directory to the repository.
2. [Create a Cloud Tasks queue](#creating-cloud-task-queue)
3. [Connect the repository to Cloud Build and set up Cloud Build triggers](#setting-up-cloud-build)


### Creating Cloud Task Queue
- See https://cloud.google.com/tasks/docs/creating-queues#creating_a_queue
- It is recommended that `maxAttempts` be set to one. This can be done by `gcloud tasks queues update <QUEUE_ID> --max-attempts=1`


### Setting Up Cloud Build
Cloud Build [configuration](cloudbuild/cloudbuild.yaml) creates asynchronous tasks using Cloud Tasks on pull requests and pushes to master to trigger the executor. The tasks pass information about the commits to the executor and can optionally pass any configurations for the executor.

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

#### Update an Import:
You can execute an import process locally. Note that this is not recommended for import scripts which take longer than a few minutes to execute because all the processing is done locally. For all prod imports, the recommended path is to Schedule an Import. 

Instead of downloading a fresh version of this repo from GitHub, this script uses the locally downloaded/cloned current state of the repo by inferring the path to the `data` root directory. A side effect is that upon completion, the local GitHub repo may have other artifacts, e.g. output CSV/TMCF files produced. You may want to revert those files if they are not intended to be committed.

Once the script runs to completion, the data directory's latest update is printed (along with the location on GCS) which can confirm whether the import actually produced new data. Note: it is a good idea to check the directory path printed to see if the expected import files are all there.

To excute an Update locally, do the following:

```
Run `./schedule_update_import.sh -u <project_id> <path_to_import>`
```

`<project_id>` is the GCP project id where the import executer is run from e.g. `datcom-import-automation-prod`.
`<path_to_import>` is the path to the import (relative to the root directory of the `data` repo), with the name of the import provided with a colon, e.g. `scripts/us_usda/quickstats:UsdaAgSurvey`.

Example invocation:

```
Run `./schedule_update_import.sh -u datcom-import-automation-prod scripts/us_usda/quickstats:UsdaAgSurvey`
```


## Local Executor [should be deprecated soon]

```
PYTHONPATH=$(pwd) python app/main.py

``

Run `. run_local_executor.sh --help` for usage.


## Configuring the Executor

The executor has a number of customizable configurations listed in
[app/configs.py](app/configs.py). Some have default values; the others need
explicit values. The Cloud Tasks tasks created by Cloud Build can pass the
configurations to the executor. To edit a configuration:
1. Add the key-value pair to "configs" field in
   data/import-automation/cloudbuild/cloudbuild.yaml if it is not already there
2. Check in the cloudbuild.yaml to GitHub
3. Go to the Cloud Build page on Google Cloud and add the key-value pair as
   a substitution variable to the trigger

Note: A scheduled cron job for updating a dataset inherits some of the
configurations for the run that creates the job. The configurations for a cron
job is stored in the body of the job. To change the configurations for a created
cron job, go to the Cloud Scheduler page on Google Cloud and edit the job
directly, or write a script to query the Cloud Scheduler API (see
https://cloud.google.com/scheduler/docs/reference/rest).


## Deploying on App Engine

```
gcloud app deploy
```

## Running Tests

```
export GITHUB_AUTH_USERNAME=<your username>
export GITHUB_AUTH_ACCESS_TOKEN=<your access token>
. run_test.sh
```
