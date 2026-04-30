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
from google.cloud.spanner_admin_database_v1 import DatabaseAdminClient
from google.cloud.spanner_admin_database_v1.types import UpdateDatabaseDdlRequest
from google.cloud.spanner_v1 import Transaction
from google.cloud.spanner_v1.param_types import STRING, TIMESTAMP, Array, INT64
from datetime import datetime, timezone
from jinja2 import Template

logging.getLogger().setLevel(logging.INFO)


class SpannerClient:
    """
    Spanner client to handle tasks like acquiring/releasing lock 
    and getting/updating import statuses.
    """
    _LOCK_ID = "global_ingestion_lock"
    _EMBEDDING_MODEL_PATH = "projects/{project}/locations/{location}/publishers/google/models/{model}"

    def __init__(self,
                 project_id: str,
                 instance_id: str,
                 database_id: str,
                 graph_database_id: str = None,
                 location: str = None,
                 model_id: str = None):
        """Initializes a Spanner client and connects to a specific database."""
        spanner_client = spanner.Client(
            project=project_id,
            client_options={'quota_project_id': project_id},
            disable_builtin_metrics=True)
        instance = spanner_client.instance(instance_id)
        database = instance.database(database_id)
        logging.info(f"Successfully initialized database: {database.name}")
        self.database = database
        self.graph_database = database
        if graph_database_id:
            self.graph_database = instance.database(graph_database_id)
            logging.info(
                f"Successfully initialized graph database: {self.graph_database.name}"
            )
        self.project_id = project_id
        self.location = location
        self.model_id = model_id

    def _get_embeddings_endpoint(self) -> str:
        """Returns the parameterized embedding model endpoint."""
        return self._EMBEDDING_MODEL_PATH.format(project=self.project_id,
                                                 location=self.location or
                                                 "us-central1",
                                                 model=self.model_id or
                                                 "text-embedding-005")

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

            row_found = False
            results = transaction.execute_sql(sql, params, param_types)
            for row in results:
                row_found = True
                current_owner, acquired_at = row[0], row[1]

            lock_is_available = False
            if not row_found:
                lock_is_available = True
            elif current_owner is None:
                lock_is_available = True
            else:
                timeout_threshold = datetime.now(timezone.utc) - acquired_at
                if timeout_threshold.total_seconds() > timeout:
                    logging.info(
                        f"Stale lock found, owned by {current_owner}. Acquiring."
                    )
                    lock_is_available = True

            if lock_is_available:
                if not row_found:
                    sql_statement = """
                        INSERT INTO IngestionLock (LockID, LockOwner, AcquiredTimestamp)
                        VALUES (@lockId, @workflowId, PENDING_COMMIT_TIMESTAMP())
                    """
                    log_msg = f"Lock successfully acquired by {workflow_id} (new row created)"
                else:
                    sql_statement = """
                        UPDATE IngestionLock
                        SET LockOwner = @workflowId, AcquiredTimestamp = PENDING_COMMIT_TIMESTAMP()
                        WHERE LockID = @lockId
                    """
                    log_msg = f"Lock successfully acquired by {workflow_id} (existing row updated)"

                transaction.execute_update(sql_statement,
                                           params={
                                               "workflowId": workflow_id,
                                               "lockId": self._LOCK_ID
                                           },
                                           param_types={
                                               "workflowId": STRING,
                                               "lockId": STRING
                                           })
                logging.info(log_msg)
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
        If import_list is not empty, return info for the imports in the list that are in 'STAGING' status.

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
            sql = "SELECT ImportName, LatestVersion, GraphPath FROM ImportStatus WHERE State = 'STAGING' AND ImportName IN UNNEST(@importNames)"
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
            # TODO: remvoe dual writes after switching to the prod setup.
            if self.graph_database and self.graph_database.name != self.database.name:
                self.graph_database.run_in_transaction(_insert)
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

    def initialize_database(self, enable_embeddings=False):
        """Initializes the database by creating all required tables and proto bundles."""
        logging.info("Initializing database...")

        query = """
            SELECT 'table' as type, table_name as name FROM information_schema.tables WHERE table_schema = ''
            UNION ALL
            SELECT 'index' as type, index_name as name FROM information_schema.indexes WHERE table_schema = '' AND table_name = 'NodeEmbedding'
            UNION ALL
            SELECT 'model' as type, model_name as name FROM information_schema.models WHERE model_schema = ''
        """

        existing_tables = []
        existing_indexes = []
        existing_models = []

        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query)
            for row in results:
                if len(row) < 2:
                    logging.warning(f"Invalid row from query: {row}")
                    continue
                obj_type = row[0]
                obj_name = row[1]
                if obj_type == 'table':
                    existing_tables.append(obj_name)
                elif obj_type == 'index':
                    existing_indexes.append(obj_name)
                elif obj_type == 'model':
                    existing_models.append(obj_name)

        logging.info(f"Existing tables: {existing_tables}")
        logging.info(f"Existing indexes: {existing_indexes}")
        logging.info(f"Existing models: {existing_models}")

        required_tables = [
            "Node", "Edge", "Observation", "ImportStatus", "IngestionHistory",
            "ImportVersionHistory", "IngestionLock"
        ]
        required_indexes = []
        required_models = []

        if enable_embeddings:
            required_tables.append("NodeEmbedding")
            required_indexes.append("NodeEmbeddingIndex")
            required_models.append("NodeEmbeddingModel")

        missing_tables = [
            t for t in required_tables if t not in existing_tables
        ]
        missing_indexes = [
            i for i in required_indexes if i not in existing_indexes
        ]
        missing_models = [
            m for m in required_models if m not in existing_models
        ]

        total_required = len(required_tables) + len(required_indexes) + len(
            required_models)
        total_missing = len(missing_tables) + len(missing_indexes) + len(
            missing_models)

        if total_missing == 0:
            logging.info("Database is properly initialized.")
            return

        if total_missing < total_required:
            raise RuntimeError(
                f"Database inconsistent state. Missing tables: {missing_tables}, missing indexes: {missing_indexes}, missing models: {missing_models}. Please clean up manually."
            )

        logging.info("Creating all tables and proto bundles...")

        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        logging.info(f"Reading schema from {schema_path}")
        try:
            with open(schema_path, 'r') as f:
                schema_content = f.read()

            ddl_statements = [
                s.strip() for s in schema_content.split(';') if s.strip()
            ]

            if enable_embeddings:
                embeddings_endpoint = self._get_embeddings_endpoint()
                embedding_schema_path = os.path.join(os.path.dirname(__file__),
                                                     'embedding_schema.sql')
                logging.info(
                    f"Reading embedding schema from {embedding_schema_path}")
                with open(embedding_schema_path, 'r') as f:
                    embedding_schema_content = f.read()
                embedding_schema_content = Template(
                    embedding_schema_content).render(
                        embeddings_endpoint=embeddings_endpoint)
                embedding_ddl_statements = [
                    s.strip()
                    for s in embedding_schema_content.split(';')
                    if s.strip()
                ]
                ddl_statements.extend(embedding_ddl_statements)
        except Exception as e:
            logging.error(f"Failed to read schema file: {e}")
            raise

        proto_path = os.path.join(os.path.dirname(__file__), 'storage.pb')
        logging.info(f"Reading proto descriptors from {proto_path}")
        try:
            with open(proto_path, 'rb') as f:
                proto_descriptors_bytes = f.read()
        except Exception as e:
            logging.error(f"Failed to read proto descriptors file: {e}")
            raise

        database_path = self.database.name
        logging.info(f"Updating DDL for {database_path} with protos")

        try:
            admin_client = DatabaseAdminClient()
            request = UpdateDatabaseDdlRequest(
                database=database_path,
                statements=ddl_statements,
                proto_descriptors=proto_descriptors_bytes)
            operation = admin_client.update_database_ddl(request=request)
            operation.result()
            logging.info("Database initialized successfully with protos.")
        except Exception as e:
            logging.error(f"Failed to update DDL with protos: {e}")
            raise
