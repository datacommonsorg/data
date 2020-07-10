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


class SystemRunModel:
    """Data model of a system run.

    The class variables below are the fields of a system run.

    TODO(intrepiditee): Add description for each field
    """
    run_id = 'run_id'
    repo_name = 'repo_name'
    branch_name = 'branch_name'
    pr_number = 'pr_number'
    commit_sha = 'commit_sha'
    time_created = 'time_created'
    time_completed = 'time_completed'
    import_attempts = 'import_attempts'
    logs = 'logs'
    status = 'status'
