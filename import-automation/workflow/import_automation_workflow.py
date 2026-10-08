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

from airflow.sdk import BaseSensorOperator, DAG, Param, Variable, task
from airflow.exceptions import AirflowException, AirflowFailException, AirflowSkipException
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

DAG_ID = os.environ.get("IMPORT_AUTOMATION_DAG_ID", "ManualRefresh")
DEFAULT_IMAGE_URI = "us-docker.pkg.dev/datcom-ci/gcr.io/dc-import-executor:stable"
DEFAULT_SKIP_PROD_INGESTION = False
DEFAULT_RESOURCES = {
    "machine": "n2-standard-8",
    "cpu": 8000,
    "memory": 32768,
    "disk": 100
}

_GCE_MACHINE_TYPES = [
    {
        "name": "n2-standard-2",
        "cpus": 2,
        "memory_gib": 8
    },
    {
        "name": "n2-standard-4",
        "cpus": 4,
        "memory_gib": 16
    },
    {
        "name": "n2-standard-8",
        "cpus": 8,
        "memory_gib": 32
    },
    {
        "name": "n2-standard-16",
        "cpus": 16,
        "memory_gib": 64
    },
    {
        "name": "n2-standard-32",
        "cpus": 32,
        "memory_gib": 128
    },
    {
        "name": "n2-standard-48",
        "cpus": 48,
        "memory_gib": 192
    },
    {
        "name": "n2-standard-64",
        "cpus": 64,
        "memory_gib": 256
    },
    {
        "name": "n2-highmem-2",
        "cpus": 2,
        "memory_gib": 16
    },
    {
        "name": "n2-highmem-4",
        "cpus": 4,
        "memory_gib": 32
    },
    {
        "name": "n2-highmem-8",
        "cpus": 8,
        "memory_gib": 64
    },
    {
        "name": "n2-highmem-16",
        "cpus": 16,
        "memory_gib": 128
    },
    {
        "name": "n2-highmem-32",
        "cpus": 32,
        "memory_gib": 256
    },
    {
        "name": "n2-highmem-48",
        "cpus": 48,
        "memory_gib": 384
    },
    {
        "name": "n2-highmem-64",
        "cpus": 64,
        "memory_gib": 512
    },
    {
        "name": "n2-highcpu-2",
        "cpus": 2,
        "memory_gib": 2
    },
    {
        "name": "n2-highcpu-4",
        "cpus": 4,
        "memory_gib": 4
    },
    {
        "name": "n2-highcpu-8",
        "cpus": 8,
        "memory_gib": 8
    },
    {
        "name": "n2-highcpu-16",
        "cpus": 16,
        "memory_gib": 16
    },
    {
        "name": "n2-highcpu-32",
        "cpus": 32,
        "memory_gib": 32
    },
]


def get_gce_instance(required_cpu: float,
                     required_memory_gib: float) -> str | None:
    """Finds the smallest GCE machine type meeting the CPU and memory (GiB) requirements."""
    suitable = [
        m for m in _GCE_MACHINE_TYPES
        if m["cpus"] >= required_cpu and m["memory_gib"] >= required_memory_gib
    ]
    if not suitable:
        return None
    suitable.sort(key=lambda x: (x["cpus"], x["memory_gib"]))
    return suitable[0]["name"]


def normalize_batch_resources(
        resource_limits: dict[str, Any] | None) -> dict[str, Any]:
    """Converts manifest resource_limits (cpu in vCPUs, memory in GiB, disk in GB) into Cloud Batch resources."""
    if not isinstance(resource_limits, dict) or not resource_limits:
        return dict(DEFAULT_RESOURCES)

    cpu_vcpu = (float(resource_limits["cpu"]) if "cpu" in resource_limits else
                DEFAULT_RESOURCES["cpu"] / 1000.0)
    mem_gib = (float(resource_limits["memory"]) if "memory" in resource_limits
               else DEFAULT_RESOURCES["memory"] / 1024.0)
    disk = int(resource_limits.get("disk", DEFAULT_RESOURCES["disk"]))

    explicit_machine = resource_limits.get("machine")
    machine = str(explicit_machine) if explicit_machine else (
        get_gce_instance(cpu_vcpu, mem_gib) or DEFAULT_RESOURCES["machine"])

    return {
        "machine": machine,
        "cpu": int(cpu_vcpu * 1000),
        "memory": int(mem_gib * 1024),
        "disk": disk,
    }


