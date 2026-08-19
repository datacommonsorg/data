# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import io
import os
import sys
from urllib.parse import urljoin
from pathlib import Path
from absl import app, logging
from bs4 import BeautifulSoup
import requests
from retry import retry

script_dir = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(script_dir, "input_files")
OUTPUT_CSV = os.path.join(INPUT_DIR, "Death_Data_Cross_Tabulation_data.csv")

SOURCE_URL = "https://wonder.cdc.gov/controller/saved/D158/D516F171"


@retry(tries=3, delay=5, backoff=2, exceptions=(requests.RequestException,))
def download_cdc_wonder_data(saved_url: str) -> str:
    """Automates CDC WONDER saved request session and downloads dataset as TSV/CSV text.

    Args:
        saved_url: Saved request URL from CDC WONDER.

    Returns:
        The raw response text (TSV formatted dataset).
    """
    session = requests.Session()

    logging.info(f"Connecting to CDC WONDER saved query: {saved_url}")
    res = session.get(saved_url, timeout=60)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")
    form = soup.find("form", id="wonderform")
    if not form:
        raise ValueError("Could not find initial wonderform on CDC WONDER page.")

    action = urljoin(saved_url, form.get("action"))
    agree_inputs = [
        (inp.get("name"), inp.get("value", ""))
        for inp in form.find_all("input")
        if inp.get("name")
    ]
    agree_inputs.append(("action-I Agree", "I Agree"))

    logging.info("Submitting Data Use Agreement (I Agree)...")
    res_agree = session.post(action, data=agree_inputs, timeout=60)
    res_agree.raise_for_status()

    soup_req = BeautifulSoup(res_agree.text, "lxml")
    form_req = soup_req.find("form", id="wonderform")
    if not form_req:
        raise ValueError("Could not find request form after agreeing to terms.")

    action_req = urljoin(saved_url, form_req.get("action"))

    # Extract all pre-populated query parameters from the form
    post_data = []
    for el in form_req.find_all(["input", "select", "textarea"]):
        name = el.get("name")
        if not name:
            continue
        if el.name == "input":
            itype = el.get("type", "text").lower()
            if itype in ["submit", "button", "reset", "image"]:
                continue
            if itype in ["checkbox", "radio"]:
                if el.has_attr("checked"):
                    post_data.append((name, el.get("value", "on")))
            else:
                post_data.append((name, el.get("value", "")))
        elif el.name == "select":
            selected_opts = [
                opt for opt in el.find_all("option") if opt.has_attr("selected")
            ]
            if selected_opts:
                for opt in selected_opts:
                    post_data.append((name, opt.get("value", "")))
            else:
                if not el.has_attr("multiple"):
                    first_opt = el.find("option")
                    if first_opt:
                        post_data.append((name, first_opt.get("value", "")))
        elif el.name == "textarea":
            post_data.append((name, el.text or ""))

    # Submit query with action-Send
    post_data.append(("action-Send", "Send"))

    logging.info("Submitting query request to CDC WONDER...")
    res_data = session.post(action_req, data=post_data, timeout=120)
    res_data.raise_for_status()

    return res_data.text


def save_tsv_as_csv(raw_text: str, output_filepath: str):
    """Converts TSV text from CDC WONDER into CSV format and writes to disk."""
    Path(os.path.dirname(output_filepath)).mkdir(parents=True, exist_ok=True)
    tsv_reader = csv.reader(io.StringIO(raw_text), delimiter="\t")

    temp_filepath = f"{output_filepath}.tmp"
    row_count = 0
    with open(temp_filepath, "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        for row in tsv_reader:
            if not row:
                continue
            if row[0].startswith("---") or (len(row) > 1 and row[1].startswith("---")):
                break
            csv_writer.writerow(row)
            row_count += 1

    os.replace(temp_filepath, output_filepath)
    logging.info(f"Successfully saved {row_count} rows to {output_filepath}")


def main(_):
    logging.info("Starting CDC WONDER download process...")
    raw_data = download_cdc_wonder_data(SOURCE_URL)

    if not raw_data or "County Code" not in raw_data:
        logging.fatal("Downloaded data is empty or missing expected headers.")

    save_tsv_as_csv(raw_data, OUTPUT_CSV)
    logging.info(f"CDC WONDER download finished successfully: {OUTPUT_CSV}")


if __name__ == "__main__":
    app.run(main)
