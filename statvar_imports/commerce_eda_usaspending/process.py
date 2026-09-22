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
import json
import os
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from absl import app
from absl import logging

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

VALID_STATE_CODES = {
    "AL", "AK", "AS", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FM", "FL",
    "GA", "GU", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "MP", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN",
    "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "VI", "PW", "MH"
}

CFDA_PROGRAMS = {
    "11.300": "Public Works",
    "11.302": "Planning",
    "11.303": "Technical Assistance",
    "11.307": "Economic Adjustment Assistance",
    "11.310": "Trade Adjustment Assistance for Firms",
    "11.312": "Research and National Technical Assistance",
    "11.313": "Trade Adjustment Assistance for Firms",
    "11.024": "Regional Innovation Strategies",
    "11.020": "Technical Assistance",
    "11.039": "Regional Technology and Innovation Hubs",
    "11.040": "Distressed Area Recompete Pilot Program",
    "11.030": "Science and Research Park Development Grants",
    "11.023": "STEM Talent Challenge"
}

MAX_PAGES_PER_FY = 500


def get_session():
    session = requests.Session()
    retries = Retry(total=5,
                    backoff_factor=1,
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
    if not (parts[0].isdigit() and parts[1].isdigit()):
        return None
    year = int(parts[0])
    month = int(parts[1])
    if month >= 10:
        return year + 1
    return year


def fetch_usaspending_data(start_year,
                           end_year,
                           session=None,
                           raw_output_path=None):
    if session is None:
        session = get_session()
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    unique_awards = {}

    for fy in range(start_year, end_year + 1):
        start_date = f"{fy - 1}-10-01"
        end_date = f"{fy}-09-30"
        page = 1
        fy_awards = []
        logging.info(f"Fetching FY {fy} awards ({start_date} to {end_date})...")

        while True:
            if page > MAX_PAGES_PER_FY:
                raise RuntimeError(
                    f"Exceeded maximum page threshold ({MAX_PAGES_PER_FY}) for FY {fy}"
                )
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
                    "award_type_codes": [
                        "02", "03", "04", "05", "F001", "F002"
                    ]
                },
                "fields": [
                    "Award ID", "Start Date", "Award Amount",
                    "Place of Performance State Code", "CFDA Number",
                    "generated_internal_id"
                ],
                "limit": 100,
                "page": page
            }
            logging.info(f"POST {url} [FY {fy} Page {page}]")

            try:
                response = session.post(url, json=payload, timeout=45)
                response.raise_for_status()
                data = response.json()
            except Exception as err:
                logging.error(f"Failed to fetch FY {fy} page {page}: {err}")
                raise

            results = data.get("results", [])
            if not results:
                break
            fy_awards.extend(results)

            if not data.get("page_metadata", {}).get("hasNext"):
                break
            page += 1
            time.sleep(0.2)

        logging.info(f"Retrieved {len(fy_awards)} awards for FY {fy}")
        for award in fy_awards:
            award_id = award.get("generated_internal_id") or award.get(
                "Award ID")
            if award_id:
                unique_awards[award_id] = award
            else:
                unique_awards[len(unique_awards)] = award

    all_awards = list(unique_awards.values())

    if raw_output_path:
        os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
        tmp_raw_path = raw_output_path + ".tmp"
        with open(tmp_raw_path, "w", encoding="utf-8") as f:
            json.dump(all_awards, f, indent=2)
        if os.path.exists(tmp_raw_path) and os.path.getsize(tmp_raw_path) > 0:
            os.replace(tmp_raw_path, raw_output_path)
            logging.info(
                f"Saved {len(all_awards)} raw awards to {raw_output_path}")

    return all_awards


def process_data(awards, start_year, end_year, output_path):
    unique_awards = {}
    for a in awards:
        award_id = a.get("generated_internal_id") or a.get("Award ID")
        if award_id:
            unique_awards[award_id] = a
        else:
            unique_awards[len(unique_awards)] = a

    data_rows = []
    unmapped_cfdas = set()
    for a in unique_awards.values():
        state_code = str(a.get("Place of Performance State Code") or
                         "").strip().upper()
        if not state_code or state_code not in VALID_STATE_CODES:
            continue

        cfda = str(a.get("CFDA Number") or "").strip()
        category = CFDA_PROGRAMS.get(cfda)
        if not category:
            if cfda:
                unmapped_cfdas.add(cfda)
            continue

        start_date = a.get("Start Date")
        fy = get_fiscal_year(start_date)
        if not fy or fy < start_year or fy > end_year:
            continue

        amount = float(a.get("Award Amount") or 0.0)
        data_rows.append({
            "Place": state_code,
            "Category": category,
            "Year": str(fy),
            "Amount": amount
        })

    if unmapped_cfdas:
        logging.warning(
            f"Encountered unmapped EDA CFDAs: {sorted(list(unmapped_cfdas))}")

    if not data_rows:
        logging.error("No records processed. Output will not be generated.")
        raise RuntimeError(
            "No records processed. Output will not be generated.")

    df = pd.DataFrame(data_rows)
    # Aggregate net amounts per Place, Category, Year
    agg_df = df.groupby(["Place", "Category",
                         "Year"])["Amount"].sum().reset_index()

    # Filter out non-positive program amounts (e.g. net de-obligations)
    # so that reported Totals are mathematically equal to the sum of published components.
    positive_agg = agg_df[agg_df["Amount"] > 0].copy()
    positive_agg["Amount"] = positive_agg["Amount"].apply(
        lambda v: int(round(v)))
    positive_agg = positive_agg[positive_agg["Amount"] > 0].copy()

    # Calculate Totals from positive components
    totals = positive_agg.groupby(["Place",
                                   "Year"])["Amount"].sum().reset_index()
    totals["Category"] = "Total"

    final_df = pd.concat([positive_agg, totals], ignore_index=True)

    # Sort
    places_sorted = sorted(list(final_df["Place"].unique()))
    final_df["place_idx"] = final_df["Place"].apply(
        lambda x: places_sorted.index(x))
    category_order = [
        "Total",
        "Distressed Area Recompete Pilot Program",
        "Economic Adjustment Assistance",
        "Planning",
        "Public Works",
        "Regional Innovation Strategies",
        "Regional Technology and Innovation Hubs",
        "Research and National Technical Assistance",
        "STEM Talent Challenge",
        "Science and Research Park Development Grants",
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

    # Format amount as integer string
    final_df["Amount"] = final_df["Amount"].astype(str)

    final_df = final_df.rename(columns={
        "Category": "State or Territory / EDA Program",
        "Amount": "Value"
    })
    # Reorder columns
    final_df = final_df[[
        "Place", "State or Territory / EDA Program", "Year", "Value"
    ]]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_output_path = output_path + ".tmp"
    final_df.to_csv(tmp_output_path, index=False, header=True)
    if os.path.exists(tmp_output_path) and os.path.getsize(tmp_output_path) > 0:
        os.replace(tmp_output_path, output_path)
        logging.info(
            f"[SUCCESS] Processed data saved successfully to {output_path}")


def main(argv):
    del argv
    start_year = 2012
    end_year = datetime.datetime.now().year + 1
    raw_output_path = os.path.join(_MODULE_DIR, "input_files",
                                   "raw_usaspending_eda_awards.json")
    output_path = os.path.join(_MODULE_DIR, "input_files",
                               "investment_cleaned.csv")

    awards = fetch_usaspending_data(start_year,
                                    end_year,
                                    raw_output_path=raw_output_path)
    logging.info(f"Total awards retrieved: {len(awards)}")

    process_data(awards, start_year, end_year, output_path)


if __name__ == "__main__":
    app.run(main)
