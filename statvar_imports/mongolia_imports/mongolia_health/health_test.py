# Copyright 2026 Google LLC
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
"""Unit tests for Mongolia Health import."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from mongolia_test_helper import MongoliaImportTestBase


class MongoliaHealthTest(MongoliaImportTestBase):
    """Test suite for Mongolia Health data processing."""

    def test_deaths_by_month_and_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='deaths_by_month_and_region',
            pvmap='deaths_by_month_and_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_infant_mortality_per_1000_live_births_by_month_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='infant_mortality_per_1000_live_births_by_month_region',
            pvmap='infant_mortality_per_1000_live_births_by_month_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_live_births_by_month_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='live_births_by_month_region',
            pvmap='live_births_by_month_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_abortions_by_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_abortions_by_region',
            pvmap='number_of_abortions_by_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_hospital_beds_by_type(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_hospital_beds_by_type',
            pvmap='number_of_hospital_beds_by_type_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved=None,
        )

    def test_number_of_mothers_delivered_child_by_month_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_mothers_delivered_child_by_month_region',
            pvmap='number_of_mothers_delivered_child_by_month_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )


if __name__ == '__main__':
    unittest.main()
