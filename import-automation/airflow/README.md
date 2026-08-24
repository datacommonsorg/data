# Cloud Batch Airflow DAG

This package contains the first Managed Airflow workflow for incrementally
moving import automation to Airflow. The `cloud_batch_container_command` DAG
submits one Cloud Batch job, waits for it to finish, and pauses for human
review.

Each DAG run supplies two required parameters:

- `image_uri`: container image for the Batch runnable
- `command`: command executed inside that container with `/bin/sh -c`

The DAG is manually triggered (`schedule=None`). Different runs of the same DAG
can use different parameter values.

## Prerequisites

The current target is Managed Airflow Gen 3 image
`composer-3-airflow-3.2.2-build.2`. As of 2026-08-24, this is the latest listed
Airflow 3.2.2 build and includes Google provider 22.2.2. Confirm that the build
has completed rollout in the target region before creating the environment.

Do not accept the default image when creating the environment: the current
default is an Airflow 2 image.

The DAG uses a deferrable operator. Ensure that the environment has at least
one Airflow triggerer in standard-resilience mode or at least two in
high-resilience mode. Managed Airflow Gen 3 normally enables triggerers, but an
environment can be configured with zero.

For a new standard-resilience environment, a minimal creation command is:

```sh
gcloud composer environments create ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  --image-version composer-3-airflow-3.2.2-build.2 \
  --service-account COMPOSER_SERVICE_ACCOUNT \
  --triggerer-count 1 \
  --triggerer-cpu 0.5 \
  --triggerer-memory 2
```

For an existing environment, check the environment configuration in the
Google Cloud console. If triggerers are disabled, enable them before running
this DAG. Updating triggerer configuration can restart Airflow components, so
do it before starting DAG runs.

## Service accounts and IAM

Three service accounts are involved. They have different responsibilities and
must not be treated as the same identity.

| Principal | Required role | Scope | Purpose |
|---|---|---|---|
| Managed Airflow environment service account | `roles/batch.jobsEditor` | Project where Batch jobs are created | Create the job and poll its status |
| Managed Airflow environment service account | `roles/iam.serviceAccountUser` | Dedicated Batch runtime service account | Attach that service account to Batch VMs (`iam.serviceAccounts.actAs`) |
| Dedicated Batch runtime service account | `roles/batch.agentReporter` | Project where Batch jobs run | Report Batch agent state |
| Dedicated Batch runtime service account | `roles/logging.logWriter` | Project where Batch jobs run | Write Batch task and agent logs |
| Google-managed Batch service agent | `roles/batch.serviceAgent` | Project where Batch jobs run | Manage the underlying Batch resources; normally granted automatically |

The Batch runtime service account also needs permissions for resources used by
the container. Examples include `roles/artifactregistry.reader` on a private
Artifact Registry repository and narrowly scoped GCS object access. These are
workload permissions and are not required merely to submit a Batch job.

The Managed Airflow environment service account does not need the workload's
GCS, database, or other data permissions unless an Airflow task accesses those
resources directly.

### 1. Identify the Managed Airflow environment service account

```sh
gcloud composer environments describe ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  --format='get(config.nodeConfig.serviceAccount)'
```

Use the returned email as `COMPOSER_SERVICE_ACCOUNT` in the following commands.

### 2. Enable required APIs

Enable Batch, Compute Engine, and Cloud Logging in the project that runs the
Batch job. Enable Artifact Registry too if the image is stored there.

```sh
gcloud services enable \
  batch.googleapis.com \
  compute.googleapis.com \
  logging.googleapis.com \
  --project PROJECT_ID
```

### 3. Create or select the Batch runtime service account

For example:

```sh
gcloud iam service-accounts create airflow-batch-runner \
  --project PROJECT_ID \
  --display-name='Airflow Cloud Batch runtime'
```

Its email is:

```text
airflow-batch-runner@PROJECT_ID.iam.gserviceaccount.com
```

