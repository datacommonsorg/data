# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Cloud Batch job configuration."""

import re
import unittest

from datacommons_airflow import cloud_batch_job


class CloudBatchJobTest(unittest.TestCase):

    def test_get_required_environment(self):
        self.assertEqual(
            'us-central1',
            cloud_batch_job.get_required_environment(
                {'CLOUD_BATCH_REGION': ' us-central1 '}, 'CLOUD_BATCH_REGION'))

    def test_get_required_environment_rejects_missing_value(self):
        with self.assertRaisesRegex(ValueError, 'CLOUD_BATCH_SERVICE_ACCOUNT'):
            cloud_batch_job.get_required_environment(
                {}, 'CLOUD_BATCH_SERVICE_ACCOUNT')

    def test_make_batch_job_id_is_valid_and_deterministic(self):
        job_id = cloud_batch_job.make_batch_job_id('manual__example', 1)

        self.assertEqual(
            job_id, cloud_batch_job.make_batch_job_id('manual__example', 1))
        self.assertLessEqual(len(job_id), 63)
        self.assertRegex(job_id, re.compile(r'^[a-z][a-z0-9-]*$'))

    def test_make_batch_job_id_changes_with_attempt(self):
        self.assertNotEqual(
            cloud_batch_job.make_batch_job_id('manual__example', 1),
            cloud_batch_job.make_batch_job_id('manual__example', 2))

    def test_build_job(self):
        job = cloud_batch_job.build_job(
            image_uri='example.com/image:latest',
            command='echo hello',
            service_account_email='batch@example.iam.gserviceaccount.com')

        task_spec = job['task_groups'][0]['task_spec']
        container = task_spec['runnables'][0]['container']
        instance_policy = job['allocation_policy']['instances'][0]['policy']

        self.assertEqual('example.com/image:latest', container['image_uri'])
        self.assertEqual('/bin/sh', container['entrypoint'])
        self.assertEqual(['-c', 'echo hello'], container['commands'])
        self.assertEqual(cloud_batch_job.MACHINE_TYPE,
                         instance_policy['machine_type'])
        self.assertEqual(0, task_spec['max_retry_count'])
        self.assertEqual('batch@example.iam.gserviceaccount.com',
                         job['allocation_policy']['service_account']['email'])
        self.assertEqual('CLOUD_LOGGING', job['logs_policy']['destination'])


if __name__ == '__main__':
    unittest.main()
