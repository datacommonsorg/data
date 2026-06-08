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
"""Utility script to extract the Data Commons Provenance hierarchy.

This script fetches all Provenance nodes from the Data Commons Knowledge Graph,
resolves their associated Dataset and Source nodes, and outputs the hierarchy
as a structured JSON file.

Requires the DC_API_KEY environment variable to be set.
"""

import json
import os
import sys

from absl import app
from absl import flags
from absl import logging

# Ensure local imports work correctly if run from repo root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.dc_api_wrapper import dc_api_wrapper, get_datacommons_client

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'output_file', 'provenances_full.json',
    'Path to the output JSON file where the hierarchy will be saved.')


def get_node_property(node_data, prop_name, default=None):
    """Helper to extract a property value from the node data dictionary."""
    if not node_data:
        return default
    arcs = node_data.get("arcs", {})
    prop_nodes = arcs.get(prop_name, {}).get("nodes", [])
    if not prop_nodes:
        return default
    return prop_nodes[0].get("value")


def get_node_dcid(node_data, prop_name):
    """Helper to extract a DCID from a property."""
    if not node_data:
        return None
    arcs = node_data.get("arcs", {})
    prop_nodes = arcs.get(prop_name, {}).get("nodes", [])
    if not prop_nodes:
        return None
    return prop_nodes[0].get("dcid")


def fetch_all_provenances(api_key: str, output_file: str) -> None:
    """Fetches Provenance nodes and traverses to Dataset and Source levels."""
    client = get_datacommons_client({'dc_api_key': api_key})

    # 1. Get all nodes of type 'Provenance'
    logging.info("Fetching Provenance DCIDs...")
    try:
        res = dc_api_wrapper(function=client.node.fetch,
                             args={
                                 'node_dcids': ['Provenance'],
                                 'expression': '<-typeOf'
                             },
                             use_cache=True)
        if not res:
            logging.error("No response from Data Commons API.")
            return

        res_dict = res.to_dict()
        provenance_nodes = res_dict.get("data", {}).get("Provenance", {}).get(
            "arcs", {}).get("typeOf", {}).get("nodes", [])
        provenance_dcids = [
            dcid for node in provenance_nodes if (dcid := node.get("dcid"))
        ]
    except Exception as e:
        logging.error(f"Error fetching provenances: {e}")
        return

    if not provenance_dcids:
        logging.warning("No provenances found.")
        return

    logging.info(f"Found {len(provenance_dcids)} provenances.")

    # 2. Fetch Provenance details and find Dataset DCIDs
    logging.info("Fetching Provenance details...")
    provenance_data_map = {}
    dataset_dcids = set()

    batch_size = 100
    for i in range(0, len(provenance_dcids), batch_size):
        batch = provenance_dcids[i:i + batch_size]
        batch_res = dc_api_wrapper(function=client.node.fetch,
                                   args={
                                       'node_dcids': batch,
                                       'expression': '->*'
                                   },
                                   use_cache=True)
        if not batch_res:
            continue
        data = batch_res.to_dict().get("data", {})

        for dcid in batch:
            node_data = data.get(dcid, {})
            prov_entry = {
                "dcid": dcid,
                "name": get_node_property(node_data, "name"),
                "description": get_node_property(node_data, "description"),
                "sourceDataUrl": get_node_property(node_data, "sourceDataUrl"),
                "license": get_node_property(node_data, "license"),
                "dataset_dcid": get_node_dcid(node_data, "isPartOf")
            }
            provenance_data_map[dcid] = prov_entry
            if prov_entry["dataset_dcid"]:
                dataset_dcids.add(prov_entry["dataset_dcid"])

    # 3. Fetch Dataset details and find Source DCIDs
    logging.info(f"Fetching {len(dataset_dcids)} Dataset details...")
    dataset_data_map = {}
    source_dcids = set()

    dataset_list = list(dataset_dcids)
    for i in range(0, len(dataset_list), batch_size):
        batch = dataset_list[i:i + batch_size]
        batch_res = dc_api_wrapper(function=client.node.fetch,
                                   args={
                                       'node_dcids': batch,
                                       'expression': '->*'
                                   },
                                   use_cache=True)
        if not batch_res:
            continue
        data = batch_res.to_dict().get("data", {})

        for dcid in batch:
            node_data = data.get(dcid, {})
            ds_entry = {
                "name": get_node_property(node_data, "name"),
                "url": get_node_property(node_data, "url"),
                "source_dcid": get_node_dcid(node_data, "isPartOf")
            }
            dataset_data_map[dcid] = ds_entry
            if ds_entry["source_dcid"]:
                source_dcids.add(ds_entry["source_dcid"])

    # 4. Fetch Source details
    logging.info(f"Fetching {len(source_dcids)} Source details...")
    source_data_map = {}
    source_list = list(source_dcids)
    for i in range(0, len(source_list), batch_size):
        batch = source_list[i:i + batch_size]
        batch_res = dc_api_wrapper(function=client.node.fetch,
                                   args={
                                       'node_dcids': batch,
                                       'expression': '->*'
                                   },
                                   use_cache=True)
        if not batch_res:
            continue
        data = batch_res.to_dict().get("data", {})

        for dcid in batch:
            node_data = data.get(dcid, {})
            source_data_map[dcid] = {
                "name": get_node_property(node_data, "name"),
                "url": get_node_property(node_data, "url")
            }

    # 5. Assemble final hierarchy
    logging.info("Assembling final hierarchy...")
    final_output = []
    for prov_dcid, prov in provenance_data_map.items():
        ds_dcid = prov.pop("dataset_dcid")
        dataset_info = None

        if ds_dcid:
            ds_data = dataset_data_map.get(ds_dcid)
            if ds_data:
                src_dcid = ds_data.get("source_dcid")
                source_info = None

                if src_dcid:
                    source_info = source_data_map.get(src_dcid)
                    
                dataset_info = {
                    "name": ds_data.get("name"),
                    "url": ds_data.get("url"),
                    "source": source_info
                }

        prov["dataset"] = dataset_info
        final_output.append(prov)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    logging.info(
        f"Successfully wrote {len(final_output)} provenances to {output_file}")


def main(_):
    api_key = os.environ.get('DC_API_KEY')
    if not api_key:
        logging.fatal(
            "DC_API_KEY environment variable not set."
        )
        sys.exit(1)

    fetch_all_provenances(api_key=api_key, output_file=FLAGS.output_file)


if __name__ == '__main__':
    app.run(main)
