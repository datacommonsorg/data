# Copyright 2021 Google LLC
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
'''
Unit tests for air_quality.py

Usage: python3 -m unittest discover -v -s ../ -p "air_quality_test.py"
'''
import unittest, csv, os, sys, tempfile

module_dir_ = os.path.dirname(__file__)

sys.path.append(module_dir_)

from air_quality import (create_csv, create_sites_mcf, get_camel_case,
                        write_csv, write_sites_mcf, write_tmcf)


class TestCriteriaGasesTest(unittest.TestCase):

    def test_write_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with open(
                    os.path.join(module_dir_, 'test_data/test_import_data.csv'),
                    'r') as f:
                test_csv = os.path.join(tmp_dir, 'test_csv.csv')
                test_sites_mcf = os.path.join(tmp_dir,
                                              'EPA_AirQuality_sites.mcf')
                create_csv(test_csv)
                create_sites_mcf(test_sites_mcf)

                reader = csv.DictReader(f)
                seen_sites = set()
                write_csv(test_csv,
                          reader,
                          sites_mcf_file_path=test_sites_mcf,
                          seen_sites=seen_sites)

                expected_csv = os.path.join(module_dir_,
                                            'test_data/test_import.csv')
                with open(test_csv, 'r') as test:
                    test_str: str = test.read()
                    with open(expected_csv, 'r') as expected:
                        expected_str: str = expected.read()
                        self.assertEqual(test_str, expected_str)

                expected_sand_mountain = (
                    'Node: dcid:epa/010499991\n'
                    'typeOf: dcs:AirQualitySite\n'
                    'name: "Sand Mountain"\n'
                    'location: [latLong 34.289001 -85.970065]\n'
                    'containedInPlace: dcid:geoId/01049\n'
                )
                expected_birmingham = (
                    'Node: dcid:epa/010730023\n'
                    'typeOf: dcs:AirQualitySite\n'
                    'name: "North Birmingham"\n'
                    'location: [latLong 33.553056 -86.815]\n'
                    'containedInPlace: dcid:geoId/01073\n'
                )
                with open(test_sites_mcf, 'r') as test_mcf:
                    test_mcf_str = test_mcf.read()
                    self.assertIn(expected_sand_mountain, test_mcf_str)
                    self.assertIn(expected_birmingham, test_mcf_str)
                    # Verify each site appears exactly once (uniqueness)
                    self.assertEqual(
                        test_mcf_str.count('Node: dcid:epa/010499991'), 1)
                    self.assertEqual(
                        test_mcf_str.count('Node: dcid:epa/010730023'), 1)

    def test_write_tmcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_tmcf = os.path.join(tmp_dir, 'test_tmcf.tmcf')
            write_tmcf(test_tmcf)

            expected_tmcf = os.path.join(module_dir_, 'EPA_AirQuality.tmcf')
            with open(test_tmcf, 'r') as test:
                test_str: str = test.read()
                with open(expected_tmcf, 'r') as expected:
                    expected_str: str = expected.read()
                    self.assertEqual(test_str, expected_str)

    def test_filter_cross_border_monitors(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': '80',
                    'County Code': '001',
                    'Site Num': '0001',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '32.5',
                    'Longitude': '-117.0',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'Mexico Monitor',
                },
                {
                    'State Code': 'CC',
                    'County Code': '004',
                    'Site Num': '0002',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '44.8',
                    'Longitude': '-66.9',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'Canada Monitor',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_csv, 'r') as f:
                reader = list(csv.DictReader(f))
                self.assertEqual(len(reader), 0)
            with open(test_sites_mcf, 'r') as f_sites:
                self.assertEqual(f_sites.read().strip(), '')

    def test_unit_mapping(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '0023',
                    'Parameter Code': '88101',
                    'POC': '1',
                    'Latitude': '33.55',
                    'Longitude': '-86.81',
                    'Pollutant Standard': 'PM25 24-hour 2012',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Micrograms/cubic meter (LC)',
                    'Arithmetic Mean': '3.8',
                    '1st Max Value': '3.8',
                    'AQI': '16',
                    'Local Site Name': 'North Birmingham',
                },
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '0023',
                    'Parameter Code': '81102',
                    'POC': '4',
                    'Latitude': '33.55',
                    'Longitude': '-86.81',
                    'Pollutant Standard': 'PM10 24-hour 2006',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Micrograms/cubic meter (25 C)',
                    'Arithmetic Mean': '11',
                    '1st Max Value': '11',
                    'AQI': '10',
                    'Local Site Name': 'North Birmingham',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_csv, 'r') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]['Units'], 'MicrogramsPerCubicMeter_lc')
                self.assertEqual(rows[1]['Units'],
                                 'MicrogramsPerCubicMeter_25C')
            with open(test_sites_mcf, 'r') as f_sites:
                test_sites_str = f_sites.read()
                self.assertEqual(
                    test_sites_str.count('Node: dcid:epa/010730023'), 1)

    def test_filter_cross_border_monitors_defensive(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': ' 80 ',
                    'County Code': '001',
                    'Site Num': '0001',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '32.5',
                    'Longitude': '-117.0',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'Mexico Monitor Padded',
                },
                {
                    'State Code': 'cc',
                    'County Code': '004',
                    'Site Num': '0002',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '44.8',
                    'Longitude': '-66.9',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'Canada Monitor Lowercase',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_csv, 'r') as f:
                reader = list(csv.DictReader(f))
                self.assertEqual(len(reader), 0)
            with open(test_sites_mcf, 'r') as f_sites:
                self.assertEqual(f_sites.read().strip(), '')

    def test_missing_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '9999',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '   ',
                    'Longitude': '',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.02',
                    '1st Max Value': '0.03',
                    'AQI': '20',
                    'Local Site Name': 'No Coords Site',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_csv, 'r') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['Site_Location'], '')
            with open(test_sites_mcf, 'r') as f_sites:
                mcf_content = f_sites.read()
                self.assertIn('Node: dcid:epa/010739999\n', mcf_content)
                self.assertIn('typeOf: dcs:AirQualitySite\n', mcf_content)
                self.assertIn('name: "No Coords Site"\n', mcf_content)
                self.assertIn('containedInPlace: dcid:geoId/01073\n', mcf_content)
                self.assertNotIn('location:', mcf_content)

    def test_site_name_newline_sanitization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '8888',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '33.5',
                    'Longitude': '-86.8',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.02',
                    '1st Max Value': '0.03',
                    'AQI': '20',
                    'Local Site Name': 'Multi-line\nSite "Name" \n ',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_sites_mcf, 'r') as f_sites:
                mcf_content = f_sites.read()
                self.assertIn('name: "Multi-line Site \\"Name\\""\n',
                              mcf_content)

    def test_seen_sites_whitespace_reloading(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            with open(test_sites_mcf, 'w') as f:
                f.write('   Node: dcid: epa/010730023  \n'
                        'typeOf: dcs:AirQualitySite\n\n')

            observations = [
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '0023',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '33.55',
                    'Longitude': '-86.81',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'North Birmingham',
                },
            ]
            # When seen_sites is not passed, it should reload from test_sites_mcf
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_sites_mcf, 'r') as f_sites:
                mcf_content = f_sites.read()
                # Should not have appended another node
                self.assertEqual(mcf_content.count('epa/010730023'), 1)

    def test_site_coordinate_enrichment_from_later_record(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '7777',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '',
                    'Longitude': '',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.02',
                    '1st Max Value': '0.03',
                    'AQI': '20',
                    'Local Site Name': '',
                },
                {
                    'State Code': '01',
                    'County Code': '073',
                    'Site Num': '7777',
                    'Parameter Code': '42401',
                    'POC': '1',
                    'Latitude': '33.55',
                    'Longitude': '-86.81',
                    'Pollutant Standard': 'SO2 1-hour 2010',
                    'Date Local': '2021-01-02',
                    'Units of Measure': 'Parts per billion',
                    'Arithmetic Mean': '0.5',
                    '1st Max Value': '1.0',
                    'AQI': '5',
                    'Local Site Name': 'Enriched Site Name',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_sites_mcf, 'r') as f_sites:
                mcf_content = f_sites.read()
                self.assertIn('Node: dcid:epa/010737777\n', mcf_content)
                self.assertIn('name: "Enriched Site Name"\n', mcf_content)
                self.assertIn('location: [latLong 33.55 -86.81]\n', mcf_content)
                self.assertEqual(mcf_content.count('epa/010737777'), 1)

    def test_defensive_county_and_site_padding(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            test_sites_mcf = os.path.join(tmp_dir, 'test_sites.mcf')
            create_csv(test_csv)
            create_sites_mcf(test_sites_mcf)
            observations = [
                {
                    'State Code': ' 1 ',
                    'County Code': ' 73 ',
                    'Site Num': ' 23 ',
                    'Parameter Code': '44201',
                    'POC': '1',
                    'Latitude': '33.5',
                    'Longitude': '-86.8',
                    'Pollutant Standard': 'Ozone 8-hour 2015',
                    'Date Local': '2021-01-01',
                    'Units of Measure': 'Parts per million',
                    'Arithmetic Mean': '0.03',
                    '1st Max Value': '0.04',
                    'AQI': '30',
                    'Local Site Name': 'Padded IDs Site',
                },
            ]
            write_csv(test_csv,
                      iter(observations),
                      sites_mcf_file_path=test_sites_mcf)
            with open(test_csv, 'r') as f:
                rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['Site_Number'], 'epa/010730023')
                self.assertEqual(rows[0]['County'], 'dcid:geoId/01073')
            with open(test_sites_mcf, 'r') as f_sites:
                mcf_content = f_sites.read()
                self.assertIn('Node: dcid:epa/010730023\n', mcf_content)
                self.assertIn('containedInPlace: dcid:geoId/01073\n',
                              mcf_content)

    def test_get_camel_case_punctuation_stripping(self):
        self.assertEqual(
            get_camel_case('Micrograms/cubic meter (25 C)'),
            'MicrogramsCubicMeter25C')
        self.assertEqual(
            get_camel_case('parts-per-million'),
            'PartsPerMillion')
        self.assertEqual(get_camel_case(' - '), '')

    def test_write_sites_mcf(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_mcf = os.path.join(tmp_dir, 'sites.mcf')
            sites_dict = {
                'epa/020200018': {
                    'name': 'Anchorage Monitor',
                    'lat': '61.21',
                    'lon': '-149.88',
                    'county': 'dcid:geoId/02020',
                },
                'epa/010730023': {
                    'name': 'North Birmingham',
                    'lat': '33.55',
                    'lon': '-86.81',
                    'county': 'dcid:geoId/01073',
                },
            }
            write_sites_mcf(test_mcf, sites_dict)
            with open(test_mcf, 'r') as f:
                content = f.read()
                # Sorted order: 010730023 must appear before 020200018
                idx_bham = content.find('Node: dcid:epa/010730023')
                idx_anch = content.find('Node: dcid:epa/020200018')
                self.assertTrue(idx_bham < idx_anch)


if __name__ == '__main__':
    unittest.main()
