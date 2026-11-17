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
"""Merge 2006-2021 historical archive with stat_var_processor 2022+ output."""

import os
from pathlib import Path

from absl import app
from absl import flags
from absl import logging
import pandas as pd

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    "historical_gcs_bucket",
    "unresolved_mcf",
    "GCS bucket containing the 2006-2021 historical baseline CSV.",
)
flags.DEFINE_string(
    "historical_gcs_blob",
    "cdc/nndss_infectious_diseases_weekly/20250206/cdc_nndss_weekly_tables.csv",
    "GCS blob path for the 2006-2021 historical baseline CSV.",
)
flags.DEFINE_string(
    "historical_local_path",
    "",
    "Optional local path to historical baseline CSV (skips GCS download).",
)
flags.DEFINE_string(
    "processor_csv",
    "",
    "Path to stat_var_processor output CSV.",
)
flags.DEFINE_string(
    "output_dir",
    "",
    "Output directory for combined cdc_nndss_weekly_tables.csv and .tmcf.",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(SCRIPT_DIR, "history")
HISTORICAL_LOCAL_FILE = os.path.join(HISTORY_DIR,
                                     "historical_cdc_nndss_weekly_tables.csv")
MEASUREMENT_METHOD = "dcs:CDC_NNDSS_Diseases_WeeklyTables"

OUTPUT_COLUMNS = [
    "observationDate",
    "observationAbout",
    "observationPeriod",
    "variableMeasured",
    "value",
    "measurementMethod",
]

TMCF_CONTENT = """Node: E:NNDSWeekly->E0
typeOf: dcs:StatVarObservation
measurementMethod: C:NNDSWeekly->measurementMethod
observationAbout: C:NNDSWeekly->observationAbout
observationDate: C:NNDSWeekly->observationDate
variableMeasured: C:NNDSWeekly->variableMeasured
value: C:NNDSWeekly->value
observationPeriod: C:NNDSWeekly->observationPeriod
"""


def load_historical(local_path: str, bucket_name: str,
                    blob_name: str) -> pd.DataFrame:
  """Load all historical baseline rows from 20250206 to ensure 0 deletions."""
  csv_path = local_path
  if not csv_path:
    from google.cloud import storage

    logging.info(
        f"Downloading historical archive from gs://{bucket_name}/{blob_name}..."
    )
    Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    bucket.blob(blob_name).download_to_filename(HISTORICAL_LOCAL_FILE)
    csv_path = HISTORICAL_LOCAL_FILE

  df = pd.read_csv(csv_path, usecols=OUTPUT_COLUMNS, dtype=str)
  df = df.reindex(columns=OUTPUT_COLUMNS)
  logging.info(f"Loaded {len(df)} historical baseline rows.")
  return df


def merge_outputs(hist_df: pd.DataFrame, processor_csv_path: str,
                  output_dir: str) -> pd.DataFrame:
    """Combine historical rows with stat_var_processor output and write final CSV/TMCF."""
    recent_df = pd.read_csv(processor_csv_path, dtype=str)
    recent_df["variableMeasured"] = recent_df["variableMeasured"].str.replace(
        r"^(dcid:|dcs:)", "", regex=True)
    recent_df["observationAbout"] = recent_df["observationAbout"].str.replace(
        r"^(dcid:|dcs:)", "", regex=True)
    recent_df["observationPeriod"] = "P1W"
    recent_df["measurementMethod"] = MEASUREMENT_METHOD
    recent_df = recent_df[OUTPUT_COLUMNS]

    combined = pd.concat([hist_df, recent_df], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=[
            "observationDate",
            "observationAbout",
            "observationPeriod",
            "variableMeasured",
        ],
        keep="last",
    )

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_csv = os.path.join(output_dir, "cdc_nndss_weekly_tables.csv")
    out_tmcf = os.path.join(output_dir, "cdc_nndss_weekly_tables.tmcf")
    combined.to_csv(out_csv, index=False)
    with open(out_tmcf, "w", encoding="utf-8") as f:
        f.write(TMCF_CONTENT)
    logging.info(f"Wrote {len(combined)} combined rows to {out_csv}.")
    return combined


def main(argv):
  del argv
  Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)
    output_dir = _FLAGS.output_dir or os.path.join(SCRIPT_DIR, "output")
    processor_csv = _FLAGS.processor_csv or os.path.join(
        output_dir, "nndss_weekly_output.csv")
    hist_df = load_historical(
        _FLAGS.historical_local_path,
        _FLAGS.historical_gcs_bucket,
        _FLAGS.historical_gcs_blob,
    )
    merge_outputs(hist_df, processor_csv, output_dir)


if __name__ == "__main__":
    app.run(main)
