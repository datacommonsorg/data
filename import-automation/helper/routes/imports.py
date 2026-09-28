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
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from clients.spanner import SpannerClient
from clients.storage import StorageClient
import config
from dependencies import get_spanner_client, get_storage_client
from routes.models import (
    BaseResponse,
    ImportState,
    ImportVersionItem,
    ResponseStatus,
    UpdateImportStatusRequest,
    UpdateImportVersionRequest,
    UpdateImportVersionResponse,
)
from utils import imports as import_utils

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/status", response_model=BaseResponse)
def update_import_status(req: UpdateImportStatusRequest,
                         spanner: SpannerClient = Depends(get_spanner_client),
                         storage: StorageClient = Depends(get_storage_client)):
    """Updates status and metadata of import jobs in ImportSummary and ImportHistory."""
    for item in req.imports:
        logging.info(
            f"Updating import {item.importName} to status {item.status}")

        import_req = {
            "importName": item.importName,
            "status": item.status,
            "jobId": req.jobId,
            "workflowId": req.workflowId,
            "executionTime": req.executionTime,
            "dataVolume": req.dataVolume,
            "latestVersion": item.latestVersion,
            "graphPath": item.graphPath,
            "nextRefresh": req.nextRefresh,
        }
        req_dict = {k: v for k, v in import_req.items() if v is not None}
        params = import_utils.get_import_params(req_dict)

        next_refresh = None
        if config.IS_BASE_DC and config.PROJECT_ID and config.LOCATION:
            next_refresh = import_utils.get_next_refresh(
                config.PROJECT_ID, config.LOCATION, item.importName)

        if next_refresh:
            params['next_refresh'] = next_refresh

        wf_id = req.workflowId or req.jobId
        status_val = item.status.value if hasattr(item.status, 'value') else item.status
        version_path = params.get('latest_version') or item.latestVersion or ""

        if item.status == ImportState.STAGING:
            version = os.path.basename(item.latestVersion or '')
            if not version:
                raise HTTPException(
                    status_code=400,
                    detail=f"Empty version for import {item.importName}")
            storage.update_version_file(item.importName,
                                        version,
                                        is_staging=True)
            storage.update_provenance_file(item.importName, version)
            storage.update_import_summary(params, version=version)
            storage.update_version_file(item.importName,
                                        version,
                                        is_staging=False)
            comment = f"import-workflow:{wf_id or ''}"
            spanner.update_import_history(item.importName,
                                          version_path,
                                          comment,
                                          workflow_id=wf_id,
                                          job_id=req.jobId,
                                          status=status_val,
                                          execution_time=req.executionTime,
                                          data_volume=req.dataVolume)
        elif item.status == ImportState.FAILURE:
            comment = f"import-failure:{wf_id or ''}"
            spanner.update_import_history(item.importName,
                                          version_path,
                                          comment,
                                          workflow_id=wf_id,
                                          job_id=req.jobId,
                                          status=status_val,
                                          execution_time=req.executionTime,
                                          data_volume=req.dataVolume)

        spanner.update_import_summary(params)
    return BaseResponse(status=ResponseStatus.OK)


@router.post("/version", response_model=UpdateImportVersionResponse)
def update_import_version(req: UpdateImportVersionRequest,
                          request: Request,
                          spanner: SpannerClient = Depends(get_spanner_client),
                          storage: StorageClient = Depends(get_storage_client)):
    """Updates version and status of multiple imports in ImportSummary and ImportHistory."""
    updated_imports = []
    import_items = []
    caller = import_utils.get_caller_identity(request) if req.override else None

    for import_name in req.imports:
        logging.info(
            f"Updating import {import_name} to version {req.version} comment: {req.comment}"
        )

        version = req.version
        if version == 'STAGING':
            version = storage.get_import_version(import_name, is_staging=True)

        summary = storage.get_import_summary(import_name, version)
        params = import_utils.get_import_params(summary)

        comment = req.comment
        if req.override:
            params['status'] = 'STAGING'
            comment = f'version-override:{caller} {comment}'
        elif params.get('status') == 'SKIP':
            version = storage.get_import_version(import_name, is_staging=False)
            summary = storage.get_import_summary(import_name, version)
            params['latest_version'] = import_utils.get_import_params(summary).get('latest_version')

        if not params.get('latest_version'):
            params['latest_version'] = version

        return_status = params.get('status') or 'FAILURE'

        wf_id = req.workflowId or req.jobId
        version_path = params.get('latest_version') or version

        if params['status'] == 'STAGING':
            storage.update_provenance_file(import_name, version)
            storage.update_version_file(import_name, version, is_staging=False)
            spanner.update_import_history(import_name,
                                          version_path,
                                          comment,
                                          workflow_id=wf_id,
                                          job_id=req.jobId,
                                          status="STAGING")
            logging.info(f"Updated import {import_name} to version {version}")
        else:
            logging.info(f"Skipping {import_name} version update")

        spanner.update_import_summary(params)

        import_items.append(
            ImportVersionItem(
                importName=import_name,
                status=return_status,
                latestVersion=params.get('latest_version')
            )
        )
        updated_imports.append(
            f"Import: {import_name} Version: {version} Status: {params['status']}"
        )

    return UpdateImportVersionResponse(status=ResponseStatus.OK,
                                       message="; ".join(updated_imports),
                                       imports=import_items)
