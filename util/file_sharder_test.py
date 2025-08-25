import unittest
import os
import tempfile
import csv
from absl import logging
from file_sharder import FileSharder, shard_file
from file_dict_io import McfFileDictIO


class TestFileSharder(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.input_file_path = os.path.join(self.test_dir.name, 'input.csv')
        self.mcf_input_file_path = os.path.join(self.test_dir.name, 'input.mcf')

    def tearDown(self):
        self.test_dir.cleanup()

    def _create_csv_file(self, data):
        with open(self.input_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _create_mcf_file(self, data):
        writer = McfFileDictIO(self.mcf_input_file_path, mode='w')
        for node in data:
            writer.write_record(node)
        writer.close()

    def test_shard_csv_file(self):
        data = [
            {
                'id': '11',
                'value': 'a'
            },
            {
                'id': '21',
                'value': 'b'
            },
            {
                'id': '11',
                'value': 'c'
            },
            {
                'id': '31',
                'value': 'd'
            },
        ]
        self._create_csv_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@3.csv')
        config = {'shard_key': '{id}'}
        shard_file(self.input_file_path, output_path, config)

        # Verify output files
        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00003.csv')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00003.csv')
        shard_2_path = os.path.join(self.test_dir.name,
                                    'output-00002-of-00003.csv')

        self.assertTrue(os.path.exists(shard_0_path))
        self.assertTrue(os.path.exists(shard_1_path))
        self.assertTrue(os.path.exists(shard_2_path))

        with open(shard_1_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['id'], '11')
            self.assertEqual(rows[1]['id'], '11')

    def test_shard_mcf_file(self):
        data = [
            {
                'Node': 'dcid:node11',
                'prop': 'a'
            },
            {
                'Node': 'dcid:node22',
                'prop': 'b'
            },
            {
                'Node': 'dcid:node11',
                'prop': 'c'
            },
            {
                'Node': 'dcid:node33',
                'prop': 'd'
            },
        ]
        self._create_mcf_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@3.mcf')
        config = {'shard_key': 'Node'}
        shard_file(self.mcf_input_file_path, output_path, config)

        # Verify output files
        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00003.mcf')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00003.mcf')
        shard_2_path = os.path.join(self.test_dir.name,
                                    'output-00002-of-00003.mcf')

        self.assertTrue(os.path.exists(shard_0_path))
        self.assertTrue(os.path.exists(shard_1_path))
        self.assertTrue(os.path.exists(shard_2_path))

        reader = McfFileDictIO(shard_0_path, 'r')
        nodes = []
        node = reader.next()
        while node:
            nodes.append(node)
            node = reader.next()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0]['Node'], 'dcid:node11')
        self.assertEqual(nodes[1]['Node'], 'dcid:node11')

    def test_skip_duplicates(self):
        data = [
            {
                'id': '1',
                'value': 'a'
            },
            {
                'id': '2',
                'value': 'b'
            },
            {
                'id': '1',
                'value': 'a'
            },  # duplicate
            {
                'id': '3',
                'value': 'd'
            },
        ]
        self._create_csv_file(data)

        output_path = os.path.join(self.test_dir.name, 'output@2.csv')
        config = {'shard_key': 'id', 'shard_skip_duplicates': True}
        shard_file(self.input_file_path, output_path, config)

        shard_0_path = os.path.join(self.test_dir.name,
                                    'output-00000-of-00002.csv')
        shard_1_path = os.path.join(self.test_dir.name,
                                    'output-00001-of-00002.csv')

        with open(shard_0_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['id'], '2')

        with open(shard_1_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['id'], '1')
            self.assertEqual(rows[1]['id'], '3')


if __name__ == '__main__':
    unittest.main()
