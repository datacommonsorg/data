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

import functions_framework
import logging
from datetime import datetime, timezone
import import_helper as helper

logging.getLogger().setLevel(logging.INFO)


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.http
def handle_feed_event(request):
    # Updates status in spanner and triggers ingestion workflow
    # for an import using CDA feed
    message = helper.parse_message(request)
    if not message:
        return 'Invalid Pub/Sub message format', 400

    attributes = message.get('attributes', {})
    message_id = message.get('messageId', '')
    if attributes.get('transfer_status') != 'TRANSFER_COMPLETED':
        return 'OK', 200

    duplicate = helper.check_duplicate(message_id)
    if duplicate:
        logging.info(f"Message {message_id} already processed. Skipping.")
        return 'OK', 200

    import_name = attributes.get('import_name')
    latest_version = attributes.get(
        'import_version',
        datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    import_step = attributes.get('import_step', '')
    graph_path = attributes.get('graph_path', "/**/*.mcf*")
    import_size = attributes.get('import_size', '')
    cron_schedule = attributes.get('cron_schedule', '')
    if import_step == 'ingestion_workflow_single' or import_step == 'ingestion_workflow_batch':
        import_status = 'STAGING'
        job_id = attributes.get('feed_name', 'cda_feed')
        helper.update_import_status(import_name, import_status, latest_version,
                                    graph_path, job_id, cron_schedule)
        if import_step == 'ingestion_workflow_single':
            # Invoke ingestion workflow to trigger dataflow job
            helper.invoke_spanner_ingestion_workflow(import_name)
    elif import_step == 'import_automation_job' or import_step == 'import_automation_e2e':
        # Invoke batch import job and optionally ingestion workflow to trigger dataflow job
        run_ingestion = True if import_step == 'import_automation_e2e' else False
        helper.invoke_import_automation_workflow(import_name, latest_version,
                                                 import_size, graph_path,
                                                 cron_schedule, run_ingestion)
    else:
        logging.info(f"Skipping import post processing.")

    return 'OK', 200
