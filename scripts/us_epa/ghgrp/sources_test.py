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
"""Tests for sources.py"""

import os
import sys
import unittest

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_epa.ghgrp import sources


class SourcesTest(unittest.TestCase):

    def test_name_to_dcid(self):
        SOURCE_COLS_TO_DCID = {
            'Stationary Combustion':
                'Annual_Emissions_StationaryCombustion',
            'Electricity Generation':
                'Annual_Emissions_ElectricityGeneration',
            'Adipic Acid Production':
                'Annual_Emissions_AdipicAcidProduction',
            'HCFC–22 Production from HFC–23 Destruction':
                'Annual_Emissions_HCFC22ProductionFromHFC23Destruction',
            'Petroleum and Natural Gas Systems – Transmission/Compression':
                'Annual_Emissions_PetroleumAndNaturalGasSystems_TransmissionOrCompression',
            'Manufacture of Electric Transmission and Distribution Equipment':
                'Annual_Emissions_ManufactureOfElectricTransmissionAndDistributionEquipment',
        }
        for col, expected in SOURCE_COLS_TO_DCID.items():
            self.assertEqual(sources.col_to_sv(col), expected)


if __name__ == '__main__':
    unittest.main()
