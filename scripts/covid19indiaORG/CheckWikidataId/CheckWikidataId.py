# Copyright 2020 Google LLC
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


# INDIA_MAP is outside the directory, so we have to change the PYTHONPATH.
import sys
sys.path.append('../')

# Import INDIA_MAP.DISTRICTS, which is a dictionary of state_iso_code->district_name->wikidataId.
from INDIA_MAP import DISTRICTS
from bs4 import BeautifulSoup
import requests
import pandas as pd

# A dictionary wikidataId->metadata.
# Keep track of wikidataId name and country it belongs to.
OUTPUT = {}

# DISTRICTS is keyed by state_iso_code->district_name->wikidataId.
for state_iso_code in DISTRICTS:
    for district_name, wikidataId in DISTRICTS[state_iso_code].items():
        # Get the site HTML for the wikidataId.
        req = requests.get("https://www.wikidata.org/wiki/" + wikidataId)

        # Make sure the response is 200, otherwise skip.
        if req.status_code != 200:
            print("Skipping: " + district_name)
            continue

        html_content = req.content

        # Parse the HTML site.
        soup = BeautifulSoup(html_content, 'html.parser')

        # Get the WikiData item's name if it exists.
        name_elem = soup.find('span', class_='wikibase-title-label')
        wikidata_name = name_elem.text if name_elem else ""

        # Check to see if place is part of India.
        # Q668 is the wikidataId for India country.
        # If element is found, then it is part of India.
        # Otherwise, district is not part of India.
        #NOTE: See README.md for more information.
        in_india = bool(soup.find("a", {"title": "Q668"}))

        # Add the output to the OUTPTU dict.
        OUTPUT[wikidataId] = {"country=India": in_india, "districtName": district_name, "wikidataName": wikidata_name}

# Rotate the dataframe.
df = pd.DataFrame(OUTPUT).T

# Add label to wikidataIds.
df.index.name = 'wikidataId'

# Export DataFrame as CSV.
df.to_csv("output.csv", index=True)
