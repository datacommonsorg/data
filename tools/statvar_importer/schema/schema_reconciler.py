# Copyright 2026 Google LLC
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
"""Class to reconcile schema nodes.

Given a dictionary of MCF nodes, such as StatVarObservations or schema,
any property or values that refers to a node that has a 'supercededBy' property
is replaced by the supercededBy node.

When reconciling schema, a set of equivalent or duplicate StatVars can be
mapped to a canonical node through the supercededBy property.
The import pipelines will then start generating the nodes with the new dcid.

When reconciling nodes into a canonical node, the old nodes can be optionally
preserved so that any users who have hardcoded the old dcid can continue to
retrieve the node. The reconciliation invokes the DC API to retrieve the
supercededBy property for all property and values.
To reconcile faster, provide a schema MCF file with the supercededBy values.

The reconciliation is automatically invoked on the output as part of the
StatVarProcessor.

To reconcile any csv or mcf file through command line, run the following:
  python schema_reconciler.py --recon_input=<list of files> \
      --recon_output=<output-file-with input nodes after reconciliation> \

To reconcile a specific set of nodes configured with supercededBy, add the
schema MCF with the following commandline option:
      --recon_schema_mcf=<mcf-file>

To reconcile values of a specific set of properties, such as
variableMeasured and measurementMethod, set the following command line option:
      --recon_property=variableMeasured,measurementMethod
"""

import os
import sys
from typing import Union

from absl import app
from absl import flags
from absl import logging

# uncomment to run pprof
# os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
# from pypprof.net_http import start_pprof_server

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR.split('/data/')[0], 'data')
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(_DATA_DIR)
sys.path.append(os.path.join(_DATA_DIR, 'util'))

# imports from data/tools/statvar_importer
import process_http_server

from mcf_file_util import load_mcf_nodes, write_mcf_nodes
from mcf_file_util import add_namespace, strip_namespace
from mcf_file_util import add_mcf_node, get_value_list

# imports from data/util
import file_util
import dc_api_wrapper as dc_api
from config_map import ConfigMap
from counters import Counters

_FLAGS = flags.FLAGS

flags.DEFINE_list('recon_schema_mcf', [],
                  'List of schema MCF files to load for reconciliation.')
flags.DEFINE_list('recon_input', [],
                  'List of MCF files to load for reconciliation.')
flags.DEFINE_string(
    'recon_output',
    '',
    'Output MCF for reconciled nodes.',
)
flags.DEFINE_list('recon_property', [],
                  'List of properties to be looked up for reconciliation.')
flags.DEFINE_bool('recon_keep_legacy_svobs', True,
                  'Keep the legacy value when reconciling nodes.')


def get_default_recon_config() -> dict:
    """Returns dictionary of default config for reconciliation."""
    if not _FLAGS.is_parsed():
        _FLAGS.mark_as_parsed()

    return {
        'recon_property': _FLAGS.recon_property,
        'recon_keep_legacy_svobs': _FLAGS.recon_keep_legacy_svobs,
    }


