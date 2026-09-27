# Copyright 2022 Google LLC
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
"""Script to aggregate CDC Data at a country level from state level data."""

import pandas as pd

from absl import app
from absl import flags

_FLAGS = flags.FLAGS


def aggregate_state_to_country(input_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates state level data to country level for Count_* StatVars."""
    df_count = input_df.loc[input_df['StatVar'].str.startswith('Count')].copy()
    if 'Unit' in df_count.columns:
        df_count.drop('Unit', axis=1,
                      inplace=True)  # Count statvars have no unit.
    df_count.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                             keep='last',
                             inplace=True)
    df_count['Quantity'] = pd.to_numeric(df_count['Quantity'], errors='coerce')
    country_df = df_count.groupby(by=['Year', 'StatVar'],
                                  as_index=False).agg({'Quantity': 'sum'})
    if pd.api.types.is_numeric_dtype(country_df['Quantity']):
        country_df['Quantity'] = country_df['Quantity'].round().astype('Int64')
    country_df.sort_values(by=['Year', 'StatVar'], inplace=True)
    return country_df


def main(argv):
    df = pd.read_csv(_FLAGS.input_path, dtype=str)
    country_df = aggregate_state_to_country(df)
    country_df.to_csv(_FLAGS.output_path, index=False)


if __name__ == "__main__":
    flags.DEFINE_string('input_path', None,
                        'Path to input CSV with state level data.')
    flags.DEFINE_string('output_path', None, 'Output CSV path.')
    flags.mark_flags_as_required(['input_path', 'output_path'])
    app.run(main)
