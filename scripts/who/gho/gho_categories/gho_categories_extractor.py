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
"""A simple script to extract the categories for WHO GHO indicators."""
import requests
import sys
import os

from absl import app

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "../.."))

_BASE_URL = "https://apps.who.int/gho/athena/api/GHO"


def _get_gho_codes():
    res = requests.get(_BASE_URL + "?format=json").json()

    dim = res['dimension'][0]
    codes = dim['code']

    gho_codes = set()
    for c in codes:
        gho_codes.add(c['label'])

    return list(gho_codes)


def _get_category(gho_code):
    gho_cat = ""
    print("             %s" % gho_code)
    url_country_usa = _BASE_URL + "/%s?filter=COUNTRY:USA&format=json" % gho_code
    url_region_afr = _BASE_URL + "/%s?filter=REGION:AFR&format=json" % gho_code
    url_country_all = _BASE_URL + "/%s?filter=COUNTRY:*&format=json" % gho_code
    url_all = _BASE_URL + "%s?format=json" % gho_code

    for url in [url_country_usa, url_region_afr, url_country_all, url_all]:
        print("     %s" % url)
        res = requests.get(url).json()
        if res['dimension']:
            break

    if not res['dimension']:
        return gho_cat

    dims = res['dimension']
    for a in dims:
        if a['display'] == 'Indicator':
            if a['code'][0]['label'] == gho_code:
                attrs = a['code'][0]['attr']
                for a in attrs:
                    if a['category'] == 'CATEGORY':
                        gho_cat = a['value']

    return gho_cat


def process_categories(output_fp):
    # Retrieve the latest.
    gho_codes = _get_gho_codes()

    categories_dict = {}
    cats_not_found_for = set()

    # Create the output file and write.
    with open(output_fp, 'w') as f:
        f.write("gho_id,category_name\n")

    time_since_last_write = 0
    buffer = []
    for i in range(len(gho_codes)):
        if i % 100 == 0:
            print("=========")
            print("i = %d" % i)
            print("=========")

        gc = gho_codes[i]
        try:
            # Now retrieve the metadata (also comes with a lot of data)
            gho_cat = _get_category(gc)
        except Exception as e:
            print("Could not retrieve results for: %s" % gc)
            print(e)
            cats_not_found_for.add(gc)
            continue

        if not gho_cat:
            print("Got nothing for: %s" % gc)
            cats_not_found_for.add(gc)
            continue

        gho_cat_name = gho_cat.title()
        categories_dict.update({gc: gho_cat_name})
        buffer.append((gc, gho_cat_name))

        time_since_last_write += 1

        if time_since_last_write >= 50:
            # Create the output file and write.
            with open(output_fp, 'a') as f:
                for b in buffer:
                    f.write("%s,%s\n" % (b[0], b[1]))
                    time_since_last_write = 0
                    buffer = []

    # Write the last few in the buffer.
    with open(output_fp, 'a') as f:
        for b in buffer:
            f.write("%s,%s\n" % (b[0], b[1]))
            time_since_last_write = 0
            buffer = []

    print(categories_dict)
    print("======")
    print("No Categories found for: ")
    print(cats_not_found_for)


def main(_):
    output_filename = os.path.join("input_data", "WHO_GHO_Categories.csv")
    process_categories(output_filename)


if __name__ == "__main__":
    app.run(main)
