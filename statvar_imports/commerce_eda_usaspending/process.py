# Copyright 2026 Google LLC
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

import datetime
import os
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from absl import app
from absl import logging

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

STATE_ABBREV = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FM": "Federated States of Micronesia",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "MP": "Northern Mariana Islands",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "VI": "U.S. Virgin Islands",
    "PW": "Palau",
    "MH": "Marshall Islands"
}

CFDA_PROGRAMS = {
    "11.300": "Public Works",
    "11.302": "Planning",
    "11.303": "Technical Assistance",
    "11.307": "Economic Adjustment Assistance",
    "11.310": "Trade Adjustment Assistance for Firms",
    "11.312": "Research and National Technical Assistance",
    "11.313": "Regional Innovation Strategies",
    "11.024": "Regional Innovation Strategies",
    "11.020": "Technical Assistance"
}


def get_session():
    session = requests.Session()
    retries = Retry(total=6,
                    backoff_factor=2,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["POST"])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_fiscal_year(date_str):
    if not date_str:
        return None
    parts = date_str.split("-")
    if len(parts) < 2:
        return None
    year = int(parts[0])
    month = int(parts[1])
    if month >= 10:
        return year + 1
    return year


def fetch_usaspending_data(start_year, end_year, session=None):
    if session is None:
        session = get_session()
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    page = 1
    all_awards = []

    # Format dates to cover the full fiscal year range
    start_date = f"{start_year - 1}-10-01"
    end_date = f"{end_year}-09-30"

    logging.info(f"Fetching awards from {start_date} to {end_date}...")

    while True:
        payload = {
            "filters": {
                "agencies": [{
                    "type": "awarding",
                    "tier": "subtier",
                    "name": "Economic Development Administration"
                }],
                "time_period": [{
                    "start_date": start_date,
                    "end_date": end_date
                }],
                "award_type_codes": ["02", "03", "04", "05", "F001", "F002"]
            },
            "fields": [
                "Award ID", "Start Date", "Award Amount",
                "Place of Performance State Code", "CFDA Number"
            ],
            "limit": 100,
            "page": page
        }
        logging.info(f"Fetching page {page}...")

        max_page_attempts = 4
        data = None
        for attempt in range(1, max_page_attempts + 1):
            try:
                response = session.post(url, json=payload, timeout=45)
                response.raise_for_status()
                data = response.json()
                break
            except Exception as err:
                logging.warning(
                    f"Attempt {attempt}/{max_page_attempts} on page {page} failed: {err}"
                )
                if attempt == max_page_attempts:
                    logging.error(
                        f"Failed page {page} after {max_page_attempts} attempts."
                    )
                    raise
                time.sleep(2**attempt)

        results = data.get("results", [])
        all_awards.extend(results)

        if not data.get("page_metadata", {}).get("hasNext"):
            break
        page += 1
        time.sleep(0.2)

    return all_awards


def process_data(awards, start_year, end_year, output_path):
    data_rows = []
    for a in awards:
        state_code = a.get("Place of Performance State Code")
        state_name = STATE_ABBREV.get(state_code)
        if not state_name:
            continue

        cfda = a.get("CFDA Number")
        category = CFDA_PROGRAMS.get(cfda)
        if not category:
            continue

        start_date = a.get("Start Date")
        fy = get_fiscal_year(start_date)
        if not fy or fy < start_year or fy > end_year:
            continue

        amount = a.get("Award Amount", 0.0)
        data_rows.append({
            "Place": state_name,
            "Category": category,
            "Year": str(fy),
            "Amount": amount
        })

    if not data_rows:
        logging.fatal("No records processed. Output will not be generated.")
        return

    df = pd.DataFrame(data_rows)
    # Aggregate
    agg_df = df.groupby(["Place", "Category",
                         "Year"])["Amount"].sum().reset_index()

    # Calculate Totals
    totals = agg_df.groupby(["Place", "Year"])["Amount"].sum().reset_index()
    totals["Category"] = "Total"

    final_df = pd.concat([agg_df, totals], ignore_index=True)

    # Sort
    places_sorted = sorted(list(final_df["Place"].unique()))
    final_df["place_idx"] = final_df["Place"].apply(
        lambda x: places_sorted.index(x))
    category_order = [
        "Total",
        "Economic Adjustment Assistance",
        "Planning",
        "Public Works",
        "Regional Innovation Strategies",
        "Research and National Technical Assistance",
        "Technical Assistance",
        "Trade Adjustment Assistance for Firms",
    ]

    def get_cat_idx(cat):
        if cat in category_order:
            return category_order.index(cat)
        return 100

    final_df["cat_idx"] = final_df["Category"].apply(get_cat_idx)
    final_df = final_df.sort_values(
        by=["place_idx", "cat_idx", "Year"]).reset_index(drop=True)
    final_df = final_df.drop(columns=["place_idx", "cat_idx"])

    # Format amount
    final_df["Amount"] = final_df["Amount"].apply(
        lambda val: str(int(round(val))) if val > 0 else "")
    # Drop rows with empty amounts
    final_df = final_df[final_df["Amount"] != ""]

    final_df = final_df.rename(columns={
        "Category": "State or Territory / EDA Program",
        "Amount": "Value"
    })
    # Reorder columns
    final_df = final_df[[
        "Place", "State or Territory / EDA Program", "Year", "Value"
    ]]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False, header=True)
    logging.info(f"✅ Processed data saved successfully to {output_path}")


def main(argv):
    del argv
    start_year = 2012
    end_year = datetime.datetime.now().year + 1
    output_path = os.path.join(_MODULE_DIR, "output", "Investment_cleaned.csv")

    awards = fetch_usaspending_data(start_year, end_year)
    logging.info(f"Total awards retrieved: {len(awards)}")

    process_data(awards, start_year, end_year, output_path)


if __name__ == "__main__":
    app.run(main)
