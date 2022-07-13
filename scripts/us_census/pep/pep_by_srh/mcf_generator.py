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
This module generates MCF file in OUTPUT directory.
There are two mcf files generated
1. population_estimate_by_srh.mcf - for importing as-is data from US Census
2. population_estimate_by_srh_agg.mcf - for importing aggregated data
"""

import os
from constants import OUTPUT_DIR, MCF_SRH, MCF_SH, MCF_RH

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def generate_mcf():
    """
    This function generates MCF file in OUTPUT directory.
    There are two mcf files generated
    1. population_estimate_by_srh.mcf - for importing as-is data from US Census
    2. population_estimate_by_srh_agg.mcf - for importing aggregated data
    OUTPUT directory is used as common between process.py and process_test.py
    """
    os.system("mkdir -p " + _CODEDIR + OUTPUT_DIR)
    genderType = ['Male', 'Female']
    hispanic = ['HispanicOrLatino', 'NotHispanicOrLatino']
    race = [
        'WhiteAlone', 'BlackOrAfricanAmericanAlone',
        'AmericanIndianOrAlaskaNativeAlone', 'AsianOrPacificIslander',
        'AsianAlone', 'NativeHawaiianOrOtherPacificIslanderAlone',
        'TwoOrMoreRaces', 'WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
        'BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
        'AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
        'AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
        'NativeHawaiianAndOtherPacificIslanderAloneOrInCombination\
WithOneOrMoreOtherRaces'
    ]

    # Count_Person_Male_NotHispanicOrLatino_WhiteAlone
    # Count_Person_Female_NotHispanicOrLatino_WhiteAlone
    # SV's are already present, hence not generating them
    mcf = ""

    for gt in genderType:
        for h in hispanic:
            for r in race:
                if 'Count_Person_' + gt + '_' + h + '_' + r not in [
                        'Count_Person_Male_NotHispanicOrLatino_WhiteAlone',
                        'Count_Person_Female_NotHispanicOrLatino_WhiteAlone'
                ]:
                    mcf += MCF_SRH.format(node_name='Count_Person_' + gt + '_' +
                                          h + '_' + r,
                                          gender=gt,
                                          race=h + '__' + r)

    for gt in genderType:
        for h in hispanic:
            mcf += MCF_SRH.format(node_name='Count_Person_' + gt + '_' + h,
                                  gender=gt,
                                  race=h)

    with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.mcf',
              'w',
              encoding='utf-8') as mcf_file:
        mcf_file.write(mcf)

    # Following section created MCF nodes for Aggregated data
    # E.g., of gggregate: Hispanic = Hispanic Male + Hispanic Female

    mcf = ""

    # Count_Person_NotHispanicOrLatino_WhiteAlone
    # SV is already present, hence not generating it.
    for h in hispanic:
        for r in race:
            if 'Count_Person_' + h + '_' + r != \
                'Count_Person_NotHispanicOrLatino_WhiteAlone':
                mcf += MCF_RH.format(node_name='Count_Person_' + h + '_' + r,
                                     race=h + '__' + r)

    with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh_agg.mcf',
              'w',
              encoding='utf-8') as mcf_file:
        mcf_file.write(mcf)


if __name__ == '__main__':
    generate_mcf()
