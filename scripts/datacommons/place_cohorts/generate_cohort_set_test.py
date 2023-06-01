"""Tests for generate_cohort_set.py."""

import io

from .generate_cohort_set import write_mcf
import unittest

TEST_DIR = 'testdata/'


class WriteMCFTest(unittest.TestCase):

    def test_subset(self):
        csv_file = TEST_DIR + 'test.csv'
        expected_mcf_file = TEST_DIR + 'expected.mcf'
        with open(expected_mcf_file, 'rt') as mcf_file:
            expected_mcf = mcf_file.read()

        with open(csv_file, 'rt') as f_in:
            f_out = io.StringIO()
            write_mcf(f_in, f_out, "AwesomePlaces", "fooId",
                      "List of awesome test places.")
        self.assertEqual(f_out.getvalue(), expected_mcf)


if __name__ == '__main__':
    unittest.main()
