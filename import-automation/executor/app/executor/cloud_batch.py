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
import json


def get_gce_instance(required_cpu: float,
                     required_memory_gib: float) -> str | None:
    """
    Finds the most cost-effective GCE instance that meets the resource requirements.
    """
    GCE_MACHINE_TYPES = [
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
    # Filter for instances that meet or exceed the CPU and memory requirements.
    # Sort the suitable instances to find the "smallest" one that fits.
    # The primary sort key is the number of CPUs, and the secondary key is memory.
    # This heuristic helps find the machine that is closest to the requested
    # resources, which is often the most cost-effective.
    suitable_instances = [
        instance for instance in GCE_MACHINE_TYPES
        if instance['cpus'] >= required_cpu and
        instance['memory_gib'] >= required_memory_gib
    ]

    if not suitable_instances:
        return None
    suitable_instances.sort(key=lambda x: (x['cpus'], x['memory_gib']))
    return suitable_instances[0]['name']


def create_job_request(import_name: str, import_config, import_spec,
                       resources: str) -> str:
    if 'resource_limits' in import_spec:
        resource_limits = import_spec['resource_limits']
        machine_type = get_gce_instance(resource_limits['cpu'],
                                        resource_limits['memory'])
        if machine_type is not None:
            resources.update(resource_limits)
            resources["machine"] = machine_type
        else:
            logging.error(
                'Not able to find a suitable VM instance type. Using default config.'
            )
            resources["machine"] = 'n2-highmem-4'

    resources["cpu"] = resources["cpu"] * 1000
    resources["memory"] = resources["memory"] * 1024
    import_config_string = json.dumps(import_config)
    job_name = import_name.split(':')[1]
    job_name = job_name.replace("_", "-").lower()
    argument_payload = {
        "jobName": job_name,
        "importName": import_name,
        "importConfig": import_config_string,
        "resources": resources
    }
    argument_string = json.dumps(argument_payload)
    final_payload = {
        "argument": argument_string,
        "callLogLevel": "CALL_LOG_LEVEL_UNSPECIFIED"
    }

    json_encoded_body = json.dumps(final_payload, indent=2)
    return json_encoded_body
