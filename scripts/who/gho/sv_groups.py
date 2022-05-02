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
import sys
import os

from absl import app

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

_SUB_CATEGORIES_MCF_TEMPLATE = """
Node: dcid:WHO/g/%s
typeOf: dcs:StatVarGroup
name: "%s"
specializationOf: dcid:WHO/g/%s
"""


def _str_to_id(s):
    # ID is Title Case.
    # ID has no spaces.
    # ID only keeps alphanumeric chars.
    s = s.title()
    s = s.replace(" ", "")
    s = re.sub(r'\W+', '', s)

    return s


def _parse_category_data(categories_fp):
    processed_maps = {}
    with open(categories_fp, "r") as cfp:
        ind_to_subcat = {}
        sub_cat_to_cat = {}
        main_cats = set()
        cr = csv.DictReader(cfp)
        for in_row in cr:
            ind = in_row['Indicator Name']
            subcat = in_row['Sub-Category']
            maincat = in_row['Main Category']

            ind_to_subcat[ind] = subcat
            sub_cat_to_cat[subcat] = maincat
            main_cats.add(maincat)

        processed_maps["indicator_to_subcats"] = ind_to_subcat
        processed_maps["subcats_to_categories"] = sub_cat_to_cat
        processed_maps["categories"] = main_cats

    return processed_maps


def process(categories_fp, output_mcf_fp):
    processed_maps = _parse_category_data(categories_fp)

    output_mcf = _ROOT_NODE_MCF

    # First process all the main catgories
    for mc in processed_maps["categories"]:
        output_mcf += _MAIN_CATEGORIES_MCF_TEMPLATE % (_str_to_id(mc),
                                                       mc.title())

    for sc, mc in processed_maps["subcats_to_categories"].items():
        output_mcf += _SUB_CATEGORIES_MCF_TEMPLATE % (
            _str_to_id(sc), sc.title(), _str_to_id(mc))

    with open(output_mcf_fp, 'w') as f2:
        for l in output_mcf:
            f2.write(l)


def main(_):
    # Validate inputs.
    input_fp = os.path.join("input_data", "WHO_GHO_Indicator_Categories.csv")
    output_fp = os.path.join("output", "WHO_categories.svg.mcf")

    process(input_fp, output_fp)


if __name__ == "__main__":
    app.run(main)
