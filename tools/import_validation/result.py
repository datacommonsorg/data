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
"""Module for the ValidationResult data class."""

from enum import Enum


class ValidationStatus(Enum):
    """Represents the outcome of a validation check."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    CONFIG_ERROR = "CONFIG_ERROR"  # For bad configuration
    DATA_ERROR = "DATA_ERROR"  # For missing columns


class ValidationResult:
    """Describes the result of the validaiton of an import."""

    def __init__(self,
                 status: ValidationStatus,
                 name: str,
                 message: str = '',
                 details: dict = None,
                 validation_params: dict = None,
                 rows_processed: int = 0,
                 rows_succeeded: int = 0,
                 rows_failed: int = 0):
        self.status = status
        self.name = name
        self.message = message  # A human-readable summary
        self.details = details if details is not None else {}
        self.validation_params = validation_params if validation_params is not None else {}
        self.rows_processed = rows_processed
        self.rows_succeeded = rows_succeeded
        self.rows_failed = rows_failed
