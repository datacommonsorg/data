# Copyright 2022 Google LLC
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
This script generates node mcf files from data/measurement_sites.csv
"""
import os
import re
from absl import app, flags
import pandas as pd

FLAGS = flags.FLAGS
flags.DEFINE_string('mmsite_input_file', './data/measurement_sites.csv',
                    'Location of the measurement_sites.csv file')
flags.DEFINE_string(
    'mmsite_output_path', './data/output',
    'Path to the directory where generated files are to be stored.')

MCF_STR = """
Node: {dcid}
name: "{name}"
typeOf: dcs:SuperfundMeasurementSite
containedInPlace: {containedIn}
location: {location}
"""


def write_to_file(row: pd.Series, file_object) -> None:
    """
    Write each measurement site node to file and generates the node dcids 
    """
    siteName = re.sub(r"[,.;@#?!&$]+\ *", "_", row['Site Name'])
    siteName = siteName.replace(' ', '')
    file_object.write(
        MCF_STR.format(
            dcid=
            f"dcid:epaSuperfundMeasurementSite/{row['containedInPlace']}/{siteName}",
            name=row['Site Name'],
            containedIn=f"epaSuperfundSiteId/{row['containedInPlace']}",
            location=row['latLong']))


def generate_mcf(input_file: str, output_path: str) -> None:
    """
    Generates the nodes.mcf from the measurement_sites csv file
    """
    site_df = pd.read_csv(input_file)
    site_df['latLong'] = site_df.apply(
        lambda row: f"[latLong {str(row['Latitude'])} {str(row['Longitude'])}]",
        axis=1)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_file = os.path.join(output_path, './measurement_site_nodes.mcf')

    f = open(output_file, 'w')
    site_df.apply(write_to_file, args=(f,), axis=1)
    f.close()


def main(_) -> None:
    generate_mcf(FLAGS.mmsite_input_file, FLAGS.mmsite_output_path)


if __name__ == '__main__':
    app.run(main)
