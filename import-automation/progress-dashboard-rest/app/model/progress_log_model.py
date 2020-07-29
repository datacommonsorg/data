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
import enum


class ProgressLog:
    """Data model of a progress log.

    The class variables below are the fields of a progress log.
    """
    # ID of the progress log as a string. This is a UUID hex string.
    log_id = 'log_id'
    # Log level as a string. Must be one of the values defined by LogLevel.
    level = 'level'
    # Log message as a string. The API stores the actual message in Google
    # Cloud Storage and converts it to an identifier. When the user queries the
    # log, the identifier is converted back to the actual message.
    message = 'message'
    # Time at which the log is created, as a string.
    # See import_attempt_model.ImportAttempt.time_created for format.
    time_logged = 'time_logged'
    # ID of the system run this progress log is attached to.
    run_id = 'run_id'
    # ID of the import attempt this progress log is attached to.
    attempt_id = 'attempt_id'


class LogLevel(enum.Enum):
    """Allowed log levels of a log.

    The level of a log can only be one of these.
    """
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


LOG_LEVELS = frozenset(level.value for level in LogLevel)
