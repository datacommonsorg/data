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

import logging
import os
from google.cloud import spanner
from google.cloud.spanner_v1 import Transaction
from google.cloud.spanner_v1.param_types import STRING, TIMESTAMP, Array, INT64
from datetime import datetime, timezone

logging.getLogger().setLevel(logging.INFO)


class SpannerClient:
    """
    Spanner client to handle tasks like acquiring/releasing lock 
    and getting/updating import statuses.
    """
    _LOCK_ID = "global_ingestion_lock"

    def __init__(self, project_id: str, instance_id: str, database_id: str):
        """Initializes a Spanner client and connects to a specific database."""
        spanner_client = spanner.Client(
            project=project_id,
            client_options={'quota_project_id': project_id},
            disable_builtin_metrics=True)
        instance = spanner_client.instance(instance_id)
        database = instance.database(database_id)
        logging.info(f"Successfully initialized database: {database.name}")
        self.database = database

    def acquire_lock(self, workflow_id: str, timeout: int) -> bool:
        """Attempts to acquire the global ingestion lock.

        Args:
            workflow_id: The ID of the workflow attempting to acquire the lock.
            timeout: The duration in seconds after which a lock is considered stale.

        Returns:
            True if the lock was acquired, False otherwise.
        """
        logging.info(f"Attempting to acquire lock for {workflow_id}")

        def _acquire(transaction: Transaction) -> bool:
            sql = "SELECT LockOwner, AcquiredTimestamp FROM IngestionLock WHERE LockID = @lockId"
            params = {"lockId": self._LOCK_ID}
            param_types = {"lockId": STRING}

            current_owner, acquired_at = None, None
            results = transaction.execute_sql(sql, params, param_types)
            for row in results:
                current_owner, acquired_at = row[0], row[1]

            lock_is_available = False
            if current_owner is None:
                lock_is_available = True
            else:
                timeout_threshold = datetime.now(timezone.utc) - acquired_at
                if timeout_threshold.total_seconds() > timeout:
                    logging.info(
                        f"Stale lock found, owned by {current_owner}. Acquiring."
                    )
                    lock_is_available = True
            if lock_is_available:
                update_sql = """
                    UPDATE IngestionLock
                    SET LockOwner = @workflowId, AcquiredTimestamp = PENDING_COMMIT_TIMESTAMP()
                    WHERE LockID = @lockId
                """
                transaction.execute_update(update_sql,
                                           params={
                                               "workflowId": workflow_id,
                                               "lockId": self._LOCK_ID
                                           },
                                           param_types={
                                               "workflowId": STRING,
                                               "lockId": STRING
                                           })
                logging.info(f"Lock successfully acquired by {workflow_id}")
                return True
            else:
                logging.info(f"Lock is currently held by {current_owner}")
                return False

        try:
            return self.database.run_in_transaction(_acquire)
        except Exception as e:
            logging.error(f'Error acquiring lock for {workflow_id}: {e}')
            raise

    def release_lock(self, workflow_id: str) -> bool:
        """Releases the global lock.

        Args:
            workflow_id: The ID of the workflow attempting to release the lock.

        Returns:
            True if the lock was released, False otherwise.
        """
        logging.info(f"Attempting to release lock for {workflow_id}")

        def _release(transaction: Transaction) -> None:
            sql = "SELECT LockOwner, AcquiredTimestamp FROM IngestionLock WHERE LockID = @lockId"
            params = {"lockId": self._LOCK_ID}
            param_types = {"lockId": STRING}

            current_owner = None
            results = transaction.execute_sql(sql, params, param_types)
            for row in results:
                current_owner = row[0]

            if current_owner == workflow_id:
                sql = """
                    UPDATE IngestionLock
                    SET LockOwner = NULL, AcquiredTimestamp = NULL
                    WHERE LockID = @lockId
                """
                transaction.execute_update(sql,
                                           params={"lockId": self._LOCK_ID},
                                           param_types={"lockId": STRING})
                logging.info(f"Lock successfully released by {workflow_id}")
                return True
            else:
                logging.info(f"Lock is currently held by {current_owner}")
                return False

        try:
            return self.database.run_in_transaction(_release)
        except Exception as e:
            logging.error(f'Error releasing lock for {workflow_id}: {e}')
            raise

    def get_import_info(self, import_list: list) -> list:
        """Get the details of imports to ingest.

        If import_list is empty, return info for ready imports.
        If import_list is not empty, return info for the imports in the list irrespective of status.

        Args:
            import_list: A list of import names to fetch details for.

        Returns:
            A list of dictionaries, where each dictionary contains 'importName', 'latestVersion', and 'graphPath'.
        """
        pending_imports = []
        logging.info(f"Fetching imports from import list {import_list}.")

        params = {}
        param_types = {}
        if import_list:
            sql = "SELECT ImportName, LatestVersion, GraphPath FROM ImportStatus WHERE ImportName IN UNNEST(@importNames)"
            params = {"importNames": import_list}
            param_types = {"importNames": Array(STRING)}
        else:
            sql = "SELECT ImportName, LatestVersion, GraphPath FROM ImportStatus WHERE State = 'STAGING'"

        # Use a read-only snapshot for this query
        try:
            with self.database.snapshot() as snapshot:
                results = snapshot.execute_sql(sql,
                                               params=params,
                                               param_types=param_types)
                for row in results:
                    import_json = {}
                    import_json['importName'] = row[0]
                    import_json['latestVersion'] = os.path.basename(row[1])
                    import_json[
                        'graphPath'] = f"{row[1].rstrip('/')}/{row[2].lstrip('/')}"
                    pending_imports.append(import_json)

            logging.info(f"Found {len(pending_imports)} import jobs.")
            return pending_imports
        except Exception as e:
            logging.error(f'Error getting import list: {e}')
            raise

    def update_ingestion_status(self, import_names: list, workflow_id: str,
                                status: str):
        """Updates the ImportStatus table.

        Args:
            import_names: List of import names.
            workflow_id: The ID of the workflow.
            status: The status of the ingestion.
        """
        if not import_names:
            return

        logging.info(f"Updated ingestion status for {import_names}")

        def _update(transaction: Transaction):
            update_sql = "UPDATE ImportStatus SET State = @importStatus, WorkflowId = @workflowId, StatusUpdateTimestamp = PENDING_COMMIT_TIMESTAMP() WHERE ImportName IN UNNEST(@importNames)"
            transaction.execute_update(update_sql,
                                       params={
                                           "importNames": import_names,
                                           "workflowId": workflow_id,
                                           "importStatus": status
                                       },
                                       param_types={
                                           "importNames": Array(STRING),
                                           "workflowId": STRING,
                                           "importStatus": STRING
                                       })

        try:
            self.database.run_in_transaction(_update)
            logging.info(f"Marked {len(import_names)} import jobs as {status}.")
        except Exception as e:
            logging.error(f'Error updating ImportStatus table: {e}')
            raise

    def update_ingestion_history(self, workflow_id: str, job_id: str,
                                 ingested_imports: list, metrics: dict):
        """Updates the IngestionHistory table.

        Args:
            workflow_id: The ID of the workflow.
            job_id: The Dataflow job ID.
            ingested_imports: List of ingested import names.
            metrics: A dictionary containing metrics about the ingestion.
        """

        logging.info(
            f"Updating IngestionHistory table for workflow {workflow_id}")

        def _insert(transaction: Transaction):
            columns = [
                "CompletionTimestamp", "IngestionFailure",
                "WorkflowExecutionID", "DataflowJobId", "IngestedImports",
                "ExecutionTime", "NodeCount", "EdgeCount", "ObservationCount"
            ]
            values = [[
                spanner.COMMIT_TIMESTAMP,
                self.check_failed_imports(), workflow_id, job_id,
                ingested_imports, metrics['execution_time'],
                metrics['node_count'], metrics['edge_count'],
                metrics['obs_count']
            ]]
            transaction.insert_or_update(table="IngestionHistory",
                                         columns=columns,
                                         values=values)

        try:
            self.database.run_in_transaction(_insert)
            logging.info(
                f"Updated IngestionHistory table for workflow {workflow_id}")
        except Exception as e:
            logging.error(f'Error updating IngestionHistory table: {e}')
            raise

    def update_import_version_history(self, import_list_json: list,
                                      workflow_id: str):
        """Updates the ImportVersionHistory table.

        Args:
            import_list_json: A list of dictionaries containing import details.
            workflow_id: The ID of the workflow.
        """
        if not import_list_json:
            return

        logging.info(
            f"Updating ImportVersionHistory table for workflow {workflow_id}")

        def _insert(transaction: Transaction):
            version_history_columns = [
                "ImportName", "Version", "UpdateTimestamp", "Comment"
            ]
            version_history_values = []
            for import_json in import_list_json:
                version_history_values.append([
                    import_json['importName'], import_json['latestVersion'],
                    spanner.COMMIT_TIMESTAMP,
                    "ingestion-workflow:" + workflow_id
                ])

            if version_history_values:
                transaction.insert(table="ImportVersionHistory",
                                   columns=version_history_columns,
                                   values=version_history_values)

        try:
            self.database.run_in_transaction(_insert)
            logging.info(
                f"Updated ImportVersionHistory table for workflow {workflow_id}"
            )
        except Exception as e:
            logging.error(f'Error updating ImportVersionHistory table: {e}')
            raise

    def check_failed_imports(self) -> bool:
        """Checks if there are any failed imports."""
        try:
            with self.database.snapshot() as snapshot:
                results = snapshot.execute_sql(
                    "SELECT 1 FROM ImportStatus WHERE State = 'PENDING' LIMIT 1"
                )
                return any(results)
        except Exception as e:
            logging.error(f'Error checking for pending imports: {e}')
            return True

    def update_import_status(self, params: dict):
        """Updates the status for the specified import job.

        Args:
            params: A dictionary containing import parameters.
        """
        import_name = params['import_name']
        job_id = params['job_id']
        execution_time = params['execution_time']
        data_volume = params['data_volume']
        status = params['status']
        latest_version = params['latest_version']
        next_refresh = datetime.fromisoformat(params['next_refresh'])
        graph_path = params['graph_path']
        logging.info(f"Updating import status in spanner {params}")

        def _record(transaction: Transaction):
            columns = [
                "ImportName", "State", "JobId", "ExecutionTime", "DataVolume",
                "NextRefreshTimestamp", "LatestVersion", "GraphPath",
                "StatusUpdateTimestamp"
            ]

            row_values = [
                import_name, status, job_id, execution_time, data_volume,
                next_refresh, latest_version, graph_path,
                spanner.COMMIT_TIMESTAMP
            ]

            if status == 'STAGING':
                columns.append("DataImportTimestamp")
                row_values.append(spanner.COMMIT_TIMESTAMP)

            transaction.insert_or_update(table="ImportStatus",
                                         columns=columns,
                                         values=[row_values])

            logging.info(f"Marked {import_name} as {status}.")

        try:
            self.database.run_in_transaction(_record)
        except Exception as e:
            logging.error(
                f'Error updating import status for {import_name}: {e}')
            raise

    def update_version_history(self, import_name: str, version: str,
                               comment: str):
        """Updates the version history table.

        Args:
            import_name: The name of the import.
            version: The version string.
            comment: The comment for the update.
        """
        import_name = import_name.split(':')[-1]
        logging.info(f"Updating version history for {import_name} to {version}")

        def _record(transaction: Transaction):
            columns = ["ImportName", "Version", "UpdateTimestamp", "Comment"]
            values = [[import_name, version, spanner.COMMIT_TIMESTAMP, comment]]
            transaction.insert(table="ImportVersionHistory",
                               columns=columns,
                               values=values)
            logging.info(f"Added version history entry for {import_name}")

        try:
            self.database.run_in_transaction(_record)
        except Exception as e:
            logging.error(
                f'Error updating version history for {import_name}: {e}')
            raise
