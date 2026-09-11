#!/usr/bin/env python3
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
"""End-to-End (E2E) Cloud Composer DAG Test Runner.

Triggers an Airflow DAG run in Google Cloud Composer via the Airflow Stable REST API,
monitors task execution states, simulates human-in-the-loop approval if applicable,
verifies the final workflow_summary XCom output, and dumps task logs upon failure.

Usage:
  python3 e2e_dag_test.py \
    --project-id=datcom-import-automation-prod \
    --location=us-central1 \
    --composer-env=import-automation-airflow \
    --dag-id=USFed_ConstantMaturityRates_Test
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import google.auth
from google.auth.transport.requests import AuthorizedSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DEFAULT_PROJECT_ID = "datcom-import-automation-prod"
DEFAULT_LOCATION = "us-central1"
DEFAULT_COMPOSER_ENV = "import-automation-airflow"
DEFAULT_DAG_ID = "USFed_ConstantMaturityRates_Test"


class GcloudCliCredentials(google.auth.credentials.Credentials):
    """Credentials backed by `gcloud auth print-access-token`."""

    def __init__(self) -> None:
        super().__init__()
        self.refresh(None)

    def refresh(self, request: Any) -> None:
        import subprocess

        self.token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            timeout=30,
        ).strip()


def get_authorized_session(project_id: str = DEFAULT_PROJECT_ID) -> AuthorizedSession:
    """Creates an AuthorizedSession with Google Cloud Platform scopes."""
    session: AuthorizedSession | None = None
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        session = AuthorizedSession(credentials)
    except Exception as adc_err:
        logging.info("ADC refresh failed (%s); using gcloud auth print-access-token...", adc_err)
        session = AuthorizedSession(GcloudCliCredentials())

    if project_id:
        session.headers.update({"x-goog-user-project": project_id})
    return session


def resolve_composer_webserver_url(
    session: AuthorizedSession,
    project_id: str,
    location: str,
    composer_env: str,
) -> str:
    """Queries the Cloud Composer API to discover the Airflow Webserver URI."""
    env_url = (
        f"https://composer.googleapis.com/v1/projects/{project_id}"
        f"/locations/{location}/environments/{composer_env}"
    )
    logging.info("Resolving Composer webserver URI from %s...", env_url)
    try:
        resp = session.get(env_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        airflow_uri = data.get("config", {}).get("airflowUri", "")
        if airflow_uri:
            return airflow_uri.rstrip("/")
    except Exception as rest_err:
        logging.warning("Composer REST API lookup failed (%s); falling back to gcloud CLI...", rest_err)
        import subprocess
        cmd = [
            "gcloud", "composer", "environments", "describe", composer_env,
            f"--location={location}",
            f"--project={project_id}",
            "--format=value(config.airflowUri)",
        ]
        airflow_uri = subprocess.check_output(cmd, text=True, timeout=30).strip()
        if airflow_uri:
            return airflow_uri.rstrip("/")
        raise RuntimeError(f"Could not resolve Composer webserver URI via REST or CLI: {rest_err}") from rest_err

    raise RuntimeError(f"Could not find config.airflowUri in Composer environment response: {data}")


def check_dag_import_errors(session: AuthorizedSession, webserver_url: str) -> None:
    """Verifies that there are no DAG import/syntax errors in Airflow."""
    err_url = f"{webserver_url}/api/v1/importErrors"
    resp = session.get(err_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    import_errors = data.get("import_errors", [])
    if import_errors:
        logging.error("Airflow reported %d DAG import error(s):", len(import_errors))
        for err in import_errors:
            logging.error(
                "File: %s\nTimestamp: %s\nStack Trace:\n%s\n%s",
                err.get("filename"),
                err.get("timestamp"),
                err.get("stack_trace"),
                "-" * 60,
            )
        raise RuntimeError(f"Aborting E2E test due to {len(import_errors)} DAG import error(s) in Airflow.")
    logging.info("Pre-flight check passed: 0 DAG import errors in Airflow.")


def ensure_dag_available_and_unpaused(
    session: AuthorizedSession,
    webserver_url: str,
    dag_id: str,
    max_wait_sec: int = 120,
) -> dict[str, Any]:
    """Waits for DAG to appear in Airflow and ensures it is unpaused."""
    dag_url = f"{webserver_url}/api/v1/dags/{dag_id}"
    start_time = time.time()

    while time.time() - start_time < max_wait_sec:
        resp = session.get(dag_url, timeout=30)
        if resp.status_code == 200:
            dag_info = resp.json()
            if dag_info.get("is_paused"):
                logging.info("DAG '%s' is currently paused. Unpausing for E2E test...", dag_id)
                patch_resp = session.patch(dag_url, json={"is_paused": False}, timeout=30)
                patch_resp.raise_for_status()
                dag_info = patch_resp.json()
            logging.info("DAG '%s' is active and ready (is_paused=%s).", dag_id, dag_info.get("is_paused"))
            return dag_info
        logging.info("Waiting for DAG '%s' to be registered in Airflow (status %d)...", dag_id, resp.status_code)
        time.sleep(10)

    raise TimeoutError(f"DAG '{dag_id}' was not found in Airflow after {max_wait_sec}s.")


def trigger_dag_run(
    session: AuthorizedSession,
    webserver_url: str,
    dag_id: str,
    run_id: str,
    conf: dict[str, Any],
) -> dict[str, Any]:
    """Triggers a new DAG run via the Airflow REST API."""
    runs_url = f"{webserver_url}/api/v1/dags/{dag_id}/dagRuns"
    payload = {
        "dag_run_id": run_id,
        "conf": conf,
    }
    logging.info("Triggering DAG '%s' with run_id='%s' and conf=%s", dag_id, run_id, json.dumps(conf))
    resp = session.post(runs_url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def dump_failed_task_logs(
    session: AuthorizedSession,
    webserver_url: str,
    dag_id: str,
    run_id: str,
    task_instances: list[dict[str, Any]],
) -> None:
    """Fetches and prints Airflow logs for any failed tasks."""
    for ti in task_instances:
        t_id = ti.get("task_id")
        state = ti.get("state")
        try_num = ti.get("try_number", 1)
        if state in ("failed", "upstream_failed") and t_id:
            log_url = f"{webserver_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{t_id}/logs/{max(1, try_num)}"
            try:
                resp = session.get(log_url, headers={"Accept": "text/plain"}, timeout=30)
                logging.error(
                    "\n%s\nTask Failure Log: %s (state=%s, try=%s)\n%s\n%s\n%s",
                    "=" * 80,
                    t_id,
                    state,
                    try_num,
                    "-" * 80,
                    resp.text[-4000:] if resp.text else "<empty log>",
                    "=" * 80,
                )
            except Exception as ex:
                logging.warning("Could not retrieve log for failed task '%s': %s", t_id, ex)


def run_e2e_test(
    project_id: str,
    location: str,
    composer_env: str,
    dag_id: str,
    webserver_url: str = "",
    skip_import_job: bool = False,
    skip_staging_ingestion: bool = False,
    run_golden_tests: bool = False,
    simulate_hitl_approval: bool = False,
    sync_wait_sec: int = 20,
    poll_interval_sec: int = 15,
    timeout_sec: int = 1800,
) -> dict[str, Any]:
    """Executes the E2E DAG test and returns the final workflow summary."""
    session = get_authorized_session(project_id)

    if not webserver_url:
        webserver_url = resolve_composer_webserver_url(
            session=session,
            project_id=project_id,
            location=location,
            composer_env=composer_env,
        )
    logging.info("Using Airflow Webserver URL: %s", webserver_url)

    if sync_wait_sec > 0:
        logging.info("Waiting %ds for Composer DAG processor to sync latest GCS files...", sync_wait_sec)
        time.sleep(sync_wait_sec)

    # 1. Pre-flight check for DAG import errors
    check_dag_import_errors(session, webserver_url)

    # 2. Ensure target DAG exists and is unpaused
    ensure_dag_available_and_unpaused(session, webserver_url, dag_id)

    # 3. Trigger DAG run
    build_tag = os.environ.get("BUILD_ID", uuid.uuid4().hex[:8])
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"e2e-test-{build_tag}-{timestamp_str}"

    conf = {
        "skipImportJob": skip_import_job,
        "skipStagingIngestion": skip_staging_ingestion,
        "skipProdIngestion": True,
        "runGoldenTests": run_golden_tests,
        "autoApproveGoldenDiff": not simulate_hitl_approval,
    }

    trigger_dag_run(session, webserver_url, dag_id, run_id, conf)

    # 4. Monitor DAG run progress
    run_url = f"{webserver_url}/api/v1/dags/{dag_id}/dagRuns/{run_id}"
    ti_url = f"{run_url}/taskInstances"
    var_url = f"{webserver_url}/api/v1/variables"

    start_time = time.time()
    approval_variable_set = False
    dag_state = "queued"
    task_instances: list[dict[str, Any]] = []

    try:
        while time.time() - start_time < timeout_sec:
            resp = session.get(run_url, timeout=30)
            resp.raise_for_status()
            dag_state = resp.json().get("state", "unknown")

            ti_resp = session.get(ti_url, timeout=30)
            ti_resp.raise_for_status()
            task_instances = ti_resp.json().get("task_instances", [])

            task_summary = ", ".join(
                f"{ti.get('task_id')}:{ti.get('state') or 'none'}"
                for ti in sorted(task_instances, key=lambda x: x.get("task_id", ""))
            )
            elapsed = int(time.time() - start_time)
            logging.info("[%04ds] DAG State: %-10s | Tasks: %s", elapsed, dag_state.upper(), task_summary)

            # Check if HumanApprovalSensor is paused waiting for approval
            for ti in task_instances:
                if ti.get("task_id") == "await_human_approval" and ti.get("state") == "up_for_reschedule":
                    if simulate_hitl_approval and not approval_variable_set:
                        logging.info(
                            "Task 'await_human_approval' is paused in reschedule mode. "
                            "Injecting Airflow Variable PROD_APPROVE_ALL='true' to unblock..."
                        )
                        session.post(
                            var_url,
                            json={"key": "PROD_APPROVE_ALL", "value": "true"},
                            timeout=30,
                        )
                        approval_variable_set = True

            if dag_state in ("success", "failed"):
                break

            time.sleep(poll_interval_sec)
        else:
            raise TimeoutError(f"DAG run '{run_id}' timed out after {timeout_sec}s (last state: {dag_state}).")

    finally:
        if approval_variable_set:
            logging.info("Cleaning up temporary Airflow Variable 'PROD_APPROVE_ALL'...")
            try:
                session.delete(f"{var_url}/PROD_APPROVE_ALL", timeout=30)
            except Exception as ex:
                logging.warning("Failed to delete temporary variable PROD_APPROVE_ALL: %s", ex)

    # 5. Evaluate final state & fetch XCom summary
    if dag_state != "success":
        logging.error("E2E DAG run '%s' FAILED with state '%s'!", run_id, dag_state)
        dump_failed_task_logs(session, webserver_url, dag_id, run_id, task_instances)
        raise RuntimeError(f"E2E test failed: DAG '{dag_id}' run '{run_id}' finished with state '{dag_state}'.")

    # Fetch workflow_summary XCom return_value
    xcom_url = f"{run_url}/taskInstances/workflow_summary/xcomEntries/return_value"
    summary_data: dict[str, Any] = {}
    try:
        xcom_resp = session.get(xcom_url, timeout=30)
        if xcom_resp.ok:
            raw_val = xcom_resp.json().get("value")
            if isinstance(raw_val, str):
                try:
                    summary_data = json.loads(raw_val)
                except Exception:
                    summary_data = {"raw": raw_val}
            elif isinstance(raw_val, dict):
                summary_data = raw_val
    except Exception as ex:
        logging.warning("Could not fetch workflow_summary XCom: %s", ex)

    logging.info(
        "\n%s\nE2E DAG TEST SUCCEEDED: %s (%s)\nWorkflow Summary XCom:\n%s\n%s",
        "=" * 80,
        dag_id,
        run_id,
        json.dumps(summary_data, indent=2),
        "=" * 80,
    )
    return summary_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Run E2E test for an Airflow DAG in Cloud Composer.")
    parser.add_argument("--project-id", default=os.environ.get("PROJECT_ID", DEFAULT_PROJECT_ID))
    parser.add_argument("--location", default=os.environ.get("LOCATION", DEFAULT_LOCATION))
    parser.add_argument("--composer-env", default=os.environ.get("COMPOSER_ENV_NAME", DEFAULT_COMPOSER_ENV))
    parser.add_argument("--dag-id", default=os.environ.get("E2E_DAG_ID", DEFAULT_DAG_ID))
    parser.add_argument("--webserver-url", default=os.environ.get("COMPOSER_WEBSERVER_URL", ""))
    parser.add_argument(
        "--skip-import-job",
        action="store_true",
        default=os.environ.get("E2E_SKIP_IMPORT_JOB", "").lower() in ("true", "1", "yes"),
        help="Skip the Cloud Batch import job step to test orchestration quickly.",
    )
    parser.add_argument(
        "--skip-staging-ingestion",
        action="store_true",
        default=os.environ.get("E2E_SKIP_STAGING_INGESTION", "").lower() in ("true", "1", "yes"),
        help="Skip the Staging Spanner ingestion step.",
    )
    parser.add_argument(
        "--run-golden-tests",
        action="store_true",
        default=os.environ.get("E2E_RUN_GOLDEN_TESTS", "").lower() in ("true", "1", "yes"),
        help="Force running staging golden verification Cloud Build.",
    )
    parser.add_argument(
        "--simulate-hitl-approval",
        action="store_true",
        default=False,
        help="Test human-in-the-loop pause and variable-based approval.",
    )
    parser.add_argument(
        "--sync-wait",
        type=int,
        default=int(os.environ.get("E2E_SYNC_WAIT_SEC", "20")),
        help="Seconds to wait for Composer DAG sync before triggering.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=15,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Maximum DAG run timeout in seconds.",
    )

    args = parser.parse_args()
    run_e2e_test(
        project_id=args.project_id,
        location=args.location,
        composer_env=args.composer_env,
        dag_id=args.dag_id,
        webserver_url=args.webserver_url,
        skip_import_job=args.skip_import_job,
        skip_staging_ingestion=args.skip_staging_ingestion,
        run_golden_tests=args.run_golden_tests,
        simulate_hitl_approval=args.simulate_hitl_approval,
        sync_wait_sec=args.sync_wait,
        poll_interval_sec=args.poll_interval,
        timeout_sec=args.timeout,
    )


if __name__ == "__main__":
    main()
