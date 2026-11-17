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
"""Shared HTTP session, SIDRA API fetch, and raw archive helpers for Brazil Census."""

import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from absl import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


def get_robust_session() -> requests.Session:
    """Configures a requests Session with retries and connection pooling."""
    session = requests.Session()
    retries = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504, 520, 522, 524],
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_raw_dir(
    target_path: str,
    default_output_file: str,
    script_dir: str,
) -> str:
    """Returns a clean directory for archiving raw downloaded payloads."""
    if os.path.abspath(target_path) == os.path.abspath(default_output_file):
        raw_dir = os.path.join(script_dir, "raw_files")
    else:
        raw_dir = os.path.join(os.path.dirname(os.path.abspath(target_path)),
                               "raw_files")
    shutil.rmtree(raw_dir, ignore_errors=True)
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


def get_history_path(
    target_path: str,
    default_output_file: str,
    script_dir: str,
    filename: str,
    subdir: str = "history",
) -> str:
    """Returns local destination path for an immutable historical CSV."""
    if os.path.abspath(target_path) == os.path.abspath(default_output_file):
        base_dir = script_dir
    else:
        base_dir = os.path.dirname(os.path.abspath(target_path))
    return os.path.join(base_dir, subdir, filename)


def sync_historical_csv(
    gcs_blob_path: str,
    local_dest_path: str,
    gcs_bucket_name: str = "unresolved_mcf",
    fallback_to_cached: bool = False,
) -> str:
    """Downloads an immutable pre-processed historical CSV from GCS atomically."""
    from google.cloud import storage

    os.makedirs(os.path.dirname(os.path.abspath(local_dest_path)),
                exist_ok=True)
    tmp_path = f"{local_dest_path}.tmp"
    try:
        client = storage.Client()
        blob = client.bucket(gcs_bucket_name).blob(gcs_blob_path)
        blob.download_to_filename(tmp_path)
        os.replace(tmp_path, local_dest_path)
        logging.info(
            f"Synced historical CSV gs://{gcs_bucket_name}/{gcs_blob_path} -> {local_dest_path}"
        )
        return local_dest_path
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if fallback_to_cached and os.path.isfile(local_dest_path):
            logging.warning(
                f"Historical CSV sync failed ({e}). Using cached copy: {local_dest_path}"
            )
            return local_dest_path
        raise RuntimeError(
            f"Error syncing historical CSV gs://{gcs_bucket_name}/{gcs_blob_path}: {e}"
        ) from e


def fetch_sidra_data(
    session: requests.Session,
    url: str,
    raw_file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetches raw JSON payload from IBGE SIDRA REST API."""
    logging.info(f"Dispatching outbound HTTP request: url={url}")
    res = session.get(url, timeout=90)
    res.raise_for_status()
    raw_json = res.json()
    if not isinstance(raw_json, list) or len(raw_json) < 2:
        raise RuntimeError(
            f"Invalid or empty response payload from SIDRA API: {url}")
    if raw_file_path:
        with open(raw_file_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False)
    return raw_json


def resolve_sidra_loc(
    record: Dict[str, Any],
    muni_map: Optional[Dict[str, str]] = None,
    skip_5101837: bool = False,
) -> Optional[str]:
    """Resolves IBGE SIDRA territorial identifier from D1C (muni) or D1N (macro)."""
    nc = str(record.get("NC", "")).strip()
    d1c = str(record.get("D1C", "")).strip()
    if nc == "6":
        if skip_5101837 and d1c == "5101837":
            return None
        return muni_map.get(d1c, d1c) if muni_map else d1c
    loc = str(record.get("D1N", "")).strip()
    return "Brazil" if loc == "Brasil" else loc


def write_df_atomically(df: pd.DataFrame, target_path: str) -> None:
    """Writes a non-empty DataFrame to target_path atomically using a temp file."""
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)
    with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            dir=target_dir,
            suffix=".csv",
            encoding="utf-8",
            newline="",
    ) as tmp_file:
        tmp_path = tmp_file.name
        df.to_csv(tmp_file, index=False, encoding="utf-8")

    if not os.path.isfile(tmp_path) or os.path.getsize(tmp_path) == 0:
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)
        raise RuntimeError(
            f"Atomic CSV write failed: {tmp_path} is missing or empty.")

    os.replace(tmp_path, target_path)
    logging.info(f"Wrote {len(df)} records to {target_path}")
