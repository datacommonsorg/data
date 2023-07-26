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
"""Script to aggregate EPH Heat Illness data from state level data."""

import pandas as pd

from absl import app
from absl import flags

flags.DEFINE_string('input_path', None,
                    'Path to input CSV with state level data.')
flags.DEFINE_string('output_path', None, 'Output CSV Path')

_FLAGS = flags.FLAGS


def main(argv):
    df = pd.read_csv(_FLAGS.input_path, dtype={'Quantity': 'float64'})

    # Aggregating all stat vars
    df.drop_duplicates(subset=['Year', 'Geo', 'StatVar'],
                       keep='first',
                       inplace=True)
    country_df = df.groupby(by=['Year', 'StatVar'],
                            as_index=False).agg({'Quantity': 'sum'})
    country_df.to_csv(_FLAGS.output_path, index=False)


if __name__ == "__main__":
    flags.mark_flags_as_required(['input_path', 'output_path'])
    app.run(main)
