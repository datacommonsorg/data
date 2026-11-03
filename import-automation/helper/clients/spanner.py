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
"""Spanner client for import helper targeting ImportSummary and ImportHistory."""

from datetime import datetime
import logging
import os
from google.cloud import spanner
from google.cloud.spanner_admin_database_v1 import DatabaseAdminClient
from google.cloud.spanner_admin_database_v1.types import UpdateDatabaseDdlRequest
from google.cloud.spanner_v1.param_types import Array, INT64, STRING
from google.cloud.spanner_v1.transaction import Transaction

logging.getLogger().setLevel(logging.INFO)


class SpannerClient:

    def __init__(self, project_id: str, instance_id: str, database_id: str):
        self.project_id = project_id
        self.instance_id = instance_id
        self.database_id = database_id

        self.client = spanner.Client(project=project_id)
        self.instance = self.client.instance(instance_id)
        self.database = self.instance.database(database_id)

    def update_import_summary(self, params: dict):
        """Updates the status for the specified import job in ImportSummary.

        Args:
            params: A dictionary containing import parameters.
        """
        import_name = params['import_name'].split(':')[-1]
        job_id = params.get('job_id')
        workflow_id = params.get('workflow_id')
        execution_time = params.get('execution_time')
        data_volume = params.get('data_volume')
        status = params.get('status')
        latest_version = params.get('latest_version')
        next_refresh_str = params.get('next_refresh')
        next_refresh = datetime.fromisoformat(next_refresh_str) if next_refresh_str else None
        graph_path = params.get('graph_path')
        logging.info(f"Updating import summary in Spanner: {params}")

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

            if workflow_id:
                columns.append("WorkflowId")
                row_values.append(workflow_id)

            if status == 'STAGING':
                columns.append("DataImportTimestamp")
                row_values.append(spanner.COMMIT_TIMESTAMP)

            transaction.insert_or_update(table="ImportSummary",
                                         columns=columns,
                                         values=[row_values])

            logging.info(f"Marked {import_name} as {status} in ImportSummary.")

        try:
            self.database.run_in_transaction(_record)
        except Exception as e:
            logging.error(f'Error updating ImportSummary for {import_name}: {e}')
            raise

    def update_import_history(self,
                              import_name: str,
                              version: str,
                              comment: str,
                              workflow_id: str | None = None,
                              job_id: str | None = None,
                              status: str | None = None,
                              execution_time: int | None = None,
                              data_volume: int | None = None):
        """Records an entry in ImportHistory.

        Args:
            import_name: The name of the import.
            version: The version string.
            comment: The comment for the update.
            workflow_id: The ID of the workflow execution if applicable.
            job_id: The batch job ID if applicable.
            status: The status of the import execution.
            execution_time: Optional execution time in seconds.
            data_volume: Optional data volume in bytes.
        """
        import_name = import_name.split(':')[-1]
        logging.info(f"Updating ImportHistory for {import_name} to version {version}")

        def _record(transaction: Transaction):
            columns = [
                "ImportName", "Version", "UpdateTimestamp",
                "WorkflowExecutionID", "JobId", "Status", "ExecutionTime",
                "DataVolume", "Comment"
            ]
            values = [[
                import_name, version, spanner.COMMIT_TIMESTAMP, workflow_id,
                job_id, status, execution_time, data_volume, comment
            ]]
            transaction.insert(table="ImportHistory",
                               columns=columns,
                               values=values)
            logging.info(f"Added ImportHistory entry for {import_name}")

        try:
            self.database.run_in_transaction(_record)
        except Exception as e:
            logging.error(f'Error updating ImportHistory for {import_name}: {e}')
            raise

    def get_import_history(self,
                           import_name: str,
                           limit: int = 10,
                           status: str = "SUCCESS") -> list[str]:
        """Queries ImportHistory for an import's version history."""
        short_name = import_name.split(':')[-1]

        def _query(transaction: Transaction):
            sql_history = """
                SELECT Version FROM ImportHistory
                WHERE ImportName = @importName AND Status = @status
                ORDER BY UpdateTimestamp DESC
                LIMIT @limit
            """
            results = transaction.execute_sql(
                sql_history,
                params={
                    'importName': short_name,
                    'limit': limit,
                    'status': status
                },
                param_types={
                    'importName': STRING,
                    'limit': INT64,
                    'status': STRING
                })
            return [row[0] for row in results]

        try:
            return self.database.run_in_transaction(_query)
        except Exception as e:
            logging.error(f"Error fetching version history for import '{short_name}': {e}")
            return []

    def initialize_database(self):
        """Initializes the database by creating ImportSummary and ImportHistory tables if missing."""
        logging.info("Checking database for ImportSummary and ImportHistory tables...")
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = ''"
        existing_tables = []
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(query)
            for row in results:
                existing_tables.append(row[0])

        required_tables = ["ImportSummary", "ImportHistory"]
        missing_tables = [t for t in required_tables if t not in existing_tables]

        if not missing_tables:
            logging.info("ImportSummary and ImportHistory tables already exist.")
            return

        logging.info(f"Missing tables: {missing_tables}. Initializing schema from schema.sql...")
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_content = f.read()

        cleaned_statements = []
        for raw_stmt in schema_content.split(';'):
            lines = [l for l in raw_stmt.splitlines() if not l.strip().startswith('--')]
            cleaned = '\n'.join(lines).strip()
            if cleaned:
                cleaned_statements.append(cleaned)

        statements_to_run = []
        for stmt in cleaned_statements:
            for t in missing_tables:
                if f"CREATE TABLE {t}" in stmt:
                    statements_to_run.append(stmt)

        if statements_to_run:
            admin_client = DatabaseAdminClient()
            request = UpdateDatabaseDdlRequest(
                database=self.database.name,
                statements=statements_to_run
            )
            operation = admin_client.update_database_ddl(request=request)
            operation.result()
            logging.info(f"Successfully created tables: {missing_tables}")
