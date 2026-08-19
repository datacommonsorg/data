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
"""Unit tests for Mongolia Demographics import."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from mongolia_test_helper import MongoliaImportTestBase


class MongoliaDemographicsTest(MongoliaImportTestBase):
    """Test suite for Mongolia Demographics data processing."""

    def test_mid_year_total_population_by_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='mid_year_total_population_by_region',
            pvmap='mid_year_total_population_by_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_households_by_region_and_urban_rural(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_households_by_region_and_urban_rural',
            pvmap='number_of_households_by_region_and_urban_rural_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_households_by_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_households_by_region',
            pvmap='number_of_households_by_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_resident_population_by_agegroup_15_and_over_and_maritalstatus(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='resident_population_by_agegroup_15_and_over_and_maritalstatus',
            pvmap='resident_population_by_agegroup_15_and_over_and_maritalstatus_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved=None,
        )

    def test_total_population_by_age_group_and_sex(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='total_population_by_age_group_and_sex',
            pvmap='total_population_by_age_group_and_sex_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved=None,
        )

    def test_total_population_by_region_and_urban_rural(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='total_population_by_region_and_urban_rural',
            pvmap='total_population_by_region_and_urban_rural_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_total_population_by_sex_and_urban_rural(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='total_population_by_sex_and_urban_rural',
            pvmap='total_population_by_sex_and_urban_rural_pvmap.csv',
            config='total_population_by_sex_and_urban_rural_metadata.csv',
            places_resolved=None,
        )


if __name__ == '__main__':
    unittest.main()
