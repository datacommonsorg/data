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
"""BigQuery client for import helper targeting ImportHistory table and ImportSummary view."""

from datetime import datetime, timezone
import logging
import os
import re
from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery

logging.getLogger().setLevel(logging.INFO)

_IDENTIFIER_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_identifier(value: str, name: str) -> str:
    if not value or not _IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid BigQuery identifier for {name}: {value!r}")
    return value


def _normalize_timestamp(value: str | datetime | None) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return str(value)


class BigQueryClient:
    """Manages import state in BigQuery using an append-only ImportHistory table and ImportSummary view."""

    def __init__(self,
                 project_id: str,
                 dataset_id: str,
                 history_table: str = "ImportHistory",
                 summary_view: str = "ImportSummary"):
        self.project_id = _validate_identifier(project_id, "project_id")
        self.dataset_id = _validate_identifier(dataset_id, "dataset_id")
        self.history_table = _validate_identifier(history_table,
                                                  "history_table")
        self.summary_view = _validate_identifier(summary_view, "summary_view")

        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"
        self.history_table_id = f"{self.dataset_ref}.{self.history_table}"
        self.summary_view_id = f"{self.dataset_ref}.{self.summary_view}"

        self.client = bigquery.Client(project=self.project_id)

    def _insert_row(self, row: dict):
        """Streams a single event row into ImportHistory, initializing schema if missing."""
        try:
            errors = self.client.insert_rows_json(self.history_table_id, [row])
        except gcp_exceptions.NotFound:
            logging.info(
                f"Table {self.history_table_id} not found; initializing BigQuery schema..."
            )
            self.initialize_database()
            errors = self.client.insert_rows_json(self.history_table_id, [row])

        if errors:
            logging.error(
                f"BigQuery insert_rows_json errors for {self.history_table_id}: {errors}"
            )
            raise RuntimeError(
                f"Failed to insert row into {self.history_table_id}: {errors}")

    def update_import_summary(self, params: dict, comment: str | None = None):
        """Records the import status event in BigQuery (updating ImportHistory and ImportSummary view).

        Args:
            params: A dictionary containing import parameters.
            comment: Optional comment describing the status/version transition.
        """
        import_name = params["import_name"].split(":")[-1]
        status = params.get("status") or ""
        job_id = params.get("job_id") or params.get("workflow_id") or None
        execution_time = params.get("execution_time")
        data_volume = params.get("data_volume")
        latest_version = params.get("latest_version") or None
        next_refresh = _normalize_timestamp(params.get("next_refresh"))
        resolved_comment = comment if comment is not None else params.get(
            "comment")

        now_iso = datetime.now(timezone.utc).isoformat()

        row = {
            "ImportName": import_name,
            "Version": latest_version,
            "Status": status,
            "JobId": job_id,
            "ExecutionTime": execution_time,
            "DataVolume": data_volume,
            "UpdateTimestamp": now_iso,
            "NextRefreshTimestamp": next_refresh,
            "Comment": resolved_comment,
        }

        logging.info(f"Recording import state in BigQuery: {row}")
        try:
            self._insert_row(row)
            logging.info(
                f"Marked {import_name} as {status} in BigQuery ({self.history_table_id})."
            )
        except Exception as e:
            logging.error(
                f"Error updating import state in BigQuery for {import_name}: {e}"
            )
            raise

    def update_import_history(self,
                              import_name: str,
                              version: str,
                              comment: str,
                              workflow_id: str | None = None,
                              job_id: str | None = None,
                              status: str | None = None,
                              execution_time: int | None = None,
                              data_volume: int | None = None,
                              next_refresh: str | None = None):
        """Records an entry in ImportHistory."""
        params = {
            "import_name": import_name,
            "latest_version": version,
            "comment": comment,
            "job_id": job_id or workflow_id,
            "status": status or "STAGING",
            "execution_time": execution_time,
            "data_volume": data_volume,
            "next_refresh": next_refresh,
        }
        self.update_import_summary(params, comment=comment)

    def get_import_history(self,
                           import_name: str,
                           limit: int = 10,
                           status: str = "SUCCESS") -> list[str]:
        """Queries ImportHistory for an import's version history."""
        short_name = import_name.split(":")[-1]
        sql_history = f"""
            SELECT Version
            FROM `{self.history_table_id}`
            WHERE ImportName = @importName AND Status = @status
            ORDER BY UpdateTimestamp DESC
            LIMIT @limit
        """
        job_config = bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("importName", "STRING", short_name),
            bigquery.ScalarQueryParameter("status", "STRING", status),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ])
        try:
            results = self.client.query(sql_history,
                                        job_config=job_config).result()
            return [row.Version for row in results if row.Version is not None]
        except Exception as e:
            logging.error(
                f"Error fetching version history from BigQuery for import '{short_name}': {e}"
            )
            return []

    def initialize_database(self):
        """Initializes the BigQuery dataset, ImportHistory table, and ImportSummary view."""
        logging.info(
            f"Initializing BigQuery dataset {self.dataset_ref}, table {self.history_table_id}, and view {self.summary_view_id}..."
        )
        dataset = bigquery.Dataset(self.dataset_ref)
        self.client.create_dataset(dataset, exists_ok=True)

        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r") as f:
            schema_content = f.read()

        rendered_schema = schema_content.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id,
            history_table=self.history_table,
            summary_view=self.summary_view,
        )

        for raw_stmt in rendered_schema.split(";"):
            lines = [
                line for line in raw_stmt.splitlines()
                if not line.strip().startswith("--")
            ]
            cleaned = "\n".join(lines).strip()
            if cleaned:
                self.client.query(cleaned).result()

        logging.info(
            f"Successfully initialized BigQuery table {self.history_table_id} and view {self.summary_view_id}."
        )
