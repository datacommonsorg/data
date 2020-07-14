# Import Executor

This directory contains code for an App Engine app that exposes
1. an endpoint at / for Cloud Tasks to trigger and that runs the user code
   that downloads and processes data files
2. an endpoint at /update that takes an absolute import name and executes
   the import
   
   
## Deploying on App Engine

The easiest way is to clone the repo in Cloud Shell and run
`gcloud app deploy`. Some constants in [`configs.py`](app/configs.py) might
need to be changed. 

## Testing on GCP

I have not figured out a way to test it locally. I have been testing it by
1. deploying the app
2. forking `datacommonsorg/data` to `data-demo`
3. creating a branch `test`
4. creating an empty pull request from `test` to `master`
3. setting up a Cloud Build trigger `task` for `data-demo` that runs task.sh in
   `intrepiditee/data-demo/import-automation/cloudbuild` on pull request
   to `master` branch
4. switching to `test` branch
4. creating `scripts/us_fed/treasury_constant_maturity_rates/manifest.json`
5. modifying some files in `treasury_constant_maturity_rates` directory
6. pushing commit with the commit message containing
   `IMPORTS=us_treasury_constant_maturity_rates`

To test the `/update` endpoint, you will have to modify `HANDLER_URI` of the
Cloud Build trigger from `/` to `/update` and modify `create_body` function in
`create_task.py` to include an `absolute_import_name` field in the task body.

You could also use Cloud Scheduler to POST to the endpoints directly. For example:
1. `Target` = `App Engine HTTP`
2. `URL` = `/update`
3. `Body` = `{"absolute_import_name": "scripts/us_fed/treausury_contant_maturity_rates:us_treausury_contant_maturity_rates"}`


## Testing locally

Run `python3 -m unittest`. See [test/test_integration](test/test_integration.py).
First lines of the generated files would be printed.