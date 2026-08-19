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
"""Unit tests for Mongolia Employment import."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from mongolia_test_helper import MongoliaImportTestBase


class MongoliaEmploymentTest(MongoliaImportTestBase):
    """Test suite for Mongolia Employment data processing."""

    def test_employment_by_classification_of_economic_activities(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='employment_by_classification_of_economic_activities_region_gender_and_agegroup',
            pvmap='employment_by_classification_of_economic_activities_region_gender_and_agegroup_pvmap.csv',
            config='metadata.csv',
            places_resolved='places_resolved.csv',
        )

    def test_employment_by_occupation(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='employment_by_occupation_by_region_gender_and_agegroup',
            pvmap='employment_by_occupation_by_region_gender_and_agegroup_pvmap.csv',
            config='employment_by_occupation_by_region_gender_and_agegroup_metadata.csv',
            places_resolved='places_resolved.csv',
        )

    def test_employment_to_population_ratio(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='employment_to_population_ratio_by_region_gender_and_agegroup',
            pvmap='employment_to_population_ratio_by_region_gender_and_agegroup_pvmap.csv',
            config='employment_to_population_ratio_by_region_gender_and_agegroup_metadata.csv',
            places_resolved='places_resolved.csv',
        )

    def test_labour_force(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='labour_force_by_region_gender_and_agegroup',
            pvmap='labour_force_by_region_gender_and_agegroup_pvmap.csv',
            config='metadata.csv',
            places_resolved='places_resolved.csv',
        )

    def test_labour_underutilization(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='labour_underutilization_by_region_gender_and_agegroup',
            pvmap='labour_underutilization_by_region_gender_and_agegroup_pvmap.csv',
            config='metadata.csv',
            places_resolved='places_resolved.csv',
        )

    def test_registered_unemployed_by_education_level(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='registered_unemployed_by_education_level_region_gender_month',
            pvmap='registered_unemployed_by_education_level_region_gender_month_pvmap.csv',
            config='metadata.csv',
            places_resolved='places_resolved.csv',
        )


if __name__ == '__main__':
    unittest.main()
