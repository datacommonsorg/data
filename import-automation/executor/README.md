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


## Local Executor

Run `. run_local_executor.sh --help` for usage.

## Running Tests

```
export GITHUB_AUTH_USERNAME=<your username>
export GITHUB_AUTH_ACCESS_TOKEN=<your access token>
. run_test.sh
```
