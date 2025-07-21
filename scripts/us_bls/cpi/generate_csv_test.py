# Copyright 2025 Google LLC
# Author: Shamim Ansari
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
import os
from absl import logging
import pandas as pd
from .generate_csv import process
from pathlib import Path

_MODULE_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(_MODULE_DIR, 'test_data')
actual_output_dir = os.path.join(TEST_DATA_DIR, 'actual_output')
input_files_dir = os.path.join(TEST_DATA_DIR, 'input_files')
output_dir = os.path.join(TEST_DATA_DIR, 'output_dir')
Path(output_dir).mkdir(parents=True, exist_ok=True)
SERIES_NAME_CPI_U = "cpi_u"
SERIES_NAME_CPI_W = "cpi_w"
SERIES_NAME_C_CPI_U = "c_cpi_u"

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestGenerateCSV(unittest.TestCase):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)

    def test_generate_csv_data(self):
        #Calling process method
        process(input_files_dir, output_dir, int(1946))
        #expected and actual comaparision for series_name_cpi_u = "cpi_u"
        expected_df_cpi_u = pd.read_csv(output_dir + "/" + SERIES_NAME_CPI_U +
                                        ".csv",
                                        sep=r"\s+",
                                        dtype="str")
        actual_df_cpi_u = pd.read_csv(actual_output_dir + "/" +
                                      SERIES_NAME_CPI_U + "_output" + ".csv",
                                      sep=r"\s+",
                                      dtype="str")
        pd.testing.assert_frame_equal(actual_df_cpi_u, expected_df_cpi_u)

        #expected and actual comaparision for series_name_cpi_w = "cpi_w"
        expected_df_cpi_w = pd.read_csv(output_dir + "/" + SERIES_NAME_CPI_W +
                                        ".csv",
                                        sep=r"\s+",
                                        dtype="str")
        actual_df_cpi_w = pd.read_csv(actual_output_dir + "/" +
                                      SERIES_NAME_CPI_W + "_output" + ".csv",
                                      sep=r"\s+",
                                      dtype="str")
        pd.testing.assert_frame_equal(actual_df_cpi_w, expected_df_cpi_w)

        #expected and actual comaparision for series_name_c_cpi_u = "c_cpi_u"
        expected_df_c_cpi_u = pd.read_csv(output_dir + "/" +
                                          SERIES_NAME_C_CPI_U + ".csv",
                                          sep=r"\s+",
                                          dtype="str")
        actual_df_c_cpi_u = pd.read_csv(
            actual_output_dir + "/" + SERIES_NAME_C_CPI_U + "_output" + ".csv",
            sep=r"\s+",
            dtype="str")
        pd.testing.assert_frame_equal(actual_df_c_cpi_u, expected_df_c_cpi_u)


if __name__ == '__main__':
    unittest.main()
