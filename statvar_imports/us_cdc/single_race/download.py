# Copyright 2026 Google LLC
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
"""Automated live downloader for CDC WONDER Single Race Mortality Data (D158).

This script automates downloading county-level mortality statistics from CDC
WONDER (Database D158: Underlying Cause of Death, Single Race).

Data is broken down by:
- Year (2018 to 2024, or specified range)
- County
- Sex (Male, Female)
- Single Race 6 (6 categories)
- ICD-10 113 Cause List

CDC WONDER imposes a hard limit of 75,000 rows per export query. This script
queries state by state, automatically detects when a state query exceeds the
75,000 row cap, and splits into smaller year chunks to download complete data.
"""

import csv
import io
import os
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from absl import app
from absl import flags
from absl import logging
from bs4 import BeautifulSoup
import requests
from retry import retry

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_DIR = os.path.join(_SCRIPT_DIR, "input_files")
SOURCE_LANDING_URL = "https://wonder.cdc.gov/ucd-icd10-expanded.html"

# 50 States + District of Columbia FIPS codes
US_STATES: Dict[str, str] = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}

# Populous states that exceed CDC WONDER's 75,000 row cap across 6 years.
# Querying directly in 2-year chunks prevents query buffer overruns and HTTP 400 errors.
LARGE_STATES: set[str] = {
    "01",
    "06",
    "12",
    "13",
    "17",
    "18",
    "21",
    "22",
    "26",
    "27",
    "28",
    "29",
    "34",
    "36",
    "37",
    "39",
    "40",
    "42",
    "45",
    "47",
    "48",
    "51",
    "53",
    "55",
}

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "states",
    "all",
    "Comma-separated 2-digit FIPS codes of states to download (e.g. '02,48'), or 'all'.",
)
flags.DEFINE_string(
    "years",
    "2018-2024",
    "Year range ('2018-2024') or comma-separated years ('2018,2019,2020').",
)
flags.DEFINE_string(
    "output_dir",
    DEFAULT_INPUT_DIR,
    "Directory where downloaded CSV files will be saved.",
)
flags.DEFINE_float(
    "delay",
    5.0,
    "Politeness delay in seconds between successive HTTP queries.",
)
flags.DEFINE_integer(
    "timeout",
    120,
    "HTTP request timeout in seconds.",
)
flags.DEFINE_bool(
    "skip_existing",
    True,
    "Skip downloading states that already have existing non-empty CSV files in output_dir.",
)
flags.DEFINE_integer(
    "batch_size",
    8,
    "Number of states to process per session before automatically refreshing session.",
)
flags.DEFINE_float(
    "batch_cooldown",
    60.0,
    "Cooldown delay in seconds between session batches to prevent rate limits.",
)


def parse_year_list(year_str: str) -> List[str]:
    """Parses a year string like '2018-2024' or '2018,2019' into a list of year strings."""
    year_str = year_str.strip()
    if "-" in year_str and not year_str.startswith("-"):
        parts = year_str.split("-")
        start, end = int(parts[0]), int(parts[1])
        return [str(y) for y in range(start, end + 1)]
    return [y.strip() for y in year_str.split(",") if y.strip()]