Use that email as `BATCH_SERVICE_ACCOUNT` below and as the value of the
`CLOUD_BATCH_SERVICE_ACCOUNT` environment variable.

### 4. Grant the Managed Airflow account permission to submit jobs

Grant Batch Job Editor on the Batch project:

```sh
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:COMPOSER_SERVICE_ACCOUNT' \
  --role='roles/batch.jobsEditor'
```

Grant Service Account User on only the dedicated Batch runtime account:

```sh
gcloud iam service-accounts add-iam-policy-binding BATCH_SERVICE_ACCOUNT \
  --project PROJECT_ID \
  --member='serviceAccount:COMPOSER_SERVICE_ACCOUNT' \
  --role='roles/iam.serviceAccountUser'
```

`roles/batch.jobsEditor` supplies `batch.jobs.create`, `batch.jobs.get`, and
the related job, operation, and task permissions used by the submit-and-wait
operator. `roles/iam.serviceAccountUser` supplies the required
`iam.serviceAccounts.actAs` permission.

### 5. Grant the Batch runtime account its baseline permissions

```sh
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:BATCH_SERVICE_ACCOUNT' \
  --role='roles/batch.agentReporter'

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:BATCH_SERVICE_ACCOUNT' \
  --role='roles/logging.logWriter'
```

Then grant only the application-specific permissions needed by the selected
container. Do not grant `roles/editor` to either service account.

Only trusted users should be allowed to trigger this DAG. Its inputs permit the
caller to choose executable code and a shell command that run with the Batch
service account's permissions.

## Configure the Managed Airflow environment

Set the project, Batch region, and Batch runtime service account used by the
DAG:

| Variable | Purpose |
|---|---|
| `GCP_PROJECT_ID` | Project in which Cloud Batch jobs are created |
| `CLOUD_BATCH_REGION` | Region in which Cloud Batch jobs are created |
| `CLOUD_BATCH_SERVICE_ACCOUNT` | Dedicated service account used by Batch VMs |

```sh
gcloud composer environments update ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  --update-env-variables=GCP_PROJECT_ID=PROJECT_ID,CLOUD_BATCH_REGION=BATCH_REGION,CLOUD_BATCH_SERVICE_ACCOUNT=BATCH_SERVICE_ACCOUNT
```

This is an environment update and can restart Airflow components. Wait for it
to complete before uploading or invoking the DAG. The DAG intentionally fails
to parse with a clear error if one of these values is absent.

## Install the DAG

Copy the complete `datacommons_airflow` package into the environment's DAG
prefix so its absolute imports continue to work:

```sh
COMPOSER_DAGS_PREFIX="$(gcloud composer environments describe ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  --format='value(config.dagGcsPrefix)')"

gcloud storage cp --recursive \
  import-automation/airflow/datacommons_airflow \
  "${COMPOSER_DAGS_PREFIX}/"
```

Managed Airflow adds the DAG directory to `PYTHONPATH`; the unique
`datacommons_airflow` package name avoids collisions with Airflow and standard
library packages. Synchronization and DAG parsing usually take approximately
one to two minutes.

After synchronization, confirm that `cloud_batch_container_command` appears in
the Airflow UI and that **Browse > DAG Import Errors** contains no error for the
package.

## Update the DAG

Run the focused tests before uploading an update:

```sh
./run_tests.sh -p import-automation/airflow
```

Resolve the DAG prefix as shown in the installation section. Upload the helper
module first and the DAG definition last:

```sh
gcloud storage cp \
  import-automation/airflow/datacommons_airflow/__init__.py \
  import-automation/airflow/datacommons_airflow/cloud_batch_job.py \
  "${COMPOSER_DAGS_PREFIX}/datacommons_airflow/"

gcloud storage cp \
  import-automation/airflow/datacommons_airflow/cloud_batch_command_dag.py \
  "${COMPOSER_DAGS_PREFIX}/datacommons_airflow/"
```

