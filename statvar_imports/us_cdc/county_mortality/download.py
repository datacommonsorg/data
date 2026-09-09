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

"""Automated live downloader for CDC WONDER County-Level Mortality Data (D158).

This script automates downloading county-level mortality statistics across all
causes of death (ICD-10 113 Cause List) from CDC WONDER (Database D158:
Underlying Cause of Death).

Data is broken down by:
- Year (2018 to 2024, or specified range)
- County (all US counties across 50 states + DC)
- ICD-10 113 Cause List (all diseases/causes)

CDC WONDER imposes a hard limit of 75,000 rows per export query. This script
queries state by state, automatically detects if a state query exceeds the
75,000 row cap, and splits into smaller year chunks to download complete data.
"""

import csv
import io
import os
from pathlib import Path
import time
from typing import List, Optional, Tuple
from urllib.parse import urljoin

from absl import app, flags, logging
from bs4 import BeautifulSoup
import requests
from retry import retry

script_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUT_DIR = os.path.join(script_dir, "input_files")

# Mapping of 2-digit FIPS codes to US State / Territory names
US_STATES = {
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

# High-population states that exceed CDC WONDER's row and memory limits when queried across 7 years.
# Querying directly in 2-year chunks prevents query buffer overruns and HTTP 400 errors.
LARGE_STATES: set[str] = {
    "01", "05", "06", "12", "13", "17", "18", "21", "22", "26", "27", "28", "29",
    "34", "36", "37", "39", "40", "42", "45", "47", "48", "51", "53", "55",
}

# States with exceptionally large county counts (e.g. Texas with 254 counties) that frequently
# trigger HTTP 504 Gateway Timeouts when queried across multiple years during peak traffic hours.
SINGLE_YEAR_STATES: set[str] = {"48"}

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
    3.0,
    "Politeness delay in seconds between successive HTTP queries.",
)
flags.DEFINE_integer(
    "timeout",
    120,
    "HTTP request timeout in seconds.",
)
flags.DEFINE_boolean(
    "skip_existing",
    True,
    "Skip downloading states that already have existing non-empty CSV files in output_dir.",
)
flags.DEFINE_integer(
    "batch_size",
    10,
    "Number of states to process per session before automatically refreshing session.",
)
flags.DEFINE_float(
    "batch_cooldown",
    20.0,
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


class CdcWonderCountyMortalityDownloader:
    """Automates CDC WONDER sessions and queries for County-Level Mortality data across all causes."""

    def __init__(
        self,
        landing_url: str = "https://wonder.cdc.gov/ucd-icd10-expanded.html",
        timeout: int = 120,
        delay: float = 3.0,
    ):
        self.landing_url = landing_url
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (DataCommons CDC Importer; contact: support@datacommons.org)"}
        )
        self.action_url: Optional[str] = None
        self.base_post_data: List[Tuple[str, str]] = []

    @retry(
        tries=3,
        delay=5,
        backoff=2,
        exceptions=(requests.RequestException, ValueError),
    )
    def init_session(self):
        """Connects to landing page, agrees to data use terms, and stores pre-populated form state."""
        if hasattr(self, "session") and self.session:
            try:
                self.session.close()
            except Exception:
                pass
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (DataCommons CDC Importer; contact: support@datacommons.org)"}
        )
        self.action_url = None
        self.base_post_data = []

        logging.info("Connecting to CDC WONDER landing page: %s", self.landing_url)
        res = self.session.get(self.landing_url, timeout=self.timeout)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "lxml")
        form = soup.find("form", id="wonderform")
        if not form:
            raise ValueError("Could not find initial wonderform on CDC WONDER page.")

        action = urljoin(self.landing_url, form.get("action"))
        agree_inputs = [
            (inp.get("name"), inp.get("value", ""))
            for inp in form.find_all("input")
            if inp.get("name")
        ]
        agree_inputs.append(("action-I Agree", "I Agree"))

        logging.info("Submitting Data Use Agreement (I Agree)...")
        res_agree = self.session.post(action, data=agree_inputs, timeout=self.timeout)
        res_agree.raise_for_status()

        soup_req = BeautifulSoup(res_agree.text, "lxml")
        form_req = soup_req.find("form", id="wonderform")
        if not form_req:
            raise ValueError("Could not find request form after agreeing to terms.")

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
                        self.base_post_data.append((name, el.get("value", "on")))
                else:
                    self.base_post_data.append((name, el.get("value", "")))
            elif el.name == "select":
                selected_opts = [opt for opt in el.find_all("option") if opt.has_attr("selected")]
                if selected_opts:
                    for opt in selected_opts:
                        self.base_post_data.append((name, opt.get("value", "")))
                else:
                    if not el.has_attr("multiple"):
                        first_opt = el.find("option")
                        if first_opt:
                            self.base_post_data.append((name, first_opt.get("value", "")))
            elif el.name == "textarea":
                self.base_post_data.append((name, el.text or ""))

        logging.info("Successfully established CDC WONDER session with action: %s", self.action_url)

    def _build_post_data(
        self, state_fips: str, years: Optional[List[str]] = None
    ) -> List[Tuple[str, str]]:
        """Constructs query payload for county-level mortality across all causes."""
        query_data: List[Tuple[str, str]] = []
        for k, v in self.base_post_data:
            # Grouping fields:
            # B_1: Year
            # B_2: County
            # B_3: ICD-10 113 Cause List
            # B_4: *None*
            # B_5: *None*
            if k == "B_1":
                query_data.append((k, "D158.V1-level1"))
            elif k == "B_2":
                query_data.append((k, "D158.V9-level2"))
            elif k == "B_3":
                query_data.append((k, "D158.V4"))
            elif k == "B_4":
                query_data.append((k, "*None*"))
            elif k == "B_5":
                query_data.append((k, "*None*"))
            elif k == "F_D158.V9":
                # Filter by state FIPS code
                query_data.append((k, state_fips))
            elif k == "F_D158.V1":
                # Year filter - handled below
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
                res = self.session.post(self.action_url, data=payload, timeout=self.timeout)

                if res.status_code == 429:
                    retry_after = res.headers.get("Retry-After")
                    wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else 1860
                    logging.warning(
                        "Encountered HTTP 429 (Too Many Requests). CDC WONDER enforces a 30-minute "
                        "IP block. Waiting %d seconds (%d min) in complete silence for block to "
                        "clear (attempt %d)...",
                        wait_seconds,
                        wait_seconds // 60,
                        attempt,
                    )
                    time.sleep(wait_seconds)
                    logging.info("Block elapsed. Re-initializing new CDC WONDER session...")
                    self.init_session()
                    payload = self._build_post_data(state_fips, years)
                    continue

                if res.status_code == 400 and ("too much data" in res.text or "simplify your filters" in res.text):
                    logging.warning(
                        "FIPS %s query returned 'too much data' (HTTP 400). Returning response for partitioning.",
                        state_fips,
                    )
                    return res.text

                res.raise_for_status()
                return res.text

            except requests.RequestException as e:
                logging.warning("Query failed for FIPS %s (attempt %d/%d): %s", state_fips, attempt, max_retries, e)
                if attempt == max_retries:
                    raise
                time.sleep(self.delay * attempt)
                self.init_session()
                payload = self._build_post_data(state_fips, years)

        raise RuntimeError(f"Failed to fetch data for state FIPS {state_fips} after {max_retries} retries.")

    def download_state(
        self, state_fips: str, years: List[str]
    ) -> List[Tuple[str, str]]:
        """Downloads county mortality data for a state, automatically partitioning if needed."""
        state_name = US_STATES.get(state_fips, f"FIPS-{state_fips}")
        results: List[Tuple[str, str]] = []
        need_partitioning = state_fips in LARGE_STATES

        if not need_partitioning:
            logging.info("Querying full year range (%s) for state FIPS %s (%s)...", years, state_fips, state_name)
            try:
                tsv_text = self.execute_query(state_fips, years)
                first_line = tsv_text.splitlines()[0] if tsv_text else ""
                if "County Code" in first_line:
                    results.append(("all", tsv_text))
                    time.sleep(self.delay)
                    return results
                logging.warning(
                    "%s response not TSV (likely exceeded 75k rows / too much data). Partitioning into chunks...",
                    state_name,
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
            logging.info("Partitioning %s (%s) into chunks...", state_name, state_fips)
            use_single_years = (len(years) <= 2) or (state_fips in SINGLE_YEAR_STATES)
            i = 0
            while i < len(years):
                if not use_single_years and (i + 1 < len(years)):
                    year_chunk = years[i : i + 2]
                    chunk_label = f"{year_chunk[0]}_{year_chunk[-1]}"
                    logging.info("Querying chunk %s for %s...", chunk_label, state_name)
                    time.sleep(self.delay)

                    chunk_tsv = ""
                    success = False
                    try:
                        chunk_tsv = self.execute_query(state_fips, year_chunk, max_retries=2)
                        chunk_first_line = chunk_tsv.splitlines()[0] if chunk_tsv else ""
                        if "County Code" in chunk_first_line:
                            success = True
                        else:
                            logging.warning(
                                "Chunk %s response for %s did not contain valid TSV data. Splitting into single years.",
                                chunk_label,
                                state_name,
                            )
                    except Exception as e:
                        logging.warning(
                            "Chunk %s for %s failed with %s. Falling back to single-year queries for this state.",
                            chunk_label,
                            state_name,
                            e,
                        )

                    if success:
                        results.append((chunk_label, chunk_tsv))
                        i += 2
                        continue
                    else:
                        use_single_years = True

                single_year = years[i]
                logging.info("Querying single year %s for %s...", single_year, state_name)
                time.sleep(self.delay)
                sy_text = self.execute_query(state_fips, [single_year])
                first_line = sy_text.splitlines()[0] if sy_text else ""
                if "County Code" not in first_line:
                    raise ValueError(f"Failed to query {state_name} even for single year {single_year}.")
                results.append((single_year, sy_text))
                i += 1

            return results


def save_tsv_as_csv(raw_tsv: str, output_csv_path: str) -> int:
    """Parses raw CDC TSV export into clean CSV format, stripping footer caveats."""
    Path(os.path.dirname(output_csv_path)).mkdir(parents=True, exist_ok=True)
    tsv_reader = csv.reader(io.StringIO(raw_tsv), delimiter="\t")

    temp_csv_path = f"{output_csv_path}.tmp"
    row_count = 0
    with open(temp_csv_path, "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        for row in tsv_reader:
            if not row:
                continue
            if row[0].startswith("---") or (len(row) > 1 and row[1].startswith("---")):
                break
            csv_writer.writerow(row)
            row_count += 1

    os.replace(temp_csv_path, output_csv_path)
    return row_count


def _has_data_rows(file_path: Path) -> bool:
    """Checks whether a CSV file contains at least one observation data row beyond the header."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return False
            for row in reader:
                if row and not row[0].startswith("---") and not row[0].startswith("Total"):
                    return True
        return False
    except Exception:
        return False


def is_state_downloaded(
    output_dir: str, state_fips: str, years: Optional[List[str]] = None
) -> bool:
    """Checks if valid non-empty CSV files for this state already exist covering requested years."""
    pattern = f"UnderlyingCauseofDeath_County_{state_fips}*.csv"
    matches = list(Path(output_dir).glob(pattern))
    if not matches:
        return False

    # Check if a single combined file exists and contains data rows for all requested years
    single_file = Path(output_dir) / f"UnderlyingCauseofDeath_County_{state_fips}.csv"
    if single_file.exists():
        found_years = set()
        try:
            with open(single_file, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header:
                    year_col_idx = 1
                    if "Year" in header:
                        year_col_idx = header.index("Year")
                    for row in reader:
                        if len(row) > year_col_idx:
                            year_val = row[year_col_idx].strip()
                            if years is None or year_val in years:
                                found_years.add(year_val)
                    if years is None and found_years:
                        return True
                    if years and len(found_years) == len(years):
                        return True
        except Exception:
            pass

    # If no specific years requested, check if any matching file has valid data rows
    if not years:
        return any(_has_data_rows(f) for f in matches)

    # Otherwise, check if every year in years is covered by at least one chunk file with data rows
    for y in years:
        year_covered = False
        for f in matches:
            if f.name == single_file.name:
                continue
            if (f"_{y}.csv" in f.name or f"_{y}_" in f.name) and _has_data_rows(f):
                year_covered = True
                break
        if not year_covered:
            return False
    return True


def download_county_mortality_data(
    states: List[str],
    years: List[str],
    output_dir: str,
    delay: float = 3.0,
    timeout: int = 120,
    skip_existing: bool = True,
    batch_size: int = 10,
    batch_cooldown: float = 20.0,
):
    """Downloads CDC County Mortality data for specified states and years."""
    os.makedirs(output_dir, exist_ok=True)
    downloader = CdcWonderCountyMortalityDownloader(timeout=timeout, delay=delay)

    total_files = 0
    total_rows = 0
    states_in_batch = 0
    failed_states = []

    for idx, state_fips in enumerate(states, start=1):
        state_name = US_STATES.get(state_fips, f"FIPS-{state_fips}")

        if skip_existing and is_state_downloaded(output_dir, state_fips, years=years):
            existing_files = list(Path(output_dir).glob(f"UnderlyingCauseofDeath_County_{state_fips}*.csv"))
            logging.info(
                "[%d/%d] Skipping %s (FIPS %s): %d existing file(s) found.",
                idx,
                len(states),
                state_name,
                state_fips,
                len(existing_files),
            )
            continue

        if downloader.action_url is None:
            downloader.init_session()

        logging.info(
            "[%d/%d] Processing %s (FIPS %s) (Session batch item %d/%d)...",
            idx,
            len(states),
            state_name,
            state_fips,
            states_in_batch + 1,
            batch_size,
        )

        try:
            results = downloader.download_state(state_fips, years)
            for chunk_label, tsv_data in results:
                if chunk_label == "all":
                    filename = f"UnderlyingCauseofDeath_County_{state_fips}.csv"
                else:
                    filename = f"UnderlyingCauseofDeath_County_{state_fips}_{chunk_label}.csv"

                filepath = os.path.join(output_dir, filename)
                rows = save_tsv_as_csv(tsv_data, filepath)
                total_files += 1
                total_rows += rows
                logging.info("Saved %s with %d rows.", filename, rows)

            states_in_batch += 1

            # Proactive session rotation after batch_size states
            if states_in_batch >= batch_size and idx < len(states):
                logging.info(
                    "Processed batch of %d states. Taking a %.1fs cooldown and refreshing session...",
                    states_in_batch,
                    batch_cooldown,
                )
                time.sleep(batch_cooldown)
                downloader.init_session()
                states_in_batch = 0

        except Exception as e:
            logging.error("Failed downloading state %s (FIPS %s): %s", state_name, state_fips, e)
            failed_states.append(state_name)

    logging.info("Download complete: Saved %d files with %d total rows in %s.", total_files, total_rows, output_dir)
    if failed_states:
        raise RuntimeError(f"Failed to download data for states: {', '.join(failed_states)}")


def main(_):
    years = parse_year_list(FLAGS.years)

    if FLAGS.states.lower() == "all":
        states = sorted(list(US_STATES.keys()))
    else:
        states = [s.strip().zfill(2) for s in FLAGS.states.split(",") if s.strip()]

    logging.info("Starting CDC County Mortality live download for %d states, years: %s", len(states), years)
    download_county_mortality_data(
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
