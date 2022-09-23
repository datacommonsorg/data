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
"""Download USGS earthquake data.

The USGS earthquake data is downloaded in pieces,
approximately in 10 year internvals. For each interval, we
first issue a count query, and finally verify the downloaded counts
against the expected count from the query.
"""

import concurrent.futures
import logging
from dataclasses import dataclass
import json
import datetime
import os
import glob
from typing import Dict, List
import requests

from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'start_date', '1900-01-01',
    'When the data should start from. Earliest is 1900-01-01.')
flags.DEFINE_string('end_date',
                    datetime.date.today().strftime('%Y-%m-%d'),
                    'When the data should end. Format is YYYY-mm-dd.')
flags.DEFINE_string('output_dir', '/tmp/usgs/', 'Folder to download to.')

DAYS_IN_TEN_YEARS = 365 * 10
DOWNLOAD_BATCH_LIMIT = 20000
DOWNLOAD_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/query.csv'
COUNT_URL = 'https://earthquake.usgs.gov/fdsnws/event/1/count'

logger = logging.getLogger(__name__)


def filename(start_date, end_date: datetime.date, part: int) -> str:
    s = start_date.strftime("%Y_%m_%d")
    e = end_date.strftime("%Y_%m_%d")
    return f"{s}_{e}_pt_{part}.csv"


def get_expected_count_in_range(start_date, end_date: datetime.date) -> int:
    """Query the expected count from USGS server."""
    params = {
        'minmagnitude': 3,
        'eventtype': 'earthquake',
        'starttime': str(start_date),
        'endtime': str(end_date)
    }
    return requests.get(COUNT_URL, params).json()


def download_file(url: str, params: Dict, output_path: str):
    logger.info('Download started: %s' % output_path)
    with requests.get(url, params=params, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content():
                f.write(chunk)
    logger.info('Download finished: %s' % output_path)


@dataclass
class Interval:
    # Download start date(inclusive).
    start_date: datetime.date
    # Download end date(exclusive), does not include this day's data.
    end_date: datetime.date

    def __str__(self):
        return self.csv()

    def csv(self):
        return f'{str(self.start_date)},{str(self.end_date)}'


def get_intervals(date_from: datetime.date,
                  date_until: datetime.date) -> List[Interval]:
    """Returns a list of download intervals."""
    start_date = date_from
    end_date = date_until
    intervals = [Interval(start_date, end_date)]
    while end_date < date_until:
        start_date = end_date + datetime.timedelta(days=1)
        end_date = min(start_date + datetime.timedelta(days=DAYS_IN_TEN_YEARS),
                       date_until)
        intervals.append(Interval(start_date, end_date))
    return intervals


def output_exists(path: str):
    return os.path.isfile(path)


def get_download_interval_jobs(destination_dir: str, interval: Interval,
                               count: int):
    start_date, end_date = interval.start_date, interval.end_date
    jobs = []
    for part, offset in enumerate(range(0, count, DOWNLOAD_BATCH_LIMIT)):
        output_path = os.path.join(destination_dir,
                                   filename(start_date, end_date, part))
        if output_exists(output_path):
            logger.info(f"Found existing fragment: {output_path}")
            continue

        params = {
            "minmagnitude": 3,
            "eventtype": "earthquake",
            "starttime": str(start_date),
            "endtime": str(end_date),
            "limit": DOWNLOAD_BATCH_LIMIT,
        }
        # offset=0 will return errors.
        if offset > 0:
            params["offset"] = offset

        # Function name, arg1, arg2 ...
        jobs.append([download_file, DOWNLOAD_URL, params, output_path])
    return jobs


def download(date_from, date_until: datetime.date, output_dir: str,
             interval_csv_to_count: Dict):
    intervals = get_intervals(date_from, date_until)
    logger.info("Download started.")
    futures = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for interval in intervals:
            # Expected count of earthquakes for this interval.
            count = interval_csv_to_count[interval.csv()]
            for job in get_download_interval_jobs(output_dir, interval, count):
                futures.append(executor.submit(*job))

        for f in concurrent.futures.as_completed(futures):
            e = f.exception()
            if e:
                raise e
    logger.info("Download completed.")


def get_expected_counts(date_from: datetime.date, date_until: datetime.date,
                        output_dir: str) -> 'Dict[str, int]':
    counts_file = os.path.join(output_dir, "counts.json")
    if os.path.isfile(counts_file):
        with open(counts_file, 'r') as f:
            return json.load(f)

    intervals = get_intervals(date_from, date_until)
    interval_to_count = dict()
    for interval in intervals:
        count = get_expected_count_in_range(interval.start_date,
                                            interval.end_date)
        interval_to_count[interval.csv()] = count

    # Write the expected count to a file for reference only.
    try:
        with open(counts_file, 'w') as f:
            json.dump(interval_to_count, f)
    except Exception as e:
        os.remove(counts_file)
        raise e

    return interval_to_count


def get_count_diff(output_dir: str, expected: Dict[str, int]):
    diff = dict()
    for interval_csv, expected in expected.items():
        got = 0
        fn = interval_csv.replace(",", "_").replace("-", "_")
        pat = os.path.join(output_dir, f"{fn}*.csv")
        for file in glob.glob(pat):
            # -1 for header line.
            got += sum(1 for line in open(file)) - 1

        if got != expected:
            diff[interval_csv] = (got, expected)
    return diff


def count_and_download(date_from, date_until: datetime.date,
                       output_dir: str) -> None:
    interval_csv_to_count = get_expected_counts(date_from, date_until,
                                                output_dir)

    download(date_from, date_until, output_dir, interval_csv_to_count)

    return get_count_diff(output_dir, interval_csv_to_count)


def main(_) -> None:
    date_from = datetime.datetime.strptime(FLAGS.start_date, '%Y-%m-%d').date()
    date_until = datetime.datetime.strptime(FLAGS.end_date, '%Y-%m-%d').date()

    os.makedirs(FLAGS.output_dir, exist_ok=True)
    diff = count_and_download(date_from, date_until, FLAGS.output_dir)
    logger.warning('Diff: %s' % json.dumps(diff))
    logger.warning('Note: USGS count query may not be 100% acccurate')
    logger.warning(
        'Please use your judgement to see if the diff is close enough.')


if __name__ == '__main__':
    app.run(main)
