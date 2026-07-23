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
"""Tests for generate_codelist_map.py."""

import os
import shutil
import sys
import tempfile
import unittest

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_DATA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import generate_codelist_map


class GenerateCodelistMapTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_value(self):
        input_pvs = {'CONCEPT': 'SERIES', 'CODE': 'POP'}
        val = generate_codelist_map.get_value('{CONCEPT}:{CODE}', input_pvs)
        val_prop = generate_codelist_map.get_value(
            'to_property(CONCEPT)', input_pvs
        )
        self.assertEqual(val_prop, 'series')

    def test_generate_code_map(self):
        code_pvs = {
            'CONCEPT': 'SERIES',
            'CODE': 'TOTAL_POP',
            'NAME_EN': 'Total Population',
            'DESCRIPTION': 'Total population of place',
        }
        pvs = generate_codelist_map.generate_code_map(code_pvs, namespace='un')
        self.assertEqual(pvs['key'], 'SERIES:TOTAL_POP')
        self.assertEqual(pvs['ConstraintProp'], 'populationType')
        self.assertEqual(pvs['ConstraintPropValue'], 'UN_SERIES-TOTAL_POP')

    def test_generate_codelist_pvmap_with_skips(self):
        csv_path = os.path.join(self.test_dir, 'test_codelist.csv')
        out_path = os.path.join(self.test_dir, 'test_output.csv')
        with open(csv_path, 'w') as f:
            f.write('CONCEPT,CODE,NAME_EN,DESCRIPTION\n')
            f.write('SERIES,TOTAL_POP,Total Population,Total population\n')
            f.write('UNIT_MULT,6,Millions,Scale factor\n')
            f.write('FREQUENCY,A,Annual,Annual data\n')
            f.write('GEOGRAPHY,USA,United States,US region\n')

        output_pvs = generate_codelist_map.generate_codelist_pvmap(
            cl_file=csv_path,
            output=out_path,
            namespace='un',
            skip_concepts_set={'UNIT_MULT', 'FREQUENCY', 'GEOGRAPHY'},
        )
        self.assertTrue(os.path.exists(out_path))
        self.assertEqual(len(output_pvs), 1)
        with open(out_path, 'r') as f:
            content = f.read()
            self.assertIn('SERIES:TOTAL_POP', content)
            self.assertNotIn('UNIT_MULT:6', content)
            self.assertNotIn('FREQUENCY:A', content)
            self.assertNotIn('GEOGRAPHY:USA', content)

    def test_generate_codelist_pvmaps_wrapper(self):
        cl1 = os.path.join(self.test_dir, 'cl1.csv')
        cl2 = os.path.join(self.test_dir, 'cl2.csv')
        out_dir = os.path.join(self.test_dir, 'out_dir')
        os.makedirs(out_dir)

        with open(cl1, 'w') as f:
            f.write('CONCEPT,CODE,NAME_EN,DESCRIPTION\n')
            f.write('SERIES,TOTAL_POP,Total Population,Total population\n')
        with open(cl2, 'w') as f:
            f.write('CONCEPT,CODE,NAME_EN,DESCRIPTION\n')
            f.write('UNIT_MEASURE,PT,Percent,Percentage\n')

        results = generate_codelist_map.generate_codelist_pvmaps(
            input_files=[cl1, cl2],
            output_path=out_dir,
            namespace='un',
        )
        self.assertEqual(len(results), 2)
        out_cl1 = os.path.join(out_dir, 'cl1_pvmap.csv')
        out_cl2 = os.path.join(out_dir, 'cl2_pvmap.csv')
        self.assertTrue(os.path.exists(out_cl1))
        self.assertTrue(os.path.exists(out_cl2))

    def test_generate_codelist_pvmaps_single_file_compatibility(self):
        cl1 = os.path.join(self.test_dir, 'single.csv')
        out_file = os.path.join(self.test_dir, 'single_out.csv')
        with open(cl1, 'w') as f:
            f.write('CONCEPT,CODE,NAME_EN,DESCRIPTION\n')
            f.write('SERIES,TOTAL_POP,Total Population,Total population\n')

        results = generate_codelist_map.generate_codelist_pvmaps(
            input_files=cl1,
            output_path=out_file,
            namespace='un',
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(os.path.exists(out_file))

    def test_normalize_skip_concepts(self):
        skips_list = ['unit_mult', 'frequency']
        self.assertEqual(
            generate_codelist_map.normalize_skip_concepts(skips_list),
            {'UNIT_MULT', 'FREQUENCY'},
        )
        skips_str = 'unit_mult, frequency; geography'
        self.assertEqual(
            generate_codelist_map.normalize_skip_concepts(skips_str),
            {'UNIT_MULT', 'FREQUENCY', 'GEOGRAPHY'},
        )
        self.assertEqual(
            generate_codelist_map.normalize_skip_concepts(None), set()
        )

    def test_resolve_output_file(self):
        cl_path = os.path.join(self.test_dir, 'sample.csv')
        out_dir = os.path.join(self.test_dir, 'resolved_dir')
        res = generate_codelist_map.resolve_output_file(
            cl_path, out_dir, is_multi_file=True
        )
        self.assertEqual(res, os.path.join(out_dir, 'sample_pvmap.csv'))

    def test_complex_error_handling_and_formatting(self):
        # 1. clean_value_str quotes and complex regex
        self.assertEqual(
            generate_codelist_map.clean_value_str(
                'foo###bar', regex=r'#+', replace='-'
            ),
            'foo-bar',
        )
        self.assertEqual(
            generate_codelist_map.clean_value_str('"  Already Wrapped  "'),
            '"Already Wrapped"',
        )

        # 2. get_value error recovery branches
        self.assertEqual(
            generate_codelist_map.get_value(
                '{CONCEPT:{CODE}', {'CONCEPT': 'S', 'CODE': '1'}
            ),
            '',
        )
        self.assertEqual(
            generate_codelist_map.get_value(
                'nonexistent_function(CONCEPT)', {'CONCEPT': 'SERIES'}
            ),
            '',
        )

        # 3. generate_codelist_pvmap missing file/template handling
        res_missing = generate_codelist_map.generate_codelist_pvmap(
            '/nonexistent/path/cl.csv', '/tmp/out.csv'
        )
        self.assertEqual(res_missing, {})

        csv_path = os.path.join(self.test_dir, 'sample.csv')
        with open(csv_path, 'w') as f:
            f.write('CONCEPT,CODE,NAME_EN,DESCRIPTION\nSERIES,1,One,Test\n')
        res_bad_tpl = generate_codelist_map.generate_codelist_pvmap(
            csv_path, '/tmp/out.csv', pvmap_template={}
        )
        self.assertEqual(res_bad_tpl, {})


if __name__ == '__main__':
    unittest.main()