Wait one to two minutes, check DAG import errors, and confirm that the expected
DAG code is displayed before triggering a new run. Updating the source files
does not restart an already running Cloud Batch job.

## Invoke the DAG

The DAG might be paused after its first upload. Unpause it in the Airflow UI or
with:

```sh
gcloud composer environments run ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  dags unpause -- cloud_batch_container_command
```

### Airflow UI

In the Airflow UI:

1. Open the `cloud_batch_container_command` DAG.
2. Select **Trigger DAG**.
3. Enter an image URI and command in the generated parameter form.
4. Trigger the run and open the `run_container_command` task.

Example values:

```text
image_uri: gcr.io/google-containers/busybox
command: echo "hello from Cloud Batch"
```

### Google Cloud CLI

Pass the two runtime parameters as DAG-run configuration:

```sh
gcloud composer environments run ENVIRONMENT_NAME \
  --project PROJECT_ID \
  --location COMPOSER_REGION \
  dags trigger -- \
  --conf='{"image_uri":"gcr.io/google-containers/busybox","command":"echo hello from Cloud Batch"}' \
  cloud_batch_container_command
```

Airflow maps this configuration into the DAG's typed parameters when
`core.dag_run_conf_overrides_params` is enabled. This is the normal setting for
runtime parameter overrides. If the setting is disabled, use the Airflow UI
trigger form or enable the setting intentionally.

Each invocation creates a separate DAG run. Concurrent runs can provide
different image and command values.

### Review the result

After the Batch job succeeds, the `review_batch_result` task waits for a human
response. Open **Required Actions** in the Airflow UI and choose:

- **Run again**: trigger a new run of this DAG with the same `image_uri` and
  `command`. The new run creates a new Cloud Batch job and pauses for review
  again.
- **Continue**: run the `continue_workflow` marker and finish the current DAG
  run successfully.

Airflow DAGs cannot contain a cycle back to an upstream task. Therefore, the
rerun is represented as a new DAG run instead of clearing the Batch task in the
current run. This preserves an audit trail for every human-requested attempt.

The reviewer needs access to the Managed Airflow UI and permission in Airflow
RBAC to respond to required actions. This does not require another Cloud Batch
IAM role for the Managed Airflow service account.

### Monitor the run

Open the `run_container_command` task in the Airflow Grid view. The task log
shows the submitted Batch job and its state changes. Use the recorded job ID to
inspect the workload in **Google Cloud console > Batch > Jobs** and to open its
Cloud Logging entries.

The selected image must contain `/bin/sh`. The Airflow task remains deferred
while the Batch job runs, so it does not occupy an Airflow worker. The task
succeeds only when the Batch job succeeds and exposes the returned Batch job
representation through XCom.

The initial machine configuration is deliberately hardcoded in
`cloud_batch_job.py`. Resource parameters can be added to the typed DAG
parameters after the execution path is proven.

## Retry behavior

Airflow task retries and Batch task retries are both disabled in this initial
version. If the task fails, inspect the exact Batch job and then clear the
Airflow task to rerun it. The cleared task gets a new try number and therefore
a new deterministic Batch job ID.

This avoids automatically launching a second job after an ambiguous submission
failure. Reattaching to an already submitted Batch job can be added separately
when recovery semantics are defined.

## Test

The focused tests cover job IDs, environment validation, and the generated
Batch job descriptor without requiring Airflow to be installed locally:

```sh
./run_tests.sh -p import-automation/airflow
```

## References

- [Install and update DAGs in Managed Airflow](https://cloud.google.com/composer/docs/composer-3/manage-dags)
- [Trigger DAGs in Managed Airflow](https://cloud.google.com/composer/docs/composer-3/schedule-and-trigger-dags)
- [Cloud Batch IAM roles](https://cloud.google.com/iam/docs/roles-permissions/batch)
- [Run a Batch job as a custom service account](https://cloud.google.com/batch/docs/create-run-job-custom-service-account)
- [Airflow human-in-the-loop operators](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/hitl.html)
