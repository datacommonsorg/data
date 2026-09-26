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

import base64
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from google.api_core import exceptions as gcp_exceptions
from app import app
from clients.bigquery import BigQueryClient as HelperBigQueryClient
import config
from dependencies import get_bigquery_client, get_storage_client
from utils import imports as import_utils

client = TestClient(app)


class AppTest(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides.clear()

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_update_import_status_success(self):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        payload = {
            "imports": [
                {
                    "importName": "import1",
                    "status": "STAGING",
                    "latestVersion": "gs://bucket/import1/version1/graph",
                    "graphPath": "graph"
                },
                {
                    "importName": "import2",
                    "status": "FAILURE",
                    "latestVersion": "gs://bucket/import2/version2/graph"
                }
            ],
            "jobId": "job123",
            "executionTime": 120,
            "dataVolume": 1024
        }

        response = client.post("/imports/status", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        # Storage should only be updated for the STAGING import
        mock_storage.update_version_file.assert_any_call("import1", "graph", is_staging=True)
        mock_storage.update_version_file.assert_any_call("import1", "graph", is_staging=False)
        mock_storage.update_provenance_file.assert_called_once_with("import1", "graph")
        self.assertEqual(mock_storage.update_import_summary.call_count, 1)

        # BigQuery update_import_summary should be called once per import (updating ImportHistory & ImportSummary view)
        self.assertEqual(mock_bigquery.update_import_summary.call_count, 2)
        first_call = mock_bigquery.update_import_summary.call_args_list[0]
        second_call = mock_bigquery.update_import_summary.call_args_list[1]
        self.assertEqual(first_call.kwargs.get("comment"), "import-workflow:job123")
        self.assertEqual(second_call.kwargs.get("comment"), "import-failure:job123")

    def test_update_import_version_success(self):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        mock_storage.get_import_version.side_effect = lambda name, is_staging=False: f"ver_{name}"
        mock_storage.get_import_summary.side_effect = lambda name, version: {
            "importName": name,
            "status": "STAGING",
            "latestVersion": f"gs://bucket/{name}/{version}.csv"
        }

        payload = {
            "imports": ["import1", "import2"],
            "version": "STAGING",
            "comment": "release-comment",
            "override": False
        }

        response = client.post("/imports/version", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")
        self.assertIn("Import: import1 Version: ver_import1 Status: STAGING", response.json()["message"])

        self.assertEqual(mock_storage.update_provenance_file.call_count, 2)
        self.assertEqual(mock_storage.update_version_file.call_count, 2)
        self.assertEqual(mock_bigquery.update_import_summary.call_count, 2)

    @patch('routes.imports.import_utils.get_caller_identity')
    def test_update_import_version_override(self, mock_get_caller):
        mock_get_caller.return_value = "tester@google.com"
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        mock_storage.get_import_version.side_effect = lambda name, is_staging=False: f"ver_{name}"
        mock_storage.get_import_summary.side_effect = lambda name, version: {
            "importName": name,
            "status": "NOT_STAGING",
            "latestVersion": f"gs://bucket/{name}/{version}.csv"
        }

        payload = {
            "imports": ["import1"],
            "version": "STAGING",
            "comment": "release-comment",
            "override": True
        }

        response = client.post("/imports/version", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        self.assertEqual(mock_bigquery.update_import_summary.call_count, 1)
        called_params, called_kwargs = mock_bigquery.update_import_summary.call_args
        self.assertEqual(called_params[0]["import_name"], "import1")
        self.assertEqual(called_params[0]["status"], "STAGING")
        self.assertEqual(called_params[0]["latest_version"], "gs://bucket/import1/ver_import1.csv")
        self.assertEqual(called_kwargs.get("comment"), "version-override:tester@google.com release-comment")

    @patch('routes.events.import_utils.invoke_import_automation_workflow')
    @patch('routes.events.import_utils.check_duplicate', return_value=False)
    @patch('routes.events.config.PROJECT_ID', 'test-project')
    @patch('routes.events.config.LOCATION', 'us-central1')
    def test_handle_feed_event_spanner_ingestion(self, mock_check_dup, mock_invoke):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        notification = {
            "attributes": {
                "transfer_status": "TRANSFER_COMPLETED",
                "import_name": "scripts/us_fed:Rates",
                "import_version": "2026-09-01",
                "post_process": "spanner_ingestion_workflow",
                "graph_path": "/**/*.mcf*"
            },
            "messageId": "msg-123",
            "data": base64.b64encode(b'{"test": "data"}').decode('utf-8')
        }

        response = client.post("/imports/feed", json={"message": notification})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        mock_invoke.assert_called_once_with(
            project_id='test-project',
            location='us-central1',
            workflow_id=config.IMPORT_AUTOMATION_WORKFLOW_ID,
            import_name="scripts/us_fed:Rates",
            latest_version="2026-09-01",
            import_size="small",
            graph_path="/**/*.mcf*",
            cron_schedule="",
            skip_import_job=True,
            skip_staging_ingestion=None,
            skip_prod_ingestion=None,
        )
        self.assertEqual(mock_bigquery.update_import_summary.call_count, 1)

    @patch('routes.events.import_utils.invoke_import_automation_workflow')
    @patch('routes.events.import_utils.check_duplicate', return_value=False)
    @patch('routes.events.config.PROJECT_ID', 'test-project')
    @patch('routes.events.config.LOCATION', 'us-central1')
    def test_handle_feed_event_import_automation(self, mock_check_dup, mock_invoke):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        notification = {
            "attributes": {
                "transfer_status": "TRANSFER_COMPLETED",
                "import_name": "scripts/us_fed:Rates",
                "import_version": "2026-09-01",
                "post_process": "import_automation_workflow",
                "graph_path": "/**/*.mcf*",
                "import_size": "medium"
            },
            "messageId": "msg-456",
            "data": base64.b64encode(b'{"test": "data"}').decode('utf-8')
        }

        response = client.post("/imports/feed", json={"message": notification})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        mock_invoke.assert_called_once_with(
            project_id='test-project',
            location='us-central1',
            workflow_id=config.IMPORT_AUTOMATION_WORKFLOW_ID,
            import_name="scripts/us_fed:Rates",
            latest_version="2026-09-01",
            import_size="medium",
            graph_path="/**/*.mcf*",
            cron_schedule="",
            skip_import_job=False,
            skip_staging_ingestion=None,
            skip_prod_ingestion=None,
        )

    @patch('routes.events.import_utils.invoke_import_automation_airflow')
    @patch('routes.events.import_utils.check_duplicate', return_value=False)
    def test_handle_feed_event_import_automation_airflow(self, mock_check_dup, mock_invoke):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        notification = {
            "attributes": {
                "transfer_status": "TRANSFER_COMPLETED",
                "import_name": "scripts/us_fed:Rates",
                "import_version": "2026-09-01",
                "post_process": "import_automation_airflow",
                "graph_path": "/**/*.mcf*",
                "import_size": "large"
            },
            "messageId": "msg-789",
            "data": base64.b64encode(b'{"test": "data"}').decode('utf-8')
        }

        response = client.post("/imports/feed", json={"message": notification})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        mock_invoke.assert_called_once_with(
            import_name="scripts/us_fed:Rates",
            latest_version="2026-09-01",
            import_size="large",
            graph_path="/**/*.mcf*",
            cron_schedule="",
            dag_id=None,
            skip_import_job=False,
            skip_staging_ingestion=None,
            skip_prod_ingestion=None,
        )

    @patch('routes.events.import_utils.invoke_import_automation_airflow')
    @patch('routes.events.import_utils.check_duplicate', return_value=False)
    def test_handle_feed_event_import_automation_airflow_with_dag_id(self, mock_check_dup, mock_invoke):
        mock_bigquery = MagicMock()
        mock_storage = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery
        app.dependency_overrides[get_storage_client] = lambda: mock_storage

        notification = {
            "attributes": {
                "transfer_status": "TRANSFER_COMPLETED",
                "import_name": "scripts/us_fed:Rates",
                "import_version": "2026-09-01",
                "post_process": "import_automation_airflow",
                "dag_id": "USFed_Rates_Custom_DAG",
                "graph_path": "/**/*.mcf*",
                "import_size": "small"
            },
            "messageId": "msg-790",
            "data": base64.b64encode(b'{"test": "data"}').decode('utf-8')
        }

        response = client.post("/imports/feed", json={"message": notification})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")

        mock_invoke.assert_called_once_with(
            import_name="scripts/us_fed:Rates",
            latest_version="2026-09-01",
            import_size="small",
            graph_path="/**/*.mcf*",
            cron_schedule="",
            dag_id="USFed_Rates_Custom_DAG",
            skip_import_job=False,
            skip_staging_ingestion=None,
            skip_prod_ingestion=None,
        )

    @patch('utils.imports.id_token.fetch_id_token', return_value="iap-id-token")
    @patch('utils.imports.requests.post')
    @patch('utils.imports.google.auth.default')
    def test_invoke_import_automation_airflow_generic_and_fallback(self, mock_auth, mock_post, mock_fetch_id_token):
        # 0. Raise ValueError when AIRFLOW_WEB_SERVER_URL is not configured
        with patch('utils.imports.config.AIRFLOW_WEB_SERVER_URL', ''):
            with self.assertRaises(ValueError):
                import_utils.invoke_import_automation_airflow(
                    import_name="scripts/new:NewImport",
                    latest_version="2026-09-17",
                )

        mock_creds = MagicMock()
        mock_creds.token = "fake-token"
        mock_auth.return_value = (mock_creds, "test-project")

        # 1. When dag_id is None and AIRFLOW_IAP_CLIENT_ID is unset -> uses default credentials and calls generic DAG
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_post.return_value = mock_resp_ok

        with patch('utils.imports.config.AIRFLOW_WEB_SERVER_URL', 'https://airflow.example.com'), \
             patch('utils.imports.config.AIRFLOW_IAP_CLIENT_ID', ''):
            import_utils.invoke_import_automation_airflow(
                import_name="scripts/new:NewImport",
                latest_version="2026-09-17",
                dag_id=None,
            )
        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, "https://airflow.example.com/api/v1/dags/manual_refresh/dagRuns")
        self.assertEqual(mock_post.call_args[1]["headers"]["Authorization"], "Bearer fake-token")

        # 2. When AIRFLOW_IAP_CLIENT_ID is configured -> uses id_token.fetch_id_token
        with patch('utils.imports.config.AIRFLOW_WEB_SERVER_URL', 'https://airflow.example.com'), \
             patch('utils.imports.config.AIRFLOW_IAP_CLIENT_ID', 'test-iap-client-id.apps.googleusercontent.com'):
            import_utils.invoke_import_automation_airflow(
                import_name="scripts/new:NewImport",
                latest_version="2026-09-17",
                dag_id=None,
            )
        mock_fetch_id_token.assert_called_once()
        self.assertEqual(mock_fetch_id_token.call_args[0][1], 'test-iap-client-id.apps.googleusercontent.com')
        self.assertEqual(mock_post.call_args[1]["headers"]["Authorization"], "Bearer iap-id-token")

        # 3. When dag_id is specified but returns 404 -> falls back to generic DAG
        mock_resp_404 = MagicMock()
        mock_resp_404.status_code = 404
        mock_post.side_effect = [mock_resp_404, mock_resp_ok]

        with patch('utils.imports.config.AIRFLOW_WEB_SERVER_URL', 'https://airflow.example.com'), \
             patch('utils.imports.config.AIRFLOW_IAP_CLIENT_ID', ''):
            import_utils.invoke_import_automation_airflow(
                import_name="scripts/new:MissingImport",
                latest_version="2026-09-17",
                dag_id="MissingImport",
            )
        self.assertEqual(mock_post.call_count, 4)
        first_try_url = mock_post.call_args_list[2][0][0]
        fallback_url = mock_post.call_args_list[3][0][0]
        self.assertEqual(first_try_url, "https://airflow.example.com/api/v1/dags/MissingImport/dagRuns")
        self.assertEqual(fallback_url, "https://airflow.example.com/api/v1/dags/manual_refresh/dagRuns")

    def test_database_initialize_endpoint(self):
        mock_bigquery = MagicMock()
        app.dependency_overrides[get_bigquery_client] = lambda: mock_bigquery

        response = client.post("/database/initialize")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OK")
        mock_bigquery.initialize_database.assert_called_once()

    @patch('clients.bigquery.bigquery.Client')
    def test_bigquery_client_initialize_database(self, mock_bq_client_cls):
        mock_bq_instance = MagicMock()
        mock_bq_client_cls.return_value = mock_bq_instance

        bq_client = HelperBigQueryClient("test-project", "import_automation")
        bq_client.initialize_database()

        mock_bq_instance.create_dataset.assert_called_once()
        self.assertEqual(mock_bq_instance.query.call_count, 2)
        executed_queries = [call.args[0] for call in mock_bq_instance.query.call_args_list]
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS `test-project.import_automation.ImportHistory`" in q for q in executed_queries))
        self.assertTrue(any("CREATE OR REPLACE VIEW `test-project.import_automation.ImportSummary`" in q for q in executed_queries))

    @patch('clients.bigquery.bigquery.Client')
    def test_bigquery_client_update_and_auto_initialize(self, mock_bq_client_cls):
        mock_bq_instance = MagicMock()
        mock_bq_client_cls.return_value = mock_bq_instance
        # First call raises NotFound, triggering initialize_database(), second call succeeds
        mock_bq_instance.insert_rows_json.side_effect = [
            gcp_exceptions.NotFound("Table not found"),
            []
        ]

        bq_client = HelperBigQueryClient("test-project", "import_automation")
        bq_client.update_import_summary({
            "import_name": "scripts/us_fed:Rates",
            "status": "STAGING",
            "job_id": "job-1",
            "workflow_id": "wf-1",
            "execution_time": 42,
            "data_volume": 2048,
            "latest_version": "gs://bucket/Rates/v1",
            "graph_path": "/**/*.mcf*",
            "next_refresh": "2026-09-24T00:00:00Z",
        }, comment="import-workflow:wf-1")

        self.assertEqual(mock_bq_instance.insert_rows_json.call_count, 2)
        mock_bq_instance.create_dataset.assert_called_once()
        inserted_row = mock_bq_instance.insert_rows_json.call_args_list[1].args[1][0]
        self.assertEqual(inserted_row["ImportName"], "Rates")
        self.assertEqual(inserted_row["Status"], "STAGING")
        self.assertEqual(inserted_row["Version"], "gs://bucket/Rates/v1")
        self.assertEqual(inserted_row["JobId"], "job-1")
        self.assertEqual(inserted_row["Comment"], "import-workflow:wf-1")
        self.assertNotIn("GraphPath", inserted_row)
        self.assertNotIn("WorkflowExecutionID", inserted_row)
        self.assertNotIn("DataImportTimestamp", inserted_row)
        self.assertIsNotNone(inserted_row["UpdateTimestamp"])


if __name__ == '__main__':
    unittest.main()
