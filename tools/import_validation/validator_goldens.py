# Copyright 2022 Google LLC
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
"""Utility functions to validate data with golden sets.

This module provides tools to compare sets of nodes (e.g., from CSV or MCF files)
against a "golden" set of expected nodes. It supports flexible matching based on
configurable property sets and handles normalization of values (like stripping
namespaces from DCIDs).

Example Use Case: Validating StatVarObservations
------------------------------------------------
You can use this to ensure that your import contains expected observations.

1. Validate based on variableMeasured and observationAbout:
   Config: {'goldens_key_property': ['variableMeasured', 'observationAbout']}
   This will check that for every golden observation, an input observation exists
   with the same StatVar and Place, regardless of the value or time.

2. Validate based on a combination of metadata:
   Config: {
       'goldens_key_property': [
           'variableMeasured', 'unit', 'scalingFactor', 'measurementMethod'
       ]
   }
   This ensures that the specific measurement metadata combinations defined in
   your goldens are present in the input nodes.

Usage:
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --validate_goldens=goldens/expected_obs.mcf \
      --goldens_key_property=variableMeasured,observationAbout

    # To generate goldens from input:
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --generate_goldens_property_sets="variableMeasured|observationAbout,observationDate,variableMeasured|unit|scalingFactor|observationPeriod|measurementMethod" \
      --validate_goldens_output=goldens/generated_goldens.csv

    # To generate goldens using a sample of input nodes:
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --goldens_sample_rows=100 \
      --generate_goldens_property_sets="variableMeasured|observationAbout" \
      --validate_goldens_output=goldens/generated_goldens.csv

    # To generate goldens capturing every unique value in every column:
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.mcf \
      --goldens_sampler_exhaustive \
      --validate_goldens_output=goldens/generated_goldens.mcf

    # To generate goldens ensuring prominent DCIDs are included if present:
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --goldens_must_include="variableMeasured:selected_svs.txt,observationAbout:selected_places.txt" \
      --validate_goldens_output=goldens/generated_goldens.csv
"""

import os
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

import file_util
import mcf_file_util
import data_sampler

from counters import Counters

flags.DEFINE_list('validate_goldens_input', None,
                  'List of files to be compared against goldens.')
flags.DEFINE_list('validate_goldens', None,
                  'List of golden files to be compared against')
flags.DEFINE_string('generate_goldens', None,
                    'Golden file to be generated from the input.')
flags.DEFINE_string('validate_goldens_output', None,
                    'Output file with missing goldens')
flags.DEFINE_list('goldens_key_property', [],
                  'Properties in golden nodes to be compared.')
flags.DEFINE_list('goldens_ignore_property', ['value'],
                  'Properties in golden nodes to be ignored.')
flags.DEFINE_list(
    'generate_goldens_property_sets', [],
    'List of property sets to generate goldens for. '
    'Each set is a pipe (|) separated list of properties. '
    'Example: "variableMeasured|observationAbout,observationDate"')
flags.DEFINE_integer(
    'goldens_sample_rows', 0,
    'Number of input rows to sample for generating goldens. '
    'If 0, all rows are used.')
flags.DEFINE_boolean(
    'goldens_sampler_exhaustive', False,
    'If True, uses exhaustive sampling to capture every '
    'unique value in the input nodes.')
flags.DEFINE_list(
    'goldens_must_include', [],
    'List of "column:file" pairs containing values (e.g. prominent DCIDs) '
    'that MUST be included in the generated goldens if they appear '
    'in the input data. '
    'Example: "variableMeasured:website/tools/nl/embeddings/input/base/sheets_svs.csv,observationAbout:places.txt"'
)
flags.DEFINE_string('goldens_ignore_comments', '#',
                    'Prefix for comments to be ignored in the golden set.')

_FLAGS = flags.FLAGS


def get_validator_goldens_config() -> dict:
    """Returns a dictionary of config parameters for MCF diff from flags.

    The config includes properties to ignore and properties to use as keys
    for matching nodes, derived from command-line flags.
    """
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()
    return {
        'goldens_ignore_property': _FLAGS.goldens_ignore_property,
        'goldens_key_property': _FLAGS.goldens_key_property,
        'goldens_must_include': _FLAGS.goldens_must_include,
        'goldens_ignore_comments': _FLAGS.goldens_ignore_comments,

        # config options for data_sampler when generating goldens
        'sampler_output_rows': _FLAGS.goldens_sample_rows,
        'sampler_exhaustive': _FLAGS.goldens_sampler_exhaustive,
        'sampler_column_keys': _FLAGS.goldens_must_include,
    }


