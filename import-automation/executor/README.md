# Import Automation Executor

This directory contains code for the executor of the import automation system,
which runs user scripts, generates CSVs and MCFs, and imports them to the Data
Commons knowledge graph using the importer.


## Endpoints (See [app/main.py](app/main.py))

1. `/`
   - Purpose: Importing to dev on pull requests
   - Required Arguments
     - `COMMIT_SHA`: Commit sha of the commit that specifies the targets
       in its commit message
   - Optional Arguments (Used only for logging to the Import Progress Dashboard)
     - `REPO_NAME`: Name of the repository from which the pull request is sent
     - `BRANCH_NAME`: Name of the branch from which the pull request is sent
     - `PR_NUMBER`: Number of the pull request
   - Required Configurations (See [app/configs.py](app/configs.py) for
     descriptions and [Configuring the Executor](#configuring-the-executor) for
     how to pass these configurations)
     - `dashboard_oauth_client_id`
     - `importer_oauth_client_id`
     - `github_auth_username`
     - `github_auth_access_token`
     - `email_account`
     - `email_token`
2. `/update`
   - Purpose: Updating datasets
   - Required Arguments
     - `absolute_import_name`: Absolute import name of the import to update
   - Required Configurations
     - `dashboard_oauth_client_id`
     - `github_auth_username`
     - `github_auth_access_token`
     - `email_account`
     - `email_token`
3. `/schedule`
   - Purpose: Scheduling cron jobs to update datasets
   - Required Arguments
     - `COMMIT_SHA`: Commit sha of the commit that specifies the targets
       in its commit message
   - Required Configurations
     - `dashboard_oauth_client_id`
     - `github_auth_username`
     - `github_auth_access_token`

## Running locally

```
PYTHONPATH=$(pwd) python app/main.py

``

## Local Executor

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
