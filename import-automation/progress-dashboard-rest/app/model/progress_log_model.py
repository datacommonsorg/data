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
Data model of a progress log.
"""


class ProgressLogModel:
    """Data model of a progress log.

    The class variables below are the fields of a progress log.

    TODO(intrepiditee): Add description for each field
    """
    log_id = 'log_id'
    level = 'level'
    message = 'message'
    time_logged = 'time_logged'
    run_id = 'run_id'
    attempt_id = 'attempt_id'
