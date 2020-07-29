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
Tests for utils.py.
"""

from datetime import datetime
import unittest

from flask_restful import reqparse

from app import utils
from app import main

IMPORT_ATTEMPT_DATABASE = ('app.resource.import_attempt'
                           '.import_attempt_database.ImportAttemptDatabase')


class UCTTest(unittest.TestCase):
    """Tests for utctime function."""

    def test_to_datetime(self):
        """Tests that the string returned by utctime can be converted to
        a datetime object and the timezone component is correct."""
        time_iso = utils.utctime()
        time_datetime = datetime.fromisoformat(time_iso)
        self.assertEqual(0, time_datetime.utcoffset().total_seconds())
        self.assertEqual('UTC', time_datetime.tzname())

    def test_to_datetime_then_back(self):
        """Tests that the string returned by utctime can be converted to
        a datetime object and remains the same when converted back."""
        time_iso = utils.utctime()
        time_datetime = datetime.fromisoformat(time_iso)
        self.assertEqual(time_iso, time_datetime.isoformat())


class RequestParserAddFieldsTest(unittest.TestCase):
    """Tests for utility functions that deal with RequestParser."""

    def test_optional_fields(self):
        """Tests that add_fields correctly adds optional fields
        to the parser."""
        parser = reqparse.RequestParser()
        optional_fields = [('attempt_id', str), ('import_name', str, 'store')]
        utils.add_fields(parser, optional_fields, required=False)

        with main.FLASK_APP.test_request_context(json={'pr_number': 1}):
            args = parser.parse_args()
            self.assertEqual({}, args)

        only_attempt_id = {'attempt_id': "0"}
        with main.FLASK_APP.test_request_context(json=only_attempt_id):
            args = parser.parse_args()
            self.assertEqual(only_attempt_id, args)

        both = {'attempt_id': '0', 'import_name': 'name'}
        with main.FLASK_APP.test_request_context(json=both):
            args = parser.parse_args()
            self.assertEqual(both, args)

    def test_required_fields(self):
        """Tests that add_fields correctly adds required fields
        to the parser."""
        parser = reqparse.RequestParser()
        required_fields = [('pr_number', int)]
        utils.add_fields(parser, required_fields, required=True)

        with_pr = {'pr_number': 1, 'import_name': 'name'}
        with main.FLASK_APP.test_request_context(json=with_pr):
            args = parser.parse_args()
            self.assertEqual({'pr_number': 1}, args)

        without_pr = {'import_name': 'name'}
        with main.FLASK_APP.test_request_context(json=without_pr):
            with self.assertRaises(Exception) as context:
                parser.parse_args()
                self.assertEqual(400, context.exception.code)

    def test_combined(self):
        """Tests that add_fields correctly adds both required and
        optional fields to a parser."""
        parser = reqparse.RequestParser()
        required_fields = [('pr_number', int)]
        optional_fields = [('logs', dict, 'append')]
        utils.add_fields(parser, required_fields, required=True)
        utils.add_fields(parser, optional_fields, required=False)

        log_1 = {'level': 'info', 'message': 'ahhhhh'}
        log_2 = {'level': 'error', 'message': 'noooo'}
        with_pr_and_logs = {'pr_number': 1, 'logs': [log_1, log_2]}

        with main.FLASK_APP.test_request_context(json=with_pr_and_logs):
            args = parser.parse_args()
            self.assertEqual(with_pr_and_logs, args)

    def test_dict(self):
        """Tests parsing dicts."""
        parser = reqparse.RequestParser()
        utils.add_fields(parser, [('field', dict, 'append')], required=True)

        body = {'field': [{'abc': '1'}, {'def': '2'}]}
        with main.FLASK_APP.test_request_context(json=body):
            self.assertEqual(body, parser.parse_args())
