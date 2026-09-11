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
"""Dynamic DAG Factory for Data Commons Imports.

Reads imports_catalog.json (compiled from manifest.json files in the data repository)
and dynamically registers an independent Airflow DAG for each import specification.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from import_automation_workflow import build_dag


def find_catalog_file() -> str | None:
    """Locates the imports_catalog.json file across known search locations."""
    candidates = [
        os.environ.get("IMPORTS_CATALOG_PATH"),
        os.path.join(current_dir, "imports_catalog.json"),
        os.path.join(current_dir, "datacommons_airflow", "imports_catalog.json"),
        "/home/airflow/gcs/dags/datacommons_airflow/imports_catalog.json",
        "/home/airflow/gcs/dags/imports_catalog.json",
    ]
    return next((p for p in candidates if p and os.path.isfile(p)), None)


def load_catalog_and_register_dags(target_globals: dict[str, Any]) -> int:
    """Loads imports_catalog.json and registers DAG instances into target_globals."""
    catalog_path = find_catalog_file()
    if not catalog_path:
        logging.info("imports_catalog.json not found; dynamic DAG factory skipped.")
        return 0

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception as e:
        logging.error("Failed to load %s: %s", catalog_path, e)
        return 0

    count = 0
    for entry in catalog:
        dag_id, full_name = entry.get("dag_id"), entry.get("full_import_name")
        if not dag_id or not full_name:
            continue
        if dag_id in target_globals:
            raise ValueError(
                f"Duplicate DAG ID '{dag_id}' encountered in {catalog_path}; "
                "cannot overwrite an already registered DAG."
            )
        cron = entry.get("cron_schedule")
        target_globals[dag_id] = build_dag(
            dag_id=dag_id,
            schedule=cron,
            import_name=full_name,
            curator_emails=entry.get("curator_emails"),
            config_override=entry.get("config_override"),
            resource_limits=entry.get("resource_limits"),
            extra_tags=["scheduled" if cron else "manual", entry.get("category", "data-commons")],
            is_paused_upon_creation=True,
        )
        count += 1

    logging.info("Registered %d import DAGs from %s", count, catalog_path)
    return count


# Automatically register DAGs in global namespace when imported by Airflow
load_catalog_and_register_dags(globals())
