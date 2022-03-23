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
"""A simple script to download existing Facilities in Data Commons."""

import os
import pathlib

import datacommons
import pandas as pd

from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('output_path', 'tmp_data', 'Output directory')


def main(_):
    assert FLAGS.output_path
    pathlib.Path(FLAGS.output_path).mkdir(exist_ok=True)
    out_file = os.path.join(FLAGS.output_path, 'existing_facilities.csv')

    q = "SELECT DISTINCT ?dcid WHERE {?a typeOf EpaReportingFacility . ?a dcid ?dcid }"
    res = datacommons.query(q)

    facility_ids = []
    for facility in res:
        facility_ids.append(facility["?dcid"])

    df = pd.DataFrame.from_dict({"epaGhgrpFacilityId": facility_ids})
    df.to_csv(out_file, mode="w", header=True, index=False)


if __name__ == '__main__':
    app.run(main)
