import logging
from google.cloud import spanner
from google.cloud.spanner_v1 import Transaction
from google.cloud.spanner_v1.param_types import STRING, TIMESTAMP, Array
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

    def get_import_status(self) -> list:
        """Get the list of pending imports to ingest."""
        pending_imports = []
        sql = "SELECT ImportName, Latestversion FROM ImportStatus WHERE State = 'PENDING'"
        # Use a read-only snapshot for this query
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(sql)
            for row in results:
                import_json = {}
                import_json['importName'] = row[0]
                import_json['latestVersion'] = row[1]
                pending_imports.append(import_json)

        logging.info(f"Found {len(pending_imports)} import jobs as PENDING.")
        return pending_imports

    def update_import_status(self, workflow_id: str, import_list: list) -> None:
        """Atomically marks pending imports as DONE and records the ingestion event."""
        succeeded_imports = []
        if not import_list:
            return
        for import_json in import_list:
            succeeded_imports.append(import_json['importName'])

        def _record(transaction: Transaction) -> None:
            # 1. Update the ImportStatus table
            update_sql = "UPDATE ImportStatus SET State = 'DONE', JobId = @workflowId, UpdateTimestamp = PENDING_COMMIT_TIMESTAMP() WHERE ImportName IN UNNEST(@importNames)"
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
            insert_sql = """
                INSERT INTO IngestionHistory (CompletionTimestamp, WorkflowExecutionID, IngestedImports)
                VALUES (PENDING_COMMIT_TIMESTAMP(), @workflowId, @importNames)
            """
            transaction.execute_update(insert_sql,
                                       params={
                                           "workflowId": workflow_id,
                                           "importNames": succeeded_imports
                                       },
                                       param_types={
                                           "workflowId": STRING,
                                           "importNames": Array(STRING)
                                       })
            logging.info(
                f"Updated ingestion history table for workflow {workflow_id}")

        self.database.run_in_transaction(_record)
