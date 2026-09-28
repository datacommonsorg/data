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

from fastapi import HTTPException
from clients.spanner import SpannerClient
from clients.storage import StorageClient
import config

_spanner_client = None
_storage_client = None


def get_spanner_client() -> SpannerClient:
    global _spanner_client
    if _spanner_client is None:
        if not config.SPANNER_PROJECT_ID or not config.SPANNER_INSTANCE_ID or not config.SPANNER_DATABASE_ID:
            raise HTTPException(
                status_code=500,
                detail="Spanner configuration is missing. Ensure SPANNER_PROJECT_ID, SPANNER_INSTANCE_ID, and SPANNER_DATABASE_ID are set."
            )
        _spanner_client = SpannerClient(
            config.SPANNER_PROJECT_ID,
            config.SPANNER_INSTANCE_ID,
            config.SPANNER_DATABASE_ID
        )
    return _spanner_client


def get_storage_client() -> StorageClient:
    global _storage_client
    if _storage_client is None:
        if not config.GCS_BUCKET_ID:
            raise HTTPException(
                status_code=500,
                detail="GCS Bucket ID configuration is missing. Ensure GCS_BUCKET_ID is set."
            )
        _storage_client = StorageClient(config.GCS_BUCKET_ID)
    return _storage_client
