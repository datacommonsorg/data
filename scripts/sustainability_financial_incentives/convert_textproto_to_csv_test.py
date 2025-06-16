import unittest
import os
import csv
import convert_textproto_to_csv


class ConvertTextprotoToCsvTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
        self.textproto_path = os.path.join(self.test_data_dir,
                                           'sample_incentives.textproto')
        self.csv_path = os.path.join(self.test_data_dir, 'output.csv')

    def tearDown(self):
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)

    def test_convert_textproto_to_csv(self):
        convert_textproto_to_csv.convert_textproto_to_csv(
            self.textproto_path, self.csv_path)
        self.assertTrue(os.path.exists(self.csv_path))

        with open(self.csv_path, 'r', encoding='utf-8') as f_actual, open(
                os.path.join(self.test_data_dir, 'expected_output.csv'),
                'r',
                encoding='utf-8') as f_expected:
            reader_actual = csv.reader(f_actual)
            reader_expected = csv.reader(f_expected)

            header_actual = next(reader_actual)
            header_expected = next(reader_expected)
            self.assertEqual(header_actual, header_expected)

            # Sort the rows to ignore order
            rows_actual = sorted(list(reader_actual))
            rows_expected = sorted(list(reader_expected))

            self.assertEqual(rows_actual, rows_expected)


if __name__ == '__main__':
    unittest.main()
