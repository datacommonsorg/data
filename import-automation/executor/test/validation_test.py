# Copyright 2020 Google LLC
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
"""
Tests for validation.py.
"""

import os
import tempfile
import unittest

from app.executor import validation


class ValidationTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self.tmp_dir.name

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_import_spec_valid(self):
        import_dir = 'scripts/us_fed'
        os.makedirs(os.path.join(self.repo_dir, import_dir, 'dir'),
                    exist_ok=True)

        script_path = os.path.join(self.repo_dir, import_dir, 'dir/foo.py')
        print(script_path)
        with open(script_path, 'w+') as script:
            script.write('line\n')
            script.flush()
        script_path = os.path.join(self.repo_dir, import_dir, 'bar.py')
        with open(script_path, 'w+') as script:
            script.write('line\n')
            script.flush()
        spec = {
            'import_name': 'treausry',
            'provenance_url': 'url',
            'provenance_description': 'description',
            'curator_emails': 'curator',
            'scripts': ['dir/foo.py', 'dir/../bar.py']
        }
        validation._is_import_spec_valid(spec, self.repo_dir, import_dir)

    def test_import_spec_valid_fields_absent(self):
        spec = {
            'import_name': 'treausry',
            'scripts': ['dir/foo.py', 'dir/../bar.py']
        }
        with self.assertRaises(ValueError) as context:
            validation._is_import_spec_valid(spec, self.repo_dir,
                                             'scripts/us_fed')
            self.assertIn(
                'provenance_url, provenance_description, curator_emails',
                str(context.exception))

    def test_import_spec_valid_script_not_exist(self):
        spec = {
            'import_name': 'treausry',
            'provenance_url': 'url',
            'provenance_description': 'description',
            'curator_emails': 'curator',
            'scripts': ['dir/foo.py', 'dir/../bar.py']
        }
        with self.assertRaises(ValueError) as context:
            validation._is_import_spec_valid(spec, self.repo_dir,
                                             'scripts/us_fed')
            self.assertIn('dir/foo.py, dir/../bar.py', str(context.exception))

    def test_manifest_valid_fields_absent(self):
        with self.assertRaises(ValueError) as context:
            validation.is_manifest_valid({}, self.repo_dir, 'scripts/us_fed')
            self.assertIn('import_specifications not found',
                          str(context.exception))
