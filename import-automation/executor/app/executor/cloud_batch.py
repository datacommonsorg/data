# Copyright 2025 Google LLC
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
This module contains utilities to help set up cloud batch jobs.
"""
from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.cloud import batch_v1

DEFAULT_RESOURCES: dict[str, Any] = {
    'machine': 'n2-standard-8',
    'cpu': 8000,
    'memory': 32768,
    'disk': 100,
}

_GCE_MACHINE_TYPES = [
    {
        'name': 'n2-standard-2',
        'cpus': 2,
        'memory_gib': 8
    },
    {
        'name': 'n2-standard-4',
        'cpus': 4,
        'memory_gib': 16
    },
    {
        'name': 'n2-standard-8',
        'cpus': 8,
        'memory_gib': 32
    },
    {
        'name': 'n2-standard-16',
        'cpus': 16,
        'memory_gib': 64
    },
    {
        'name': 'n2-standard-32',
        'cpus': 32,
        'memory_gib': 128
    },
    {
        'name': 'n2-standard-48',
        'cpus': 48,
        'memory_gib': 192
    },
    {
        'name': 'n2-standard-64',
        'cpus': 64,
        'memory_gib': 256
    },
    {
        'name': 'n2-highmem-2',
        'cpus': 2,
        'memory_gib': 16
    },
    {
        'name': 'n2-highmem-4',
        'cpus': 4,
        'memory_gib': 32
    },
    {
        'name': 'n2-highmem-8',
        'cpus': 8,
        'memory_gib': 64
    },
    {
        'name': 'n2-highmem-16',
        'cpus': 16,
        'memory_gib': 128
    },
    {
        'name': 'n2-highmem-32',
        'cpus': 32,
        'memory_gib': 256
    },
    {
        'name': 'n2-highmem-48',
        'cpus': 48,
        'memory_gib': 384
    },
    {
        'name': 'n2-highmem-64',
        'cpus': 64,
        'memory_gib': 512
    },
    {
        'name': 'n2-highcpu-2',
        'cpus': 2,
        'memory_gib': 2
    },
    {
        'name': 'n2-highcpu-4',
        'cpus': 4,
        'memory_gib': 4
    },
    {
        'name': 'n2-highcpu-8',
        'cpus': 8,
        'memory_gib': 8
    },
    {
        'name': 'n2-highcpu-16',
        'cpus': 16,
        'memory_gib': 16
    },
    {
        'name': 'n2-highcpu-32',
        'cpus': 32,
        'memory_gib': 32
    },
]

_MAX_GCE_CPUS = max(instance['cpus'] for instance in _GCE_MACHINE_TYPES)
_MAX_GCE_MEMORY_GIB = max(
    instance['memory_gib'] for instance in _GCE_MACHINE_TYPES)


def _format_resource_value(value: int | float) -> int | float:
    return (int(value)
            if isinstance(value, float) and value.is_integer() else value)


def get_gce_instance(required_cpu: float,
                     required_memory_gib: float) -> str | None:
    """
    Finds the most cost-effective GCE instance that meets the resource requirements.
    """
    # Filter for instances that meet or exceed the CPU and memory requirements.
    # Sort the suitable instances to find the "smallest" one that fits.
    # The primary sort key is the number of CPUs, and the secondary key is memory.
    # This heuristic helps find the machine that is closest to the requested
    # resources, which is often the most cost-effective.
    suitable_instances = [
        instance for instance in _GCE_MACHINE_TYPES
        if instance['cpus'] >= required_cpu and
        instance['memory_gib'] >= required_memory_gib
    ]

    if not suitable_instances:
        return None
    suitable_instances.sort(key=lambda x: (x['cpus'], x['memory_gib']))
    return suitable_instances[0]['name']


def normalize_batch_resources(
    resource_limits: dict[str, Any] | None,
    context: str | None = None,
) -> dict[str, Any]:
    """Converts manifest resource_limits (cpu in vCPUs, memory in GiB, disk in GB) into Cloud Batch resources."""
    if not resource_limits:
        return dict(DEFAULT_RESOURCES)
    if not isinstance(resource_limits, dict):
        ctx = f' for {context}' if context else ''
        raise ValueError(f'Invalid resource_limits{ctx}: expected an object, '
                         f'got {type(resource_limits).__name__}.')

    try:
        cpu_vcpu = (float(resource_limits['cpu']) if 'cpu' in resource_limits
                    else DEFAULT_RESOURCES['cpu'] / 1000.0)
        mem_gib = (float(resource_limits['memory']) if 'memory'
                   in resource_limits else DEFAULT_RESOURCES['memory'] / 1024.0)
        disk = int(resource_limits.get('disk', DEFAULT_RESOURCES['disk']))
    except (TypeError, ValueError) as exc:
        ctx = f' for {context}' if context else ''
        raise ValueError(
            f'Invalid resource_limits{ctx}: cpu, memory, and disk must be numeric.'
        ) from exc

    explicit_machine = resource_limits.get('machine')
    if explicit_machine:
        machine = str(explicit_machine)
    else:
        machine = get_gce_instance(cpu_vcpu, mem_gib)
        if machine is None:
            ctx = f' for {context}' if context else ''
            raise ValueError(
                f'No supported GCE machine type satisfies requested '
                f'resource_limits{ctx} '
                f'(cpu={_format_resource_value(cpu_vcpu)} vCPU, '
                f'memory={_format_resource_value(mem_gib)} GiB); '
                f'maximum supported is {_MAX_GCE_CPUS} vCPU, '
                f'{_MAX_GCE_MEMORY_GIB} GiB.')

    return {
        'machine': machine,
        'cpu': int(cpu_vcpu * 1000),
        'memory': int(mem_gib * 1024),
        'disk': disk,
    }


def create_job_request(import_name: str, import_config: dict,
                       import_spec: dict) -> str:
    resources = {}
    if import_spec.get('resource_limits'):
        resources = normalize_batch_resources(import_spec['resource_limits'],
                                              context=import_name)

    import_config_string = json.dumps(import_config)
    argument_payload = {
        "importName": import_name,
        "importConfig": import_config_string,
    }
    if resources:
        argument_payload["resources"] = resources
    final_payload = {"argument": json.dumps(argument_payload)}
    json_encoded_body = json.dumps(final_payload, indent=2)
    return json_encoded_body


def execute_cloud_batch_job(project_id: str, location: str, job_name: str,
                            import_name: str, gcs_bucket: str,
                            image_uri: str) -> batch_v1.Job | None:
    """Creates and runs a job using the Cloud Batch API.

    Args:
        project_id: ID of the GCP project.
        location: Region where the job will be created.
        job_name: Name of the job.
        import_name: Name of the import.
        gcs_bucket: GCS bucket name for import configuration.
        image_uri: URI of the container image to run.

    Returns:
        The job object if successful, otherwise None.
    """
    from google.cloud import batch_v1

    client = batch_v1.BatchServiceClient()

    # Define what will be done as part of the job.
    runnable = batch_v1.Runnable()
    runnable.container = batch_v1.Runnable.Container()
    runnable.container.image_uri = image_uri
    runnable.container.commands = [
        f"--import_name={import_name}",
        f'--import_config={json.dumps({"gcp_project_id": project_id, "gcs_project_id": project_id, "storage_prod_bucket_name": gcs_bucket})}'
    ]

    # We can specify what resources are requested by a task.
    resources = batch_v1.ComputeResource()
    resources.cpu_milli = 4000  # 4 CPUs
    resources.memory_mib = 32768  # 32 GB

    # Mount gcs bucket as a volume.
    volume = batch_v1.Volume()
    volume.gcs.remote_path = gcs_bucket
    volume.mount_path = '/tmp/gcs'

    task = batch_v1.TaskSpec()
    task.runnables = [runnable]
    task.volumes = [volume]
    task.compute_resource = resources
    task.max_retry_count = 1
    task.max_run_duration = "1800s"

    # Tasks are grouped inside a job using TaskGroups.
    group = batch_v1.TaskGroup()
    group.task_count = 1
    group.task_spec = task

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = "n2-standard-8"
    policy.provisioning_model = batch_v1.AllocationPolicy.ProvisioningModel.STANDARD
    disk = batch_v1.AllocationPolicy.Disk()
    disk.image = "projects/debian-cloud/global/images/family/debian-12"
    disk.size_gb = 100
    policy.boot_disk = disk
    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    allocation_policy = batch_v1.AllocationPolicy()
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.parent = f"projects/{project_id}/locations/{location}"
    create_request.job_id = job_name
    create_request.job = job

    logging.info("Creating job: %s", job_name)
    created_job = client.create_job(create_request)

    for _ in range(60):  # Timeout: one hour.
        job = client.get_job(name=created_job.name)
        job_state = job.status.state
        logging.info("Job %s status: %s", job_name, job_state.name)
        if job_state == batch_v1.JobStatus.State.SUCCEEDED:
            return job
        if job_state == batch_v1.JobStatus.State.FAILED:
            logging.error("Job %s failed.", job_name)
            return None
        time.sleep(60)

    logging.error("Job %s timed out.", job_name)
    return None
