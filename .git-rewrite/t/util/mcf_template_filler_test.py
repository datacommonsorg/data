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
"""Tests for util.mcf_template_filler."""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import absolute_import
import unittest

from util import mcf_template_filler

POP_TEMPLATE = """
Node: Pop_payroll_est_{geo_id}_{naics_code}_{operation_type}_{tax_status}
typeOf: schema:StatisticalPopulation
populationType: dcs:USCEstablishment
location: dcid:{geo_id}
payrollStatus: dcs:WithPayroll
naics: dcs:NAICS/{naics_code}
operationType: dcs:{operation_type}
taxStatus: dcs:{tax_status}
"""

OBS_TEMPLATE = """
Node: Obs_on_Pop_payroll_est_{geo_id}_{naics_code}_{operation_type}_{tax_status}_{year}_{mprop}
typeOf: schema:Observation
observedNode: l:Pop_payroll_est_{geo_id}_{naics_code}_{operation_type}_{tax_status}
observationDate: "{year}"
measuredProperty: dcs:{mprop}
measuredValue: {mval}
"""

NAMELESS_POP_TEMPLATE = """
typeOf: schema:StatisticalPopulation
populationType: dcs:USCEstablishment
location: dcid:{geo_id}
"""

NAMELESS_OBS_TEMPLATE = """
typeOf: schema:Observation
observedNode: l:Pop_payroll_est_{geo_id}_{naics_code}_{operation_type}_{tax_status}
observationDate: "{year}"
measuredProperty: dcs:{mprop}
measuredValue: {mval}
"""


class MCFTemplateFillerTest(unittest.TestCase):

    def test_example_usage(self):
        example_template = """
Node: People_in_geoId_{geo_id}_{race}_{gender}_{random_field}
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: geoId/{geo_id}
race: dcs:{race}
gender: dcs:{gender}
randomOptionalProperty: {random_field}
"""

        templater = mcf_template_filler.Filler(example_template,
                                               required_vars=['geo_id'])
        var_dict1 = {'geo_id': '05', 'race': 'White'}
        pop1 = templater.fill(var_dict1)
        expected = """
Node: People_in_geoId_05_White__
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: geoId/05
race: dcs:White
"""
        self.assertEqual(pop1, expected)

        var_dict2 = {'geo_id': '05', 'gender': 'Female'}
        pop2 = templater.fill(var_dict2)
        expected = """
Node: People_in_geoId_05__Female_
typeOf: schema:StatisticalPopulation
populationType: schema:Person
location: geoId/05
gender: dcs:Female
"""
        self.assertEqual(pop2, expected)

    def test_pop_and_2_obs_with_all_pv(self):
        """Use separate templates for Pop Obs, and use Obs template repeatedly."""
        templater = mcf_template_filler.Filler(POP_TEMPLATE,
                                               required_vars=['geo_id'])
        template_vars = {
            'geo_id': 'geoId/06',
            'naics_code': '11',
            'operation_type': 'Manufacturer',
            'tax_status': 'ExemptFromTax'
        }
        result = templater.fill(template_vars)

        expected = """
Node: Pop_payroll_est_geoId/06_11_Manufacturer_ExemptFromTax
typeOf: schema:StatisticalPopulation
populationType: dcs:USCEstablishment
location: dcid:geoId/06
payrollStatus: dcs:WithPayroll
naics: dcs:NAICS/11
operationType: dcs:Manufacturer
taxStatus: dcs:ExemptFromTax
"""
        self.assertEqual(result, expected)

        templater = mcf_template_filler.Filler(
            OBS_TEMPLATE, required_vars=['year', 'mprop', 'mval'])
        template_vars['year'] = '2000'
        template_vars['mprop'] = 'count'
        template_vars['mval'] = 0
        result = templater.fill(template_vars)

        expected = """
Node: Obs_on_Pop_payroll_est_geoId/06_11_Manufacturer_ExemptFromTax_2000_count
typeOf: schema:Observation
observedNode: l:Pop_payroll_est_geoId/06_11_Manufacturer_ExemptFromTax
observationDate: "2000"
measuredProperty: dcs:count
measuredValue: 0
"""
        self.assertEqual(result, expected)

        template_vars['year'] = '2001'
        template_vars['mprop'] = 'count'
        template_vars['mval'] = 144
        result = templater.fill(template_vars)

        expected = """
Node: Obs_on_Pop_payroll_est_geoId/06_11_Manufacturer_ExemptFromTax_2001_count
typeOf: schema:Observation
observedNode: l:Pop_payroll_est_geoId/06_11_Manufacturer_ExemptFromTax
observationDate: "2001"
measuredProperty: dcs:count
measuredValue: 144
"""
        self.assertEqual(result, expected)

    def test_unified_pop_obs_with_missing_optional_pv(self):
        # Can combine templates, like Pop + Obs
        pop_obs_template = POP_TEMPLATE + OBS_TEMPLATE
        templater = mcf_template_filler.Filler(
            pop_obs_template, required_vars=['geo_id', 'year', 'mprop', 'mval'])
        template_vars = {
            'geo_id': 'geoId/06',
            'naics_code': '11',
            'tax_status': 'ExemptFromTax',
            'year': '2000',
            'mprop': 'count',
            'mval': 42,
        }
        result = templater.fill(template_vars)

        expected = """
Node: Pop_payroll_est_geoId/06_11__ExemptFromTax
typeOf: schema:StatisticalPopulation
populationType: dcs:USCEstablishment
location: dcid:geoId/06
payrollStatus: dcs:WithPayroll
naics: dcs:NAICS/11
taxStatus: dcs:ExemptFromTax

Node: Obs_on_Pop_payroll_est_geoId/06_11__ExemptFromTax_2000_count
typeOf: schema:Observation
observedNode: l:Pop_payroll_est_geoId/06_11__ExemptFromTax
observationDate: "2000"
measuredProperty: dcs:count
measuredValue: 42
"""
        self.assertEqual(result, expected)

    def test_pop_with_missing_req_pv(self):
        templater = mcf_template_filler.Filler(
            POP_TEMPLATE, required_vars=['geo_id', 'tax_status'])
        template_vars = {
            'geo_id': 'geoId/06',
            'naics_code': '11',
            'operation_type': 'Manufacturer',
        }
        with self.assertRaises(ValueError):
            templater.fill(template_vars)

    def test_require_node_name(self):
        with self.assertRaises(ValueError):
            mcf_template_filler.Filler(NAMELESS_POP_TEMPLATE)

        with self.assertRaises(ValueError):
            mcf_template_filler.Filler(NAMELESS_OBS_TEMPLATE)

        bad_node = """
typeOf: badNode
location: dcid:badPlace
"""
        with self.assertRaises(ValueError):
            mcf_template_filler.Filler(POP_TEMPLATE + bad_node)


if __name__ == '__main__':
    unittest.main()
