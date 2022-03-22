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
