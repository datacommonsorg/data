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
        self.mode = kwargs.get('mode', 'poke')
        self.poke_interval = kwargs.get('poke_interval', 60)
        self.timeout = kwargs.get('timeout', 604800)
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
            mock_t.trigger_rule = d_kwargs.get('trigger_rule', 'all_success')
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


class MockParam:

    def __init__(self, default=None, **kwargs):
        self.value = default
        self.default = default
        self.kwargs = kwargs


mock_sdk = MagicMock()
mock_sdk.DAG = MockDAG
mock_sdk.Param = MockParam
mock_sdk.task = mock_task
mock_sdk.BaseSensorOperator = MockBaseSensorOperator
sys.modules['airflow'] = mock_airflow
sys.modules['airflow.sdk'] = mock_sdk
sys.modules['airflow.exceptions'] = MagicMock()


class MockAirflowException(Exception):
    pass


class MockAirflowFailException(Exception):
    pass


class MockAirflowSkipException(Exception):
    pass


sys.modules['airflow.exceptions'].AirflowException = MockAirflowException
sys.modules[
    'airflow.exceptions'].AirflowFailException = MockAirflowFailException
sys.modules[
    'airflow.exceptions'].AirflowSkipException = MockAirflowSkipException
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
)
import import_automation_workflow
import import_dags_factory


