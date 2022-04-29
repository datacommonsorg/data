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

from absl import app

INDICATOR_MAP_FILE = "indicator_map.json"
DUPLICATE_INDICATOR_NAMES_FILE = "duplicate_indicator_names.json"


def generate_indicator_map_using_properties_mcf():
    indicator_map = {}
    # who_properties.mcf is the schema file for all the properties in WHO stat vars
    mcf_file = open("who_properties.mcf")
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
    f = open(INDICATOR_MAP_FILE, "w+")
    f.write(json.dumps(indicator_map))


def generate_duplicate_indicator_names():
    with open(INDICATOR_MAP_FILE, "r+") as indicator_map:
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
    f = open(DUPLICATE_INDICATOR_NAMES_FILE, "w+")
    f.write(json.dumps(duplicates))


def get_name(i_name, dcid, i_code, name_replacements, dup_i_names):
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


def generate_mcf_with_processed_names():
    with open(INDICATOR_MAP_FILE, "r+") as indicator_map:
        indicator_map = json.load(indicator_map)
    with open(DUPLICATE_INDICATOR_NAMES_FILE, "r+") as dup_i_names:
        dup_i_names = json.load(dup_i_names)
    with open("name_replacements.json", "r+") as name_replacements:
        name_replacements = json.load(name_replacements)
    # original who stat vars mcf
    mcf_file = open("who_gho_stat_vars.mcf")
    mcf_file_lines = mcf_file.readlines()
    # the new who stat vars with names updated
    processed_file = open("updated_who_gho_stat_vars.mcf", "w")
    missing_i_code_names = set()
    curr_node_lines = []
    dcid = ""
    i_code = ""
    for line in mcf_file_lines:
        curr_node_lines.append(line)
        if line == '\n':
            i_name = indicator_map.get(i_code, "")
            if not i_name:
                missing_i_code_names.add(i_code)
                continue
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
    f = open("missing_i_code_names.json", "w+")
    f.write(json.dumps(list(missing_i_code_names)))


def main(_):
    generate_indicator_map_using_properties_mcf()
    generate_duplicate_indicator_names()
    generate_mcf_with_processed_names()


if __name__ == '__main__':
    app.run(main)
