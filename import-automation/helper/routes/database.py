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

import logging
from fastapi import APIRouter, Depends, HTTPException
from clients.bigquery import BigQueryClient
from dependencies import get_bigquery_client
from routes.models import BaseResponse, ResponseStatus
from utils.logging import log_start

router = APIRouter(prefix="/database", tags=["database"])


@router.post("/initialize", response_model=BaseResponse)
@log_start
def initialize_database(bigquery: BigQueryClient = Depends(get_bigquery_client)):
    """Initializes BigQuery by creating the ImportHistory table and ImportSummary view."""
    try:
        bigquery.initialize_database()
        return BaseResponse(status=ResponseStatus.OK)
    except Exception as e:
        logging.error(f"Failed to initialize BigQuery database in import-helper: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )
