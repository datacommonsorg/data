# Copyright 2023 Google LLC
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
This module provides a class to track the status of imports.
"""

import dataclasses
import enum
import json
import logging
import os
from typing import List

@enum.unique
class ImportStatus(enum.Enum):
    """
    The status of an import.
    """
    UNKNOWN = 0
    STARTED = 1
    SUCCESS = 2
    FAILURE = 3

@dataclasses.dataclass
class ImportTracker:
    """
    Tracks the status of an import.
    """
    import_name: str
    status: ImportStatus = ImportStatus.UNKNOWN
    message: str = ''

    def to_json(self) -> str:
        """
        Returns the tracker as a JSON string.
        """
        data = dataclasses.asdict(self)
        data['status'] = self.status.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_string: str) -> 'ImportTracker':
        """
        Returns an ImportTracker from a JSON string.
        """
        data = json.loads(json_string)
        data['status'] = ImportStatus(data['status'])
        return cls(**data)