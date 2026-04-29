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
"""Script to generate provisional nodes for undefined references in MCF files.

This script scans a directory for .mcf files, identifies all referenced nodes
(using dcid:, dcs:, or schema: prefixes), and checks if they are defined
locally. For any missing definitions, it optionally checks a Spanner database
to see if the nodes already exist in the knowledge graph. Finally, it
generates a 'provisional_nodes.mcf' file containing definitions for any
nodes that are still missing.

Usage:
    python3 generate_provisional_nodes.py --directory=/path/to/mcf/files \
        --spanner_project=datcom-store \
        --spanner_instance=dc-kg-test \
        --spanner_database=dc_graph_2025_11_07
"""
import os
import re
import time
import logging
import csv
import io
import sys

from absl import app
from absl import flags
from google.cloud import spanner

FLAGS = flags.FLAGS
flags.DEFINE_string("directory", os.getcwd(),
                    "Directory to scan (default: current working directory)")
flags.DEFINE_bool("no_spanner", False, "Skip Spanner check")
flags.DEFINE_string("spanner_project", "datcom-store", "Spanner project ID")
flags.DEFINE_string("spanner_instance", "dc-kg-test", "Spanner instance ID")
flags.DEFINE_string("spanner_database", "dc_graph_2025_11_07",
                    "Spanner database ID")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Spanner Configuration
BATCH_SIZE = 1000  # Number of IDs to query at once

# Increase CSV field size limit for large MCF values
csv.field_size_limit(sys.maxsize)

ENTITY_PREFIXES = ("dcid:", "dcs:", "schema:")


def strip_prefix(s):
    """Strips common prefixes (dcid:, dcs:, schema:) from a string."""
    # Strip common prefixes
    for prefix in ENTITY_PREFIXES:
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


def is_quoted(s):
    """Checks if a string is surrounded by double quotes."""
    s = s.strip()
    return s.startswith('"') and s.endswith('"')


def strip_quotes(s):
    """Removes surrounding double quotes from a string if present."""
    s = s.strip()
    if is_quoted(s):
        return s[1:-1]
    return s


