# Copyright 2020 Google LLC
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

import unittest
import os
import filecmp


class PreprocessCSVTest(unittest.TestCase):

    def test_generate_tmcf(self):
        output_columns = ['Date', 'GeoId',
                          'COVID19CumulativeTestResults', 'COVID19NewTestResults',
                          'COVID19CumulativePositiveTestResults', 'COVID19NewPositiveTestResults',
                          'COVID19CumulativeNegativeTestResults', 'COVID19NewNegativeTestResults']

        TEMPLATE_MCF_GEO = """
Node: E:COVIDTracking_States->E0
typeOf: schema:State
dcid: C:COVIDTracking_States->GeoId
"""

        TEMPLATE_MCF_TEMPLATE = """
Node: E:COVIDTracking_States->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: E:COVIDTracking_States->E0
observationDate: C:COVIDTracking_States->Date
value: C:COVIDTracking_States->{stat_var}
"""

        stat_vars = output_columns[2:]
        with open('test_tmcf.tmcf', 'w', newline='') as f_out:
            f_out.write(TEMPLATE_MCF_GEO)
            for i in range(len(stat_vars)):
                f_out.write(TEMPLATE_MCF_TEMPLATE.format_map({'index': i + 1, 'stat_var': output_columns[2:][i]}))

        same = filecmp.cmp('test_tmcf.tmcf', 'test_expected_tmcf.tmcf')
        os.remove('test_tmcf.tmcf')

        self.assertTrue(same)

if __name__ == '__main__':
    unittest.main()