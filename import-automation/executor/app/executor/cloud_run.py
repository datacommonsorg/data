# Copyright 2024 Google LLC
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
"""Interface for Cloud Run API.

This module contains utilities to:
- Create or update an existing cloud run job (create_or_update_cloud_run_job)
- Execute an existing cloud run job. (execute_run_job)
"""
import datetime
import os
import time

from absl import logging
from google.api_core.exceptions import NotFound
from google.cloud import run_v2


def create_or_update_cloud_run_job(
    project_id: str,
    location: str,
    job_id: str,
    image: str,
    env_vars: dict,
) -> run_v2.Job:
    """Creates a new cloud run job or updates an existing one.

  If the jobs exists, the container is updated with new image and environment
  variables.
  The uses the sync API and blocks the caller until the jobs is ready.

  Args:
    project_id: Google cloud project.
    location: Region for the execution, such as 'us-central1'
    job_id: Name of the job
    image: Container image URL such as 'gcr.io/your-project/your-image:latest'
    env_vars: dict of environment variables as {'VAR': '<value>'}

  Returns:
    Job created as a dict.
  """
    job_id = get_job_id(job_id)
    client = run_v2.JobsClient()
    parent = f"projects/{project_id}/locations/{location}"
    job_name = f"{parent}/jobs/{job_id}"

    # Prepare environment variables for the job.
    env = []
    for var, value in env_vars.items():
        env.append(run_v2.EnvVar(name=var, value=value))

    container = run_v2.Container(image=image, env=env)
    exe_template = run_v2.ExecutionTemplate(template=run_v2.TaskTemplate(
        containers=[container]))
    new_job = run_v2.Job(template=exe_template)
    logging.info(f"Creating job {job_name}: {new_job}")

    # Look for existing job to update
    job = None
    try:
        job = client.get_job(request=run_v2.GetJobRequest(name=job_name))
        logging.info(f"Found existing job {job_name}: {job}")
    except NotFound:
        logging.info(f"No existing job, creating new job: {job_name}")

    if not job:
        # Create a new Cloud Run Job
        create_request = run_v2.CreateJobRequest(parent=parent,
                                                 job_id=job_id,
                                                 job=new_job)
        create_operation = client.create_job(request=create_request)
        result = create_operation.result()  # Blocks until job completes
        logging.info(f"Job creation result {job_name}: {result}")
    else:
        # Update existing Cloud Run job
        # Overrides container settings including image, env
        job.template.template.containers = new_job.template.template.containers
        logging.info(f"Updating job {job_name}: {job}")
        update_request = run_v2.UpdateJobRequest(job=job)
        update_operation = client.update_job(request=update_request)
        result = update_operation.result()  # Blocks until update completes
        logging.info(f"Job updated {job_name}: {result}")
    return result


def execute_cloud_run_job(
    project_id: str,
    location: str,
    job_id: str,
) -> run_v2.Job:
    """Execute a cloud run job and block until the execution completes.

  The job parameters should match an existing job.

  Args:
    project_id: Google cloud project.
    location: Region for the execution, such as 'us-central1'
    job_id: Name of the job

  Returns:
    Job after execution is complete.
  """
    job_id = get_job_id(job_id)
    client = run_v2.JobsClient()
    parent = f"projects/{project_id}/locations/{location}"
    job_name = f"{parent}/jobs/{job_id}"

    # Run the job
    run_request = run_v2.RunJobRequest(name=job_name)
    logging.info(f"Executing {job_name}: {run_request}")
    run_operation = client.run_job(request=run_request)
    result = run_operation.result()  # Blocks until job completes
    logging.info(f"Execute result {job_name}: {result}")
    return result


def delete_cloud_run_job(project_id: str, location: str,
                         job_id: str) -> run_v2.Job:
    """Delete an existing cloud run job.

  Args:
    project_id: Google cloud project.
    location: Region for the execution, such as 'us-central1'
    job_id: Name of the job

  Returns:
    Jobs that is deleted
  """
    job_id = get_job_id(job_id)
    client = run_v2.JobsClient()
    parent = f"projects/{project_id}/locations/{location}"
    job_name = f"{parent}/jobs/{job_id}"

    # Delete the job
    del_request = run_v2.DeleteJobRequest(name=job_name)
    logging.info(f"Deleting {job_name}: {del_request}")
    del_operation = client.delete_job(request=del_request)
    result = del_operation.result()
    logging.info(f"Job deletion {job_name}: {result}")
    return result


def get_job_id(job_id: str) -> str:
    """Returns a valid job_id with lower case, digits and '-' only.

  Args:
    job_id: input string with proposed job-id

  Returns:
    job_if string with alphanumeric and '-' characters.
  """
    chars = []
    for c in job_id.lower():
        if c.isalnum() or c == "-":
            chars.append(c)
        else:
            chars.append("-")
    return "".join(chars).strip("-")
