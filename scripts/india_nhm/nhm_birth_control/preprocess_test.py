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

import os
import unittest
from india_nhm.base.data_cleaner import NHMDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
cols_to_nodes = {
    'District':
        'District',
    'DistrictCode':
        'DistrictCode',
    'Date':
        'Date',
    'Number of Vasectomies Conducted (Public + Pvt.)':
        'Count_BirthControlEvent_Vasectomy',
    'Number of Vasectomies Conducted':
        'Count_BirthControlEvent_Vasectomy',
    'Number of Tubectomies Conducted (Public + Pvt.)':
        'Count_BirthControlEvent_Tubectomy',
    'Number of Tubectomies Conducted':
        'Count_BirthControlEvent_Tubectomy',
    'Total Sterilisation Conducted':
        'Count_BirthControlEvent_Sterilization',
    '% Male Sterlisation (Vasectomies) to Total sterilisation':
        'Count_BirthControlEvent_Vasectomy_AsFractionOf_Count_BirthControlEvent_Sterlization',
    'Total cases of deaths following Sterlisation ( Male + Female)':
        'Count_Death_BirthControlSterilization',
    'Total IUCD Insertions done(public+private)':
        'Count_BirthControlEvent_IUCDInsertion',
    'Total Interval IUCD Insertions done':
        'Count_BirthControlEvent_IUCDInsertion',
    '% IUCD insertions in public plus private institutions to all family planning methods ( IUCD plus permanent)':
        'Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent',
    '% IUCD insertions to all family planning methods ( IUCD plus permanent)':
        'Count_BirthControlEvent_IUCDInsertion_AsFractionOf_Count_BirthControlEvent',
    'Oral Pills distributed':
        'Count_ContraceptiveDistribution_OralPill',
    'Combined Oral Pills distributed':
        'Count_ContraceptiveDistribution_OralPill',
    'Condom pieces distributed':
        'Count_ContraceptiveDistribution_Condom',
}

clean_names = {
    'District':
        'District',
    'DistrictCode':
        'lgdCode',
    'Date':
        'Date',
    'Number of Vasectomies Conducted (Public + Pvt.)':
        'Number of Vasectomies Conducted (Public and Private Institutions)',
    'Number of Vasectomies Conducted':
        'Number of Vasectomies Conducted (Public and Private Institutions)',
    'Number of Tubectomies Conducted (Public + Pvt.)':
        'Number of Tubectomies Conducted (Public and Private Institutions)',
    'Number of Tubectomies Conducted':
        'Number of Tubectomies Conducted (Public and Private Institutions)',
    'Total Sterilisation Conducted':
        'Total Sterilisation Conducted',
    '% Male Sterlisation (Vasectomies) to Total sterilisation':
        'Percent of Male Sterlisation (Vasectomies) to Total sterilisation',
    'Total cases of deaths following Sterlisation ( Male + Female)':
        'Total cases of deaths following Sterilisation (Male and Female)',
    'Total IUCD Insertions done(public+private)':
        'Total IUCD Insertions done',
    'Total Interval IUCD Insertions done':
        'Total IUCD Insertions done',
    '% IUCD insertions in public plus private institutions to all family planning methods ( IUCD plus permanent)':
        'Percent of IUCD insertions to all family planning methods',
    '% IUCD insertions to all family planning methods ( IUCD plus permanent)':
        'Percent of IUCD insertions to all family planning methods',
    'Oral Pills distributed':
        'Oral Pills distributed',
    'Combined Oral Pills distributed':
        'Combined Oral Pills distributed',
    'Condom pieces distributed':
        'Condom pieces distributed',
}


class TestPreprocess(unittest.TestCase):

    maxDiff = None

    def test_create_csv(self):
        expected_file = open(os.path.join(module_dir_, 'test/expected.csv'))
        expected_data = expected_file.read()
        expected_file.close()

        loader = NHMDataLoaderBase(
            data_folder=os.path.join(module_dir_, 'test/'),
            dataset_name='test_gen',
            cols_dict=cols_to_nodes,
            clean_names=clean_names,
            final_csv_path=os.path.join(module_dir_, "test/test_gen.csv"))
        loader.generate_csv()

        result_file = open(os.path.join(module_dir_, 'test/test_gen.csv'))
        result_data = result_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir_, 'test/test_gen.csv'))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()
