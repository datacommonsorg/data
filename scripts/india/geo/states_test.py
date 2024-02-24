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

import csv
import os
import pandas as pd
import unittest
from india.geo.states import IndiaStatesMapper


class TestPreprocess(unittest.TestCase):

    def test_get_state_name_to_iso_code_mapping(self):
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_iso_code_mapping(
                "DADRA AND NAGAR HAVELI AND DAMAN AND DIU"), "IN-DH")
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_iso_code_mapping(
                "ANDHRA PRADESH"), "IN-AP")
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_iso_code_mapping(
                "DADRA AND NAGAR HAVELI"), "IN-DN")
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_iso_code_mapping(
                "JAMMU & KASHMIR"), "IN-JK")

    def test_get_state_name_to_census2001_code_mapping(self):
        # In 2001, LADAKH was part of JAMMU AND KASHMIR, So it should return the code of JAMMU AND KASHMIR
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "LADAKH", district_name=None),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "JAMMU AND KASHMIR", district_name=None))
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "JAMMU AND KASHMIR"), "01")

        # In 2001, TELANGANA was part of ANDHRA PRADESH, So it should return the code of JAMMU AND KASHMIR
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "TELANGANA", district_name=None),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "ANDHRA PRADESH", district_name=None))
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "TELANGANA"), "28")

        # In 2001, Uttarakhand was known Uttaranchal
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "UTTARANCHAL", district_name=None),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "UTTARAKHAND", district_name=None))
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "UTTARANCHAL"), "05")

        # In 2001, district DADRA AND NAGAR HAVELI" was part of UT "DADRA AND NAGAR HAVELI"
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
                district_name="DADRA AND NAGAR HAVELI"),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "DADRA AND NAGAR HAVELI", district_name=None))
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "DADRA AND NAGAR HAVELI"), "26")

        # In 2001, district DAMAN was part of UT "DAMAN AND DIU"
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
                district_name="DAMAN"),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "DAMAN AND DIU", district_name=None))
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "DAMAN AND DIU"), "25")

        # In 2001, district DIU was part of UT "DAMAN AND DIU"
        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU",
                district_name="DIU"),
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "DAMAN AND DIU", district_name=None))

        self.assertEqual(
            IndiaStatesMapper.get_state_name_to_census2001_code_mapping(
                "MAHARASHTRA"), "27")


if __name__ == '__main__':
    unittest.main()
