# Copyright 2022 Google LLC
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
This module generates TMCF file in OUTPUT directory.
There are two tmcf files are generated
1. population_estimate_by_srh.tmcf - for importing as-is datq from US Census
2. population_estimate_by_srh_agg.tmcf - for importing aggregated data
"""

import os
from constants import OUTPUT_DIR
from constants import POPULATION_ESTIMATE_BY_SRH, POPULATION_ESTIMATE_BY_SRH_AGG

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
os.system("mkdir -p " + _CODEDIR + OUTPUT_DIR)


def generate_tmcf():
    """
    This function generates MCF file in OUTPUT directory.
    There are two mcf files generated
    1. population_estimate_by_srh.mcf - for importing as-is data from US Census
    2. population_estimate_by_srh_agg.mcf - for importing aggregated data
    OUTPUT directory is used as common between process.py and process_test.py
    """

    with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.tmcf',
              'w',
              encoding='utf-8') as file:
        file.writelines(POPULATION_ESTIMATE_BY_SRH)

    with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh_agg.tmcf',
              'w',
              encoding='utf-8') as file:
        file.writelines(POPULATION_ESTIMATE_BY_SRH_AGG)


if __name__ == '__main__':
    generate_tmcf()
