# Copyright 2020 Google LLC
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
Data model of a system run.
"""
import enum


class SystemRun:
    """Data model of a system run.

    This class is not a data class. The class variables below are the fields
    of a system run and their values are the field names. They are used
    to index system run entities.
    """
    # ID of the system run as a string. This is a UUID hex string.
    run_id = 'run_id'
    # Name of the repository from which the pull request is created,
    # if applicable, as a string.
    repo_name = 'repo_name'
    # Name of the branch from which the pull request is created,
    # if applicable, as a string.
    branch_name = 'branch_name'
    # Number of the pull request, is applicable, as an int.
    pr_number = 'pr_number'
    # ID of the commit as a string, if applicable.
    commit_sha = 'commit_sha'
    # Time at which the system run is created, as a string.
    # See import_attempt_model.ImportAttempt.time_created for format.
    time_created = 'time_created'
    # Time at which the system run is completed, as a string.
    # See import_attempt_model.ImportAttempt.time_created for format.
    time_completed = 'time_completed'
    # List of IDs of the import attempts executed by this system run, each
    # as a string.
    import_attempts = 'import_attempts'
    # List of IDs of progress logs attached to this system run, each
    # as a string.
    logs = 'logs'
    # Status of the system run, as a string.
    # Must be one of the defined values by SystemRunStatus.
    status = 'status'


FIELDS = frozenset(name for name in vars(SystemRun)
                   if not name.startswith('__'))


class SystemRunStatus(enum.Enum):
    """Allowed status of a system run.

    The status of a system run can only be one of these.
    """
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


SYSTEM_RUN_STATUS = frozenset(status.value for status in SystemRunStatus)
