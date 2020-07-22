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

from requests import exceptions


class ResponseMock:
    """Simple mock of a HTTP response."""

    def __init__(self, code, data=None, raw=None):
        self.status_code = code
        self.data = data
        self.raw = raw

    def raise_for_status(self):
        if self.status_code != 200:
            raise exceptions.HTTPError

    def json(self):
        self.raise_for_status()
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


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
                return False
            for i in range(min(len(lines_to_test), num_lines)):
                expected_line = expected_lines[i]
                line_to_test = lines_to_test[i]
                if expected_line != line_to_test:
                    print('WANT:', expected_line)
                    print('GOT:', line_to_test)
                    return False
            return True
