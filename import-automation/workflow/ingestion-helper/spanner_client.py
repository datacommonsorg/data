import logging
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
            project=project_id, client_options={'quota_project_id': project_id})
        instance = spanner_client.instance(instance_id)
        database = instance.database(database_id)
        logging.info(f"Successfully initialized database: {database.name}")
        self.database = database

    def acquire_lock(self, workflow_id: str, timeout: int) -> bool:
        """Attempts to acquire the global ingestion lock."""
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

        return self.database.run_in_transaction(_acquire)

    def release_lock(self, workflow_id: str) -> bool:
        """Releases the global lock."""
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

        return self.database.run_in_transaction(_release)

    def get_import_list(self, import_list: list) -> list:
        """Get the list of imports ready to ingest."""
        pending_imports = []
        sql = "SELECT ImportName, LatestVersion FROM ImportStatus WHERE State = 'READY'"
        # Use a read-only snapshot for this query
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(sql)
            for row in results:
                if not import_list or row[0] in import_list:
                    import_json = {}
                    import_json['importName'] = row[0]
                    import_json['latestVersion'] = row[1]
                    pending_imports.append(import_json)

        logging.info(f"Found {len(pending_imports)} import jobs as READY.")
        return pending_imports

    def update_ingestion_status(self, import_list_json: list, workflow_id: str,
                                job_id: str, metrics: dict):
        """Marks the ingested imports as DONE and records the ingestion event."""
        logging.info(f"Marking import status for {import_list_json} as DONE.")

        succeeded_imports = []
        for import_json in import_list_json:
            succeeded_imports.append(import_json['importName'])

        def _record(transaction: Transaction):
            # 1. Update the ImportStatus table
            if succeeded_imports:
                update_sql = "UPDATE ImportStatus SET State = 'DONE', WorkflowId = @workflowId, StatusUpdateTimestamp = PENDING_COMMIT_TIMESTAMP() WHERE ImportName IN UNNEST(@importNames)"
                updated_rows = transaction.execute_update(
                    update_sql,
                    params={
                        "importNames": succeeded_imports,
                        "workflowId": workflow_id
                    },
                    param_types={
                        "importNames": Array(STRING),
                        "workflowId": STRING
                    })
                logging.info(f"Marked {updated_rows} import jobs as DONE.")

            # 2. Insert into the IngestionHistory table
            columns = [
                "CompletionTimestamp", "WorkflowExecutionID", "DataflowJobId",
                "IngestedImports", "NodeCount", "EdgeCount", "ObservationCount"
            ]
            values = [[
                spanner.COMMIT_TIMESTAMP, workflow_id, job_id,
                succeeded_imports, metrics['node_count'], metrics['edge_count'],
                metrics['obs_count']
            ]]
            transaction.insert_or_update(table="IngestionHistory",
                                         columns=columns,
                                         values=values)
            logging.info(
                f"Updated ingestion history table for workflow {workflow_id}")

        self.database.run_in_transaction(_record)

    def update_import_status(self, params: dict):
        """Updates the status for the specified import job."""
        import_name = params['import_name']
        job_id = params['job_id']
        duration = params['duration']
        data = params['data']
        status = params['status']
        version = params['version']
        next_refresh = params['next_refresh']
        logging.info(f"Updating import status for {import_name} to {status}")

        def _record(transaction: Transaction):
            columns = [
                "ImportName", "State", "JobId", "ExecutionTime", "DataVolume",
                "NextRefreshTimestamp", "LatestVersion", "StatusUpdateTimestamp"
            ]

            row_values = [
                import_name, status, job_id, duration, data, next_refresh,
                version, spanner.COMMIT_TIMESTAMP
            ]
            logging.info(row_values)

            if status == 'READY':
                columns.append("DataImportTimestamp")
                row_values.append(spanner.COMMIT_TIMESTAMP)

            transaction.insert_or_update(table="ImportStatus",
                                         columns=columns,
                                         values=[row_values])

            logging.info(f"Marked {import_name} as {status}.")

        self.database.run_in_transaction(_record)