# Get a fingerprint for the node with the given properties
def get_node_fingerprint(node: dict,
                         key_property: set = None,
                         ignore_property: set = None,
                         normalize: bool = True,
                         strip_namespaces: bool = True) -> str:
    """Returns a string key for the node based on the values for key_properties.

    The fingerprint is a semi-colon separated string of "prop=value" pairs,
    sorted alphabetically by property name to ensure consistency.

    Args:
        node: dictionary of property:values for a node.
        key_property: set of properties to be used as key.
            If empty all properties are used.
        ignore_property: set of properties not used to generate the key.
        normalize: boolean to indicate if the values need to be normalized,
            such as stripping out namespace prefix
        strip_namespaces: boolean to indicate if DCID namespaces should be
            removed during normalization.

    Returns:
        string that is a unique fingerprint for the node with the key properties.
    """
    if key_property is None:
        # If no key properties are specified, use all properties currently in the node.
        key_property = set(node.keys())
    if ignore_property is None:
        ignore_property = set()

    key_tokens = []
    # Sort keys to ensure the resulting fingerprint string is deterministic.
    keys = sorted(list(node.keys()))
    for prop in keys:
        value = node.get(prop)
        # Skip properties that are not in the key set or are explicitly ignored.
        if prop not in key_property or prop in ignore_property:
            continue
        # Normalize the value (e.g., strip spaces, quotes, or DCID namespaces).
        if normalize:
            value = normalize_value(value, strip_namespaces)
        key_tokens.append(f'{prop}={value}')

    # Join tokens with a delimiter that is unlikely to be in the property names or values.
    return ';'.join(key_tokens)


def normalize_value(value: str, strip_namespaces: bool = True) -> str:
    """Returns a normalized value for comparison.

    Normalization handles:
    1. Stripping leading/trailing whitespace and double quotes.
    2. Removing namespaces from DCID references (e.g., 'dcid:Count_Person' -> 'Count_Person').
    3. Normalizing lists by sorting elements.
    4. Trimming trailing zeros from floats.
    """
    if isinstance(value, str):
        # Remove surrounding quotes and spaces which are common in various file formats.
        value = value.strip(' "')
        # If the string contains special characters, check for specific DC types.
        if not value.isalnum():
            if ':' in value and strip_namespaces:
                # String appears to be a DCID reference with a namespace.
                return mcf_file_util.strip_namespace(value)
            if ',' in value:
                # String appears to be a comma-separated list.
                return mcf_file_util.normalize_list(value)

        # Return the stripped string if no other normalization applied.
        return value
    if isinstance(value, float):
        # Standardize float representation by removing redundant trailing zeros.
        return str(value).rstrip('0')

    # For other types, return their string representation.
    return str(value)


def _is_commented_node(fingerprint: str, comment_char: str = '#') -> bool:
    """Returns True if the node fingerprint is commented.

    Args:
      fingerprint: string fingerprint of the node of the form 'prop=value;...'

    Returns:
      True if any property or value is commented.
    """
    if not comment_char:
        return False
    if fingerprint.startswith(
            comment_char
    ) or f';{comment_char}' in fingerprint or f'={comment_char}' in fingerprint:
        return True
    return False


