import unittest
import os
import csv
import convert_textproto_to_csv


class ConvertTextprotoToCsvTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(os.path.dirname(__file__), 'testdata')
        self.textproto_path = os.path.join(self.test_data_dir,
                                           'all_incentives.textproto')
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
            reader_actual = csv.DictReader(f_actual)
            reader_expected = csv.DictReader(f_expected)

            # Convert to lists of dicts
            rows_actual = list(reader_actual)
            rows_expected = list(reader_expected)

            # Compare sets of dictionaries to ignore row order
            self.assertEqual(len(rows_actual), len(rows_expected))
            for row_a in rows_actual:
                self.assertIn(row_a, rows_expected)


if __name__ == '__main__':
    unittest.main()