class CdcWonderSingleRaceDownloader:
    """Automates CDC WONDER sessions and queries for Single Race mortality data."""

    def __init__(
        self,
        landing_url: str = SOURCE_LANDING_URL,
        timeout: int = 120,
        delay: float = 2.0,
    ):
        self.landing_url = landing_url
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent":
            "Mozilla/5.0 (DataCommons CDC Importer; contact: support@datacommons.org)"
        })
        self.action_url: Optional[str] = None
        self.base_post_data: List[Tuple[str, str]] = []

    @retry(tries=3,
           delay=5,
           backoff=2,
           exceptions=(requests.RequestException, ValueError))
    def init_session(self):
        """Accesses landing page, submits agreement, and extracts base query form parameters."""
        if hasattr(self, "session") and self.session:
            try:
                self.session.close()
            except Exception:
                pass
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent":
            "Mozilla/5.0 (DataCommons CDC Importer; contact: support@datacommons.org)"
        })
        self.action_url = None
        self.base_post_data = []

        logging.info("Connecting to CDC WONDER landing page: %s",
                     self.landing_url)
        res = self.session.get(self.landing_url, timeout=self.timeout)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "lxml")
        form = soup.find("form", id="wonderform")
        if not form:
            raise ValueError(
                "Could not find initial wonderform on CDC WONDER page.")

        action = urljoin(self.landing_url, form.get("action"))
        agree_inputs = [(inp.get("name"), inp.get("value", ""))
                        for inp in form.find_all("input") if inp.get("name")]
        agree_inputs.append(("action-I Agree", "I Agree"))

        logging.info("Submitting Data Use Agreement (I Agree)...")
        res_agree = self.session.post(action,
                                      data=agree_inputs,
                                      timeout=self.timeout)
        res_agree.raise_for_status()

        soup_req = BeautifulSoup(res_agree.text, "lxml")
        form_req = soup_req.find("form", id="wonderform")
        if not form_req:
            raise ValueError(
                "Could not find request form after agreeing to terms.")

        self.action_url = urljoin(self.landing_url, form_req.get("action"))

        # Extract pre-populated query parameters
        self.base_post_data = []
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
                        self.base_post_data.append(
                            (name, el.get("value", "on")))
                else:
                    self.base_post_data.append((name, el.get("value", "")))
            elif el.name == "select":
                selected_opts = [
                    opt for opt in el.find_all("option")
                    if opt.has_attr("selected")
                ]
                if selected_opts:
                    for opt in selected_opts:
                        self.base_post_data.append((name, opt.get("value",
                                                                  "")))
                else:
                    if not el.has_attr("multiple"):
                        first_opt = el.find("option")
                        if first_opt:
                            self.base_post_data.append(
                                (name, first_opt.get("value", "")))
            elif el.name == "textarea":
                self.base_post_data.append((name, el.text or ""))

        logging.info(
            "Successfully established CDC WONDER session with action: %s",
            self.action_url)

    def _build_post_data(
            self,
            state_fips: str,
            years: Optional[List[str]] = None) -> List[Tuple[str, str]]:
        """Constructs query payload for single race mortality with groupings and filters."""
        query_data: List[Tuple[str, str]] = []
        for k, v in self.base_post_data:
            # Grouping fields:
            # B_1: Year
            # B_2: County
            # B_3: Sex
            # B_4: Single Race 6
            # B_5: ICD-10 113 Cause List
            if k == "B_1":
                query_data.append((k, "D158.V1-level1"))
            elif k == "B_2":
                query_data.append((k, "D158.V9-level2"))
            elif k == "B_3":
                query_data.append((k, "D158.V7"))
            elif k == "B_4":
                query_data.append((k, "D158.V42"))
            elif k == "B_5":
                query_data.append((k, "D158.V4"))
            elif k == "F_D158.V9":
                # Filter by state FIPS code
                query_data.append((k, state_fips))
            elif k == "F_D158.V1":
                # Year filter - handle separately below if specific years requested
                if not years:
                    query_data.append((k, v))
            else:
                query_data.append((k, v))

        if years:
            for y in years:
                query_data.append(("F_D158.V1", y))

        query_data.append(("action-Export Results", "Export Results"))
        return query_data

    def execute_query(
        self,
        state_fips: str,
        years: Optional[List[str]] = None,
        max_retries: int = 5,
    ) -> str:
        """Executes query with automatic 429 rate-limit backoff and session renewal."""
        if not self.action_url or not self.base_post_data:
            self.init_session()

        payload = self._build_post_data(state_fips, years)

        for attempt in range(1, max_retries + 1):
            try:
                res = self.session.post(self.action_url,
                                        data=payload,
                                        timeout=self.timeout)
                if res.status_code == 429:
                    retry_after = res.headers.get("Retry-After")
                    # CDC WONDER WAF explicitly states:
                    # "Your IP address has been temporarily blocked... Please wait 30 minutes before trying again."
                    # Any probe before 30 minutes resets the firewall penalty timer.
                    # Therefore, on 429 we must pause for the full 30 minutes (+ 1 min buffer) in complete silence.
                    wait_time = int(
                        retry_after) if retry_after and retry_after.isdigit(
                        ) else 1860  # 31 minutes
                    logging.warning(
                        "Encountered HTTP 429 (Too Many Requests). CDC WONDER enforces a 30-minute IP block. "
                        "Waiting %d seconds (%d min) in complete silence for block to clear (attempt %d)...",
                        wait_time,
                        wait_time // 60,
                        attempt,
                    )
                    time.sleep(wait_time)
                    # Re-initialize session to renew cookies and session ID
                    try:
                        self.init_session()
                        payload = self._build_post_data(state_fips, years)
                    except Exception as e:
                        logging.warning("Session re-initialization error: %s",
                                        e)
                    continue

                if res.status_code == 400:
                    logging.warning(
                        "CDC WONDER returned HTTP 400 (likely query buffer overrun for large state). Returning for partitioning."
                    )
                    return "CDC WONDER 400 Bad Request (query too large)"

                res.raise_for_status()
                return res.text
            except (requests.RequestException, ValueError) as e:
                if attempt == max_retries:
                    raise
                wait_time = 15 * attempt
                logging.warning(
                    "Request error: %s. Renewing session and retrying in %d seconds (attempt %d/%d)...",
                    e,
                    wait_time,
                    attempt,
                    max_retries,
                )
                time.sleep(wait_time)
                try:
                    self.init_session()
                    payload = self._build_post_data(state_fips, years)
                except Exception as session_err:
                    logging.warning("Session re-initialization error: %s",
                                    session_err)

        raise RuntimeError(
            f"Failed to query {state_fips} after {max_retries} attempts.")

    def download_state(self, state_fips: str,
                       years: List[str]) -> List[Tuple[str, str]]:
        """Downloads data for a given state.

        Automatically detects if the state exceeds the 75,000 row limit, times out,
        or encounters server errors across all years, and partitions into smaller chunks.

        Returns:
            List of tuples: (chunk_label, tsv_content)
        """
        state_name = US_STATES.get(state_fips, f"FIPS-{state_fips}")
        logging.info("Querying data for %s (FIPS %s) for years %s...",
                     state_name, state_fips, years)

        need_partitioning = False

        if state_fips in LARGE_STATES and len(years) > 2:
            logging.info(
                "%s is a high-volume state (>75k rows). Querying directly in 2-year chunks...",
                state_name)
            need_partitioning = True
        else:
            # Try querying all years first
            try:
                response_text = self.execute_query(state_fips, years)
                first_line = response_text.split("\n", 1)[0]
                if "County Code" in first_line:
                    logging.info(
                        "Successfully fetched %s (all requested years in 1 query).",
                        state_name)
                    return [("all", response_text)]
                else:
                    logging.warning(
                        "%s response not TSV (likely exceeded 75k rows: %s). Partitioning into chunks...",
                        state_name,
                        response_text[:120].strip().replace("\n", " "),
                    )
                    need_partitioning = True
            except Exception as e:
                logging.warning(
                    "Querying all %d years for %s encountered %s. Partitioning into year chunks...",
                    len(years),
                    state_name,
                    e,
                )
                need_partitioning = True

        if need_partitioning:
            # Partition years into 2-year chunks
            chunk_results = []
            chunk_size = 2 if len(years) > 2 else 1
            for i in range(0, len(years), chunk_size):
                year_chunk = years[i:i + chunk_size]
                chunk_label = f"{year_chunk[0]}_{year_chunk[-1]}" if len(
                    year_chunk) > 1 else year_chunk[0]
                logging.info(
                    "Querying %s for chunk %s (%s)...",
                    state_name,
                    chunk_label,
                    year_chunk,
                )
                time.sleep(self.delay)
                chunk_text = self.execute_query(state_fips, year_chunk)
                chunk_first_line = chunk_text.split("\n", 1)[0]

                if "County Code" not in chunk_first_line:
                    # If 2-year chunk is still too big, try 1-year chunks
                    if len(year_chunk) > 1:
                        logging.warning(
                            "Chunk %s still too large for %s. Splitting into 1-year chunks...",
                            chunk_label,
                            state_name,
                        )
                        for single_year in year_chunk:
                            time.sleep(self.delay)
                            sy_text = self.execute_query(
                                state_fips, [single_year])
                            if "County Code" not in sy_text.split("\n", 1)[0]:
                                raise ValueError(
                                    f"Failed to query {state_name} even for single year {single_year}."
                                )
                            chunk_results.append((single_year, sy_text))
                    else:
                        raise ValueError(
                            f"Failed to query {state_name} for chunk {chunk_label}: {chunk_text[:300]}"
                        )
                else:
                    chunk_results.append((chunk_label, chunk_text))

            return chunk_results


