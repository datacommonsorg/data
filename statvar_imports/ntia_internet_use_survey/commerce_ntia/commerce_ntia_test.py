# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit and regression tests for commerce_ntia statvar import."""

import os
import subprocess
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, '../../../'))
_TOOLS_DIR = os.path.join(_DATA_DIR, 'tools/statvar_importer')
sys.path.insert(0, _TOOLS_DIR)
sys.path.insert(0, os.path.join(_DATA_DIR, 'util'))
from counters import Counters
from mcf_diff import diff_mcf_files


class CommerceNtiaTest(unittest.TestCase):

    def setUp(self):
        self.testdata_dir = os.path.join(_SCRIPT_DIR, 'testdata')
        self.processor_path = os.path.join(_TOOLS_DIR, 'stat_var_processor.py')
        self.pv_map = os.path.join(_SCRIPT_DIR, 'ntia_pvmap.csv')
        self.metadata = os.path.join(_SCRIPT_DIR, 'ntia_metadata.csv')

    def test_stat_var_processor_ntia_output(self):
        """Tests that stat_var_processor generates expected outputs for ntia-data.csv."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, 'ntia_output')
            cmd = [
                sys.executable,
                self.processor_path,
                f'--input_data={os.path.join(self.testdata_dir, "ntia-data.csv")}',
                f'--pv_map={self.pv_map}',
                f'--config_file={self.metadata}',
                f'--output_path={output_path}',
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0,
                             f'Processor failed: {res.stderr}')

            # Verify CSV
            gen_csv = os.path.join(tmp_dir, 'ntia_output.csv')
            exp_csv = os.path.join(self.testdata_dir, 'ntia_output.csv')
            with open(gen_csv,
                      encoding='utf-8') as g, open(exp_csv,
                                                   encoding='utf-8') as e:
                self.assertEqual(g.read().strip(), e.read().strip())

            # Verify TMCF
            gen_tmcf = os.path.join(tmp_dir, 'ntia_output.tmcf')
            exp_tmcf = os.path.join(self.testdata_dir, 'ntia_output.tmcf')
            with open(gen_tmcf,
                      encoding='utf-8') as g, open(exp_tmcf,
                                                   encoding='utf-8') as e:
                self.assertEqual(g.read().strip(), e.read().strip())

            # Verify StatVar MCF
            gen_mcf = os.path.join(tmp_dir, 'ntia_output_stat_vars.mcf')
            exp_mcf = os.path.join(self.testdata_dir,
                                   'ntia_output_stat_vars.mcf')
            counters = Counters()
            diff = diff_mcf_files(gen_mcf, exp_mcf,
                                  {'show_diff_nodes_only': True}, counters)
            self.assertEqual(len(diff), 0, f'MCF diff found: {diff}')


if __name__ == '__main__':
    unittest.main()
