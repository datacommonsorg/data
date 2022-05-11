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
"""A simple script to parse the WHO GHO indicator categories."""
import csv
import re
import requests
import sys
import os

from absl import app

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

# Now use the above mappings.
_ROOT_NODE_MCF = """Node: dcid:dc/g/WHO/Root
typeOf: dcs:StatVarGroup
name: "Global Health Observatory"
specializationOf: dcid:dc/g/Uncategorized
"""

_MAIN_CATEGORIES_MCF_TEMPLATE = """
Node: dcid:WHO/g/%s
typeOf: dcs:StatVarGroup
name: "%s"
specializationOf: dcid:dc/g/WHO/Root
"""

_COUNTERS_SV_GROUPS = {
    "lines_processed": 0,
    "svs_processed": 0,
    "other_category": 0,
    "existing_categories": 0,
}


def counters_print(counter_dict):
    result = []
    for k, v in counter_dict.items():
        result.append(k + " -> " + str(v))
    return "\n".join(result)


def _str_to_id(s):
    # ID is Title Case.
    # ID has no spaces.
    # ID only keeps alphanumeric chars.
    s = s.title()
    s = s.replace(" ", "")
    s = re.sub(r'\W+', '', s)

    return s


def _name_to_dcid(line):
    return line.split("Node: dcid:WHO/")[1]


def _mprop_to_dcid(line):
    return line.split("measuredProperty: dcs:who/")[1]


def _mprop_to_dcid(line):
    return line.split("who/")[1]


def _get_svs_from_input(input_sv_fp):
    gho_codes = set()
    with open(input_sv_fp, 'r') as f:
        lines = f.readlines()
        current_sv = []
        for l in lines:
            if l[:4] == "Node":
                c = _name_to_dcid(l).replace("\n", "")
                gho_codes.add(c)
            if l[:16] == "measuredProperty":
                c = _mprop_to_dcid(l).replace("\n", "")
                gho_codes.add(c)

    return gho_codes


def _get_gho_code_to_category(input_category_map_fp):
    mapping = {}
    with open(input_category_map_fp, "r") as cfp:
        cr = csv.DictReader(cfp)
        for in_row in cr:
            id = in_row['gho_id']
            cat_name = in_row['category_name']

            if cat_name == "0":
                cat_name = "Other"

            mapping[id] = cat_name

    return mapping


def _write_category_mcf(code_to_cat, output_category_mcf_fp):

    unique_categories = set(code_to_cat.values())

    output_mcf = _ROOT_NODE_MCF

    # Process all the vategories.
    for mc_name in sorted(unique_categories):
        output_mcf += _MAIN_CATEGORIES_MCF_TEMPLATE % (_str_to_id(mc_name),
                                                       mc_name.title())

    with open(output_category_mcf_fp, 'w') as f2:
        for l in output_mcf:
            f2.write(l)


def process_categories(input_sv_fp, input_category_map_fp,
                       output_category_mcf_fp, output_sv_fp):
    # Parse the required GHO codes for existing SVs.
    existing_codes = _get_svs_from_input(input_sv_fp)

    # Get the gho_code to category mapping.
    code_to_cat = _get_gho_code_to_category(input_category_map_fp)

    # Write the SV Categories as groups.
    _write_category_mcf(code_to_cat, output_category_mcf_fp)

    with open(input_sv_fp, 'r') as f:
        lines = f.readlines()
        if lines[-1] != "\n":
            lines.append("\n")

        output_lines = []

        current_sv = []
        current_gho_id = "-1"
        current_cat = ""

        for l in lines:
            # Get the actual gho code (dcid) for the SV.
            if l[:16] == "measuredProperty":
                current_gho_id = _mprop_to_dcid(l).replace("\n", "")

            elif l == "\n":
                # Next SV has begun.
                _COUNTERS_SV_GROUPS["svs_processed"] += 1

                # Process the previous SV.
                for sv_line in current_sv:
                    # If 'memberOf: ' already exists, ignore it because we
                    # will be updating it.
                    if 'memberOf:' in sv_line:
                        _COUNTERS_SV_GROUPS["existing_categories"] += 1
                        continue
                    else:
                        output_lines.append(sv_line)

                if current_gho_id in code_to_cat:
                    current_cat = code_to_cat[current_gho_id]
                else:
                    current_cat = "Other"
                    _COUNTERS_SV_GROUPS["other_category"] += 1

                current_cat = _str_to_id(current_cat)
                output_lines.append("memberOf: dc/g/WHO/%s\n" % current_cat)

                # Now start the process for the new SV.
                current_sv = []
                current_gho_id = "-1"
                current_cat = ""

            current_sv.append(l)
            _COUNTERS_SV_GROUPS["lines_processed"] += 1

    print(counters_print(_COUNTERS_SV_GROUPS))

    with open(output_sv_fp, 'w') as fw:
        for l in output_lines:
            fw.write(l)


def main(_):
    # Required inputs (see the assertions below).

    # Input # 1: An mcf file with existing WHO GHO StatVars for which we want to
    #   insert/update the categories/SVGroups.
    input_sv_fp = os.path.join("input_data", "WHO_GHO_Indicator_SVs.mcf")

    # Input # 2: A csv file which has two columns: gho_id, category_name.
    #   This file contains the mapping from GHO codes to their associated
    #   categories on the WHO/GHO website.
    input_category_map_fp = os.path.join("input_data", "WHO_GHO_Categories.csv")

    # Validate inputs.
    assert os.path.exists(input_sv_fp)
    assert os.path.exists(input_category_map_fp)

    # Output files will be produced/written to the output/ folder under the
    # output folder.
    output_group_fp = os.path.join("output", "WHO_GHO_Categories.svg.mcf")
    output_sv_fp = os.path.join("output", "WHO_GHO_StatVars.mcf")

    process_categories(input_sv_fp, input_category_map_fp, output_group_fp,
                       output_sv_fp)


if __name__ == "__main__":
    app.run(main)