# Compare nodes in a dictionary to nodes in a golden set
def validator_compare_nodes(input_nodes: dict,
                            golden_nodes: dict,
                            config: dict = None,
                            counters: Counters = None) -> list:
    """Returns a summary of the differences in the input and golden nodes.

    It only compares the properties defined in the golden nodes against the 
    corresponding properties in the input_nodes.

    Args:
        input_nodes: dictionary of nodes which are dictionary of property:values.
            { <key1>: { <prop1>: <value1> ,,,}, <key2>: { <prop2>: <value2>..}
        golden_nodes: dictionary of key to expected nodes with property:values.
            These nodes may have fewer properties than input_nodes.
        config: dictionary of config parameters such as ignore lists and
            normalization settings.
        counters: Output counters for tracking match statistics.

    Returns:
        A list of fingerprints for golden nodes that were not matched in the input.
    """

    if counters is None:
        counters = Counters()

    if config is None:
        config = get_validator_goldens_config()

    # Extract configuration parameters with defaults.
    ignore_props = config.get('goldens_ignore_property', {})
    ignore_comments = config.get('goldens_ignore_comments', True)
    normalize = config.get('goldens_normalize', True)
    strip_namespaces = config.get('goldens_strip_namespaces', True)
    golden_key_props = set(config.get('goldens_key_property', {}))
    key_delimiter = config.get('golden_key_delimiter', '|')

    # Step 1: Group golden nodes by their set of properties.
    # Different golden nodes might specify different subsets of properties to match on.
    golden_key_sets = {}
    logging.debug(f'Extracting properties for {len(golden_nodes)} goldens')
    for node_key, node in golden_nodes.items():
        node_props = set()
        for prop in node.keys():
            if not prop:
                continue
            if ignore_comments and prop.startswith('#'):
                continue
            if prop in ignore_props:
                continue
            if golden_key_props and prop not in golden_key_props:
                continue
            node_props.add(prop)

        # Use the joined sorted property names as a key for the group.
        node_props_key = key_delimiter.join(sorted(list(node_props)))
        if node_props_key not in golden_key_sets:
            golden_key_sets[node_props_key] = {}
        golden_key_sets[node_props_key][node_key] = node

    logging.info(
        f'Comparing {len(input_nodes)} nodes against {len(golden_nodes)} goldens in {len(golden_key_sets)} sets using properties: {golden_key_sets.keys()}'
    )
    counters.add_counter('validate-goldens-sets', len(golden_key_sets))
    counters.add_counter('validate-goldens-inputs', len(input_nodes))
    counters.add_counter('validate-goldens-expected', len(golden_nodes))

    # Step 2: Generate fingerprints for all expected golden nodes.
    # We only generate a fingerprint for each node using its own relevant property set.
    golden_matches = dict()
    for node_props_key, nodes_group in golden_key_sets.items():
        key_props = node_props_key.split(key_delimiter)
        for node in nodes_group.values():
            key = get_node_fingerprint(node,
                                       key_property=key_props,
                                       ignore_property=ignore_props,
                                       normalize=normalize,
                                       strip_namespaces=strip_namespaces)
            # Initialize match count to 0.
            golden_matches[key] = 0

    # Step 3: Iterate through input nodes and try to match them against the golden fingerprints.
    for node in input_nodes.values():
        # An input node might match different golden "shapes" (sets of properties).
        for node_props_key in golden_key_sets.keys():
            key_props = node_props_key.split(key_delimiter)
            key = get_node_fingerprint(node,
                                       key_property=key_props,
                                       ignore_property=ignore_props,
                                       normalize=normalize,
                                       strip_namespaces=strip_namespaces)
            if key in golden_matches:
                golden_matches[key] += 1
                counters.add_counter('validate-goldens-input-matched', 1)

    # Step 4: Identify which golden fingerprints had no corresponding input nodes.
    missing_goldens = []
    comment_char = config.get('goldens_ignore_comments', '#')
    for key, count in golden_matches.items():
        if count > 0:
            # This key got matches.
            counters.add_counter('validate-goldens-matched', 1)
        else:
            if _is_commented_node(key, comment_char):
                # No matches for this key. Ignore commented keys.
                counters.add_counter('validate-goldens-ignored', 1)
            else:
                missing_goldens.append(key)
                counters.add_counter('validate-goldens-missing', 1)

    if missing_goldens:
        logging.error(
            f'Missing {len(missing_goldens)} among {len(golden_nodes)} goldens in {len(input_nodes)} input nodes.'
        )
        logging.debug(f'Missing goldens: {missing_goldens}')
    else:
        logging.info(
            f'Goldens match successful: {len(golden_nodes)} goldens matched {len(input_nodes)} inputs'
        )

    return missing_goldens


