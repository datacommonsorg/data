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


class ImportAttemptModel:
    """Data model of an import attempt.

    The class variables below are the fields of an import attempt.

    TODO(intrepiditee): Add description for each field
    """
    attempt_id = 'attempt_id'
    run_id = 'run_id'
    import_name = 'import_name'
    absolute_import_name = 'absolute_import_name'
    provenance_url = 'provenance_url'
    provenance_description = 'provenance_description'
    status = 'status'
    time_created = 'time_created'
    time_completed = 'time_completed'
    logs = 'logs'
    template_mcf_url = 'template_mcf_url'
    node_mcf_url = 'node_mcf_url'
    csv_url = 'csv_url'
