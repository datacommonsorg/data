#!/usr/bin/env python3
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
"""Consolidates the 403 legacy Demographic CSVs from CNS into 2 historical baseline CSVs."""

import csv
import os
import re
import subprocess
import tempfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    "cns_dir",
    "/cns/jv-d/home/datcom/v3_mcf/country/indonesia",
    "Legacy CNS directory containing the 403 demographic CSVs.",
)
flags.DEFINE_string(
    "output_dir",
    "historical",
    "Output directory for the 2 consolidated historical baseline CSVs.",
)

OUTPUT_COLUMNS = [
    "observationAbout",
    "observationDate",
    "value",
    "variableMeasured",
    "unit",
    "scalingFactor",
]

# Regex patterns for the 4 demographic sub-categories (403 files total):
# 1A: idn_population.csv, idn_population_2016.csv .. idn_population_2022.csv
# 1B: idn_<province>_population_<year>.csv
POPULATION_FILE_RE = re.compile(
    r"^idn_(?:[a-z_]+_)?population(?:_\d{4})?\.csv$"
)

# 1C: idn_age_gender_population_2018.csv .. idn_age_gender_population_2022.csv
# 1D: idn_<province>_age_gender_<year>.csv
AGE_GENDER_FILE_RE = re.compile(
    r"^idn_(?:age_gender_population_\d{4}|[a-z_]+_age_gender_\d{4})\.csv$"
)


def list_cns_csvs(cns_dir: str) -> list[str]:
  """Lists all CSV files in the root of cns_dir using fileutil."""
  cmd = ["fileutil", "ls", f"{cns_dir}/*.csv"]
  result = subprocess.run(cmd, capture_output=True, text=True, check=True)
  files = []
  for line in result.stdout.splitlines():
    line = line.strip()
    if line.endswith(".csv"):
      files.append(line)
  return sorted(files)


def normalize_dcid(val: str) -> str:
  """Normalizes observationAbout/variableMeasured strings."""
  val = val.strip()
  val = val.removeprefix("dcid:")
  if val.endswith(")"):
    val = val.rstrip(")")
  return val


def consolidate_files(
    cns_files: list[str], output_csv_path: str, local_staging_dir: str
) -> None:
  """Copies CNS CSVs locally in batch, merges, deduplicates, and writes output."""
  if not cns_files:
    logging.warning("No matching files found for %s", output_csv_path)
    return

  logging.info(
      "Copying %d CNS files to local staging for %s...",
      len(cns_files),
      output_csv_path,
  )
  subprocess.run(
      ["fileutil", "cp", "-f"] + cns_files + [f"{local_staging_dir}/"],
      check=True,
  )

  deduped_rows = {}
  total_rows_read = 0

  for cns_path in sorted(cns_files):
    fname = os.path.basename(cns_path)
    local_path = os.path.join(local_staging_dir, fname)
    with open(local_path, mode="r", encoding="utf-8-sig", newline="") as f:
      reader = csv.DictReader(f)
      # Strip whitespace from fieldnames
      if reader.fieldnames:
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]
      for row in reader:
        total_rows_read += 1
        obs_about = normalize_dcid(row.get("observationAbout", ""))
        obs_date = row.get("observationDate", "").strip()
        var_measured = row.get("variableMeasured", "").strip()
        val = row.get("value", "").strip()
        unit = row.get("unit", "").strip()
        scaling = row.get("scalingFactor", "").strip()

        if not obs_about or not obs_date or not var_measured or val == "":
          continue

        if not var_measured.startswith("dcid:"):
          var_measured = f"dcid:{var_measured}"

        key = (obs_about, obs_date, var_measured)
        deduped_rows[key] = {
            "observationAbout": obs_about,
            "observationDate": obs_date,
            "value": val,
            "variableMeasured": var_measured,
            "unit": unit,
            "scalingFactor": scaling,
        }

  os.makedirs(os.path.dirname(output_csv_path) or ".", exist_ok=True)
  with open(output_csv_path, mode="w", encoding="utf-8", newline="") as out_f:
    writer = csv.DictWriter(out_f, fieldnames=OUTPUT_COLUMNS)
    writer.writeheader()
    for key in sorted(deduped_rows.keys()):
      writer.writerow(deduped_rows[key])

  logging.info(
      "Wrote %s: %d unique observations (from %d raw rows across %d files).",
      output_csv_path,
      len(deduped_rows),
      total_rows_read,
      len(cns_files),
  )


def main(_):
  all_cns_csvs = list_cns_csvs(FLAGS.cns_dir)
  pop_files = []
  age_gender_files = []

  for path in all_cns_csvs:
    fname = os.path.basename(path)
    if AGE_GENDER_FILE_RE.match(fname):
      age_gender_files.append(path)
    elif POPULATION_FILE_RE.match(fname):
      pop_files.append(path)

  logging.info(
      "Found %d Total Population CSVs and %d Age/Gender CSVs (Total = %d).",
      len(pop_files),
      len(age_gender_files),
      len(pop_files) + len(age_gender_files),
  )

  os.makedirs(FLAGS.output_dir, exist_ok=True)
  with tempfile.TemporaryDirectory() as tmp_dir:
    pop_stage = os.path.join(tmp_dir, "pop")
    ag_stage = os.path.join(tmp_dir, "ag")
    os.makedirs(pop_stage, exist_ok=True)
    os.makedirs(ag_stage, exist_ok=True)

    consolidate_files(
        pop_files,
        os.path.join(
            FLAGS.output_dir, "idn_population_historical_1971_2022.csv"
        ),
        pop_stage,
    )
    consolidate_files(
        age_gender_files,
        os.path.join(
            FLAGS.output_dir, "idn_age_gender_historical_2010_2022.csv"
        ),
        ag_stage,
    )


if __name__ == "__main__":
  app.run(main)
