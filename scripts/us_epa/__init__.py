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
"""Test discovery configuration for scripts/us_epa."""

import importlib
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_TEST_SUBDIRS = (
    'airdata',
    'ejscreen',
    'facility',
    'ghgrp',
    'national_emissions_inventory',
    'parent_company',
)


def load_tests(loader, standard_tests, pattern):
    pattern = pattern or '*_test.py'
    helper_test_mod = importlib.import_module(
        f'{__name__}.facilities_helper_test')
    standard_tests.addTests(loader.loadTestsFromModule(helper_test_mod))
    for subdir in _TEST_SUBDIRS:
        subdir_path = os.path.join(_THIS_DIR, subdir)
        if os.path.isdir(subdir_path):
            standard_tests.addTests(
                loader.discover(start_dir=subdir_path, pattern=pattern))
    return standard_tests
