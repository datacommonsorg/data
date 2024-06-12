# Copyright 2022 Google LLC
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
"""Tests for brfss_asthma_import.py"""

import os
import unittest
import pandas as pd
from pandas.testing import assert_frame_equal

from .brfss_asthma_import import process_brfss_asthma


class ProcessTest(unittest.TestCase):

    def test_brfss_asthma_extracted_data(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        base_path = os.path.join(base_path, './data/test_data')
        inputfile_path = os.path.join(
            base_path, "./Extracted_State-maps-for-asthma-prevalence.tsv")
        process_brfss_asthma(input_dataset=inputfile_path,
                             sep="\t",
                             output_path=base_path)

        ## validate the csvs
        test_df = pd.read_csv(os.path.join(base_path, 'brfss_asthma.csv'))
        expected_df = pd.read_csv(
            os.path.join(base_path, 'brfss_asthma_expected.csv'))
        assert_frame_equal(test_df, expected_df)

        ## validate the statvar mcf
        f = open(os.path.join(base_path, 'brfss_asthma.mcf'), 'r')
        test_mcf = f.read()
        f.close()

        f = open(os.path.join(base_path, 'brfss_asthma_expected.mcf'), 'r')
        expected_mcf = f.read()
        f.close()

        self.assertEqual(test_mcf, expected_mcf)

        ## validate the template mcf
        f = open(os.path.join(base_path, 'brfss_asthma.tmcf'), 'r')
        test_tmcf = f.read()
        f.close()

        f = open(os.path.join(base_path, 'brfss_asthma_expected.tmcf'), 'r')
        expected_tmcf = f.read()
        f.close()

        self.assertEqual(test_tmcf, expected_tmcf)

        # clean up
        os.remove(os.path.join(base_path, 'brfss_asthma.csv'))
        os.remove(os.path.join(base_path, 'brfss_asthma.tmcf'))
        os.remove(os.path.join(base_path, 'brfss_asthma.mcf'))


if __name__ == '__main__':
    unittest.main()
