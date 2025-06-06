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
"""Tests the import_data.py script.

    Typical usage:

    python3 test_import.py
"""
import os
import sys
import unittest
import pandas as pd

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_bea.states_gdp import import_data
from us_bea.states_gdp import import_industry_data_and_gen_mcf

# _MODULE_DIR is the path to where this test is running from.
_MODULE_DIR = os.path.dirname(__file__)

_TEST_DATA_DIR = os.path.join(_MODULE_DIR, "test_csvs")


class USStateQuarterlyGDPImportTest(unittest.TestCase):

    def test_date_converter(self):
        """Tests the date converter function used to process raw data."""
        date_conv_fn = import_data.StateGDPDataLoader.date_to_obs_date

        self.assertEqual(date_conv_fn("2005:Q1"), "2005-03")
        self.assertEqual(date_conv_fn("2005:Q2"), "2005-06")
        self.assertEqual(date_conv_fn("2005:Q3"), "2005-09")
        self.assertEqual(date_conv_fn("2005:Q4"), "2005-12")
        self.assertEqual(date_conv_fn("1999:Q1"), "1999-03")
        self.assertEqual(date_conv_fn("2020:Q2"), "2020-06")

    def test_geoid_converter(self):
        """Tests the geoid converter function used to process raw data."""
        geoid_conv_fn = import_data.StateGDPDataLoader.convert_geoid

        self.assertEqual(geoid_conv_fn('   "1000"'), "geoId/10")
        self.assertEqual(geoid_conv_fn("1000"), "geoId/10")
        self.assertEqual(geoid_conv_fn("10"), "geoId/10")
        self.assertEqual(geoid_conv_fn("10    "), "geoId/10")
        self.assertEqual(geoid_conv_fn('10""""""'), "geoId/10")
        self.assertEqual(geoid_conv_fn("25100"), "geoId/25")
        self.assertEqual(geoid_conv_fn('   "760000"'), "geoId/76")
        self.assertEqual(geoid_conv_fn('123""""""'), "geoId/12")

    def test_data_processing_tiny(self):
        """Tests end-to-end data cleaning on a tiny example."""
        raw_df = pd.read_csv(os.path.join(_TEST_DATA_DIR, "test_tiny_raw.csv"))

        clean_df = pd.read_csv(os.path.join(_TEST_DATA_DIR,
                                            "test_tiny_cleaned.csv"),
                               index_col=['GeoId', 'Quarter'])

        loader = import_data.StateGDPDataLoader()

        raw_csv_string = raw_df.to_csv(index=False)

        loader.process_data(raw_csv_string)

        pd.testing.assert_frame_equal(clean_df, loader.clean_df)

    def test_data_processing_small(self):
        """Tests end-to-end data cleaning on a small example."""
        raw_df = pd.read_csv(os.path.join(_TEST_DATA_DIR, "test_small_raw.csv"),
                             index_col=0)
        clean_df = pd.read_csv(
            os.path.join(_TEST_DATA_DIR, "test_small_cleaned.csv"))
        loader = import_data.StateGDPDataLoader()

        raw_csv_string = raw_df.to_csv(index=False)
        loader.process_data(raw_csv_string)
        clean_df = clean_df.set_index(['GeoId', 'Quarter'])

        pd.testing.assert_frame_equal(clean_df, loader.clean_df)


class USStateQuarterlyPerIndustryImportTest(unittest.TestCase):

    def test_data_processing_tiny(self):
        """Tests end-to-end data cleaning on a tiny example."""
        raw_df = pd.read_csv(
            os.path.join(_TEST_DATA_DIR, "test_industry_tiny_raw.csv"))

        clean_df = pd.read_csv(os.path.join(_TEST_DATA_DIR,
                                            "test_industry_tiny_cleaned.csv"),
                               index_col=0)

        loader = import_industry_data_and_gen_mcf.StateGDPIndustryDataLoader()

        raw_csv_string = raw_df.to_csv(index=False)

        loader.process_data(raw_csv_string)  # Pass the CSV string

        pd.testing.assert_frame_equal(clean_df, loader.clean_df)

    def test_value_converter(self):
        """Tests value converter function that cleans out empty datapoints."""
        val_conv_fn = (import_industry_data_and_gen_mcf.
                       StateGDPIndustryDataLoader.value_converter)
        self.assertEqual(val_conv_fn("(D)"), -1)
        self.assertEqual(val_conv_fn("(E)"), -1)
        self.assertEqual(val_conv_fn("356785)"), -1)
        self.assertEqual(val_conv_fn("35678.735"), 35678.735)
        self.assertEqual(val_conv_fn(5), 5)
        self.assertEqual(val_conv_fn(35678.735), 35678.735)
        self.assertEqual(val_conv_fn(""), -1)

    def test_industry_class(self):
        """Tests industry class converter function that cleans out empty

        datapoints.
        """
        ind_conv_fn = (import_industry_data_and_gen_mcf.
                       StateGDPIndustryDataLoader.convert_industry_class)

        prefix = "dcs:USStateQuarterlyIndustryGDP_NAICS_"
        self.assertEqual(ind_conv_fn("35"), prefix + "35")
        self.assertEqual(ind_conv_fn("987"), prefix + "987")
        self.assertEqual(ind_conv_fn("35-37"), prefix + "35_37")
        self.assertEqual(ind_conv_fn("35-37,40"), prefix + "35_37_40")
        self.assertEqual(ind_conv_fn("13-97,2,45-78"), prefix + "13_97_2_45_78")


if __name__ == "__main__":
    unittest.main()
