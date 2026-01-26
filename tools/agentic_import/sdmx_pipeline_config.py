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
"""Configuration dataclasses for the SDMX agentic import pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

# SDMX flag names shared across pipeline modules.
FLAG_SDMX_ENDPOINT = "sdmx.endpoint"
FLAG_SDMX_AGENCY = "sdmx.agency"
FLAG_SDMX_DATAFLOW_ID = "sdmx.dataflow.id"
FLAG_SDMX_DATAFLOW_KEY = "sdmx.dataflow.key"
FLAG_SDMX_DATAFLOW_PARAM = "sdmx.dataflow.param"


@dataclass(frozen=True)
class SdmxDataflowConfig:
    """Configuration for SDMX dataflow."""
    id: str | None = None
    key: str | None = None
    param: str | None = None


@dataclass(frozen=True)
class SdmxConfig:
    """Configuration for SDMX data access."""
    endpoint: str | None = None
    agency: str | None = None
    dataflow: SdmxDataflowConfig = field(default_factory=SdmxDataflowConfig)


@dataclass(frozen=True)
class SampleConfig:
    """Configuration for data sampling."""
    rows: int = 1000


@dataclass(frozen=True)
class RunConfig:
    """Configuration for pipeline execution."""
    command: str
    dataset_prefix: str | None = None
    working_dir: str | None = None
    run_only: str | None = None
    force: bool = False
    verbose: bool = False
    skip_confirmation: bool = False
    gemini_cli: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    """Aggregated configuration for the pipeline."""
    sdmx: SdmxConfig = field(default_factory=SdmxConfig)
    sample: SampleConfig = field(default_factory=SampleConfig)
    run: RunConfig = field(default_factory=lambda: RunConfig(command="python"))