class SchemaReconciler:
    """Class to reconcile nodes with schema.
      Supports the following reconciliation:
      - If a schema definition for a property or value has a supercededBy
        property, update the value to use the superceded node.
      - To restrict schema lookup through DC APIs for reconciliation to specific
        properties, set the recon_property config.

      It supports the following config options:
        - recon_keep_legacy_svobs: retain old StatVarObservation nodes
            if any value in the svobs is reconciled to a new dcid.
        - recon_lookup_api: Enable or disable API lookup for schema definition
            for any property or value.
            If disabled, use the schema_mcf option to specify a list of MCF files
            containing nodes with the supercededBy property.
        - recon_property: Restrict reconciliation to values of these listed
            properties.

    Usage:
         # Create a SchemaReconciler loaded with MCF schema nodes.
         resolver = SchemaReconciler(mcf_files)

         # Reconcile a list of nodes with property:values.
         input_nodes = { <dcid>: { <prop1>: <value1> }, ...}
         output_nodes = recon.reconcile_nodes(input_nodes)
         # if value1 is remapped to valueNew with supercededBy in schema,
         # output nodes = { <dcid>: { <prop1>: <valueNew> }, ...}
    """

    def __init__(self,
                 schema_mcf_files: list = '',
                 config: dict = {},
                 counters: Counters = None):
        """Initializes the SchemaReconciler with schema files and configuration.

        Args:
            schema_mcf_files: List of MCF files containing schema definitions.
            config: Configuration dictionary for reconciliation.
            counters: Counters object for tracking metrics.
        """
        self._counters = counters
        if self._counters is None:
            self._counters = Counters()
        self._config = ConfigMap(config_dict=get_default_recon_config())
        if config:
            self._config.add_configs(config)

        self._schema_nodes = {}
        self.load_schema_mcf(schema_mcf_files)

    def load_schema_mcf(self, schema_mcf_files: list):
        """Load nodes from schema MCF files and add to the index."""
        mcf_nodes = load_mcf_nodes(schema_mcf_files, {})
        self.add_schema_nodes(mcf_nodes)
        logging.info(
            f'Loaded {len(mcf_nodes)} schema MCF nodes: {schema_mcf_files}')

    def add_schema_nodes(self, schema_nodes: dict):
        """Load nodes into schema used for reconciliation."""
        if not schema_nodes:
            return
        for node in schema_nodes.values():
            add_mcf_node(node, self._schema_nodes)
            self._counters.add_counter('recon-schema-nodes', 1)

    def reconcile_nodes(self,
                        nodes: dict,
                        keep_legacy_obs: bool = None,
                        remapped_dcids: dict = None) -> int:
        """Return the reconciled nodes.
        Any values in the input nodes that are supercededBy new nodes are updated
        to the new node.

        In case the node is a StatVarObservation with single value per property,
        the node is replicated with the new property:value.

        If config{'recon_keep_legacy_svobs'} is set the old svobs node is
        also retained.

        If config('recon_lookup_api') is set, the DC API is used to fetch schema
        for nodes referenced in the input but are not in the schema preloaded.

        Args:
          nodes: dictionary of nodes as dict of property:values.
          keep_legacy_obs: if True, preserves the existing StatVarObservation nodes
            and add a new node with modified property:values.
          remapped_dcids: dictionary of dcids to be remapped with updated dcids.
            if not set, looks up schema for supercededBy property for each unique dcid.
            remapped_dcids are assumed to have 'dcid:' prefix in the key.
            { 'dcid:OldId': 'dcid:NewId' ... }

        Returns:
          The number of nodes remapped.
        """
        num_remapped = 0
        if keep_legacy_obs is None:
            keep_legacy_obs = self._config.get('recon_keep_legacy_svobs', True)
        logging.info(f'Looking up {len(nodes)} nodes for reconciliation.')

        # Identify all DCIDs in input nodes that need to be remapped based on schema.
        if not remapped_dcids:
            remapped_dcids = self.lookup_remapped_schema(nodes)
        if not remapped_dcids:
            # No dcids to be remapped. Return the original nodes.
            logging.info(f'No remapped dcids in {len(nodes)} nodes')
            self._counters.add_counter('recon-unmodified-nodes', len(nodes))
            return num_remapped

        logging.info(
            f'Got {len(remapped_dcids)} remapped dcids for {len(nodes)} nodes')

        # Iterate through each node and update properties or values that have been remapped.
        keys = list(nodes.keys())
        for key in keys:
            node = nodes.get(key)
            if not node:
                continue

            # Process all property-value pairs for the current node.
            # Collect any modifications in new_pvs and keep original values in new_node.
            new_node = {}
            new_pvs = {}
            for prop, value in node.items():
                remapped_prop = remapped_dcids.get(add_namespace(prop), prop)
                values = get_value_list(value)
                remapped_values = []
                for val in values:
                    remapped_values.append(
                        remapped_dcids.get(add_namespace(val), val))

                if remapped_prop != prop or remapped_values != values:
                    # Property:value is modified. Add the new property:value.
                    new_pvs[strip_namespace(remapped_prop)] = ",".join(
                        remapped_values)
                else:
                    # No modification to property:value. Copy it over.
                    new_node[prop] = value

            if not new_pvs:
                self._counters.add_counter('recon-unmodified-nodes', 1)
                continue

            # Merge modified properties and values into the new node representation.
            new_node.update(new_pvs)

            # Update the original nodes dictionary.
            # For StatVarObservations, we can optionally keep the legacy observation.
            typeof = strip_namespace(node.get('typeOf', ''))
            if typeof == 'StatVarObservation' and keep_legacy_obs:
                # Create a new duplicate node with a new dcid to preserve history.
                new_key = f'{key}-1'
                new_node['Node'] = new_key
                if 'dcid' in new_node:
                    new_node['dcid'] = new_key
                nodes[new_key] = new_node

                self._counters.add_counter('recon-new-nodes', 1)
            else:
                # Update the existing node in place if no legacy preservation is required.
                node.clear()
                node.update(new_node)
                self._counters.add_counter('recon-updated-nodes', 1)
            num_remapped += 1

        logging.info(f'Remapped {num_remapped} nodes out of {len(nodes)}')
        return num_remapped

    def lookup_remapped_schema(self,
                               nodes: dict,
                               schema_nodes: dict = None) -> dict:
        """Lookup new property or value in the nodes and add to the cached schema.

        Args:
          nodes: dictionary of nodes as dict of property:values.

        Returns:
          dictionary of dcids that have to be remapped with updated dcid.
        """
        if schema_nodes is None:
            schema_nodes = self._schema_nodes

        # dictionary of dcid mapped to a new dcid.
        remapped_dcids = {}
        recon_props = self._config.get('recon_property', [])

        # Get a list of new dcids to be looked up from both properties and values.
        lookup_dcids = set()
        for dcid, pvs in nodes.items():
            for prop, value in pvs.items():
                # Check if reconciliation is restricted to specific properties.
                if recon_props and prop not in recon_props:
                    continue
                if not prop or prop.startswith('#') or not prop[0].islower():
                    # Ignore invalid properties.
                    continue

                # Check if the property itself has a replacement in the cached schema.
                schema_node = self.get_schema_node(prop)
                if not schema_node:
                    lookup_dcids.add(prop)
                else:
                    remapped_prop = self.get_remapped_dcid(prop, schema_node)
                    if remapped_prop and remapped_prop != prop:
                        remapped_dcids[add_namespace(prop)] = remapped_prop

                # Check if any of the values for this property have replacements in the cached schema.
                values = get_value_list(value)
                for val in values:
                    if val.startswith('#') or val.startswith('"') or ' ' in val:
                        # ignore value that is a quoted string and not a
                        # reference to another node
                        continue
                    schema_node = self.get_schema_node(val)
                    if not schema_node:
                        lookup_dcids.add(val)
                    else:
                        remapped_val = self.get_remapped_dcid(val, schema_node)
                        if remapped_val and remapped_val != val:
                            remapped_dcids[add_namespace(val)] = remapped_val

        # If some DCIDs are not found in the local schema cache, fetch them using the DC API.
        if lookup_dcids and not self._config.get('recon_lookup_api', True):
            # DC API lookup is disabled.
            # Use any remapped dcids collected from existing schema.
            logging.warning(
                f'SchemaRecon ignoring {len(lookup_dcids)} new dcids not in schema.'
            )
            return remapped_dcids

        # Batch lookup DC API for supercededBy for selected unique dcids.
        new_schema_nodes = dc_api.dc_api_get_node_property(
            list(lookup_dcids), 'supercededBy')
        self._counters.add_counter('recon-lookup-schema', len(lookup_dcids))
        for dcid, node in new_schema_nodes.items():
            add_mcf_node(node, schema_nodes)
            self._counters.add_counter('recon-lookup-schema-response', 1)
            self._counters.add_counter('recon-schema-nodes', 1)

            remapped_dcid = self.get_remapped_dcid(dcid)
            if remapped_dcid:
                remapped_dcids[add_namespace(dcid)] = remapped_dcid

        return remapped_dcids

    def get_schema_node(self, dcid: str) -> dict:
        """Returns a schema node with the given dcid."""
        node = self._schema_nodes.get(add_namespace(dcid))
        if not node:
            # Try without namespace
            node = self._schema_nodes.get(strip_namespace(dcid))
        return node

    def get_remapped_dcid(self, dcid: str, schema_node: dict = None) -> str:
        """Returns the remapped dcid from the schema for the given node.

        Args:
          dcid: dcid to be looked up for a remapped dcid.
          schema_node: (optional) schema definition for the dcid with the
            supercededBy property, if any.

        Returns:
          new dcid that superceded the input dcid.
          None if the dcid is not present in the schema nodes
          '' string if the schema node is present, but has no supercededBy
        """
        if not schema_node:
            schema_node = self.get_schema_node(dcid)
        if not schema_node:
            return None
        return schema_node.get('supercededBy', '')


def schema_reconcile_nodes(nodes: dict,
                           config: dict = None,
                           schema_nodes: dict = None,
                           schema_files: list = None,
                           counters: Counters = None) -> bool:
    """Reconcile a set of nodes."""
    recon = SchemaReconciler(schema_files, config, counters)
    recon.add_schema_nodes(schema_nodes)
    return recon.reconcile_nodes(nodes)


def main(_):
    """Main entry point for reconciling MCF files from the command line."""
    # Launch a web server if --http_port is set.
    if process_http_server.run_http_server(script=__file__, module=__name__):
        return

    # if _FLAGS.debug:
    #  logging.set_verbosity(2)

    counters = Counters()
    nodes = load_mcf_nodes(_FLAGS.recon_input)
    is_remapped = schema_reconcile_nodes(nodes, get_default_recon_config(), {},
                                         _FLAGS.recon_schema_mcf, counters)
    if is_remapped and _FLAGS.recon_output:
        write_mcf_nodes(nodes, _FLAGS.recon_output)
    counters.print_counters()


if __name__ == '__main__':
    app.run(main)
