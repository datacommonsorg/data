# Copyright 2021 Google LLC
#
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
"""Tests for gas.py"""

import os
import sys
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_epa.ghgrp import gas


class GasTest(unittest.TestCase):

    def test_name_to_dcid(self):
        GAS_COL_NAMES_TO_DCID = {
            'Total reported direct emissions':
                'Annual_Emissions_GreenhouseGas',
            'CO2 emissions (non-biogenic)':
                'Annual_Emissions_CarbonDioxide_NonBiogenic',
            'Methane (CH4) emissions':
                'Annual_Emissions_Methane',
            'Nitrous Oxide (N2O) emissions':
                'Annual_Emissions_NitrousOxide',
            'HFC emissions':
                'Annual_Emissions_HFC',
            'PFC emissions':
                'Annual_Emissions_PFC',
            'SF6 emissions':
                'Annual_Emissions_SF6',
            'NF3 emissions':
                'Annual_Emissions_NF3',
            'Other Fully Fluorinated GHG emissions':
                'Annual_Emissions_EPA_OtherFullyFluorinatedGHG',
            'HFE emissions':
                'Annual_Emissions_HFE',
            'Very Short-lived Compounds emissions':
                'Annual_Emissions_VeryShortLivedCompounds',
            'Other GHGs (metric tons CO2e)':
                'Annual_Emissions_EPA_OtherGHGs',
            'Biogenic CO2 emissions (metric tons)':
                'Annual_Emissions_CarbonDioxide_Biogenic',
            'Total reported emissions from Onshore Oil & Gas Production':
                'Annual_Emissions_GreenhouseGas',
            'Total reported emissions from Gathering & Boosting':
                'Annual_Emissions_GreenhouseGas',
            'Total reported direct emissions from Local Distribution Companies':
                'Annual_Emissions_GreenhouseGas',
            'Methane (CH4) emissions ':
                'Annual_Emissions_Methane',
        }
        for col, expected in GAS_COL_NAMES_TO_DCID.items():
            self.assertEqual(gas.col_to_sv(col), expected)


if __name__ == '__main__':
    unittest.main()
