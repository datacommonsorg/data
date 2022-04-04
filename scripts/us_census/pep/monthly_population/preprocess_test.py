"""
Script to automate the testing for USA Population preprocess script.
"""

import os
import unittest
from os import path
from preprocess import CensusUSACountryPopulation
# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
test_data_folder = os.path.join(module_dir_, "test_data")
op_data_folder = os.path.join(module_dir_, "test_output_data")


class TestPreprocess(unittest.TestCase):
    """
    TestPreprocess is inherting unittest class
    properties which further requried for unit testing
    """

    cleaned_csv_file_path = os.path.join(op_data_folder, "data.csv")
    mcf_file_path = os.path.join(op_data_folder, "test_census.mcf")
    tmcf_file_path = os.path.join(op_data_folder, "test_census.tmcf")

    #ip_data_path = [os.path.join(test_data_folder, "test_data_2000_1998.txt")]
    ip_data_path = [os.path.join(test_data_folder, "test_census_data.xlsx")]

    base = CensusUSACountryPopulation(ip_data_path, cleaned_csv_file_path,
                                      mcf_file_path, tmcf_file_path)
    base.process()

    def test_mcf_tmcf_files(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like MCF File
        """
        expected_mcf_file_path = os.path.join(
            test_data_folder, "expected_USA_Population_Count.mcf")

        expected_tmcf_file_path = os.path.join(
            test_data_folder, "expected_USA_Population_Count.tmcf")

        with open(expected_mcf_file_path,
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        with open(self.mcf_file_path, encoding="UTF-8") as mcf_file:
            mcf_data = mcf_file.read()

        with open(self.tmcf_file_path, encoding="UTF-8") as tmcf_file:
            tmcf_data = tmcf_file.read()

        if path.exists(self.mcf_file_path):
            os.remove(self.mcf_file_path)
        if path.exists(self.tmcf_file_path):
            os.remove(self.tmcf_file_path)

        self.assertEqual(expected_mcf_data.strip(), mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(), tmcf_data.strip())

    def test_create_csv(self):
        """
        This method is required to test between output generated
        preprocess script and excepted output files like CSV
        """
        expected_csv_file_path = os.path.join(
            test_data_folder, "expected_USA_Population_Count.csv")

        expected_csv_data = ""
        with open(expected_csv_file_path,
                  encoding="utf-8-sig") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        with open(self.cleaned_csv_file_path, encoding="utf-8-sig") as csv_file:
            csv_data = csv_file.read()

        if path.exists(self.cleaned_csv_file_path):
            os.remove(self.cleaned_csv_file_path)

        self.assertEqual(expected_csv_data.strip(), csv_data.strip())
