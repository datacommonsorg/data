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
"""Unit tests for Data Commons Import Automation Airflow Workflow."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Mock airflow modules before importing workflow modules
mock_airflow = MagicMock()
mock_sensors = MagicMock()


class MockBaseSensorOperator:
    template_fields = ()

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.downstream_list = []
        self.task_id = kwargs.get('task_id', 'sensor')
        if MockDAG.current_dag:
            MockDAG.current_dag.tasks.append(self)

    def execute(self, context):
        return self.poke(context)

    def __rshift__(self, other):
        self.downstream_list.append(other)
        return other


class MockDAG:
    current_dag = None

    def __init__(self, *args, **kwargs):
        self.tasks = []
        self.is_paused_upon_creation = kwargs.get('is_paused_upon_creation',
                                                  True)
        self.params = kwargs.get('params', {})

    def __enter__(self):
        MockDAG.current_dag = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        MockDAG.current_dag = None


def mock_task(*d_args, **d_kwargs):

    def decorator(f):

        def wrapper(*args, **kwargs):
            mock_t = MagicMock()
            mock_t.task_id = d_kwargs.get('task_id', f.__name__)
            mock_t.downstream_list = []
            mock_t.__rshift__ = lambda self, other: (self.downstream_list.
                                                     append(other), other)[1]
            if MockDAG.current_dag:
                MockDAG.current_dag.tasks.append(mock_t)
            return mock_t

        wrapper.function = f
        return wrapper

    if d_args and callable(d_args[0]):
        return decorator(d_args[0])
    return decorator


mock_sensors.base.BaseSensorOperator = MockBaseSensorOperator
sys.modules['airflow'] = mock_airflow
mock_airflow.DAG = MockDAG
sys.modules['airflow.sensors'] = mock_sensors
sys.modules['airflow.sensors.base'] = mock_sensors.base
mock_decorators = MagicMock()
mock_decorators.task = mock_task
sys.modules['airflow.decorators'] = mock_decorators
sys.modules['airflow.exceptions'] = MagicMock()


class MockAirflowFailException(Exception):
    pass


sys.modules[
    'airflow.exceptions'].AirflowFailException = MockAirflowFailException
sys.modules['airflow.models'] = MagicMock()
sys.modules['airflow.models.param'] = MagicMock(
    Param=lambda default=None, **kwargs: default)
sys.modules['airflow.providers'] = MagicMock()
sys.modules['airflow.providers.google'] = MagicMock()
sys.modules['airflow.providers.google.cloud'] = MagicMock()
sys.modules['airflow.providers.google.cloud.hooks'] = MagicMock()
sys.modules['airflow.providers.google.cloud.hooks.cloud_build'] = MagicMock()
sys.modules['airflow.providers.google.cloud.hooks.gcs'] = MagicMock()
sys.modules['airflow.providers.google.cloud.hooks.cloud_batch'] = MagicMock()
sys.modules['airflow.providers.google.cloud.sensors'] = MagicMock()
mock_wf_sensor_mod = MagicMock()
mock_wf_sensor_mod.WorkflowExecutionSensor = MockBaseSensorOperator
sys.modules[
    'airflow.providers.google.cloud.sensors.workflows'] = mock_wf_sensor_mod
sys.modules['airflow.utils'] = MagicMock()
sys.modules['airflow.utils.trigger_rule'] = MagicMock()
sys.modules[
    'airflow.utils.trigger_rule'].TriggerRule.NONE_FAILED = 'none_failed'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import build_manifest_catalog
import import_dag_e2e_test
import golden_verification
from golden_verification import (
    HumanApprovalSensor,
    get_golden_trigger_id,
    is_golden_test_import,
)
import import_automation_workflow
import import_dags_factory


class ImportAutomationWorkflowTest(unittest.TestCase):

    def setUp(self):
        golden_verification.Variable.get.side_effect = None
        golden_verification.Variable.get.return_value = ''

    def test_allowlist(self):
        self.assertTrue(is_golden_test_import('Schema'))
        self.assertTrue(is_golden_test_import('scripts/entities:Schema'))
        self.assertTrue(is_golden_test_import('Place'))
        self.assertFalse(
            is_golden_test_import('USFed_ConstantMaturityRates_Test'))
        self.assertFalse(is_golden_test_import('scripts/us_fed:treasury'))

    def test_trigger_id(self):
        self.assertEqual(get_golden_trigger_id('Schema'),
                         'ingestion-golden-verification')
        self.assertEqual(get_golden_trigger_id('Place'),
                         'ingestion-golden-verification')
        self.assertEqual(get_golden_trigger_id('Unknown'),
                         'ingestion-golden-verification')
        self.assertEqual(
            get_golden_trigger_id('Schema', custom_trigger='custom-trig'),
            'custom-trig',
        )

    def test_approval_sensor_no_diff(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': False,
            'prUrl': '',
        }
        context = {'ti': ti_mock, 'params': {}}
        self.assertTrue(sensor.poke(context))

    def test_approval_sensor_skipped_golden(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='OtherImport')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SKIPPED',
            'hasDiff': False,
        }
        context = {'ti': ti_mock, 'params': {}}
        self.assertTrue(sensor.poke(context))

    def test_approval_sensor_auto_approve_param(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': True,
            'prUrl': 'https://github.com/datacommonsorg/website/pull/123',
        }
        context = {'ti': ti_mock, 'params': {'autoApproveGoldenDiff': True}}
        self.assertTrue(sensor.poke(context))

    def test_approval_sensor_diff_pending(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': True,
            'prUrl': 'https://github.com/datacommonsorg/website/pull/123',
            'buildId': 'bld-456',
            'logUrl': 'https://console.cloud.google.com/build/123',
        }
        context = {'ti': ti_mock, 'params': {}}
        golden_verification.Variable.get.return_value = ''
        self.assertFalse(sensor.poke(context))

    def test_approval_sensor_diff_approved_via_variable(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': True,
            'prUrl': 'https://github.com/datacommonsorg/website/pull/123',
        }
        context = {'ti': ti_mock, 'params': {}}

        def var_get_mock(key, default_var=''):
            if key == 'PROD_APPROVE_test-job-123':
                return 'true'
            return default_var

        golden_verification.Variable.get.side_effect = var_get_mock
        self.assertTrue(sensor.poke(context))

    def test_approval_sensor_diff_rejected_via_variable(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': True,
            'prUrl': 'https://github.com/datacommonsorg/website/pull/123',
        }
        context = {'ti': ti_mock, 'params': {}}

        def var_get_mock(key, default_var=''):
            if key == 'PROD_REJECT_test-job-123':
                return 'true'
            return default_var

        golden_verification.Variable.get.side_effect = var_get_mock
        with self.assertRaises(MockAirflowFailException):
            sensor.poke(context)

    def test_approval_sensor_execute_output(self):
        sensor = HumanApprovalSensor(job_id='test-job-123',
                                     import_name='Schema')
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {
            'status': 'SUCCESS',
            'hasDiff': False,
            'prUrl': '',
        }
        context = {'ti': ti_mock, 'params': {}}
        result = sensor.execute(context)
        self.assertEqual(result['status'], 'APPROVED')
        self.assertFalse(result['hasDiff'])
        self.assertIn('approvedAt', result)

    def test_verify_golden_tests_skipped_import(self):
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {'status': 'SUCCESS'}
        context = {
            'ti': ti_mock,
            'params': {
                'importName': 'NonAllowlistedImport'
            },
        }
        res = golden_verification.verify_golden_tests.function(**context)
        self.assertEqual(res['status'], 'SKIPPED')
        self.assertFalse(res['hasDiff'])

    def test_verify_golden_tests_skipped_staging_failure(self):
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {'status': 'FAILED'}
        context = {
            'ti': ti_mock,
            'params': {
                'importName': 'Schema'
            },
        }
        res = golden_verification.verify_golden_tests.function(**context)
        self.assertEqual(res['status'], 'SKIPPED')
        self.assertFalse(res['hasDiff'])

    @patch('golden_verification._run_cloud_build_verification')
    @patch('golden_verification._fetch_diff_summary')
    def test_verify_golden_tests_success_with_diff(self, mock_fetch, mock_run):
        mock_run.return_value = {
            'id': 'build-999',
            'status': 'SUCCESS',
            'logUrl': 'https://console.cloud.google.com/build/999',
        }
        mock_fetch.return_value = {
            'has_diff': True,
            'pr_url': 'https://github.com/datacommonsorg/website/pull/999',
            'branch_name': 'schema-golden-diff-build-999',
        }
        ti_mock = MagicMock()
        ti_mock.xcom_pull.return_value = {'status': 'SUCCESS'}
        context = {
            'ti': ti_mock,
            'params': {
                'importName': 'Schema'
            },
        }
        res = golden_verification.verify_golden_tests.function(**context)
        self.assertEqual(res['status'], 'SUCCESS')
        self.assertTrue(res['hasDiff'])
        self.assertEqual(res['prUrl'],
                         'https://github.com/datacommonsorg/website/pull/999')
        self.assertEqual(res['branchName'], 'schema-golden-diff-build-999')

    def test_load_catalog_includes_schema(self):
        data_dir = os.path.abspath(os.path.join(CURRENT_DIR, '../..'))
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog_path = os.path.join(tmpdir, 'imports_catalog.json')
            build_manifest_catalog.build_catalog(
                data_dir=data_dir,
                output_path=catalog_path,
            )
            with patch.dict(os.environ, {'IMPORTS_CATALOG_PATH': catalog_path}):
                target = {}
                count = import_dags_factory.load_catalog_and_register_dags(
                    target)
                self.assertGreaterEqual(count, 198)
                self.assertIn('Schema', target)
                self.assertIn('manual_refresh', target)
                schema_dag = target['Schema']
                self.assertIsNotNone(schema_dag)
                for dag_id, dag in target.items():
                    self.assertTrue(
                        dag.is_paused_upon_creation,
                        f'DAG {dag_id} is not paused upon creation',
                    )
                    expected_skip_prod = import_automation_workflow.is_prod_denylisted(
                        dag_id)
                    self.assertEqual(
                        dag.params.get('skipProdIngestion'),
                        expected_skip_prod,
                        f'DAG {dag_id} does not default skipProdIngestion to {expected_skip_prod}',
                    )

    def test_build_dag_pipeline_wiring(self):
        dag = import_automation_workflow.build_dag(dag_id='test_dag',
                                                   import_name='Schema')
        tasks = {t.task_id: t for t in dag.tasks}
        expected_tasks = [
            'run_import_job',
            'run_validation_job',
            'trigger_staging_ingestion',
            'wait_staging_ingestion',
            'verify_golden_tests',
            'await_human_approval',
            'ingest_prod',
            'workflow_summary',
        ]
        for task_id in expected_tasks:
            self.assertIn(task_id, tasks)

        # Check downstream ordering
        self.assertIn(tasks['run_validation_job'],
                      tasks['run_import_job'].downstream_list)
        self.assertIn(tasks['trigger_staging_ingestion'],
                      tasks['run_validation_job'].downstream_list)
        self.assertIn(tasks['wait_staging_ingestion'],
                      tasks['trigger_staging_ingestion'].downstream_list)
        self.assertIn(tasks['verify_golden_tests'],
                      tasks['wait_staging_ingestion'].downstream_list)
        self.assertIn(tasks['await_human_approval'],
                      tasks['verify_golden_tests'].downstream_list)
        self.assertIn(tasks['ingest_prod'],
                      tasks['await_human_approval'].downstream_list)
        self.assertIn(tasks['workflow_summary'],
                      tasks['ingest_prod'].downstream_list)

    @patch('import_automation_workflow._run_cloud_run_job')
    def test_validation_job_and_batch_config(self, mock_run_cr_job):
        context = {
            'params': {
                'importName': 'scripts/us_fed:USFed_ConstantMaturityRates_Test',
                'importConfig': {
                    'custom_flag': True,
                    'invoke_import_validation': True
                },
            }
        }
        cfg = import_automation_workflow.resolve_workflow_context(context)
        batch_cfg = json.loads(cfg['batchImportConfig'])
        orig_cfg = json.loads(cfg['importConfig'])

        self.assertFalse(batch_cfg['invoke_import_validation'])
        self.assertFalse(batch_cfg['invoke_differ_tool'])
        self.assertTrue(batch_cfg['custom_flag'])
        self.assertTrue(orig_cfg['invoke_import_validation'])
        self.assertEqual(cfg['validationJobName'], 'import-validator-job')

        mock_run_cr_job.return_value = {'status': 'SUCCEEDED'}
        res = import_automation_workflow.run_validation_job.function(**context)
        self.assertEqual(res['status'], 'SUCCESS')
        mock_run_cr_job.assert_called_once()
        call_args = mock_run_cr_job.call_args[1]
        self.assertEqual(call_args['job_name'], 'import-validator-job')
        self.assertIn(
            '--import_name=scripts/us_fed:USFed_ConstantMaturityRates_Test',
            call_args['args'])


class E2EDagRunnerTest(unittest.TestCase):

    @patch('import_dag_e2e_test.get_authorized_session')
    def test_e2e_runner_success_and_hitl(self, mock_get_session):
        session_mock = MagicMock()
        session_mock.approved = False
        mock_get_session.return_value = session_mock

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            if url.endswith('/environments/import-automation-airflow'):
                resp.json.return_value = {
                    'config': {
                        'airflowUri':
                            'https://mock-composer.googleusercontent.com'
                    }
                }
            elif url.endswith('/importErrors'):
                resp.json.return_value = {'import_errors': []}
            elif url.endswith('/dags/USFed_ConstantMaturityRates_Test'):
                resp.json.return_value = {
                    'dag_id': 'USFed_ConstantMaturityRates_Test',
                    'is_paused': True
                }
            elif '/dagRuns/' in url and url.endswith('/taskInstances'):
                if not getattr(session_mock, 'approved', False):
                    resp.json.return_value = {
                        'task_instances': [{
                            'task_id': 'await_human_approval',
                            'state': 'up_for_reschedule'
                        }]
                    }
                else:
                    resp.json.return_value = {
                        'task_instances': [
                            {
                                'task_id': 'await_human_approval',
                                'state': 'success'
                            },
                            {
                                'task_id': 'workflow_summary',
                                'state': 'success'
                            },
                        ]
                    }
            elif '/taskInstances/workflow_summary/xcomEntries/return_value' in url:
                resp.json.return_value = {
                    'value':
                        json.dumps({
                            'jobId': 'test-job',
                            'status': 'SUCCESS'
                        })
                }
            elif '/dagRuns/' in url:
                state = 'success' if getattr(session_mock, 'approved',
                                             False) else 'running'
                resp.json.return_value = {'state': state}
            return resp

        def mock_post(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            if url.endswith('/variables'):
                session_mock.approved = True
            resp.json.return_value = {'dag_run_id': 'test-run'}
            return resp

        def mock_patch(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.ok = True
            if '/variables/' in url:
                session_mock.approved = True
            resp.json.return_value = {
                'dag_id': 'USFed_ConstantMaturityRates_Test',
                'is_paused': False
            }
            return resp

        session_mock.get.side_effect = mock_get
        session_mock.post.side_effect = mock_post
        session_mock.patch.side_effect = mock_patch

        summary = import_dag_e2e_test.run_e2e_test(
            project_id='datcom-import-automation-prod',
            location='us-central1',
            composer_env='import-automation-airflow',
            dag_id='USFed_ConstantMaturityRates_Test',
            simulate_hitl_approval=True,
            sync_wait_sec=0,
            poll_interval_sec=0,
            timeout_sec=10,
        )
        self.assertEqual(summary['status'], 'SUCCESS')
        self.assertTrue(session_mock.delete.called)


if __name__ == '__main__':
    unittest.main()
