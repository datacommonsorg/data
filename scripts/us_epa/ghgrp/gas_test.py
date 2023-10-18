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
                'Annual_Emissions_GreenhouseGas_NonBiogenic',
            'CO2 emissions (non-biogenic)':
                'Annual_Emissions_CarbonDioxide_NonBiogenic',
            'Methane (CH4) emissions':
                'Annual_Emissions_Methane_NonBiogenic',
            'Nitrous Oxide (N2O) emissions':
                'Annual_Emissions_NitrousOxide_NonBiogenic',
            'HFC emissions':
                'Annual_Emissions_Hydrofluorocarbon_NonBiogenic',
            'PFC emissions':
                'Annual_Emissions_Perfluorocarbon_NonBiogenic',
            'SF6 emissions':
                'Annual_Emissions_SulfurHexafluoride_NonBiogenic',
            'NF3 emissions':
                'Annual_Emissions_NitrogenTrifluoride_NonBiogenic',
            'Other Fully Fluorinated GHG emissions':
                'Annual_Emissions_EPA_OtherFullyFluorinatedCompound_NonBiogenic',
            'HFE emissions':
                'Annual_Emissions_Hydrofluoroether_NonBiogenic',
            'Very Short-lived Compounds emissions':
                'Annual_Emissions_VeryShortLivedCompounds_NonBiogenic',
            'Other GHGs (metric tons CO2e)':
                'Annual_Emissions_EPA_OtherGreenhouseGas_NonBiogenic',
            'Biogenic CO2 emissions (metric tons)':
                'Annual_Emissions_CarbonDioxide_Biogenic',
            'Total reported emissions from Onshore Oil & Gas Production':
                'Annual_Emissions_GreenhouseGas_NonBiogenic',
            'Total reported emissions from Gathering & Boosting':
                'Annual_Emissions_GreenhouseGas_NonBiogenic',
            'Total reported direct emissions from Local Distribution Companies':
                'Annual_Emissions_GreenhouseGas_NonBiogenic',
        }
        for col, expected in GAS_COL_NAMES_TO_DCID.items():
            self.assertEqual(gas.col_to_sv(col), expected)


if __name__ == '__main__':
    unittest.main()
