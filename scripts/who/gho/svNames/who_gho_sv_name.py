# Copyright 2022 Google LLC
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
import json
import os
from absl import app
from absl import flags

INDICATOR_MAP_FILE = "indicator_map.json"
DUPLICATE_INDICATOR_NAMES_FILE = "duplicate_indicator_names.json"

FLAGS = flags.FLAGS
flags.DEFINE_string('who_properties_file', 'who_properties.mcf',
                    'path to mcf file with WHO property nodes.')
flags.DEFINE_string('who_sv_file', 'who_gho_stat_vars.mcf',
                    'path to mcf file with WHO stat var nodes.')
flags.DEFINE_string('output_dir', '',
                    'dir to output generated MCF file and artifacts')


def generate_indicator_map_using_properties_mcf(properties_file, output_dir):
    """ 
    Generate a map of WHO indicator code to indicator name using an MCF file of
    WHO property nodes.
    Args:
        properties_file: path to the mcf file with WHO property nodes
        output_dir: directory to output the map
    """
    indicator_map = {}
    # who_properties.mcf is the schema file for all the properties in WHO stat vars
    mcf_file_lines = []
    with open(properties_file) as mcf_file:
        mcf_file_lines = mcf_file.readlines()
    i_code = ""
    i_name = ""
    for line in mcf_file_lines:
        if line == '\n':
            if i_code and i_name:
                indicator_map[i_code] = i_name
                i_code = ""
                i_name = ""
        if line.startswith("Node"):
            dcid = line[11:].strip()
            # the nodes we care about have dcid of the form who/<WHO indicator code>
            dcid_split = dcid.split("/")
            if len(dcid_split) > 1 and dcid_split[0] == "who":
                i_code = dcid_split[1]
        if line.startswith("description"):
            i_name = line[14:]
            i_name = i_name.strip().replace("\"", "")
    if i_code and i_name:
        indicator_map[i_code] = i_name
    with open(os.path.join(output_dir, INDICATOR_MAP_FILE), "w+") as f:
        f.write(json.dumps(indicator_map))


def generate_duplicate_indicator_names(output_dir):
    """ 
    Generate a map of WHO indicator names to list of indicator codes that match
    that name (only for indicator names that have multiple matching codes).
    Args:
        output_dir: directory to output the map
    """
    with open(os.path.join(output_dir, INDICATOR_MAP_FILE),
              "r+") as indicator_map:
        indicator_map = json.load(indicator_map)
    name_to_code = {}
    for code, name in indicator_map.items():
        if not name in name_to_code:
            name_to_code[name] = []
        name_to_code[name].append(code)
    duplicates = {}
    for name in name_to_code:
        if len(name_to_code[name]) > 1:
            duplicates[name] = name_to_code[name]
    with open(os.path.join(output_dir, DUPLICATE_INDICATOR_NAMES_FILE),
              "w+") as f:
        f.write(json.dumps(duplicates))


def get_name(i_name, dcid, i_code, name_replacements, dup_i_names):
    """
    Generate a stat var name using the indicator name, indicator code, and dcid
    of the stat var.
    Args:
        i_name: indicator name
        dcid: dcid of the stat var
        i_code: indicator code
        name_replacements: map of string to replacement string to use in the
            name.
        dup_i_names: map of indicator name to list of indicator codes that use
            that name for indicator names used by more than one indicator code.
    """
    # dcids should either be in the form WHO/<i_code>_<additional property values> OR WHO/<i_code>
    dcid_split = dcid.split(i_code + "_")
    additional_values = ""
    if len(dcid_split) > 1:
        additional_values = dcid_split[1].replace("_", ",")
    additional_values_name = ''.join(
        ' ' + c if c.isupper() else c for c in additional_values)
    if additional_values_name:
        additional_values_name = "," + additional_values_name
    for s, replacement in name_replacements.items():
        additional_values_name = additional_values_name.replace(s, replacement)
    name = i_name + additional_values_name
    name = name.title()
    if i_name in dup_i_names:
        name = i_name.title(
        ) + " (" + i_code + ")" + additional_values_name.title()
    return name


def generate_mcf_with_processed_names(properties_file, sv_file,
                                      name_replacements_file, output_dir):
    """
    Generate a new mcf file with generated stat var names.
    Args:
        properties_file: path to the mcf file with WHO property nodes
        sv_file: path to the mcf file with WHO stat var nodes that need names
            generated.
        output_dir: directory to output the map
    """
    generate_indicator_map_using_properties_mcf(properties_file, output_dir)
    generate_duplicate_indicator_names(output_dir)
    with open(os.path.join(output_dir, INDICATOR_MAP_FILE),
              "r+") as indicator_map:
        indicator_map = json.load(indicator_map)
    with open(os.path.join(output_dir, DUPLICATE_INDICATOR_NAMES_FILE),
              "r+") as dup_i_names:
        dup_i_names = json.load(dup_i_names)
    with open(name_replacements_file, "r+") as name_replacements:
        name_replacements = json.load(name_replacements)
    # original who stat vars mcf
    mcf_file_lines = []
    with open(sv_file) as mcf_file:
        mcf_file_lines = mcf_file.readlines()
    # the new who stat vars with names updated
    with open(os.path.join(output_dir, "updated_who_gho_stat_vars.mcf"),
              "w") as processed_file:
        missing_i_code_names = set()
        curr_node_lines = []
        dcid = ""
        i_code = ""
        for idx, line in enumerate(mcf_file_lines):
            if line.startswith("name"):
                continue
            curr_node_lines.append(line)
            if line == '\n' or idx == len(mcf_file_lines) - 1:
                i_name = indicator_map.get(i_code, "")
                if not i_name:
                    missing_i_code_names.add(i_code)
                else:
                    name = get_name(i_name, dcid, i_code, name_replacements,
                                    dup_i_names)
                    curr_node_lines.insert(1, "name: \"" + name + "\"\n")
                    processed_file.writelines(curr_node_lines)
                curr_node_lines = []
                dcid = ""
                i_code = ""
                continue
            if line.startswith("Node"):
                dcid = line[11:].strip()
            if line.startswith("measuredProperty"):
                # measuredProperty will be who/<i-code>
                i_code = line.split("/")[1].strip()
    with open(os.path.join(output_dir, "missing_i_code_names.json"), "w+") as f:
        f.write(json.dumps(list(missing_i_code_names)))


def main(_):
    generate_mcf_with_processed_names(FLAGS.who_properties_file,
                                      FLAGS.who_sv_file,
                                      "name_replacements.json",
                                      FLAGS.output_dir)


if __name__ == '__main__':
    app.run(main)
