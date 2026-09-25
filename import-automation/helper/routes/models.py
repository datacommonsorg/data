# Copyright 2026 Google LLC
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

from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    OK = "OK"
    SUCCESS = "SUCCESS"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    DONE = "DONE"
    RUNNING = "RUNNING"


class BaseResponse(BaseModel):
    status: ResponseStatus = Field(description="Execution status")
    message: Optional[str] = Field(default=None, description="Optional message")


class ImportState(str, Enum):
    STAGING = "STAGING"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    SKIP = "SKIP"
    VALIDATION = "VALIDATION"


class ImportStatusItem(BaseModel):
    importName: str
    status: ImportState
    latestVersion: Optional[str] = None
    graphPath: Optional[str] = None


class UpdateImportStatusRequest(BaseModel):
    imports: List[ImportStatusItem]
    jobId: Optional[str] = None
    workflowId: Optional[str] = None
    executionTime: Optional[int] = None
    dataVolume: Optional[int] = None
    nextRefresh: Optional[str] = None


class UpdateImportVersionRequest(BaseModel):
    imports: List[str]
    version: str
    comment: str
    workflowId: Optional[str] = None
    jobId: Optional[str] = None
    override: Optional[bool] = False
    triggerIngestion: Optional[bool] = False


class ImportVersionItem(BaseModel):
    importName: str
    status: ImportState
    latestVersion: Optional[str] = None


class UpdateImportVersionResponse(BaseResponse):
    imports: List[ImportVersionItem] = Field(default_factory=list)
