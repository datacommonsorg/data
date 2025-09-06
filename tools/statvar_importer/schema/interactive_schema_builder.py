# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An interactive script to build a schema with human oversight.

This script orchestrates the schema generation process, pausing at critical
junctures to allow the user to validate and correct the tool's assumptions.

Workflow:
1.  Generate an initial Property-Value (PV) map from a source data file.
2.  Present the PV map to the user for review.
3.  Allow the user to interactively edit, add, or delete mappings.
4.  Once the user accepts the PV map, generate the supporting schema nodes.
5.  Present the new schema nodes for a final review.
6.  Save both the validated PV-map and the new schema MCF.
"""

import os
import sys
from typing import Dict, List

from absl import app
from absl import flags
from absl import logging

# Add the parent directory to the path to import other modules.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))

# These imports are necessary to bring the flags they define into the global
# namespace for this script to use.
import data_annotator
import llm_pvmap_generator
import genai_helper
import schema_generator
from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from config_map import ConfigMap
from counters import Counters

FLAGS = flags.FLAGS

# Define only the flags that are unique to this interactive script.
# Other flags are defined in the imported modules.
flags.DEFINE_string('data_file', '', 'The path to the input data file (e.g., a CSV).')
flags.DEFINE_string('output_pvmap_file', 'validated_pvmap.csv', 'The file to save the validated PV map to.')


flags.DEFINE_string('output_schema_mcf', 'generated_schema.mcf', 'The file to save the new schema nodes to.')

def flatten_pvmap(pv_map: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    """Flattens a PV-map into a list of single PVs for easier editing."""
    flat_list = []
    for source_string, pvs in pv_map.items():
        if not pvs:
            flat_list.append({"source": source_string, "prop": "", "val": ""})
        else:
            for prop, val in pvs.items():
                flat_list.append({"source": source_string, "prop": prop, "val": val})
    return flat_list

def reconstruct_pvmap(flat_pv_list: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Reconstructs a PV-map dictionary from a flattened list."""
    pv_map = {}
    for item in flat_pv_list:
        source = item["source"]
        prop = item["prop"]
        val = item["val"]
        if source not in pv_map:
            pv_map[source] = {}
        if prop:  # Avoid adding empty properties
            pv_map[source][prop] = val
    return pv_map

def present_pvmap_for_review(flat_pv_list: List[Dict[str, str]]) -> None:
    """Formats and prints the flattened PV-list to the console."""
    print("\n" + "="*80)
    print(" Proposed Property-Value Mappings for Review")
    print("="*80)

    if not flat_pv_list:
        print("No mappings to display.")
        print("-" * 80)
        return

    # Determine column widths
    max_source = max(len(item['source']) for item in flat_pv_list) if flat_pv_list else 0
    max_prop = max(len(item['prop']) for item in flat_pv_list) if flat_pv_list else 0
    max_val = max(len(item['val']) for item in flat_pv_list) if flat_pv_list else 0
    max_source = max(max_source, len("Source String"))
    max_prop = max(max_prop, len("Proposed Property"))
    max_val = max(max_val, len("Proposed Value"))


    # Print header
    header = f"| {'#':<3} | {'Source String':<{max_source}} | {'Proposed Property':<{max_prop}} | {'Proposed Value':<{max_val}} |"
    print(header)
    print("-" * len(header))

    # Print rows
    for i, item in enumerate(flat_pv_list):
        row_str = f"| {i+1:<3} | {item['source']:<{max_source}} | {item['prop']:<{max_prop}} | {item['val']:<{max_val}} |"
        print(row_str)
    print("-" * len(header))

def present_schema_for_review(schema_nodes: Dict[str, Dict[str, str]]) -> None:
    """Formats and prints the newly generated schema nodes for final review."""
    print("\n" + "="*80)
    print(" Generated Schema Nodes for Final Review")
    print("="*80)

    if not schema_nodes:
        print("No new schema nodes were generated.")
        print("-" * 80)
        return

    # Determine column widths
    max_dcid = max(len(dcid) for dcid in schema_nodes.keys())
    max_type = max(len(pvs.get('typeOf', '')) for pvs in schema_nodes.values())
    max_name = max(len(pvs.get('name', '')) for pvs in schema_nodes.values())
    max_dcid = max(max_dcid, len("DCID"))
    max_type = max(max_type, len("typeOf"))
    max_name = max(max_name, len("Name"))

    # Print header
    header = f"| {'DCID':<{max_dcid}} | {'typeOf':<{max_type}} | {'Name':<{max_name}} |"
    print(header)
    print("-" * len(header))

    # Print rows
    for dcid, pvs in schema_nodes.items():
        row_str = f"| {dcid:<{max_dcid}} | {pvs.get('typeOf', ''):<{max_type}} | {pvs.get('name', ''):<{max_name}} |"
        print(row_str)
    print("-" * len(header))


