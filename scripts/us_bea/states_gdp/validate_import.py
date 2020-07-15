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
"""
Validate the import_data.py script. Checks that the BEA database has not been
updated in a way that would make the script invalid or obsolete.

    Typical usage:

    python3 validate_import.py
"""
import unittest
import re
import numpy as np
from import_data import StateGDPDataLoader

class USStateQuarterlyGDPImportVal(unittest.TestCase):
    def test_download_data(self):
        """Tests that data gets downloaded properly.

        Tests that all US States (rows) are represented in the downloaded data.
        Tests that all measurement periods of interest (cols) are represented
        in the downloaded data.
        """
        loader = StateGDPDataLoader()
        loader.download_data()

        # Test that all states appear in downloaded data.
        all_states = set(loader._US_STATES)
        data_states = all_states.intersection(set(loader.raw_df['GeoName']))
        self.assertSetEqual(all_states, data_states)

        # Test that the quarters in the downloaded data are exactly the ones
        # from the years 2005-2019.
        years = range(2005, 2020)
        quarters = range(1, 5)
        all_quarters = {f"{y}:Q{q}" for y in years for q in quarters}
        all_quarters.add("2020:Q1")
        cols = loader.raw_df.columns
        data_quarters = {q for q in cols if re.match(r"....:Q.", q)}
        self.assertSetEqual(all_quarters, data_quarters)

    def test_process_data(self):
        """Tests that raw data gets processed properly.

        Tests that all columns in processed data are as expected.
        Checks that all types are as expected.
        """
        loader = StateGDPDataLoader()
        loader.download_data()
        loader.process_data()

        clean_df = loader.clean_df
        expected_col_types = {"Quarter": np.object,
                              "GeoId": np.object,
                              "chained_2012_dollars": np.float64,
                              "quantity_index": np.float64,
                              "current_dollars": np.float64}
        # Check that the resulting columns are as expected.
        expected_cols = set(expected_col_types.keys())
        self.assertSetEqual(set(clean_df.columns), expected_cols)

        # Checks for desired types per column.
        for col, col_type in zip(clean_df.columns, clean_df.dtypes):
            self.assertEqual(col_type, expected_col_types[col])

    def test_exceptions(self):
        """Tests that trying to call functions prematurely raises exceptions."""
        loader = StateGDPDataLoader()
        with self.assertRaises(ValueError):
            loader.process_data()

        loader = StateGDPDataLoader()
        with self.assertRaises(ValueError):
            loader.save_csv()

        loader = StateGDPDataLoader()
        loader.download_data()
        with self.assertRaises(ValueError):
            loader.save_csv()

        loader = StateGDPDataLoader()
        loader.download_data()
        loader.process_data()
        loader.save_csv()


if __name__ == '__main__':
    unittest.main()
