# Copyright 2020 Google LLC
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
"""
Testing utilities.
"""

import requests.exceptions
import google.api_core.exceptions


class ResponseMock:
    """Mock class for request.Response."""

    def __init__(self, code, data=None, raw=None, headers=None):
        self.status_code = code
        self.data = data
        self.raw = raw
        self.headers = headers

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError

    def json(self):
        self.raise_for_status()
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter_content(self, chunk_size):
        # Unused
        del chunk_size
        for line in self.raw:
            yield line

    def text(self):
        return str(self.data)


def compare_lines(expected_path, to_test_path, num_lines, reverse=False):
    """Compares the first n lines of two files.

    Args:
        expected_path: Path to the file with the expected content, as a string.
        to_test_path: Path to the file to compare with the expected file,
            as a string.
        num_lines: Number of lines to compare, as an int.
        reverse: Whether to compare the last n lines, as a boolean.

    Returns:
        True, if the two files have the same content. False, otherwise.
    """
    with open(expected_path, 'rb') as expected:
        with open(to_test_path, 'rb') as to_test:
            expected_lines = None
            lines_to_test = None
            if reverse:
                expected_lines = expected.readlines()[-num_lines:]
                lines_to_test = to_test.readlines()[-num_lines:]
            else:
                expected_lines = expected.readlines()[:num_lines]
                lines_to_test = to_test.readlines()[:num_lines]
            if len(lines_to_test) != len(expected_lines):
                print(f'Expected to test {len(lines_to_test)} lines but '
                      f'got {len(expected_lines)} lines')
                return False
            for i in range(min(len(lines_to_test), num_lines)):
                expected_line = expected_lines[i]
                line_to_test = lines_to_test[i]
                if expected_line != line_to_test:
                    print('WANT:', expected_line)
                    print('GOT:', line_to_test)
                    return False
            return True


class SchedulerJobMock(dict):
    """Mock class for google.cloud.scheduler.types.Job."""

    @property
    def http_target(self):
        return SchedulerJobMock(self.__getitem__('http_target'))

    @property
    def app_engine_http_target(self):
        return SchedulerJobMock(self.__getitem__('app_engine_http_target'))

    @property
    def body(self):
        return self.__getitem__('body')


class SchedulerClientMock:
    """Mock class for google.cloud.scheduler.CloudSchedulerClient."""

    def __init__(self):
        self.jobs = {}

    def create_job(self, location_path, job):
        job = SchedulerJobMock(job)
        self.jobs[job["name"]] = job
        return job

    def delete_job(self, job_path):
        if job_path not in self.jobs:
            raise google.api_core.exceptions.GoogleAPICallError(
                'Job does not exist')
        return self.jobs.pop(job_path)

    def location_path(self, project, location):
        return f'projects/{project}/locations/{location}'

    def job_path(self, project, location, job):
        return f'projects/{project}/locations/{location}/jobs/{job}'