def check_spanner_nodes(node_ids, project, instance_id, database_id):
    """
    Checks which of the given node_ids exist in the Spanner Node table.
    
    Args:
        node_ids: A collection of node IDs (strings) to check against Spanner.
        project: Spanner project ID.
        instance_id: Spanner instance ID.
        database_id: Spanner database ID.
        
    Returns:
        A set containing the node IDs that were found in the Spanner database.
    """
    existing_nodes = set()
    node_ids_list = list(node_ids)

    if not node_ids_list:
        return existing_nodes

    logging.info(
        f"Checking {len(node_ids_list)} potential missing nodes in Spanner...")

    try:
        spanner_client = spanner.Client(project=project)
        instance = spanner_client.instance(instance_id)
        database = instance.database(database_id)

        # Using a single snapshot for consistency across batches
        with database.snapshot(multi_use=True) as snapshot:
            total_batches = (len(node_ids_list) + BATCH_SIZE - 1) // BATCH_SIZE

            for i in range(0, len(node_ids_list), BATCH_SIZE):
                batch_num = (i // BATCH_SIZE) + 1
                if batch_num % 10 == 0 or batch_num == 1 or batch_num == total_batches:
                    logging.info(
                        f"Processing batch {batch_num}/{total_batches}...")

                batch = node_ids_list[i:i + BATCH_SIZE]

                try:
                    result = snapshot.execute_sql(
                        "SELECT subject_id FROM Node WHERE subject_id IN UNNEST(@ids)",
                        params={"ids": batch},
                        param_types={
                            "ids":
                                spanner.param_types.Array(
                                    spanner.param_types.STRING)
                        })

                    # Consume the result fully
                    for row in result:
                        existing_nodes.add(row[0])

                except Exception as e:
                    logging.error(f"Error in batch {batch_num}: {e}")

    except Exception as e:
        logging.error(f"Failed to connect to Spanner or create snapshot: {e}")

    return existing_nodes


def generate_provisional_nodes(scan_dir,
                               no_spanner=False,
                               spanner_project=None,
                               spanner_instance=None,
                               spanner_database=None):
    """
    Scans a directory of MCF files to find undefined nodes referenced in properties.
    
    Args:
        scan_dir: The local directory containing .mcf files to scan.
        no_spanner: If True, skips checking Cloud Spanner for existing nodes.
        spanner_project: Spanner project ID.
        spanner_instance: Spanner instance ID.
        spanner_database: Spanner database ID.
        
    Returns:
        The path to the generated provisional_nodes.mcf file.
    """
    start_time = time.time()
    root_dir = os.path.abspath(scan_dir)
    output_dir = root_dir

    defined_nodes = set()
    referenced_properties = set()
    referenced_values = set()

    # Regex to capture "Key: Value"
    pair_re = re.compile(r"^(\w+):\s*(.*)$")

    logging.info(f"Scanning directory: {root_dir}")

    # Walk through the directory to process each .mcf file
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if ".mcf" not in filename:
                continue

            # Skip the output file itself if it already exists from a previous run
            if filename == "provisional_nodes.mcf":
                continue

            filepath = os.path.join(dirpath, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                current_node_id = None

                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//") or line.startswith(
                            "#"):
                        continue

                    # Check for Node definition (e.g., "Node: dcid:City")
                    if line.startswith("Node:"):
                        if current_node_id:
                            defined_nodes.add(current_node_id)

                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            current_node_id = strip_prefix(
                                strip_quotes(parts[1]))
                        else:
                            current_node_id = None
                        continue

                    # Check for Property: Value pairs
                    match = pair_re.match(line)
                    if match:
                        key = match.group(1).strip()
                        value_str = match.group(2).strip()

                        # If explicitly defining dcid as a property, use that as the node ID
                        if key == "dcid":
                            current_node_id = strip_prefix(
                                strip_quotes(value_str))
                            continue

                        # 1. The Key (Property) is a reference to a Property node (e.g., "containedInPlace")
                        referenced_properties.add(strip_prefix(key))

                        # 2. The Value: Only check for explicit prefixes indicating references (e.g., "dcid:geoId/06")
                        f_io = io.StringIO(value_str)
                        reader = csv.reader(f_io, skipinitialspace=True)
                        try:
                            tokens = next(reader)
                        except StopIteration:
                            tokens = []

                        for token in tokens:
                            if not token:
                                continue

                            clean_token = strip_quotes(token)

                            # Only strict prefixes are references
                            if clean_token.startswith(ENTITY_PREFIXES):
                                ref_id = strip_prefix(clean_token)
                                referenced_values.add(ref_id)

            # Add the last node of the file
            if current_node_id:
                defined_nodes.add(current_node_id)

    # Calculate initially missing nodes (referenced but not defined locally)
    missing_props = referenced_properties - defined_nodes
    missing_values = referenced_values - defined_nodes
    all_missing_local = missing_props | missing_values

    # Filter out empty strings if any
    all_missing_local = {m for m in all_missing_local if m}

    logging.info(f"Found {len(defined_nodes)} defined nodes.")
    logging.info(f"Found {len(referenced_properties)} referenced properties.")
    logging.info(f"Found {len(referenced_values)} referenced values.")
    logging.info(f"Found {len(all_missing_local)} locally missing definitions.")

    # Save locally missing nodes to a file (pre-Spanner check) for debugging/audit
    local_missing_file_path = os.path.join(output_dir,
                                           "local_missing_nodes.txt")
    with open(local_missing_file_path, "w") as f:
        for m in sorted(all_missing_local):
            f.write(f"{m}\n")
    logging.info(
        f"Written locally missing nodes (pre-Spanner) to {local_missing_file_path}"
    )

    # Check Spanner for existence of these missing nodes
    existing_in_spanner = set()
    if not no_spanner:
        existing_in_spanner = check_spanner_nodes(all_missing_local,
                                                  spanner_project,
                                                  spanner_instance,
                                                  spanner_database)

        if existing_in_spanner:
            logging.info(
                f"Found {len(existing_in_spanner)} nodes in Spanner (will not be emitted)."
            )
    else:
        logging.info("Skipping Spanner check as requested.")

    # Final missing set = missing locally AND missing in Spanner
    final_missing = all_missing_local - existing_in_spanner

    logging.info(f"Final missing count: {len(final_missing)}")

    # Generate the provisional nodes MCF file
    output_file_path = os.path.join(output_dir, "provisional_nodes.mcf")
    with open(output_file_path, "w") as out:
        for m in sorted(final_missing):
            if m in missing_props:
                node_type = "dcs:Property"
            else:
                node_type = "dcs:ProvisionalNode"

            # We don't print to stdout, we write to file directly to be useful
            node_def = f"Node: dcid:{m}\ntypeOf: {node_type}\nisProvisional: dcs:True\n\n"
            out.write(node_def)

    logging.info(f"Written missing nodes to {output_file_path}")

    end_time = time.time()
    logging.info(f"Total runtime: {end_time - start_time:.2f} seconds")
    return output_file_path


def main(_):
    output_path = generate_provisional_nodes(FLAGS.directory, FLAGS.no_spanner,
                                             FLAGS.spanner_project,
                                             FLAGS.spanner_instance,
                                             FLAGS.spanner_database)
    logging.info(f"Generated provisional nodes at: {output_path}")


if __name__ == "__main__":
    app.run(main)
