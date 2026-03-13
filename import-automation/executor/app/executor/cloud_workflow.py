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
"""
This module contains utilities to help set up and run cloud workflows.
"""
import json
import time

from absl import logging
from google.cloud.workflows import executions_v1


def trigger_workflow_and_wait(project_id: str, location: str, workflow_id: str,
                              workflow_args: dict):
    """Triggers a workflow and waits for its completion.

    Args:
        project_id: ID of the GCP project.
        location: Region where the workflow is located.
        workflow_id: ID of the workflow to execute.
        workflow_args: Arguments to pass to the workflow.

    Returns:
        The result of the execution if successful.

    Raises:
        RuntimeError: If the workflow execution fails.
    """
    execution_client = executions_v1.ExecutionsClient()
    parent = execution_client.workflow_path(project_id, location, workflow_id)

    logging.info(
        f"Triggering workflow: {workflow_id} with args: {workflow_args}")

    try:
        execution = executions_v1.Execution(argument=json.dumps(workflow_args))
        response = execution_client.create_execution(parent=parent,
                                                     execution=execution)
        execution_name = response.name
        logging.info(f"Execution started: {execution_name}")

        # Poll for execution completion
        backoff_delay = 1
        while True:
            execution = execution_client.get_execution(
                request={"name": execution_name})
            state = execution.state

            if state != executions_v1.Execution.State.ACTIVE:
                logging.info(f"Execution finished with state: {state}")
                if state == executions_v1.Execution.State.SUCCEEDED:
                    logging.info(f"Workflow {workflow_id} succeeded.")
                    return execution.result
                else:
                    logging.error(
                        f"Workflow {workflow_id} failed: {execution.error}")
                    raise RuntimeError(
                        f"Workflow {workflow_id} failed with state {state}")

            time.sleep(backoff_delay)
            backoff_delay = min(backoff_delay * 2,
                                60)  # Exponential backoff up to 60s

    except Exception as e:
        logging.error(f"Error executing workflow {workflow_id}: {e}")
        raise