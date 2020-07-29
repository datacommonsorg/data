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
Data model of an import attempt.
"""
import enum


class ImportAttempt:
    """Data model of an import attempt.

    The class variables below are the fields of an import attempt.
    """
    # ID of the import attempt as a string. This is a UUID hex string.
    attempt_id = 'attempt_id'
    # ID of the system run as a string. This is a UUID hex string.
    run_id = 'run_id'
    # Relative import name as a string parsed from the manifest.
    import_name = 'import_name'
    # Absolute import name as a string of the form
    # <path to the directory with the manifest>:<import_name>, e.g.,
    # scripts/us_fed/treasury:US_FED_constant_maturity_rates
    absolute_import_name = 'absolute_import_name'
    # Provenance URL parsed from the manifest.
    provenance_url = 'provenance_url'
    # Provenance description parsed from the manifest.
    provenance_description = 'provenance_description'
    # Status of the import attempt, as a string.
    # Must be one of the defined values by ImportAttemptStatus.
    status = 'status'
    # Creation time as a string of the import attempt.
    # Must be in ISO 8601 format with UTC timezone of the form
    # 'YYYY-MM-DDTHH:MM:SS.ffffff+00:00', e.g.,
    # '2020-06-30T04:28:53.717569+00:00'.
    time_created = 'time_created'
    # Completion time as a string of the import attempt. See time_created for
    # format.
    time_completed = 'time_completed'
    # List of IDs of progress logs attached to this import attempt, each
    # as a string.
    logs = 'logs'
    # List of import inputs. Each import input is a dict with three fields:
    # import_input_url, node_mcf_url, and csv_url.
    import_inputs = 'import_inputs'


class ImportAttemptStatus(enum.Enum):
    """Allowed status of an import attempt.

    The status of an import attempt can only be one of these.
    """
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


IMPORT_ATTEMPT_STATUS = frozenset(
    status.value for status in ImportAttemptStatus)
