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

from datetime import datetime, timezone
import logging
import croniter
from fastapi import APIRouter, Depends, HTTPException, Request
from clients.spanner import SpannerClient
from clients.storage import StorageClient
import config
from dependencies import get_spanner_client, get_storage_client
from routes.imports import update_import_status
from routes.models import (
    BaseResponse,
    ImportState,
    ImportStatusItem,
    ResponseStatus,
    UpdateImportStatusRequest,
)
from utils import imports as import_utils

router = APIRouter(prefix="/imports", tags=["events"])


@router.post("/feed", response_model=BaseResponse)
async def handle_feed_event(
    request: Request,
    spanner: SpannerClient = Depends(get_spanner_client),
    storage: StorageClient = Depends(get_storage_client),
):
    """Processes Pub/Sub push notification for CDA transfer completion."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message = import_utils.parse_message(body)
    if not message:
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")

    attributes = message.get('attributes', {})
    message_id = message.get('messageId', '')
    if attributes.get('transfer_status') != 'TRANSFER_COMPLETED':
        return BaseResponse(status=ResponseStatus.OK, message="Transfer not completed; skipped.")

    duplicate = import_utils.check_duplicate(config.GCS_BUCKET_ID, message_id)
    if duplicate:
        logging.info(f"Message {message_id} already processed. Skipping.")
        return BaseResponse(status=ResponseStatus.OK, message="Duplicate message skipped.")

    import_name = attributes.get('import_name')
    if not import_name:
        raise HTTPException(status_code=400, detail="Missing import_name in attributes")

    latest_version = attributes.get(
        'import_version',
        datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    post_process = attributes.get('post_process', 'spanner_ingestion_workflow')
    graph_path = attributes.get('graph_path', "/**/*.mcf*")
    import_size = attributes.get('import_size', 'small')
    cron_schedule = attributes.get('cron_schedule', '')
    dag_id = attributes.get('dag_id')

    skip_staging_ingestion = (
        attributes.get('skip_staging_ingestion').lower() == 'true'
        if attributes.get('skip_staging_ingestion') else None
    )
    skip_prod_ingestion = (
        attributes.get('skip_prod_ingestion').lower() == 'true'
        if attributes.get('skip_prod_ingestion') else None
    )

    if post_process == 'spanner_ingestion_workflow':
        feed_name = attributes.get('feed_name', 'cda_feed')
        base_version_path = f"gs://{config.GCS_BUCKET_ID}/{import_name.replace(':', '/')}/{latest_version}"

        next_refresh = None
        if cron_schedule:
            try:
                next_refresh = croniter.croniter(
                    cron_schedule,
                    datetime.now(timezone.utc)).get_next(datetime).isoformat()
            except (croniter.CroniterError) as e:
                logging.error(
                    f"Error calculating next refresh from schedule '{cron_schedule}': {e}"
                )

        status_req = UpdateImportStatusRequest(
            imports=[
                ImportStatusItem(
                    importName=import_name,
                    status=ImportState.STAGING,
                    latestVersion=base_version_path,
                    graphPath=graph_path
                )
            ],
            jobId=feed_name,
            nextRefresh=next_refresh
        )
        update_import_status(status_req, spanner=spanner, storage=storage)

        # Invoke Import Automation workflow to trigger staging and prod ingestion
        if config.PROJECT_ID and config.LOCATION:
            import_utils.invoke_import_automation_workflow(
                project_id=config.PROJECT_ID,
                location=config.LOCATION,
                workflow_id=config.IMPORT_AUTOMATION_WORKFLOW_ID,
                import_name=import_name,
                latest_version=latest_version,
                import_size=import_size,
                graph_path=graph_path,
                cron_schedule=cron_schedule,
                skip_import_job=True,
                skip_staging_ingestion=skip_staging_ingestion,
                skip_prod_ingestion=skip_prod_ingestion,
            )
    elif post_process == 'import_automation_workflow':
        if config.PROJECT_ID and config.LOCATION:
            import_utils.invoke_import_automation_workflow(
                project_id=config.PROJECT_ID,
                location=config.LOCATION,
                workflow_id=config.IMPORT_AUTOMATION_WORKFLOW_ID,
                import_name=import_name,
                latest_version=latest_version,
                import_size=import_size,
                graph_path=graph_path,
                cron_schedule=cron_schedule,
                skip_import_job=False,
                skip_staging_ingestion=skip_staging_ingestion,
                skip_prod_ingestion=skip_prod_ingestion,
            )
    elif post_process == 'import_automation_airflow':
        # Invoke Cloud Composer Airflow DAG for import automation
        import_utils.invoke_import_automation_airflow(
            import_name=import_name,
            latest_version=latest_version,
            import_size=import_size,
            graph_path=graph_path,
            cron_schedule=cron_schedule,
            dag_id=dag_id,
            skip_import_job=False,
            skip_staging_ingestion=skip_staging_ingestion,
            skip_prod_ingestion=skip_prod_ingestion,
        )
    else:
        logging.info(f"Skipping import post processing for post_process={post_process}.")

    return BaseResponse(status=ResponseStatus.OK, message="Event processed successfully.")
