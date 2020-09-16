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
"""A script to generate a new place CohortSet, and its members based on a CSV."""

import csv

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string("csv", None, "Path to the raw csv containing the places.")
flags.DEFINE_string("set_id", None, "DCID and name of the CohortSet.")
flags.DEFINE_string(
    "place_id_property", None,
    "The CSV column with the place identifiers. It should also be the DCID of the property."
)
flags.DEFINE_string("place_type", None,
                    "The DCID of the Place type of CohortSet members.")
flags.DEFINE_string(
    "set_description", None,
    "Optional description of the CohortSet. Used as the value of `description`."
)


def write_mcf(f_in, f_out, set_id, place_id_property, place_type,
              set_description):
    """Generates a CohortSet and attaches places from the input file."""
    cohort_set = f"""
Node: dcid:{set_id}
name: "{set_id}"
typeOf: dcs:CohortSet
"""
    if set_description:
        cohort_set += f"description: \"{set_description}\"\n"
    members_list = []

    dict_reader = csv.DictReader(f_in)
    for row in dict_reader:
        place_id = row[place_id_property]
        members_list.append(f"l:{place_id}")
        f_out.write(f"""
Node: {place_id}
{place_id_property}: "{place_id}"
typeOf: dcs:{place_type}
""")

    cohort_set += "member: %s" % ', '.join(members_list)
    f_out.write(cohort_set)


def main(argv):
    f_in = open(FLAGS.csv, 'r')
    f_out = open(FLAGS.csv.replace('.csv', '.mcf'), 'w')
    write_mcf(f_in, f_out, FLAGS.set_id, FLAGS.place_id_property,
              FLAGS.place_type, FLAGS.set_description)
    f_in.close()
    f_out.close()


if __name__ == "__main__":
    flags.mark_flag_as_required('csv')
    flags.mark_flag_as_required('set_id')
    flags.mark_flag_as_required('place_type')
    flags.mark_flag_as_required('place_id_property')

    app.run(main)