def enter_editing_mode(pv_map: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Handles the interactive editing loop for the user."""
    flat_pv_list = flatten_pvmap(pv_map)

    while True:
        present_pvmap_for_review(flat_pv_list)
        edit_choice = input(
            "\nEnter the number (#) of the row to edit.\n"
            "- To add a new mapping, type 'add'.\n"
            "- To delete a row, type 'delete'.\n"
            "- When you are finished, type 'done'.\n"
            "Your choice: "
        ).lower().strip()

        if edit_choice == 'done':
            return reconstruct_pvmap(flat_pv_list)

        elif edit_choice == 'add':
            source = input("Enter the source string: ").strip()
            prop = input("Enter the property: ").strip()
            val = input("Enter the value: ").strip()
            if source and prop and val:
                flat_pv_list.append({"source": source, "prop": prop, "val": val})
                print("Mapping added.")
            else:
                print("Source, property, and value cannot be empty.")
            continue

        elif edit_choice == 'delete':
            try:
                row_num = int(input("Enter the number (#) of the row to delete: "))
                if 1 <= row_num <= len(flat_pv_list):
                    del flat_pv_list[row_num - 1]
                    print("Row deleted.")
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
            continue

        else:
            try:
                row_num = int(edit_choice)
                if not (1 <= row_num <= len(flat_pv_list)):
                    print("Invalid number.")
                    continue

                item_to_edit = flat_pv_list[row_num - 1]
                print(f"\nEditing row #{row_num}: {item_to_edit}")

                new_source = input(f"Enter new source string (current: '{item_to_edit['source']}'): ").strip()
                new_prop = input(f"Enter new property (current: '{item_to_edit['prop']}'): ").strip()
                new_val = input(f"Enter new value (current: '{item_to_edit['val']}'): ").strip()

                # Only update if the user provided new input
                if new_source: item_to_edit['source'] = new_source
                if new_prop: item_to_edit['prop'] = new_prop
                if new_val: item_to_edit['val'] = new_val
                print("Row updated.")

            except ValueError:
                print("Invalid input. Please enter a number, 'add', 'delete', or 'done'.")


def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')

    if not FLAGS.data_file:
        raise app.UsageError('Must specify a --data_file.')

    print(f"Starting interactive schema building for: {FLAGS.data_file}")

    # Step 1: Generate Initial PV-Map
    counters = Counters()
    config_dict = {
        'llm_data_annotation': FLAGS.llm_data_annotation,
        'google_api_key': FLAGS.google_api_key,
        'llm_model': FLAGS.llm_model,
        'sample_pvmap': FLAGS.llm_sample_pvmap,
        'sample_data': FLAGS.llm_sample_data,
        'sample_statvars': FLAGS.llm_sample_statvars,
        'context': FLAGS.llm_data_context,
        'llm_pvmap_prompt': FLAGS.llm_pvmap_prompt,
        'llm_request': FLAGS.llm_request,
        'llm_response': FLAGS.llm_response,
        'llm_dry_run': FLAGS.genai_dry_run,
    }
    config = ConfigMap(filename=FLAGS.config_file if 'config_file' in FLAGS else '', config_dict=config_dict)

    print("Generating initial PV-map...")
    FLAGS.data_annotator_input = FLAGS.data_file
    initial_pvmap = data_annotator.generate_pvmap(
        data_file=FLAGS.data_file,
        pv_map_output="", # Don't write to file yet
        config=config,
        counters=counters
    )

    if not initial_pvmap:
        print("Could not generate an initial PV-map. Exiting.")
        return

    validated_pvmap = initial_pvmap

    # Main PV-Map feedback loop
    while True:
        flat_map = flatten_pvmap(validated_pvmap)
        present_pvmap_for_review(flat_map)

        choice = input(
            "\nPlease review the mappings above.\n"
            "- To accept and proceed to schema generation, type 'accept'.\n"
            "- To edit, type 'edit'.\n"
            "- To quit without saving, type 'quit'.\n"
            "Your choice: "
        ).lower().strip()

        if choice == 'accept':
            break
        elif choice == 'quit':
            print("Exiting without saving.")
            return
        elif choice == 'edit':
            validated_pvmap = enter_editing_mode(validated_pvmap)
        else:
            print("\nInvalid choice. Please type 'accept', 'edit', or 'quit'.")

    # Phase 2: Generate and Review Schema
    print("\nGenerating new schema nodes based on the validated PV-map...")
    existing_schema = load_mcf_nodes(FLAGS.schema_mcf)
    new_schema_nodes = schema_generator.generate_schema_nodes(
        nodes=validated_pvmap,
        schema=existing_schema,
        config=config.get_configs()
    )

    # Final review loop
    while True:
        present_schema_for_review(new_schema_nodes)
        final_choice = input(
            "\nPlease review the new schema nodes.\n"
            "- To accept and save all files, type 'accept'.\n"
            "- To discard and quit, type 'quit'.\n"
            "Your choice: "
        ).lower().strip()

        if final_choice == 'accept':
            # Save both the validated PV-map and the new schema
            data_annotator.write_pv_map(validated_pvmap, FLAGS.output_pvmap_file)
            print(f"Validated PV-map saved to {FLAGS.output_pvmap_file}")
            write_mcf_nodes(new_schema_nodes, FLAGS.output_schema_mcf)
            print(f"New schema nodes saved to {FLAGS.output_schema_mcf}")
            break
        elif final_choice == 'quit':
            print("Exiting without saving any files.")
            break
        else:
            print("\nInvalid choice. Please type 'accept' or 'quit'.")


if __name__ == '__main__':
    app.run(main)
