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
"""Builds a consolidated JSON catalog of import specifications from manifest.json files.

Usage:
  # Scan all manifests in data repository:
  python3 build_manifest_catalog.py

  # Scan a specific subfolder (e.g. scripts/us_fed):
  python3 build_manifest_catalog.py --subfolder=scripts/us_fed
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from typing import Any


def strip_leading_scripts(path_str: str) -> str:
    """Safely removes only the leading 'scripts' directory component from a path."""
    parts = os.path.normpath(path_str).split(os.sep)
    if parts and parts[0] == "scripts":
        parts = parts[1:]
    return "/".join(parts)




def build_catalog(
    data_dir: str,
    subfolder: str | None = None,
    output_path: str | None = None,
) -> list[dict[str, Any]]:
    """Scans manifest.json files and compiles all import specifications into a list."""
    base_search = os.path.join(data_dir, subfolder) if subfolder else data_dir
    search_pattern = os.path.join(base_search, "**/manifest.json")
    manifest_files = sorted(glob.glob(search_pattern, recursive=True))

    catalog: list[dict[str, Any]] = []
    seen_dag_ids: dict[str, str] = {}

    for manifest_path in manifest_files:
        rel_dir = os.path.relpath(os.path.dirname(manifest_path), data_dir)
        # Skip Schema and entities imports as requested
        if rel_dir.startswith("scripts/entities") or "entities" in rel_dir:
            continue

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {manifest_path}: {e}")
            continue

        import_specs = data.get("import_specifications", [])
        for spec in import_specs:
            import_name = spec.get("import_name")
            if not import_name:
                continue

            dag_id = import_name
            if dag_id in seen_dag_ids:
                prev_manifest = seen_dag_ids[dag_id]
                raise ValueError(
                    f"Duplicate DAG ID '{dag_id}' detected in '{manifest_path}'. "
                    f"This DAG ID is already defined in '{prev_manifest}'. "
                    "Each import specification must have a globally unique import_name / DAG ID."
                )
            seen_dag_ids[dag_id] = manifest_path

            subpath = strip_leading_scripts(rel_dir)
            category = subpath.split("/")[0] if subpath else "general"

            entry = {
                "dag_id": dag_id,
                "import_name": import_name,
                "full_import_name": f"{rel_dir}:{import_name}",
                "script_dir": rel_dir,
                "cron_schedule": spec.get("cron_schedule"),
                "curator_emails": spec.get("curator_emails", ["support@datacommons.org"]),
                "provenance_description": spec.get("provenance_description", ""),
                "provenance_url": spec.get("provenance_url", ""),
                "config_override": spec.get("config_override", {}),
                "resource_limits": spec.get("resource_limits", {}),
                "category": category,
            }
            catalog.append(entry)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(catalog, out, indent=2)
        print(f"Wrote {len(catalog)} import specifications to {output_path}")

    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile manifest.json files into imports_catalog.json")
    parser.add_argument(
        "--data-dir",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
        help="Path to the data repository root",
    )
    parser.add_argument(
        "--subfolder",
        default=None,
        help="Optional subfolder to restrict scan (e.g. scripts/us_fed)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "imports_catalog.json"),
        help="Output path for the compiled catalog JSON",
    )
    args = parser.parse_args()

    catalog = build_catalog(
        data_dir=args.data_dir,
        subfolder=args.subfolder,
        output_path=args.output,
    )
    print(f"Catalog build complete: {len(catalog)} DAG entries compiled.")


if __name__ == "__main__":
    main()