class ImportAutomationWorkflowTest(unittest.TestCase):

    def setUp(self):
        golden_verification.Variable.get.side_effect = None
        golden_verification.Variable.get.return_value = ''

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

        def var_get_mock(key, default=''):
            if key == 'PROD_APPROVE_test-job-123':
                return 'true'
            return default

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

        def var_get_mock(key, default=''):
            if key == 'PROD_REJECT_test-job-123':
                return 'true'
            return default

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
                'importName': 'Schema',
                'runGoldenTests': True,
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
                'importName': 'Schema',
                'runGoldenTests': True,
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
                self.assertGreater(count, 0)
                self.assertIn('Schema', target)
                self.assertIn('ManualRefresh', target)
                schema_dag = target['Schema']
                self.assertIsNotNone(schema_dag)

    def test_build_dag_pipeline_wiring(self):
        dag = import_automation_workflow.build_dag(dag_id='test_dag',
                                                   import_name='Schema')
        tasks = {t.task_id: t for t in dag.tasks}
        expected_tasks = [
            'run_import_job',
            'update_import_version',
            'trigger_staging_ingestion',
            'wait_staging_ingestion',
            'trigger_prod_ingestion',
            'wait_prod_ingestion',
            'workflow_summary',
        ]
        for task_id in expected_tasks:
            self.assertIn(task_id, tasks)
        self.assertNotIn('run_validation_job', tasks)
        self.assertNotIn('verify_golden_tests', tasks)
        self.assertNotIn('await_human_approval', tasks)
        self.assertNotIn('skipValidationJob', dag.params)
        self.assertNotIn('dryRunIngestion', dag.params)
        self.assertNotIn('forceIngestion', dag.params)

        # Ensure wait/sensor tasks run in reschedule mode so they do not hold worker slots
        self.assertEqual(tasks['run_import_job'].mode, 'reschedule')
        self.assertEqual(tasks['wait_staging_ingestion'].mode, 'reschedule')
        self.assertEqual(tasks['wait_prod_ingestion'].mode, 'reschedule')
        self.assertEqual(tasks['trigger_prod_ingestion'].trigger_rule,
                         'none_failed')
        self.assertEqual(tasks['workflow_summary'].trigger_rule, 'none_failed')

        # Check downstream ordering
        self.assertIn(tasks['update_import_version'],
                      tasks['run_import_job'].downstream_list)
        self.assertIn(tasks['trigger_staging_ingestion'],
                      tasks['update_import_version'].downstream_list)
        self.assertIn(tasks['wait_staging_ingestion'],
                      tasks['trigger_staging_ingestion'].downstream_list)
        self.assertIn(tasks['trigger_prod_ingestion'],
                      tasks['wait_staging_ingestion'].downstream_list)
        self.assertIn(tasks['wait_prod_ingestion'],
                      tasks['trigger_prod_ingestion'].downstream_list)
        self.assertIn(tasks['workflow_summary'],
                      tasks['wait_prod_ingestion'].downstream_list)

    @patch('import_automation_workflow._run_cloud_run_job')
    def test_validation_job_and_batch_config(self, mock_run_cr_job):
        context = {
            'params': {
                'importName': 'scripts/us_fed:USFed_ConstantMaturityRates_Test',
                'importConfig': {
                    'custom_flag': True,
                },
            }
        }
        cfg = import_automation_workflow.resolve_workflow_context(context)
        batch_cfg = json.loads(cfg['batchImportConfig'])
        orig_cfg = json.loads(cfg['importConfig'])

        self.assertNotIn('skipValidationJob', cfg)
        self.assertNotIn('invoke_import_validation', batch_cfg)
        self.assertNotIn('invoke_differ_tool', batch_cfg)
        self.assertTrue(batch_cfg['custom_flag'])
        self.assertEqual(batch_cfg, orig_cfg)
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

    def test_skip_import_job_skips_batch_and_validation_jobs(self):
        context = {
            'params': {
                'importName': 'scripts/us_fed:USFed_ConstantMaturityRates_Test',
                'skipImportJob': True,
            }
        }
        with self.assertRaises(MockAirflowSkipException):
            import_automation_workflow.run_import_job.function(**context)
        with self.assertRaises(MockAirflowSkipException):
            import_automation_workflow.run_validation_job.function(**context)

        dag = import_automation_workflow.build_dag(dag_id='test_skip_dag',
                                                   import_name='Schema')
        tasks = {t.task_id: t for t in dag.tasks}
        self.assertEqual(tasks['update_import_version'].trigger_rule,
                         'none_failed')

    def test_normalize_manifest_resource_limits(self):
        dag = import_automation_workflow.build_dag(
            dag_id='EIA_Electricity',
            import_name='scripts/us_eia/opendata:EIA_Electricity',
            resource_limits={
                'cpu': 8,
                'memory': 64,
                'disk': 100
            },
        )
        cfg = import_automation_workflow.resolve_workflow_context({'dag': dag})
        self.assertEqual(
            cfg['resources'],
            {
                'machine': 'n2-highmem-8',
                'cpu': 8000,
                'memory': 65536,
                'disk': 100,
            },
        )
        spec = import_automation_workflow._build_batch_job_spec(
            image_uri=cfg['imageUri'],
            import_name=cfg['importName'],
            import_config=cfg['batchImportConfig'],
            job_id=cfg['jobId'],
            resources=cfg['resources'],
            gcs_mount_bucket=cfg['gcsMountBucket'],
        )
        compute = spec['taskGroups'][0]['taskSpec']['computeResource']
        instance = spec['allocationPolicy']['instances'][0]['policy']
        self.assertEqual(compute['cpuMilli'], 8000)
        self.assertEqual(compute['memoryMib'], 65536)
        self.assertEqual(instance['machineType'], 'n2-highmem-8')
        self.assertEqual(instance['bootDisk']['sizeGb'], 100)

    @patch('import_automation_workflow.trigger_environment_ingestion')
    def test_trigger_prod_ingestion_skips_and_pushes_xcom(self, mock_trigger):
        ti_mock = MagicMock()

        def xcom_pull(task_ids=None):
            if task_ids == 'update_import_version':
                return {
                    'status': 'SKIP',
                    'importEntry': {
                        'importName': 'TestImport',
                        'latestVersion': 'gs://bucket/TestImport/v1/*.mcf*',
                    },
                }
            if task_ids == 'trigger_staging_ingestion':
                return {
                    'status': 'SKIPPED',
                    'message': 'No imports need ingestion'
                }
            return None

        ti_mock.xcom_pull.side_effect = xcom_pull
        mock_trigger.return_value = {
            'status': 'SKIPPED',
            'message': 'No imports need ingestion',
        }
        context = {
            'ti': ti_mock,
            'params': {
                'importName': 'scripts/test:TestImport',
                'skipStagingIngestion': False,
                'skipProdIngestion': False,
            },
        }
        with self.assertRaises(MockAirflowSkipException):
            import_automation_workflow.trigger_prod_ingestion.function(
                **context)
        ti_mock.xcom_push.assert_called_once_with(
            key='return_value',
            value={
                'status': 'SKIPPED',
                'message': 'No imports need ingestion',
            },
        )

    @patch('import_automation_workflow._make_http_post')
    def test_update_import_version_with_conf_override(self, mock_post):
        mock_post.return_value = {
            'status':
                'OK',
            'message':
                'Import: TestImport Version: 2026_10_06 Status: STAGING',
            'imports': [{
                'importName': 'scripts/test:TestImport',
                'status': 'STAGING',
                'latestVersion': 'gs://bucket/TestImport/2026_10_06/*.mcf*',
            }],
        }
        dag_run = MagicMock()
        dag_run.conf = {
            'importName': 'scripts/test:TestImport',
            'version': '2026_10_06',
            'overrideVersion': True,
            'comment': 'Manual validation',
        }
        dag_run.run_id = 'version_update__TestImport__2026_10_06'
        context = {'dag_run': dag_run}

        res = import_automation_workflow.update_import_version.function(
            **context)
        self.assertEqual(res['status'], 'STAGING')
        self.assertEqual(
            res['importEntry'],
            {
                'importName': 'TestImport',
                'latestVersion': 'gs://bucket/TestImport/2026_10_06/*.mcf*',
            },
        )
        mock_post.assert_called_once_with(
            'https://import-helper-service-879489846695.us-central1.run.app/imports/version',
            {
                'imports': ['scripts/test:TestImport'],
                'version':
                    '2026_10_06',
                'override':
                    True,
                'comment':
                    'import-workflow:version_update__TestImport__2026_10_06 Manual validation',
            },
        )

    @patch('import_automation_workflow.CloudBatchHook')
    def test_cloud_batch_import_sensor_submit_reschedule_and_succeed(
            self, mock_batch_hook_cls):
        hook_mock = MagicMock()
        conn_mock = MagicMock()
        hook_mock.get_conn.return_value = conn_mock
        mock_batch_hook_cls.return_value = hook_mock

        not_found_err = Exception('404 Job not found')
        running_job = MagicMock()
        running_job.name = 'projects/p/locations/r/jobs/test-job-1'
        running_job.status.state = 3  # RUNNING
        running_job.create_time = None

        succeeded_job = MagicMock()
        succeeded_job.name = 'projects/p/locations/r/jobs/test-job-1'
        succeeded_job.status.state = 4  # SUCCEEDED
        succeeded_job.create_time = None

        conn_mock.get_job.side_effect = [
            not_found_err,
            running_job,
            succeeded_job,
        ]
        hook_mock.submit_batch_job.return_value = running_job

        sensor = import_automation_workflow.CloudBatchImportSensor(
            task_id='run_import_job',
            import_name='scripts/test:TestImport',
            mode='reschedule',
            poke_interval=60,
            timeout=604800,
        )
        context = {
            'params': {
                'importName': 'scripts/test:TestImport',
                'jobId': 'test-job-1',
                'projectId': 'p',
                'region': 'r',
            }
        }

        # Poke 1: Job does not exist -> submits job -> state RUNNING -> returns False
        self.assertFalse(sensor.poke(context))
        hook_mock.submit_batch_job.assert_called_once()
        self.assertEqual(hook_mock.submit_batch_job.call_args[1]['job_name'],
                         'test-job-1')

        # Poke 2: Job exists and is RUNNING -> does not re-submit -> returns False
        self.assertFalse(sensor.poke(context))
        hook_mock.submit_batch_job.assert_called_once()

        # Poke 3 via execute(): Job SUCCEEDED -> returns XCom result dict
        res = sensor.execute(context)
        self.assertEqual(res['status'], 'SUCCESS')
        self.assertEqual(res['jobId'], 'test-job-1')
        self.assertEqual(res['name'], 'projects/p/locations/r/jobs/test-job-1')
        self.assertIn('executionTime', res)

    @patch('import_automation_workflow._report_import_failure')
    @patch('import_automation_workflow.CloudBatchHook')
    def test_cloud_batch_import_sensor_failure_reports_and_raises(
            self, mock_batch_hook_cls, mock_report_failure):
        hook_mock = MagicMock()
        conn_mock = MagicMock()
        hook_mock.get_conn.return_value = conn_mock
        mock_batch_hook_cls.return_value = hook_mock

        failed_job = MagicMock()
        failed_job.name = 'projects/p/locations/r/jobs/test-job-fail'
        failed_job.status.state = 5  # FAILED
        ev = MagicMock()
        ev.description = 'Task exited with non-zero code 1'
        failed_job.status.status_events = [ev]
        failed_job.create_time = None
        conn_mock.get_job.return_value = failed_job

        sensor = import_automation_workflow.CloudBatchImportSensor(
            task_id='run_import_job',
            import_name='scripts/test:TestImport',
        )
        context = {
            'params': {
                'importName': 'scripts/test:TestImport',
                'jobId': 'test-job-fail',
                'projectId': 'p',
                'region': 'r',
            }
        }

        with self.assertRaises(MockAirflowException) as ctx:
            sensor.poke(context)
        self.assertIn('FAILED', str(ctx.exception))
        mock_report_failure.assert_called_once()
        hook_mock.submit_batch_job.assert_not_called()

    def test_staging_and_prod_denylist_skips_ingestion(self):
        with patch.object(import_automation_workflow, 'STAGING_DENYLIST',
                          frozenset({'DenylistedImport'})), patch.object(
                              import_automation_workflow, 'PROD_DENYLIST',
                              frozenset({'DenylistedImport'})):
            dag = import_automation_workflow.build_dag(
                dag_id='DenylistedImport',
                import_name='scripts/test:DenylistedImport',
            )
            self.assertTrue(dag.params['skipStagingIngestion'].default)
            self.assertTrue(dag.params['skipProdIngestion'].default)

            cfg = import_automation_workflow.resolve_workflow_context(
                {'dag': dag})
            self.assertTrue(cfg['skipStagingIngestion'])
            self.assertTrue(cfg['skipProdIngestion'])

            ti_mock = MagicMock()
            with self.assertRaises(MockAirflowSkipException):
                import_automation_workflow.trigger_staging_ingestion.function(
                    dag=dag, ti=ti_mock)
            ti_mock.xcom_push.assert_called_once_with(
                key='return_value',
                value={
                    'status': 'SKIPPED',
                    'message': 'Staging ingestion skipped',
                },
            )


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