def load_nodes_from_file(files: str) -> dict:
    """Returns a dictionary of nodes loaded from the files.

    Supports CSV and MCF formats.
    - CSV files: Each row is loaded as a node.
    - MCF files: Each node is loaded based on its DCID.
    """
    nodes = {}
    input_files = file_util.file_get_matching(files)
    for input_file in input_files:
        if file_util.file_is_csv(input_file):
            # For CSV, we treat each row as a dictionary of column:value.
            # Nodes are keyed by their index in the combined loaded set.
            file_nodes = file_util.file_load_csv_dict(input_file,
                                                      key_index=True)
            for node in file_nodes.values():
                nodes[len(nodes)] = node
        else:
            # For MCF or JSON, we assume nodes are already keyed by DCID.
            file_nodes = mcf_file_util.load_mcf_nodes(input_file)
            for dcid, node in file_nodes.items():
                # Ensure the dcid is present in the node dictionary itself.
                if 'dcid' not in node:
                    node['dcid'] = mcf_file_util.strip_namespace(dcid)
                mcf_file_util.add_mcf_node(node, nodes)

    logging.info(f'Loaded {len(nodes)} nodes from {input_files}')
    return nodes


def generate_goldens(input_files: str,
                     property_sets: list,
                     output_file: str = None,
                     config: dict = None,
                     counters: Counters = None) -> dict:
    """Generates a set of unique golden nodes from input files.

    For each input node and each property set in property_sets, it extracts
    the values for those properties and creates a unique golden node.
    If sampling is requested, a representative sample of input nodes is used
    as the basis for generating the golden nodes.

    Args:
        input_files: Glob pattern or list of input data files.
        property_sets: List of sets/lists of properties to extract.
            Example: [{'variableMeasured'}, {'observationAbout', 'variableMeasured'}]
        output_file: Path to write the generated goldens to (MCF format).
        config: Configuration for normalization and sampling.
        counters: Output counters.

    Returns:
        A dictionary of unique golden nodes keyed by their fingerprints.
    """
    if counters is None:
        counters = Counters()

    if config is None:
        config = get_validator_goldens_config()

    # Apply sampling if requested.
    sampler_rows = config.get('sampler_output_rows', 0)
    exhaustive = config.get('sampler_exhaustive', False)
    must_include_values = data_sampler.load_column_keys(
        config.get('sampler_column_keys', []))
    if must_include_values:
        for col, vals in must_include_values.items():
            counters.add_counter(f'generate-goldens-include-{col}', len(vals))
    if sampler_rows > 0 or exhaustive:
        logging.info(
            f'Sampling rows from {input_files} (exhaustive={exhaustive}, rows={sampler_rows})'
        )
        if exhaustive:
            config['sampler_column_regex'] = '.*'

        # Generate a representative sample with unique values across columns.
        with tempfile.NamedTemporaryFile(mode='w+t', suffix='.csv',
                                         delete=True) as sampled_file:
            sampler = data_sampler.DataSampler(config_dict=config,
                                               counters=counters)
            sampler.sample_csv_file(input_files, output_file=sampled_file.name)
            input_nodes = load_nodes_from_file(sampled_file.name)
            logging.info(
                f'Using sampled file: {sampled_file} with {len(input_nodes)} nodes'
            )
            counters.add_counter(f'generate-goldens-sampled-nodes',
                                 len(input_nodes))
    else:
        input_nodes = load_nodes_from_file(input_files)
        counters.add_counter('generate-goldens-input-nodes', len(input_nodes))

        # If not sampling, but must_include_values are provided, use them as a filter
        # to focus goldens on prominent DCIDs if requested.
        if must_include_values:
            filtered_nodes = {}
            for k, node in input_nodes.items():
                match = False
                for col, vals in must_include_values.items():
                    if node.get(col) in vals:
                        match = True
                        break
                if match:
                    filtered_nodes[k] = node

            logging.info(
                f'Filtered {len(input_nodes)} nodes down to {len(filtered_nodes)} matching prominent DCIDs.'
            )
            input_nodes = filtered_nodes
            counters.add_counter('generate-goldens-filtered-nodes',
                                 len(filtered_nodes))

    normalize = config.get('goldens_normalize', True)
    strip_namespaces = config.get('goldens_strip_namespaces', True)
    ignore_props = set(config.get('goldens_ignore_property', []))

    golden_nodes = {}
    for node in input_nodes.values():
        # If no property sets are provided, use all properties in the current node
        # except those that are explicitly ignored.
        effective_property_sets = property_sets
        if not effective_property_sets:
            node_props = set(node.keys()) - ignore_props
            if node_props:
                effective_property_sets = [node_props]
            else:
                continue

        for props in effective_property_sets:
            # Create a dictionary for this specific property set from the input node.
            golden_node = {}
            has_all_props = True
            for prop in props:

                if prop in node:
                    golden_node[prop] = node[prop]
                else:
                    # If a node is missing one of the properties in a set,
                    # we skip this combination.
                    has_all_props = False
                    break

            if not has_all_props or not golden_node:
                continue

            # Generate a unique key for this golden node shape.
            key = get_node_fingerprint(golden_node,
                                       key_property=props,
                                       normalize=normalize,
                                       strip_namespaces=strip_namespaces)

            if key not in golden_nodes:
                golden_nodes[key] = golden_node
                counters.add_counter('generate-goldens-unique', 1)

            counters.add_counter('generate-goldens-processed', 1)

    logging.info(
        f'Generated {len(golden_nodes)} unique goldens from {len(input_nodes)} input nodes.'
    )
    counters.add_counter('generated-golden-output', len(golden_nodes))

    if golden_nodes and output_file:
        logging.info(f'Writing {len(golden_nodes)} goldens to {output_file}')
        if file_util.file_is_csv(output_file):
            file_util.file_write_csv_dict(golden_nodes,
                                          output_file,
                                          key_column_name=None)
        else:
            mcf_file_util.write_mcf_nodes([golden_nodes], output_file)

    return golden_nodes


