import unittest
from unittest import mock

from app.resource import import_attempt
from test import utils
from test.utils import EXAMPLE_ATTEMPT


class ImportAttemptListTest(unittest.TestCase):
    """Tests for ImportAttemptList."""

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects several attempts to the database."""
        attempt_0 = EXAMPLE_ATTEMPT
        attempt_1 = {'attempt_id': '1', 'import_name': 'name', 'pr_number': 1}
        attempt_2 = {'attempt_id': '2', 'import_name': 'name', 'pr_number': 1}
        attempt_3 = {'attempt_id': '3', 'import_name': 'nameeeee'}
        returns = [attempt_0, attempt_1, attempt_2, attempt_3]
        with mock.patch(utils.PARSE_ARGS) as utils.PARSE_ARGS:
            utils.PARSE_ARGS.side_effect = returns
            self.attempts = returns

            self.resource = import_attempt.ImportAttemptByID()
            self.resource.put(attempt_0['attempt_id'])
            self.resource.put(attempt_1['attempt_id'])
            self.resource.put(attempt_2['attempt_id'])
            self.resource.put(attempt_3['attempt_id'])
            self.resource = self.resource

    @mock.patch(utils.PARSE_ARGS, lambda self: {'import_name': 'name'})
    def test_get_by_name(self):
        """Tests filtering by import_name returns the correct attempts."""
        attempt_list = app.resource.import_attempt_list.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(3, len(attempts))
        self.assertIn(self.attempts[0], attempts)
        self.assertIn(self.attempts[1], attempts)
        self.assertIn(self.attempts[2], attempts)

    @mock.patch(utils.PARSE_ARGS, lambda self: {'attempt_id': '1'})
    def test_get_by_id(self):
        """Tests filtering by attempt_id returns the only correct attempt."""
        attempt_list = app.resource.import_attempt_list.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(1, len(attempts))
        self.assertIn(self.attempts[1], attempts)

    @mock.patch(utils.PARSE_ARGS,
                lambda self: {'import_name': 'name', 'pr_number': 1})
    def test_get_by_name_and_repo_num(self):
        """Tests filtering by import_name and pr_number returns
        the correct attempts."""
        attempt_list = app.resource.import_attempt_list.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual(2, len(attempts))
        self.assertIn(self.attempts[1], attempts)
        self.assertIn(self.attempts[2], attempts)

    @mock.patch(utils.PARSE_ARGS, lambda self: {'import_name': 'noooo'})
    def test_get_not_exist(self):
        """Tests empty result."""
        attempt_list = app.resource.import_attempt_list.ImportAttemptList()
        attempts = attempt_list.get()
        self.assertEqual([], attempts)