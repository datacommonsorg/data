# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
sdmx_models.py

This module defines the data models for SDMX artifacts.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SdmxDataflow:
    """Represents a single SDMX dataflow with its essential metadata."""
    id: str
    name: str
    description: str
    agency_id: str
    version: str


@dataclass
class SdmxStructureMessage:
    """A container for structured metadata from the SDMX client."""
    dataflows: List[SdmxDataflow] = field(default_factory=list)