def validate_goldens(inputs: str | dict,
                     golden_files: str,
                     output_file: str = None,
                     config: dict = None,
                     counters: Counters = None) -> list:
    """Validate records in the input files against goldens.

    This is the high-level entry point for comparing two sets of files.

    Args:
        inputs: Glob pattern for list of input data files or
            dictionary of input nodes.
        golden_files: Glob pattern or list of golden data files.
        output_file: Path to write missing goldens to.
        config: Validation configuration.
        counters: Counters for tracking progress and results.
    """
    if config is None:
        config = get_validator_goldens_config()

    # Load all nodes from input and golden files.
    if isinstance(inputs, dict):
        input_nodes = inputs
    else:
        input_nodes = load_nodes_from_file(inputs)
    golden_files_list = file_util.file_get_matching(golden_files)
    golden_nodes = load_nodes_from_file(golden_files_list)

    # Run the core comparison logic.
    missing_goldens = validator_compare_nodes(input_nodes, golden_nodes, config,
                                              counters)

    # Optionally write out the missing fingerprints to a CSV for debugging.
    if missing_goldens and output_file:
        if output_file.endswith('/') or os.path.isdir(output_file):
            # Append a default filename if only a directory was provided.
            output_file = os.path.join(
                output_file,
                'goldens_missing_' + os.path.basename(golden_files_list[0]))
        logging.info(
            f'Writing {len(missing_goldens)} missing goldens to {output_file}')
        file_util.file_write_csv_dict(dict(enumerate(missing_goldens)),
                                      output_file)
    return missing_goldens


def main(_):
    """Main entry point for the validator script."""
    logging.set_verbosity(2)
    counters = Counters()

    if _FLAGS.generate_goldens:
        # Generation Mode
        property_sets = []
        for p_set_str in _FLAGS.generate_goldens_property_sets:
            property_sets.append(set(p_set_str.split('|')))

        generate_goldens(_FLAGS.validate_goldens_input,
                         property_sets,
                         output_file=_FLAGS.generate_goldens,
                         config=get_validator_goldens_config(),
                         counters=counters)
    if _FLAGS.validate_goldens:
        # Validation Mode
        validate_goldens(_FLAGS.validate_goldens_input,
                         _FLAGS.validate_goldens,
                         output_file=_FLAGS.validate_goldens_output,
                         config=get_validator_goldens_config(),
                         counters=counters)


if __name__ == '__main__':
    app.run(main)
