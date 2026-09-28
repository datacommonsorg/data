# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Airflow DAG for Data Commons Import Automation.

Orchestrates Cloud Batch data imports, updates metadata via import-helper Cloud Run,
and triggers Spanner ingestion Cloud Workflows for staging and production.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable

from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowException, AirflowFailException, AirflowSkipException
from airflow.models import Variable
from airflow.models.param import Param
from airflow.providers.google.cloud.hooks.cloud_batch import CloudBatchHook
from airflow.providers.google.cloud.sensors.workflows import WorkflowExecutionSensor
from airflow.utils.trigger_rule import TriggerRule

# Enable Jinja templating for project_id on WorkflowExecutionSensor
WorkflowExecutionSensor.template_fields = (
    *WorkflowExecutionSensor.template_fields, "project_id")

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from golden_verification import (
    HumanApprovalSensor,
    get_golden_test_imports,
    is_golden_test_import,
    verify_golden_tests,
)

# -----------------------------------------------------------------------------
# Configuration & Helpers
# -----------------------------------------------------------------------------

DAG_ID = os.environ.get("IMPORT_AUTOMATION_DAG_ID", "manual_refresh")
DEFAULT_IMAGE_URI = "us-docker.pkg.dev/datcom-ci/gcr.io/dc-import-executor:stable"
DEFAULT_RESOURCES = {
    "machine": "n2-standard-8",
    "cpu": 8000,
    "memory": 32768,
    "disk": 100
}

PROD_DENYLIST = frozenset({
    "CDC500",
    "CDC_OzoneCounty",
    "CDC_PM25County",
    "CensusCountyBusinessPatterns",
    "CensusSAHIE",
    "EIA_Electricity",
    "EPA_EJSCREEN",
    "EPA_GHGRP",
    "FARS_CrashData",
    "FBIGovCrime",
    "IndiaNSS_HealthAilments",
    "India_RBIStateDomesticProduct",
    "NASA_VIIRSActiveFiresEvents",
    "NCES_PrivateSchool",
    "NCES_PublicSchool",
    "NCES_SchoolDistrict",
    "NOAA_GPCC_StandardardizedPrecipitationIndex",
    "NOAA_GlobalForecastSystem",
    "OECDRegionalDemography_Population",
    "UNEnergy",
    "USCensusPEP_AgeSexRaceHispanicOrigin",
    "USDA_AgricultureCensus",
    "USFed_ConstantMaturityRates_Test",
    "USNationalPrisonerStatistics",
    "WorldBankDatasets",
})


def is_prod_denylisted(import_name: str) -> bool:
    short_name = import_name.split(":")[-1]
    return import_name in PROD_DENYLIST or short_name in PROD_DENYLIST


def get_config_var(key: str, default: str = "") -> str:
    """Reads configuration from Airflow Variable or OS environment."""
    fallback = os.environ.get(key, default)
    try:
        return Variable.get(key, default_var=fallback)
    except Exception:
        return fallback


def generate_job_id(import_name: str, timestamp: int | None = None) -> str:
    """Generates a valid RFC 1035 Cloud Batch job ID."""
    cleaned = re.sub(r"[^a-z0-9-]", "-",
                     import_name.split(":")[-1][:50].lower()).strip("-")
    job_id = f"{cleaned}-{timestamp or int(time.time())}"
    return job_id if job_id[0].isalpha() else f"job-{job_id}"[:63]


def _get_oidc_token(audience: str) -> str | None:
    """Fetches an OIDC identity token for invoking Cloud Run services."""
    from google.auth.transport.requests import Request
    req = Request()
    try:
        from google.oauth2 import id_token
        return id_token.fetch_id_token(req, audience)
    except Exception:
        try:
            import google.auth
            creds, _ = google.auth.default()
            creds.refresh(req)
            return getattr(creds, "id_token", None) or getattr(
                creds, "token", None)
        except Exception as ex:
            logging.error("OIDC token fetch failed: %s", ex)
            return None