PROD_DENYLIST = frozenset({
    "Brazil_RuralDevelopmentProgram",
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
    "FireWFIGS",
    "INPE_Fire_Event_Count",
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
    """Reads configuration from OS environment or Airflow Variable."""
    env_val = os.environ.get(key)
    if env_val:
        return env_val
    try:
        return Variable.get(key, default=default)
    except Exception:
        return default


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


_BATCH_STATE_BY_INT = {
    0: "STATE_UNSPECIFIED",
    1: "QUEUED",
    2: "SCHEDULED",
    3: "RUNNING",
    4: "SUCCEEDED",
    5: "FAILED",
    6: "DELETION_IN_PROGRESS",
    7: "CANCELLATION_IN_PROGRESS",
    8: "CANCELLED",
}
_BATCH_TERMINAL_FAILURE_STATES = frozenset({
    "FAILED",
    "DELETION_IN_PROGRESS",
    "CANCELLATION_IN_PROGRESS",
    "CANCELLED",
})


def _get_batch_job_state(job: Any) -> str:
    """Extracts normalized uppercase state name from a Cloud Batch Job object."""
    status = getattr(job, "status", None)
    state = getattr(status, "state", None) if status is not None else None
    if state is None and isinstance(job, dict):
        state = (job.get("status") or {}).get("state")
    if state is None:
        return "STATE_UNSPECIFIED"
    name = getattr(state, "name", None)
    if isinstance(name, str) and name:
        return name.upper()
    if isinstance(state, int) and state in _BATCH_STATE_BY_INT:
        return _BATCH_STATE_BY_INT[state]
    if isinstance(state, str) and state:
        s = state.strip().upper()
        if s.startswith("STATE."):
            s = s.split(".", 1)[1]
        return s
    return str(state).upper()


def _is_not_found_error(exc: Exception) -> bool:
    """Returns True if exc represents a 404 NotFound error from Cloud Batch."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 404:
        return True
    cls_name = type(exc).__name__
    msg = str(exc)
    return "NotFound" in cls_name or "404" in msg or "not found" in msg.lower()


def _is_already_exists_error(exc: Exception) -> bool:
    """Returns True if exc represents a 409 AlreadyExists error from Cloud Batch."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 409:
        return True
    cls_name = type(exc).__name__
    msg = str(exc)
    return ("AlreadyExists" in cls_name or "409" in msg or
            "already exists" in msg.lower())


def _compute_batch_exec_time(
    job: Any,
    context: dict[str, Any],
    fallback_start_time: float,
) -> int:
    """Computes total elapsed seconds for a Cloud Batch job across reschedule pokes."""
    if job is not None:
        for attr in ("create_time", "createTime"):
            ct = getattr(job, attr, None)
            if ct is not None and hasattr(ct, "timestamp"):
                try:
                    ts = ct.timestamp()
                    if isinstance(ts, (int, float)):
                        return max(0, int(time.time() - ts))
                except Exception:
                    pass
    dag_run = context.get("dag_run")
    start_dt = getattr(dag_run, "start_date", None) if dag_run else None
    if start_dt is not None and hasattr(start_dt, "timestamp"):
        try:
            ts = start_dt.timestamp()
            if isinstance(ts, (int, float)):
                return max(0, int(time.time() - ts))
        except Exception:
            pass
    return max(0, int(time.time() - fallback_start_time))


class CloudBatchImportSensor(BaseSensorOperator):
    """Submits and polls a Google Cloud Batch import job in reschedule mode.

    Running in ``mode="reschedule"`` ensures each poke executes quickly and releases
    the Celery worker slot between checks. This prevents long-running imports (>6h)
    from exceeding the Redis Celery ``visibility_timeout`` (21,600s) and failing
    with ``ServerResponseError: Invalid auth token`` on redelivery.
    """

    template_fields = ("import_name",)

    def __init__(
        self,
        import_name: str = "",
        gcp_conn_id: str = "google_cloud_default",
        mode: str = "reschedule",
        poke_interval: int = 60,
        timeout: int = 604800,
        **kwargs: Any,
    ):
        super().__init__(
            mode=mode,
            poke_interval=poke_interval,
            timeout=timeout,
            **kwargs,
        )
        self.import_name = import_name
        self.gcp_conn_id = gcp_conn_id
        self._job_result: dict[str, Any] = {}

    def poke(self, context: dict[str, Any]) -> bool:
        cfg = resolve_workflow_context(context,
                                       default_import_name=self.import_name)
        if cfg["skipImportJob"]:
            logging.info(
                "skipImportJob is True; skipping Cloud Batch import job.")
            raise AirflowSkipException(
                "Import job skipped by configuration (skipImportJob=True).")

        hook = CloudBatchHook(gcp_conn_id=self.gcp_conn_id)
        job_resource_name = (
            f"projects/{cfg['projectId']}/locations/{cfg['region']}/jobs/{cfg['jobId']}"
        )
        poke_start_time = time.time()
        job = None

        try:
            try:
                job = hook.get_conn().get_job(name=job_resource_name)
            except Exception as get_err:
                if not _is_not_found_error(get_err):
                    raise
                job_spec = _build_batch_job_spec(
                    cfg["imageUri"],
                    cfg["importName"],
                    cfg["batchImportConfig"],
                    cfg["jobId"],
                    cfg["resources"],
                    cfg["gcsMountBucket"],
                    cfg["gcsMountPath"],
                )
                logging.info(
                    "Submitting Cloud Batch job '%s' (%s, %s)...",
                    cfg["jobId"],
                    cfg["projectId"],
                    cfg["region"],
                )
                try:
                    job = hook.submit_batch_job(
                        job_name=cfg["jobId"],
                        job=job_spec,
                        region=cfg["region"],
                        project_id=cfg["projectId"],
                    )
                except Exception as submit_err:
                    if _is_already_exists_error(submit_err):
                        logging.info(
                            "Cloud Batch job '%s' already exists; fetching status.",
                            cfg["jobId"],
                        )
                        job = hook.get_conn().get_job(name=job_resource_name)
                    else:
                        raise

            job_name_attr = getattr(job, "name", None)
            if isinstance(job_name_attr, str) and job_name_attr:
                job_resource_name = job_name_attr

            state = _get_batch_job_state(job)
            if state == "SUCCEEDED":
                exec_time = _compute_batch_exec_time(job, context,
                                                     poke_start_time)
                logging.info("Cloud Batch job '%s' succeeded in %ss.",
                             cfg["jobId"], exec_time)
                self._job_result = {
                    "status": "SUCCESS",
                    "jobId": cfg["jobId"],
                    "name": job_resource_name,
                    "executionTime": exec_time,
                    "result": str(job),
                }
                return True

            if state in _BATCH_TERMINAL_FAILURE_STATES:
                status_events = getattr(getattr(job, "status", None),
                                        "status_events", None) or []
                event_desc = "; ".join(
                    getattr(ev, "description", str(ev))
                    for ev in status_events[-3:])
                detail = f" (events: {event_desc})" if event_desc else ""
                raise RuntimeError(
                    f"Cloud Batch job '{cfg['jobId']}' entered terminal state {state}{detail}"
                )

            logging.info(
                "Cloud Batch job '%s' is in state %s; rescheduling next check in %ss.",
                cfg["jobId"],
                state,
                self.poke_interval,
            )
            return False
        except Exception as e:
            exec_time = _compute_batch_exec_time(job, context, poke_start_time)
            helper_url = cfg["helperUrlFn"](cfg["importHelperService"], "")
            _report_import_failure(helper_url, cfg["jobId"], cfg["importName"],
                                   cfg["gcsImportBucket"], exec_time)
            raise AirflowException(f"Cloud Batch import job failed: {e}") from e

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        super().execute(context)
        if self._job_result:
            return self._job_result
        cfg = resolve_workflow_context(context,
                                       default_import_name=self.import_name)
        return {
            "status":
                "SUCCESS",
            "jobId":
                cfg["jobId"],
            "name":
                f"projects/{cfg['projectId']}/locations/{cfg['region']}/jobs/{cfg['jobId']}",
            "executionTime":
                0,
            "result":
                "",
        }


def run_import_job(
    import_name: str = "",
    task_id: str = "run_import_job",
    **kwargs: Any,
) -> CloudBatchImportSensor:
    """Creates a reschedule-mode sensor that submits and monitors a Cloud Batch import job."""
    return CloudBatchImportSensor(
        task_id=task_id,
        import_name=import_name,
        **kwargs,
    )


def _run_import_job_fn(import_name: str = "", **context: Any) -> dict[str, Any]:
    sensor = CloudBatchImportSensor(
        task_id="run_import_job",
        import_name=import_name,
    )
    if not sensor.poke(context):
        cfg = resolve_workflow_context(context, default_import_name=import_name)
        return {
            "status": "RUNNING",
            "jobId": cfg["jobId"],
        }
    return sensor._job_result


run_import_job.function = _run_import_job_fn  # type: ignore[attr-defined]


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
    if cfg["skipImportJob"]:
        logging.info(
            "skipImportJob is True; skipping Cloud Run validation job.")
        raise AirflowSkipException(
            "Validation job skipped by configuration (skipImportJob=True).")

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
        helper_url = cfg["helperUrlFn"](cfg["importHelperService"], "")
        _report_import_failure(helper_url, cfg["jobId"], cfg["importName"],
                               cfg["gcsImportBucket"], exec_time)
        raise AirflowException(f"Cloud Run validation job failed: {e}") from e


# -----------------------------------------------------------------------------
# Cloud Workflows & Ingestion Helpers
# -----------------------------------------------------------------------------


def update_import_version_helper(cfg: dict[str, Any]) -> dict[str, Any]:
    """Updates import version once in prod import-helper-service and returns importEntry."""
    import_helper_url = cfg["helperUrlFn"](cfg["importHelperService"], "")
    comment = f"import-workflow:{cfg['runId']}"
    if cfg.get("comment"):
        comment = f"{comment} {cfg['comment']}"
    version_res = _make_http_post(
        f"{import_helper_url}/imports/version", {
            "imports": [cfg["importName"]],
            "version": cfg.get("version") or "STAGING",
            "override": bool(cfg.get("overrideVersion", False)),
            "comment": comment,
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
    return {
        "status": target.get("status", "STAGING"),
        "importEntry": import_entry,
        "message": version_res.get("message", ""),
    }


def trigger_environment_ingestion(
    cfg: dict[str, Any],
    env_suffix: str,
    import_entry: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Triggers Spanner ingestion via ingestion-helper for the target environment."""
    if not import_entry:
        version_res = update_import_version_helper(cfg)
        if version_res.get("status") == "SKIPPED":
            return version_res
        import_entry = version_res["importEntry"]

    ingestion_helper_url = cfg["helperUrlFn"](cfg["ingestionHelperService"],
                                              env_suffix)

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
                    if hasattr(v, "value"):
                        return v.value
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

    validation_job_name = cfg_val("validationJobName", "import-validator-job",
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

    import_config_str = json.dumps(import_config_dict)
    batch_import_config_str = import_config_str

    exec_dt = (context.get("logical_date") or
               getattr(dag_run, "logical_date", None) or
               getattr(dag_run, "run_after", None) or
               getattr(dag_run, "start_date", None))
    run_ts = int(exec_dt.timestamp()) if exec_dt else int(time.time())
    run_id = dag_run.run_id if dag_run else f"manual__{datetime.now(timezone.utc).isoformat()}"

    def helper_url(service_name: str, suffix: str = "") -> str:
        svc = f"{service_name}{suffix}"
        return f"https://{svc}-{project_number}.{region}.run.app" if project_number else f"https://{svc}.{region}.run.app"

    return {
        "projectId":
            project_id,
        "region":
            region,
        "projectNumber":
            project_number,
        "importName":
            import_name,
        "jobId":
            get_val("jobId") or generate_job_id(import_name, run_ts),
        "imageUri":
            get_val("imageUri", DEFAULT_IMAGE_URI),
        "importConfig":
            import_config_str,
        "batchImportConfig":
            batch_import_config_str,
        "validationJobName":
            validation_job_name,
        "gcsMountBucket":
            gcs_mount_bucket,
        "gcsImportBucket":
            gcs_import_bucket,
        "gcsMountPath":
            get_val("gcsMountPath", "/tmp/gcs"),
        "helperUrlFn":
            helper_url,
        "importHelperService":
            import_helper,
        "ingestionHelperService":
            ingestion_helper,
        "spannerWorkflowName":
            spanner_workflow,
        "skipImportJob":
            to_bool("skipImportJob"),
        "skipStagingIngestion":
            to_bool("skipStagingIngestion"),
        "skipProdIngestion":
            is_prod_denylisted(import_name)
            or to_bool("skipProdIngestion", DEFAULT_SKIP_PROD_INGESTION),
        "dryRunIngestion":
            to_bool("dryRunIngestion"),
        "forceIngestion":
            to_bool("forceIngestion"),
        "version":
            get_val("version", "STAGING"),
        "overrideVersion":
            to_bool("overrideVersion") or to_bool("override"),
        "comment":
            get_val("comment", ""),
        "resources": {
            **DEFAULT_RESOURCES,
            **(get_val("resources")
               if isinstance(get_val("resources"), dict) else {}),
        },
        "runId":
            run_id,
    }


# -----------------------------------------------------------------------------
# Airflow Tasks
# -----------------------------------------------------------------------------


@task(task_id="update_import_version", trigger_rule=TriggerRule.NONE_FAILED)
def update_import_version(**context) -> dict[str, Any]:
    """Updates import version once in prod import-helper-service."""
    cfg = resolve_workflow_context(context)
    return update_import_version_helper(cfg)


@task(task_id="trigger_staging_ingestion")
def trigger_staging_ingestion(**context) -> dict[str, Any]:
    """Triggers staging Spanner ingestion via ingestion-helper."""
    cfg = resolve_workflow_context(context)
    if cfg["skipStagingIngestion"]:
        raise AirflowSkipException(
            "Staging ingestion skipped by configuration (skipStagingIngestion=True)."
        )

    ti = context.get("ti")
    version_res = ti.xcom_pull(task_ids="update_import_version") if ti else None
    if isinstance(version_res, dict) and version_res.get("status") == "SKIPPED":
        raise AirflowSkipException(
            f"Staging ingestion skipped: {version_res.get('message', 'Skipped')}"
        )

    import_entry = version_res.get("importEntry") if isinstance(
        version_res, dict) else None
    res = trigger_environment_ingestion(cfg,
                                        env_suffix="-staging",
                                        import_entry=import_entry)
    if res.get("status") == "SKIPPED":
        if ti:
            ti.xcom_push(key="return_value", value=res)
        raise AirflowSkipException(
            f"Staging ingestion skipped: {res.get('message', 'Skipped')}")

    return res


@task(task_id="trigger_prod_ingestion", trigger_rule=TriggerRule.NONE_FAILED)
def trigger_prod_ingestion(**context) -> dict[str, Any]:
    """Triggers prod Spanner ingestion via ingestion-helper."""
    cfg = resolve_workflow_context(context)
    ti = context.get("ti")
    version_res = ti.xcom_pull(task_ids="update_import_version") if ti else None
    staging_res = ti.xcom_pull(
        task_ids="trigger_staging_ingestion") if ti else None

    def _skip_prod(message: str) -> None:
        res = {"status": "SKIPPED", "message": message}
        if ti:
            ti.xcom_push(key="return_value", value=res)
        raise AirflowSkipException(f"Production ingestion skipped: {message}")

    if isinstance(version_res, dict) and version_res.get("status") == "SKIPPED":
        _skip_prod(version_res.get("message", "Import version skipped"))

    # Check if an upstream golden test verification or pre-prod gate reported failure
    for gate_task_id in ("verify_golden_tests", "verify_schema_golden_gate",
                         "pre_prod_gate"):
        gate_res = ti.xcom_pull(task_ids=gate_task_id) if ti else None
        if isinstance(gate_res,
                      dict) and gate_res.get("status") in ("FAILURE", "FAILED"):
            logging.error(
                "Pre-prod gate '%s' failed: %s. Blocking production promotion.",
                gate_task_id, gate_res)
            res = {
                "status":
                    "BLOCKED",
                "message":
                    f"Blocked by pre-prod gate {gate_task_id}: {gate_res.get('message', 'FAILURE')}"
            }
            if ti:
                ti.xcom_push(key="return_value", value=res)
                raise AirflowSkipException(res["message"])
            return res

    if cfg["skipProdIngestion"]:
        logging.info(
            "skipProdIngestion is True; skipping production ingestion.")
        _skip_prod("Production ingestion skipped")

    if not cfg["skipStagingIngestion"] and (
            not isinstance(staging_res, dict) or staging_res.get("status")
            not in ("SUBMITTED", "SUCCESS", "SKIPPED")):
        logging.info(
            "Staging ingestion was not triggered or was skipped; skipping production ingestion."
        )
        _skip_prod("Staging was not executed; skipping production ingestion.")

    import_entry = version_res.get("importEntry") if isinstance(
        version_res, dict) else None
    res = trigger_environment_ingestion(cfg,
                                        env_suffix="",
                                        import_entry=import_entry)
    if res.get("status") == "SKIPPED":
        _skip_prod(res.get("message", "Skipped"))

    return res


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
    has_validation = bool(dag_task_ids and "run_validation_job" in dag_task_ids)
    stages = [
        ("import", "run_import_job"),
        *([("validation", "run_validation_job")] if has_validation else []),
        ("version", "update_import_version"),
        ("staging_trigger", "trigger_staging_ingestion"),
        ("staging_wait", "wait_staging_ingestion"),
        *([
            ("golden_check", "verify_golden_tests"),
            ("human_approval", "await_human_approval"),
        ] if has_golden else []),
        ("prod", "trigger_prod_ingestion"),
        ("prod_wait", "wait_prod_ingestion"),
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

    failed = [
        f"{k} ({v.get('status')})" for k, v in results.items()
        if isinstance(v, dict) and v.get("status") in ("FAILURE", "FAILED")
    ]
    if not failed and ti is not None and (
            dag_task_ids is None or "trigger_prod_ingestion" in dag_task_ids):
        prod_trigger_val = ti.xcom_pull(task_ids="trigger_prod_ingestion")
        if prod_trigger_val is None:
            failed.append("prod (upstream_failed or failed)")
        elif (
                isinstance(prod_trigger_val, dict) and
                prod_trigger_val.get("status") == "SUBMITTED" and
            (dag_task_ids is None or "wait_prod_ingestion" in dag_task_ids) and
                ti.xcom_pull(task_ids="wait_prod_ingestion") is None):
            failed.append("prod_wait (upstream_failed or failed)")
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
        Param(default={},
              type=["null", "string", "object"],
              description="Import configuration JSON"),
    "skipImportJob":
        Param(default=False,
              type="boolean",
              description="Skip Batch import job"),
    "skipStagingIngestion":
        Param(default=False,
              type="boolean",
              description="Skip staging ingestion"),
    "skipProdIngestion":
        Param(default=DEFAULT_SKIP_PROD_INGESTION,
              type="boolean",
              description="Skip prod ingestion"),
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
              type=["null", "string"],
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
                      type=["null", "string", "object"],
                      description="Import configuration JSON")
        } if config_override else {}),
        **({
            "resources":
                Param(normalize_batch_resources(resource_limits),
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
        prod_wait = WorkflowExecutionSensor(
            task_id="wait_prod_ingestion",
            project_id=
            "{{ (ti.xcom_pull(task_ids='trigger_prod_ingestion') or {}).get('projectId', '') }}",
            location=
            "{{ (ti.xcom_pull(task_ids='trigger_prod_ingestion') or {}).get('location', '') }}",
            workflow_id=
            "{{ (ti.xcom_pull(task_ids='trigger_prod_ingestion') or {}).get('workflowId', '') }}",
            execution_id=
            "{{ (ti.xcom_pull(task_ids='trigger_prod_ingestion') or {}).get('executionId', '') }}",
            mode="reschedule",
            poke_interval=60,
            timeout=21600,
        )
        batch_task = run_import_job(import_name=import_name)
        version_task = update_import_version()
        staging_task = trigger_staging_ingestion()
        prod_task = trigger_prod_ingestion()
        summary_task = workflow_summary()

        pipeline: list[Any] = [
            batch_task, version_task, staging_task, staging_wait
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

        pipeline.extend([prod_task, prod_wait, summary_task])

        for upstream, downstream in zip(pipeline, pipeline[1:]):
            upstream >> downstream

    return dag_instance
