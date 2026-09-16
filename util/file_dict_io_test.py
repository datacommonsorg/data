import unittest
import os
import tempfile
from file_dict_io import CsvFileDictIO, McfFileDictIO, open_dict_file


class TestFileDictIO(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_csv_write_and_read(self):
        csv_file_path = os.path.join(self.test_dir.name, 'test.csv')
        headers = ['name', 'age']
        data = [{'name': 'Alice', 'age': '30'}, {'name': 'Bob', 'age': '25'}]

        # Write CSV
        writer = CsvFileDictIO(csv_file_path, mode='w', headers=headers)
        for row in data:
            writer.write_record(row)
        writer.close()

        # Read CSV
        reader = CsvFileDictIO(csv_file_path, mode='r')
        read_data = []
        while True:
            row = reader.next()
            if row is None:
                break
            read_data.append(row)
        reader.close()

        self.assertEqual(headers, reader.headers())
        self.assertEqual(data, read_data)

    def test_mcf_write_and_read(self):
        mcf_file_path = os.path.join(self.test_dir.name, 'test.mcf')
        headers = ['# Test MCF']
        data = [{
            'Node': 'dcid:node1',
            'prop1': 'dcid:value1',
            'prop2': '"value2"'
        }, {
            'Node': 'dcid:node2',
            'prop1': 'dcid:value3',
            'prop2': '"value4"'
        }]

        # Write MCF
        writer = McfFileDictIO(mcf_file_path, mode='w', headers=headers)
        for node in data:
            writer.write_record(node)
        writer.close()

        # Read MCF
        reader = McfFileDictIO(mcf_file_path, mode='r')
        read_data = []
        while True:
            node = reader.next()
            if node is None:
                break
            read_data.append(node)
        reader.close()

        # Normalize read data for comparison
        normalized_read_data = []
        for node in read_data:
            normalized_node = {}
            for key, value in node.items():
                if key.startswith('#'):
                    continue
                if isinstance(value, list) and len(value) == 1:
                    normalized_node[key] = value[0]
                else:
                    normalized_node[key] = value
            normalized_read_data.append(normalized_node)

        self.assertEqual(len(data), len(normalized_read_data))
        for i in range(len(data)):
            self.assertDictEqual(data[i], normalized_read_data[i])

    def test_open_dict_file(self):
        csv_file_path = os.path.join(self.test_dir.name, 'test.csv')
        mcf_file_path = os.path.join(self.test_dir.name, 'test.mcf')

        csv_file = open_dict_file(csv_file_path, 'w', headers=['a', 'b'])
        self.assertIsInstance(csv_file, CsvFileDictIO)
        csv_file.close()

        mcf_file = open_dict_file(mcf_file_path, 'w')
        self.assertIsInstance(mcf_file, McfFileDictIO)
        mcf_file.close()


if __name__ == '__main__':
    unittest.main()