def _make_http_post(url: str,
                    body: dict[str, Any],
                    timeout: int = 60) -> dict[str, Any]:
    """Posts JSON payload to an authenticated Cloud Run endpoint with retries."""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util import Retry

    headers = {"Content-Type": "application/json"}
    token = _get_oidc_token(url)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    session = requests.Session()
    retries = Retry(total=3,
                    backoff_factor=2,
                    status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    resp = session.post(url, json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def _report_import_failure(helper_url: str, job_id: str, import_name: str,
                           bucket: str, exec_time: int) -> None:
    """Notifies import-helper of a batch job failure to update Spanner metadata."""
    try:
        _make_http_post(
            f"{helper_url}/imports/status", {
                "jobId":
                    job_id,
                "executionTime":
                    exec_time,
                "imports": [{
                    "importName":
                        import_name,
                    "status":
                        "FAILURE",
                    "latestVersion":
                        f"gs://{bucket}/{import_name.replace(':', '/')}"
                }],
            })
    except Exception as e:
        logging.error("Failed reporting import failure: %s", e)


# -----------------------------------------------------------------------------
# Cloud Batch Job Spec & TaskFlow Operator
# -----------------------------------------------------------------------------


def _build_batch_job_spec(
    image_uri: str,
    import_name: str,
    import_config: str,
    job_id: str,
    resources: dict[str, Any],
    gcs_mount_bucket: str,
    gcs_mount_path: str = "/tmp/gcs",
) -> dict[str, Any]:
    """Builds a dictionary-based Cloud Batch job descriptor."""
    sa_email = get_config_var("CLOUD_BATCH_SERVICE_ACCOUNT")
    task_spec = {
        "runnables": [{
            "container": {
                "imageUri":
                    image_uri,
                "commands": [
                    f"--import_name={import_name}",
                    f"--import_config={import_config}"
                ]
            },
            "environment": {
                "variables": {
                    "IMPORT_NAME": import_name,
                    "BATCH_JOB_NAME": job_id
                }
            },
        }],
        "computeResource": {
            "cpuMilli": int(resources.get("cpu", 8000)),
            "memoryMib": int(resources.get("memory", 32768))
        },
        **({
            "volumes": [{
                "gcs": {
                    "remotePath": gcs_mount_bucket
                },
                "mountPath": gcs_mount_path
            }]
        } if gcs_mount_bucket else {}),
    }
    policy = {
        "instances": [{
            "policy": {
                "machineType": str(resources.get("machine", "n2-standard-8")),
                "provisioningModel": "STANDARD",
                "bootDisk": {
                    "image":
                        "projects/debian-cloud/global/images/family/debian-12",
                    "sizeGb":
                        int(resources.get("disk", 100))
                },
            },
            "installOpsAgent": True,
        }],
        **({
            "serviceAccount": {
                "email": sa_email
            }
        } if sa_email else {}),
    }
    return {
        "taskGroups": [{
            "taskSpec": task_spec,
            "taskCount": 1,
            "parallelism": 1
        }],
        "allocationPolicy": policy,
        "logsPolicy": {
            "destination": "CLOUD_LOGGING"
        },
    }


@task(task_id="run_import_job")
def run_import_job(import_name: str = "", **context) -> dict[str, Any]:
    """Submits and monitors Google Cloud Batch import jobs using CloudBatchHook."""
    cfg = resolve_workflow_context(context, default_import_name=import_name)
    if cfg["skipImportJob"]:
        logging.info("skipImportJob is True; skipping Cloud Batch import job.")
        return {
            "status": "SKIPPED",
            "message": "Import job skipped by configuration"
        }

    hook = CloudBatchHook(gcp_conn_id="google_cloud_default")
    job_spec = _build_batch_job_spec(
        cfg["imageUri"],
        cfg["importName"],
        cfg["batchImportConfig"],
        cfg["jobId"],
        cfg["resources"],
        cfg["gcsMountBucket"],
        cfg["gcsMountPath"],
    )

    start_time = time.time()
    logging.info("Submitting Cloud Batch job '%s' (%s, %s)...", cfg["jobId"],
                 cfg["projectId"], cfg["region"])
    try:
        submitted_job = hook.submit_batch_job(
            job_name=cfg["jobId"],
            job=job_spec,
            region=cfg["region"],
            project_id=cfg["projectId"],
        )
        job_resource_name = (
            getattr(submitted_job, "name", None) or
            f"projects/{cfg['projectId']}/locations/{cfg['region']}/jobs/{cfg['jobId']}"
        )
        job = hook.wait_for_job(
            job_name=job_resource_name,
            timeout=604800,
        )
        exec_time = int(time.time() - start_time)
        logging.info("Cloud Batch job '%s' succeeded in %ss.", cfg["jobId"],
                     exec_time)
        return {
            "status": "SUCCESS",
            "jobId": cfg["jobId"],
            "name": job_resource_name,
            "executionTime": exec_time,
            "result": str(job),
        }
    except Exception as e:
        exec_time = int(time.time() - start_time)
        helper_url = cfg["helperUrlFn"](cfg["importHelperService"], "-staging")
        _report_import_failure(helper_url, cfg["jobId"], cfg["importName"],
                               cfg["gcsImportBucket"], exec_time)
        raise AirflowException(f"Cloud Batch import job failed: {e}") from e


def _run_cloud_run_job(
    project_id: str,
    region: str,
    job_name: str,
    args: list[str],
    timeout_seconds: int = 7200,
    poll_interval: int = 15,
) -> dict[str, Any]:
    """Triggers a Cloud Run v2 Job execution and polls the LRO until completion."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    session = AuthorizedSession(creds)

    run_url = f"https://run.googleapis.com/v2/projects/{project_id}/locations/{region}/jobs/{job_name}:run"
    payload = {
        "overrides": {
            "containerOverrides": [{
                "args": args,
            }]
        }
    }
    logging.info("Triggering Cloud Run job '%s' via %s with args: %s", job_name,
                 run_url, args)
    resp = session.post(run_url, json=payload, timeout=60)
    resp.raise_for_status()
    operation = resp.json()
    op_name = operation.get("name")
    if not op_name:
        raise RuntimeError(
            f"Cloud Run jobs.run did not return an operation name: {operation}")

    logging.info(
        "Waiting for Cloud Run job operation '%s' to complete (timeout: %ss)...",
        op_name, timeout_seconds)
    op_url = f"https://run.googleapis.com/v2/{op_name}"
    start_time = time.time()

    while True:
        if operation.get("done"):
            if "error" in operation:
                err = operation["error"]
                raise RuntimeError(
                    f"Cloud Run job '{job_name}' failed with error: {err}")
            response_data = operation.get("response", {})
            failed_count = response_data.get("failedCount", 0)
            cancelled_count = response_data.get("cancelledCount", 0)
            if failed_count > 0 or cancelled_count > 0:
                raise RuntimeError(
                    f"Cloud Run job '{job_name}' execution failed "
                    f"(failedCount={failed_count}, cancelledCount={cancelled_count}): {response_data}"
                )
            logging.info("Cloud Run job '%s' completed successfully.", job_name)
            return response_data or operation

        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(
                f"Cloud Run job '{job_name}' operation '{op_name}' timed out after {timeout_seconds}s."
            )

        time.sleep(poll_interval)
        poll_resp = session.get(op_url, timeout=60)
        poll_resp.raise_for_status()
        operation = poll_resp.json()


@task(task_id="run_validation_job")
def run_validation_job(import_name: str = "", **context) -> dict[str, Any]:
    """Executes the Cloud Run validation job after the Batch import job."""
    cfg = resolve_workflow_context(context, default_import_name=import_name)
    if cfg["skipImportJob"] or cfg.get("skipValidationJob"):
        logging.info(
            "Skipping Cloud Run validation job (skipImportJob=%s, skipValidationJob=%s).",
            cfg["skipImportJob"],
            cfg.get("skipValidationJob"),
        )
        return {
            "status": "SKIPPED",
            "message": "Validation job skipped by configuration"
        }

    start_time = time.time()
    try:
        res = _run_cloud_run_job(
            project_id=cfg["projectId"],
            region=cfg["region"],
            job_name=cfg["validationJobName"],
            args=[
                f"--import_name={cfg['importName']}",
                f"--import_config={cfg['importConfig']}",
            ],
            timeout_seconds=7200,
        )
        exec_time = int(time.time() - start_time)
        return {
            "status": "SUCCESS",
            "jobName": cfg["validationJobName"],
            "executionTime": exec_time,
            "result": str(res),
        }
    except Exception as e:
        exec_time = int(time.time() - start_time)
        helper_url = cfg["helperUrlFn"](cfg["importHelperService"], "-staging")
        _report_import_failure(helper_url, cfg["jobId"], cfg["importName"],
                               cfg["gcsImportBucket"], exec_time)
        raise AirflowException(f"Cloud Run validation job failed: {e}") from e


# -----------------------------------------------------------------------------
# Cloud Workflows & Ingestion Helpers
# -----------------------------------------------------------------------------


def trigger_environment_ingestion(cfg: dict[str, Any],
                                  env_suffix: str) -> dict[str, Any]:
    """Updates version via import-helper and triggers Spanner ingestion via ingestion-helper."""
    import_helper_url = cfg["helperUrlFn"](cfg["importHelperService"],
                                           env_suffix)
    ingestion_helper_url = cfg["helperUrlFn"](cfg["ingestionHelperService"],
                                              env_suffix)

    version_res = _make_http_post(
        f"{import_helper_url}/imports/version", {
            "imports": [cfg["importName"]],
            "version": "STAGING",
            "override": False,
            "comment": f"import-workflow:{cfg['runId']}",
        })

    imports_res = version_res.get("imports", [])
    if not imports_res or imports_res[0].get("status") not in ("STAGING",
                                                               "SKIP"):
        msg = version_res.get("message", "Status not STAGING or SKIP")
        logging.info(
            "Import status is not STAGING or SKIP (%s); skipping Spanner ingestion.",
            msg)
        return {"status": "SKIPPED", "message": f"Skipped: {msg}"}

    target = imports_res[0]
    import_entry = {
        "importName":
            target.get("importName", cfg["importName"]).split(":")[-1],
        "latestVersion":
            target.get("latestVersion", ""),
    }

    ingest_res = _make_http_post(
        f"{ingestion_helper_url}/imports/ingest", {
            "importList": [import_entry],
            "dryRun": cfg.get("dryRunIngestion", False),
            "forceIngestion": cfg.get("forceIngestion", False),
        })

    if ingest_res.get("status") == "SKIPPED":
        logging.info("Ingestion helper skipped ingestion: %s",
                     ingest_res.get("message"))
        return {
            "status": "SKIPPED",
            "message": ingest_res.get("message", "Skipped")
        }

    if ingest_res.get("status") != "SUBMITTED":
        raise RuntimeError(
            f"Ingestion helper returned unexpected status: {ingest_res.get('status')}"
        )

    exec_name = ingest_res.get("executionName", "")
    if not exec_name:
        raise RuntimeError(
            "Ingestion helper returned status 'SUBMITTED' but executionName was empty."
        )

    logging.info("Triggered ingestion workflow execution: %s", exec_name)

    parts = exec_name.split("/")
    # Cloud Workflows execution format: projects/{project}/locations/{location}/workflows/{workflow}/executions/{execution_id}
    project_id = parts[1] if len(parts) >= 2 else cfg["projectId"]
    location = parts[3] if len(parts) >= 4 else cfg["region"]
    workflow_id = parts[5] if len(parts) >= 6 else cfg["spannerWorkflowName"]
    execution_id = parts[7] if len(parts) >= 8 else ""

    return {
        "status": "SUBMITTED",
        "executionName": exec_name,
        "projectId": project_id,
        "location": location,
        "workflowId": workflow_id,
        "executionId": execution_id,
    }


# -----------------------------------------------------------------------------
# Workflow Context Resolver
# -----------------------------------------------------------------------------


def resolve_workflow_context(context: dict[str, Any],
                             default_import_name: str = "") -> dict[str, Any]:
    """Normalizes runtime parameters, environment variables, and fallback defaults."""
    dag_run, dag = context.get("dag_run"), context.get("dag")
    conf = dag_run.conf if dag_run and dag_run.conf else {}
    params = context.get("params") or {}
    dag_params = getattr(dag, "params", {}) if dag else {}

    def get_val(key: str, default: Any = None) -> Any:
        for src in (conf, params, dag_params):
            if hasattr(src, "get"):
                v = src.get(key)
                if v is not None and v != "":
                    return getattr(v, "default", v)
        return default

    def cfg_val(key: str, default: str, *env_keys: str) -> str:
        v = get_val(key)
        if v:
            return str(v)
        for ek in env_keys:
            ev = get_config_var(ek)
            if ev:
                return ev
        return default

    def to_bool(key: str, default: bool = False) -> bool:
        v = get_val(key, default)
        return v is True or str(v).lower() == "true"

    import_name = get_val("importName", default_import_name) or getattr(
        dag, "dag_id", "")
    if not import_name:
        raise ValueError(
            "Parameter 'importName' is required to execute the import workflow."
        )

    project_id = cfg_val("projectId", "datcom-ci", "GCP_PROJECT_ID",
                         "PROJECT_ID")
    region = cfg_val("region", "us-central1", "CLOUD_BATCH_REGION", "LOCATION")
    default_proj_num = "965988403328" if project_id == "datcom-import-automation-prod" else "879489846695"
    project_number = cfg_val("projectNumber", default_proj_num,
                             "PROJECT_NUMBER")
    gcs_mount_bucket = cfg_val("gcsMountBucket", "datcom-ci-test",
                               "GCS_MOUNT_BUCKET")
    gcs_import_bucket = cfg_val("gcsImportBucket", "datcom-ci-test",
                                "GCS_BUCKET_ID")
    import_helper = cfg_val("importHelperService", "import-helper-service",
                            "IMPORT_HELPER_SERVICE")
    ingestion_helper = cfg_val("ingestionHelperService",
                               "ingestion-helper-service",
                               "INGESTION_HELPER_SERVICE")
    spanner_workflow = cfg_val("spannerWorkflowName",
                               "spanner-ingestion-workflow",
                               "SPANNER_INGESTION_WORKFLOW_NAME")

    env_suffix = cfg_val("envSuffix", "", "ENV_SUFFIX")
    validation_job_name = cfg_val("validationJobName",
                                  f"import-validator-job{env_suffix}",
                                  "VALIDATION_JOB_NAME")

    import_config = get_val("importConfig")
    if not import_config or import_config == "{}":
        import_config_dict: dict[str, Any] = {
            "gcp_project_id": project_id,
            "gcs_project_id": project_id,
            "storage_prod_bucket_name": gcs_import_bucket,
            "gcs_bucket_volume_mount": gcs_mount_bucket,
        }
    elif isinstance(import_config, str):
        try:
            import_config_dict = json.loads(import_config)
        except Exception:
            import_config_dict = {}
    elif isinstance(import_config, dict):
        import_config_dict = dict(import_config)
    else:
        import_config_dict = {}

    batch_config_dict = dict(import_config_dict)
    batch_config_dict["invoke_import_validation"] = False
    batch_config_dict["invoke_differ_tool"] = False

    import_config_str = json.dumps(import_config_dict)
    batch_import_config_str = json.dumps(batch_config_dict)

    exec_dt = context.get("logical_date") or context.get("execution_date")
    run_ts = int(exec_dt.timestamp()) if exec_dt else int(time.time())
    run_id = dag_run.run_id if dag_run else f"manual__{datetime.now(timezone.utc).isoformat()}"

    def helper_url(service_name: str, suffix: str = "") -> str:
        svc = f"{service_name}{suffix}"
        return f"https://{svc}-{project_number}.{region}.run.app" if project_number else f"https://{svc}.{region}.run.app"

    return {
        "projectId": project_id, "region": region, "projectNumber": project_number,
        "importName": import_name, "jobId": get_val("jobId") or generate_job_id(import_name, run_ts),
        "imageUri": get_val("imageUri", DEFAULT_IMAGE_URI),
        "importConfig": import_config_str,
        "batchImportConfig": batch_import_config_str,
        "envSuffix": env_suffix,
        "validationJobName": validation_job_name,
        "skipValidationJob": to_bool("skipValidationJob", False),
        "gcsMountBucket": gcs_mount_bucket, "gcsImportBucket": gcs_import_bucket,
        "gcsMountPath": get_val("gcsMountPath", "/tmp/gcs"),
        "helperUrlFn": helper_url,
        "importHelperService": import_helper, "ingestionHelperService": ingestion_helper,
        "spannerWorkflowName": spanner_workflow,
        "skipImportJob": to_bool("skipImportJob"),
        "skipStagingIngestion": to_bool("skipStagingIngestion"),
        "skipProdIngestion": is_prod_denylisted(import_name) or to_bool("skipProdIngestion", True),
        "dryRunIngestion": to_bool("dryRunIngestion"),
        "forceIngestion": to_bool("forceIngestion"),
        "resources": {**DEFAULT_RESOURCES, **(get_val("resources") if isinstance(get_val("resources"), dict) else {})},
        "runId": run_id,
    }


# -----------------------------------------------------------------------------
# Airflow Tasks
# -----------------------------------------------------------------------------


@task(task_id="trigger_staging_ingestion")
def trigger_staging_ingestion(**context) -> dict[str, Any]:
    """Updates staging version and triggers Spanner ingestion via ingestion-helper."""
    cfg = resolve_workflow_context(context)
    if cfg["skipStagingIngestion"]:
        raise AirflowSkipException(
            "Staging ingestion skipped by configuration (skipStagingIngestion=True)."
        )

    res = trigger_environment_ingestion(cfg, env_suffix="-staging")
    if res.get("status") == "SKIPPED":
        raise AirflowSkipException(
            f"Staging ingestion skipped: {res.get('message', 'Skipped')}")

    return res


@task(task_id="ingest_prod", trigger_rule=TriggerRule.NONE_FAILED)
def ingest_prod(**context) -> dict[str, Any]:
    """Updates prod version and triggers fire-and-forget prod Spanner ingestion."""
    cfg = resolve_workflow_context(context)
    ti = context.get("ti")
    staging_res = ti.xcom_pull(
        task_ids="trigger_staging_ingestion") if ti else None

    # Check if an upstream golden test verification or pre-prod gate reported failure
    for gate_task_id in ("verify_golden_tests", "verify_schema_golden_gate",
                         "pre_prod_gate"):
        gate_res = ti.xcom_pull(task_ids=gate_task_id) if ti else None
        if isinstance(gate_res,
                      dict) and gate_res.get("status") in ("FAILURE", "FAILED"):
            logging.error(
                "Pre-prod gate '%s' failed: %s. Blocking production promotion.",
                gate_task_id, gate_res)
            return {
                "status":
                    "BLOCKED",
                "message":
                    f"Blocked by pre-prod gate {gate_task_id}: {gate_res.get('message', 'FAILURE')}"
            }

    if cfg["skipProdIngestion"]:
        logging.info(
            "skipProdIngestion is True; skipping production ingestion.")
        return {"status": "SKIPPED", "message": "Production ingestion skipped"}

    if not cfg["skipStagingIngestion"] and not staging_res:
        logging.info(
            "Staging ingestion was not triggered or was skipped; skipping production ingestion."
        )
        return {
            "status":
                "SKIPPED",
            "message":
                "Staging was not executed; skipping production ingestion."
        }

    return trigger_environment_ingestion(cfg, env_suffix="")


@task(task_id="workflow_summary", trigger_rule=TriggerRule.ALL_DONE)
def workflow_summary(**context) -> dict[str, Any]:
    """Aggregates workflow outputs and fails the DAG run if any upstream task failed."""
    cfg, ti = resolve_workflow_context(context), context.get("ti")
    default_res = {"status": "SKIPPED"}
    dag = context.get("dag")
    dag_task_ids = set(
        dag.task_ids) if dag and hasattr(dag, "task_ids") else None
    has_golden = (("verify_golden_tests" in dag_task_ids) if dag_task_ids
                  is not None else is_golden_test_import(cfg["importName"]))
    stages = [
        ("import", "run_import_job"),
        ("validation", "run_validation_job"),
        ("staging_trigger", "trigger_staging_ingestion"),
        ("staging_wait", "wait_staging_ingestion"),
        *([
            ("golden_check", "verify_golden_tests"),
            ("human_approval", "await_human_approval"),
        ] if has_golden else []),
        ("prod", "ingest_prod"),
    ]
    results = {
        name:
            default_res if val is None else (val if isinstance(val, dict) else {
                "status": "SUCCESS",
                "result": val
            }) for name, tid in stages
        for val in [(ti.xcom_pull(task_ids=tid) if ti else default_res)]
    }
    for gate_task_id in ("verify_schema_golden_gate", "pre_prod_gate"):
        gate_val = ti.xcom_pull(task_ids=gate_task_id) if ti else None
        if gate_val is not None:
            results[gate_task_id] = gate_val if isinstance(
                gate_val, dict) else {
                    "status": "SUCCESS",
                    "result": gate_val
                }

    summary = {
        "jobId": cfg["jobId"],
        "importName": cfg["importName"],
        **results
    }
    logging.info("Workflow summary: %s", json.dumps(summary, indent=2))

    dag_run = context.get("dag_run")
    failed = [
        t.task_id
        for t in (dag_run.get_task_instances() if dag_run else [])
        if t.task_id != "workflow_summary" and t.state in ("failed",
                                                           "upstream_failed")
    ]
    failed += [
        f"{k} ({v.get('status')})" for k, v in results.items()
        if isinstance(v, dict) and v.get("status") in ("FAILURE", "FAILED")
    ]
    if failed:
        error_msg = f"Workflow failed in upstream stage(s): {', '.join(dict.fromkeys(failed))}"
        logging.error(error_msg)
        raise AirflowFailException(error_msg)

    return summary


# -----------------------------------------------------------------------------
# DAG Factory
# -----------------------------------------------------------------------------

default_args = {
    "owner": "data-commons",
    "depends_on_past": False,
    "retries": 0,
    "email_on_failure": False,
    "email_on_retry": False,
}

base_dag_params = {
    "importName":
        Param(default="", type="string", description="Full import name"),
    "imageUri":
        Param(default=DEFAULT_IMAGE_URI,
              type="string",
              description="Executor container image"),
    "importConfig":
        Param(default="{}",
              type=["string", "object"],
              description="Import configuration JSON"),
    "skipImportJob":
        Param(default=False,
              type="boolean",
              description="Skip Batch import job"),
    "skipValidationJob":
        Param(default=False,
              type="boolean",
              description="Skip Cloud Run validation job"),
    "validationJobName":
        Param(default="",
              type="string",
              description="Cloud Run validation job name override"),
    "skipStagingIngestion":
        Param(default=False,
              type="boolean",
              description="Skip staging ingestion"),
    "skipProdIngestion":
        Param(default=True, type="boolean", description="Skip prod ingestion"),
    "dryRunIngestion":
        Param(default=False, type="boolean", description="Dry run ingestion"),
    "forceIngestion":
        Param(default=False,
              type="boolean",
              description="Force ingestion even if already SUCCESS"),
    "resources":
        Param(default=DEFAULT_RESOURCES,
              type="object",
              description="Batch job resources"),
}

golden_dag_params = {
    "runGoldenTests":
        Param(default=False,
              type="boolean",
              description="Force staging golden verification gate"),
    "skipGoldenTests":
        Param(default=False,
              type="boolean",
              description="Skip staging golden verification gate"),
    "goldenTestTriggerId":
        Param(default="",
              type="string",
              description="Cloud Build trigger ID override"),
    "goldenTestBranch":
        Param(default="master",
              type="string",
              description="Cloud Build branch override"),
    "goldenTestProjectId":
        Param(default="datcom-ci",
              type="string",
              description="Cloud Build project ID override"),
    "goldenDiffBucket":
        Param(default="datcom-ci-test",
              type="string",
              description="GCS bucket containing golden diff summaries"),
    "autoApproveGoldenDiff":
        Param(
            default=False,
            type="boolean",
            description=
            "Auto-approve staging golden diffs without waiting for human input"
        ),
}

dag_params = {
    **base_dag_params,
    **golden_dag_params,
}


def build_dag(
    dag_id: str = DAG_ID,
    schedule: str | None = None,
    import_name: str = "",
    curator_emails: list[str] | None = None,
    config_override: dict[str, Any] | None = None,
    resource_limits: dict[str, Any] | None = None,
    extra_tags: list[str] | None = None,
    is_paused_upon_creation: bool = True,
    pre_prod_gate_factory: Callable[[], Any] | None = None,
    golden_test_allowlist: set[str] | None = None,
) -> DAG:
    """Builds and returns an Airflow DAG instance for import automation."""
    allowlist = golden_test_allowlist if golden_test_allowlist is not None else get_golden_test_imports(
    )
    has_golden_check = (is_golden_test_import(import_name, allowlist=allowlist)
                        or is_golden_test_import(dag_id, allowlist=allowlist))

    params = {
        **base_dag_params,
        **(golden_dag_params if has_golden_check else {}),
        **({
            "importName":
                Param(import_name,
                      type="string",
                      description="Full import name")
        } if import_name else {}),
        **({
            "importConfig":
                Param(config_override,
                      type=["string", "object"],
                      description="Import configuration JSON")
        } if config_override else {}),
        **({
            "resources":
                Param({
                    **DEFAULT_RESOURCES,
                    **resource_limits
                },
                      type="object",
                      description="Batch job resources")
        } if resource_limits else {}),
    }

    dag_instance = DAG(
        dag_id=dag_id,
        default_args={
            **default_args,
            **({
                "email": curator_emails
            } if curator_emails else {})
        },
        description=
        f"Orchestrates import automation for {import_name or dag_id}",
        schedule=schedule,
        start_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        catchup=False,
        max_active_runs=10,
        params=params,
        tags=["data-commons", "import-automation"] + (extra_tags or []),
        is_paused_upon_creation=is_paused_upon_creation,
    )

    with dag_instance:
        staging_wait = WorkflowExecutionSensor(
            task_id="wait_staging_ingestion",
            project_id=
            "{{ (ti.xcom_pull(task_ids='trigger_staging_ingestion') or {}).get('projectId', '') }}",
            location=
            "{{ (ti.xcom_pull(task_ids='trigger_staging_ingestion') or {}).get('location', '') }}",
            workflow_id=
            "{{ (ti.xcom_pull(task_ids='trigger_staging_ingestion') or {}).get('workflowId', '') }}",
            execution_id=
            "{{ (ti.xcom_pull(task_ids='trigger_staging_ingestion') or {}).get('executionId', '') }}",
            mode="reschedule",
            poke_interval=60,
            timeout=21600,
        )
        batch_task = run_import_job(import_name=import_name)
        validation_task = run_validation_job(import_name=import_name)
        staging_task = trigger_staging_ingestion()
        prod_task = ingest_prod()
        summary_task = workflow_summary()

        pipeline: list[Any] = [
            batch_task, validation_task, staging_task, staging_wait
        ]
        if has_golden_check:
            golden_task = verify_golden_tests()
            approval_task = HumanApprovalSensor(
                task_id="await_human_approval",
                import_name=import_name,
            )
            pipeline.extend([golden_task, approval_task])

        if pre_prod_gate_factory:
            custom_gate = pre_prod_gate_factory()
            pipeline.append(custom_gate)

        pipeline.extend([prod_task, summary_task])

        for upstream, downstream in zip(pipeline, pipeline[1:]):
            upstream >> downstream

    return dag_instance