def save_tsv_as_csv(raw_tsv: str, output_filepath: str) -> int:
    """Converts TSV text from CDC WONDER into CSV format, writing atomically."""
    Path(os.path.dirname(output_filepath)).mkdir(parents=True, exist_ok=True)
    tsv_reader = csv.reader(io.StringIO(raw_tsv), delimiter="\t")

    temp_filepath = f"{output_filepath}.tmp"
    row_count = 0
    with open(temp_filepath, "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        for row in tsv_reader:
            if not row:
                continue
            # Stop at metadata notes footer
            if row[0].startswith("---") or (len(row) > 1
                                            and row[1].startswith("---")):
                break
            csv_writer.writerow(row)
            row_count += 1

    os.replace(temp_filepath, output_filepath)
    logging.info("Saved %d rows to %s", row_count, output_filepath)
    return row_count


def is_state_downloaded(output_dir: str,
                        state_fips: str,
                        years: Optional[List[str]] = None) -> bool:
    """Checks if valid non-empty CSV files for this state already exist in output_dir."""
    pattern = f"UnderlyingCauseofDeath_SingleRace_{state_fips}*.csv"
    matches = list(Path(output_dir).glob(pattern))
    if not matches:
        return False
    # Verify that all found files are non-empty (> 100 bytes)
    if not all(f.stat().st_size > 100 for f in matches):
        return False
    if years:
        latest_year = years[-1]
        has_chunk = any(
            f.name.endswith(f"_{latest_year}.csv")
            or f"_{latest_year}_" in f.name for f in matches)
        if has_chunk:
            return True
        single_file = Path(
            output_dir) / f"UnderlyingCauseofDeath_SingleRace_{state_fips}.csv"
        if single_file.exists():
            content = single_file.read_text(encoding="utf-8", errors="replace")
            return f",{latest_year}," in content
        return False
    return True


def download_single_race_data(
    states: List[str],
    years: List[str],
    output_dir: str,
    delay: float = 3.0,
    timeout: int = 120,
    skip_existing: bool = True,
    batch_size: int = 10,
    batch_cooldown: float = 20.0,
):
    """Downloads CDC Single Race mortality data for specified states and years."""
    os.makedirs(output_dir, exist_ok=True)
    downloader = CdcWonderSingleRaceDownloader(timeout=timeout, delay=delay)
    downloader.init_session()

    total_files = 0
    total_rows = 0
    states_in_batch = 0

    for idx, state_fips in enumerate(states, start=1):
        state_name = US_STATES.get(state_fips, f"FIPS-{state_fips}")

        if skip_existing and is_state_downloaded(
                output_dir, state_fips, years=years):
            existing_files = list(
                Path(output_dir).glob(
                    f"UnderlyingCauseofDeath_SingleRace_{state_fips}*.csv"))
            logging.info(
                "[%d/%d] Skipping %s (FIPS %s): %d existing file(s) found.",
                idx,
                len(states),
                state_name,
                state_fips,
                len(existing_files),
            )
            continue

        logging.info(
            "[%d/%d] Processing %s (FIPS %s) (Session batch item %d/%d)...",
            idx,
            len(states),
            state_name,
            state_fips,
            states_in_batch + 1,
            batch_size,
        )

        chunks = downloader.download_state(state_fips, years)

        for chunk_label, tsv_data in chunks:
            if chunk_label == "all":
                filename = f"UnderlyingCauseofDeath_SingleRace_{state_fips}.csv"
            else:
                filename = f"UnderlyingCauseofDeath_SingleRace_{state_fips}_{chunk_label}.csv"

            output_file = os.path.join(output_dir, filename)
            rows = save_tsv_as_csv(tsv_data, output_file)
            total_files += 1
            total_rows += rows

        states_in_batch += 1

        # Automatically refresh session after each batch of 10 states
        if states_in_batch >= batch_size and idx < len(states):
            logging.info(
                "Completed session batch of %d states. Cooling down for %.1fs and renewing CDC session...",
                states_in_batch,
                batch_cooldown,
            )
            time.sleep(batch_cooldown)
            downloader.init_session()
            states_in_batch = 0
        elif idx < len(states):
            time.sleep(delay)

    logging.info("Download complete: Saved %d files with %d total rows in %s.",
                 total_files, total_rows, output_dir)


def main(_):
    years = parse_year_list(FLAGS.years)

    if FLAGS.states.lower() == "all":
        states = sorted(list(US_STATES.keys()))
    else:
        states = [
            s.strip().zfill(2) for s in FLAGS.states.split(",") if s.strip()
        ]

    logging.info(
        "Starting CDC Single Race live download for %d states, years: %s",
        len(states), years)
    download_single_race_data(
        states=states,
        years=years,
        output_dir=FLAGS.output_dir,
        delay=FLAGS.delay,
        timeout=FLAGS.timeout,
        skip_existing=FLAGS.skip_existing,
        batch_size=FLAGS.batch_size,
        batch_cooldown=FLAGS.batch_cooldown,
    )


if __name__ == "__main__":
    app.run(main)
