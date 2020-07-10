import unittest
from unittest import mock

from app.resource import import_attempt_list
from test import utils


class ImportAttemptListTest(unittest.TestCase):
    """Tests for ImportAttemptList."""

    @classmethod
    def setUpClass(cls):
        cls.emulator = utils.start_emulator()

    @classmethod
    def tearDownClass(cls):
        utils.terminate_emulator(cls.emulator)

    @mock.patch('app.utils.create_datastore_client',
                utils.create_test_datastore_client)
    def setUp(self):
        """Injects several import attempts to the database."""
        attempt_0 = {'attempt_id': '0', 'import_name': 'name', 'run_id': '0'}
        attempt_1 = {'attempt_id': '1', 'import_name': 'name', 'run_id': '1'}
        attempt_2 = {'attempt_id': '2', 'import_name': 'name', 'run_id': '1'}
        attempt_3 = {'attempt_id': '3', 'import_name': 'eman', 'run_id': '3'}
        returns = [attempt_0, attempt_1, attempt_2, attempt_3]
        with mock.patch(utils.PARSE_ARGS) as parse_args:
            parse_args.side_effect = returns
            self.attempts = returns

            self.resource = import_attempt_list.ImportAttemptList()
            for _ in returns:
                self.resource.post()

    @mock.patch(utils.PARSE_ARGS, lambda self: {'import_name': 'name'})
    def test_get_by_name(self):
        """Tests filtering by import_name returns the correct attempts."""
        attempts = self.resource.get()
        self.assertEqual(4, len(attempts))
        self.assertEqual(self.attempts, attempts)

    @mock.patch(utils.PARSE_ARGS, lambda self: {'attempt_id': '1'})
    def test_get_by_id(self):
        """Tests filtering by attempt_id returns the only correct attempt."""
        attempts = self.resource.get()
        self.assertEqual(1, len(attempts))
        self.assertIn(self.attempts[1], attempts)

    @mock.patch(utils.PARSE_ARGS,
                lambda self: {'import_name': 'name', 'run_id': '1'})
    def test_get_by_import_name_and_run_id(self):
        """Tests filtering by import_name and pr_number returns
        the correct attempts."""
        attempts = self.resource.get()
        self.assertEqual(2, len(attempts))
        self.assertIn(self.attempts[1], attempts)
        self.assertIn(self.attempts[2], attempts)

    @mock.patch(utils.PARSE_ARGS, lambda self: {'import_name': 'noooo'})
    def test_get_not_exist(self):
        """Tests empty result."""
        attempts = self.resource.get()
        self.assertEqual([], attempts)
