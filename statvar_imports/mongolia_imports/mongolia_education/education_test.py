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
"""Unit tests for Mongolia Education import."""

import os
import sys
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

from mongolia_test_helper import MongoliaImportTestBase


class MongoliaEducationTest(MongoliaImportTestBase):
    """Test suite for Mongolia Education data processing."""

    def test_students_of_universities_and_colleges_by_professional_field(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='students_of_universities_and_colleges_by_professional_field',
            pvmap='students_of_universities_and_colleges_by_professional_field_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_students_in_teritary_educational_institutions_by_sex_and_educational_degree(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='students_in_teritary_educational_institutions_by_sex_and_educational_degree',
            pvmap='students_in_teritary_educational_institutions_by_sex_and_educational_degree_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_students_in_universities_and_colleges_by_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_students_in_universities_and_colleges_by_region',
            pvmap='number_of_students_in_universities_and_colleges_by_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_kindergartens_by_region(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_kindergartens_by_region',
            pvmap='number_of_kindergartens_by_region_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )

    def test_number_of_full_time_teachers_in_universities_and_colleges_by_sex(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='number_of_full_time_teachers_in_universities_and_colleges_by_sex',
            pvmap='number_of_full_time_teachers_in_universities_and_colleges_by_sex_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved=None,
        )

    def test_graduates_of_universities_and_colleges_by_professional_field(self):
        self.verify_processing(
            import_dir=_SCRIPT_DIR,
            prefix='graduates_of_universities_and_colleges_by_professional_field',
            pvmap='graduates_of_universities_and_colleges_by_professional_field_pvmap.csv',
            config='mongolia_metadata.csv',
            places_resolved='mongolia_place_resolver.csv',
        )


if __name__ == '__main__':
    unittest.main()
