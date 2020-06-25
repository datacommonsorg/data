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
import preprocess_csv_helper

class PreprocessCSVHelperTest(unittest.TestCase):

    def test_generate_dcid_for_county(self):
        counties = ['ALPINE', 'SIERRA', 'SUTTER', 'MONO', 'MARIPOSA', 'MODOC',
       'CALAVERAS', 'LASSEN', 'SAN BENITO', 'TRINITY', 'INYO', 'PLUMAS',
       'COLUSA', 'GLENN', 'DEL NORTE', 'AMADOR', 'SISKIYOU', 'LAKE',
       'TEHAMA', 'TUOLUMNE', 'YOLO', 'NEVADA', 'MENDOCINO', 'KINGS',
       'EL DORADO', 'YUBA', 'MERCED', 'IMPERIAL', 'HUMBOLDT', 'NAPA',
       'SANTA CRUZ', 'BUTTE', 'MARIN', 'SAN LUIS OBISPO', 'MADERA',
       'SHASTA', 'SOLANO', 'MONTEREY', 'SONOMA', 'PLACER', 'TULARE',
       'SANTA BARBARA', 'SAN MATEO', 'SAN JOAQUIN', 'VENTURA',
       'STANISLAUS', 'KERN', 'CONTRA COSTA', 'FRESNO', 'SAN FRANCISCO',
       'SACRAMENTO', 'ALAMEDA', 'RIVERSIDE', 'SANTA CLARA',
       'SAN BERNARDINO', 'ORANGE', 'SAN DIEGO', 'LOS ANGELES']
        county_to_dcid = preprocess_csv_helper.generate_dcid_for_county(counties)
        self.assertEqual(len(counties), len(county_to_dcid))
        self.assertEqual(county_to_dcid['ALAMEDA'], 'geoId/06001')
        self.assertEqual(county_to_dcid['FRESNO'], 'geoId/06019')
        self.assertEqual(county_to_dcid['YUBA'], 'geoId/06115')

    def test_preserve_leading_zero(self):
        tests = {
            '12345678': '012345678',
            '101211': '000101211',
            '0': '000000000'}
        self.assertEqual(preprocess_csv_helper.preserve_leading_zero('12345678'), tests['12345678'])
        self.assertEqual(preprocess_csv_helper.preserve_leading_zero('101211'), tests['101211'])
        self.assertEqual(preprocess_csv_helper.preserve_leading_zero('0'), tests['0'])

    def test_get_camel_formatting_name(self):
        tests = {
            'SkIllED nUrsING fACILiTY': 'SkilledNursingFacility',
            '': '',
            '   Harry Potter': 'HarryPotter'}
        self.assertEqual(preprocess_csv_helper.get_camel_formatting_name('SkIllED nUrsING fACILiTY'),
                         tests['SkIllED nUrsING fACILiTY'])
        self.assertEqual(preprocess_csv_helper.get_camel_formatting_name('   Harry Potter'),
                         tests['   Harry Potter'])

    def test_get_camel_formatting_name_list(self):
        tests = ['SKILLED NURSING FACILITY',
            'INTERMEDIATE CARE FACILITY-DD/H/N/CN/IID',
            'CONGREGATE LIVING HEALTH FACILITY', 'INTERMEDIATE CARE FACILITY',
            'HOSPICE FACILITY', 'GENERAL ACUTE CARE HOSPITAL',
            'ACUTE PSYCHIATRIC HOSPITAL', 'HOSPICE',
            'PEDIATRIC DAY HEALTH & RESPITE CARE FACILITY',
            'CHRONIC DIALYSIS CLINIC', 'CHEMICAL DEPENDENCY RECOVERY HOSPITAL',
            'CORRECTIONAL TREATMENT CENTER']
        results = ['SkilledNursingFacility',
            'IntermediateCareFacility-dd/h/n/cn/iid',
            'CongregateLivingHealthFacility',
            'IntermediateCareFacility',
            'HospiceFacility',
            'GeneralAcuteCareHospital',
            'AcutePsychiatricHospital',
            'Hospice',
            'PediatricDayHealth&RespiteCareFacility',
            'ChronicDialysisClinic',
            'ChemicalDependencyRecoveryHospital',
            'CorrectionalTreatmentCenter']

        tests_respected = preprocess_csv_helper.get_camel_formatting_name_list(tests)
        self.assertEqual(len(tests_respected), len(results))
        for i in range(len(tests_respected)):
            self.assertEqual(tests_respected[i], results[i])

if __name__ == '__main__':
    unittest.main()


