# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Class to store StatVars and StatVarObs in a map."""

import csv
import datetime
import os
import re
import sys

from absl import logging

import file_util
import property_value_utils as pv_utils
from filter_data_outliers import filter_data_svobs
from mcf_file_util import get_numeric_value, write_mcf_nodes, add_namespace, strip_namespace, load_mcf_nodes
from mcf_filter import drop_existing_mcf_nodes
from mcf_diff import diff_mcf_node_pvs, fingerprint_mcf_nodes
from schema_resolver import SchemaResolver
from schema_generator import generate_schema_nodes, generate_statvar_name
from schema_checker import sanity_check_nodes

from config_map import ConfigMap
from counters import Counters, CounterOptions
from dc_api_wrapper import dc_api_is_defined_dcid
from statvar_dcid_generator import get_statvar_dcid

from utils import _capitalize_first_char, _str_from_number, _pvs_has_any_prop


class StatVarsMap:
    """Class to store StatVars and StatVarObs in a map.

  _statvar_map: dictionary with dcid as the key mapped

     to a dictionary of property:values
  _statvar_obs_map:
     dictionary with the fingerprint of place+date+variable as key
     mapped to dictionary of property:values for StatVarObs.

  Both maps may include additional internal properties such as '#Error...',
  '#input' that are used for validation and debugging.

  Processing options are passed in through a config object.
  The following configurations are used in this class:
    - schemaless: bool: to indicate support for schemaless statvars.
    - statvar_dcid_ignore_values: set of values in data source to be ignored
        such as 'NA', 'X', etc.
    - default_statvar_pvs: default property:values applicable to Statvars
    - default_svobs_pvs: default property:values applicable to StatVarVObs
    - required_statvar_properties: mandatory properties for a StatVar
    - required_statvarobs_properties: mandatory properties for a StatVarObs
    - duplicate_statvars_key: internal property to store a reference to
       duplicate statvar with same dcid but different properties.
       Such statVars and corresponding SVObs are dropped from the output.
       This is usually caused by insufficiently specified StatVar
       missing some properties.
    - duplicate_svobs_key: internal property for duplicate SVObs
        for the same place+year+StatVar but different values.
        If aggregate_duplicate_svobs is enabled, such duplicates are aggregated.
        If not this is treated as an error and the SVObs and
        the corresponding Statvars are dropped from the output.
    - aggregate_duplicate_svobs: aggregate SVObs with the same
        place+date+StatVar based on the '#Aggregate' property
        which indicates type of aggregation such as sum/min/max.
    - merged_pvs_prop: internal property (#MergedSVObs) to store references
        to SVObs that were aggregated to obtain the final value.
    - schemaless_statvar_comment_undefined_pvs: if True, when emitting
      schemaless statvars, valid properties that are not yet defined
        in the DC APi are commented out.
        If any such commented properties exist in a StatVar,
        it is converted to a schemaless statvar, i.e,
        its measuredProperty is set to its dcid.

  StatVars and StatVarObs are validated for duplicate values
  with conflicting dcids before being emited to output files.
  """

    # PVs for StatVarObs ignored when looking for dups
    _IGNORE_SVOBS_KEY_PVS = {
        'value': '',
        'measurementResult': '',
    }

    def __init__(self, config_dict: dict = None, counters_dict: dict = None):
        self._config = ConfigMap(config_dict=config_dict)
        self._counters = Counters(
            counters_dict=counters_dict,
            options=CounterOptions(debug=self._config.get('debug', False)),
        )
        # Dictionary of statvar dcid->{PVs}
        self._statvars_map = {}
        # Dictionary of existing statvars keyed by fingerprint
        self._statvar_resolver = SchemaResolver(
            self._config.get('existing_statvar_mcf', None))

        # Dictionary of statvar obs_key->{PVs}
        self._statvar_obs_map = {}
        # Unique values seen per SVObs property.
        self._statvar_obs_props = dict()
        # Cache for DC API lookups.
        self._dc_api_ids_cache = {}
        # Mapping of statvar DCIDs to be renamed.
        self._statvar_dcid_remap = file_util.file_load_csv_dict(
            filename=self._config.get('statvar_dcid_remap_csv', ''),
            value_column='dcid',
        )
        logging.info(
            f'Loaded remapped statvar dcid: {self._statvar_dcid_remap}')

    def add_default_pvs(self, default_pvs: dict, pvs: dict) -> dict:
        """Add default values for any missing PVs.

    Args:
      default_pvs: dictionary with default property:values. properties with a
        valid value not in pvs are added to it.
      pvs: dictionary of property:values to be modified.

    Returns:
      dictionary of property:values after addition of default PVs.
    """
        if default_pvs:
            for prop, value in default_pvs.items():
                if (pv_utils.is_valid_property(
                        prop, self._config.get('schemaless', False)) and
                        value and prop not in pvs):
                    pvs[prop] = value
        return pvs

    def get_valid_pvs(self, pvs: dict) -> dict:
        """Return all valid property:value in the dictionary.

    Args:
      pvs: dictionary of property:value mappings. property is considered valid
        if if begins with a lower case or config for schemaless statvars is
        enabled. schemaless statvars can have capitalized properties that are
        commented out in the mcf. value is considered valid if it has no
        unresolved references.

    Returns:
      dictionary of valid property:value mappings
    """
        valid_pvs = {}
        for prop, value in pvs.items():
            if pv_utils.is_valid_property(
                    prop, self._config.get(
                        'schemaless',
                        False)) and pv_utils.is_valid_value(value):
                valid_pvs[prop] = value
        return valid_pvs

    def add_dict_to_map(
        self,
        key: str,
        pvs: dict,
        pv_map: dict,
        duplicate_prop: str = None,
        allow_equal_pvs: bool = True,
        ignore_props: list = [],
    ) -> bool:
        """Returns true if the key:pvs is added to the pv_map,

      False if key already exists and values don't match.
    Args:
      key: the key to be added to the pv_map
      pvs: the dictionary value mapped to the key
      pv_map: (output) dictionary to which key is to be added.
      duplicate_prop: In case of duplicate entries, add this duplicate prop
        mapped to the pvs dict into the existing entry.
      allow_equal_pvs: If True duplicate pvs with the same property:value is not
        considered an error.

    Returns:
      True if the key:pvs tuple was added to the pv_map.
    """
        if key in pv_map:
            has_diff, diff_str, added, deleted, modified = diff_mcf_node_pvs(
                self.get_valid_pvs(pvs),
                self.get_valid_pvs(pv_map[key]),
                config={'ignore_property': ignore_props},
            )
            if allow_equal_pvs and not has_diff:
                return True
            else:
                logging.level_debug() and logging.debug(
                    f'Duplicate entry {key} in map for {pvs}, diff: {diff_str}')
                if duplicate_prop:
                    map_pvs = pv_map[key]
                    if duplicate_prop not in map_pvs:
                        map_pvs[duplicate_prop] = []
                    map_pvs[duplicate_prop].append(pvs)
                return False
        pv_map[key] = pvs
        return True

    def _get_dcid_term_for_pv(self, prop: str, value: str) -> str:
        """Returns the dcid term for the property:value to be used in the node's dcid.

    Args:
      prop: the property label
      value: value of the property

    Returns:
      string to be used for this PV in the dcid.
    For schemaless statvars, the property and value is used for the dcid term.
    Otherwise the term is constructed from the value.
    """
        if not value:
            return _capitalize_first_char(prop)

        if not isinstance(value, str):
            # For numeric values use the property and value.
            return _capitalize_first_char(
                re.sub(r'[^A-Za-z0-9_/]', '_',
                       f'{prop}_{value}').replace('__', '_'))
        prefix = ''
        value = strip_namespace(value)
        if self._config.get('schemaless', False):
            # Add the property prefix for schemaless PVs.
            if not pv_utils.is_valid_property(
                    prop, schemaless=False) and pv_utils.is_valid_property(
                        prop, schemaless=True):
                prop = prop.removeprefix('# ')
                if prop != value:
                    prefix = _capitalize_first_char(f'{prop}_')
        if value[0] == '[':
            # Generate term for quantity range with start and optional end, unit.
            quantity_pat = (
                r'\[ *(?P<unit1>[A-Z][A-Za-z0-9_/]*)? *(?P<start>[0-9\.]+|-)?'
                r' *(?P<end>[0-9\.]+|-)? *(?P<unit2>[A-Z][A-Za-z0-9_]*)? *\]')
            matches = re.search(quantity_pat, value)
            if matches:
                match_dict = matches.groupdict()
                if match_dict:
                    start = match_dict.get('start', None)
                    end = match_dict.get('end', None)
                    unit1 = match_dict.get('unit1', None)
                    unit2 = match_dict.get('unit2', None)
                    unit = ''
                    if unit1:
                        unit = f'{unit1}'
                    elif unit2:
                        unit = f'{unit2}'
                    value_term = ''
                    if start == '-' and end:
                        value_term = f'{end}OrLess'
                    elif start and end == '-':
                        value_term = f'{start}OrMore'
                    elif not end:
                        value_term = f'{start}'
                    else:
                        value_term = f'{start}To{end}'
                    value_term += unit
                    return prefix + value_term
        return prefix + _capitalize_first_char(value)

    def _get_schemaless_statvar_props(self, pvs: dict) -> list:
        """Returns a list of schemaless properties from the dictionary of property:values.

    Properties not defined in schema can be capitalized or commented.
    """
        schemaless_props = []
        for prop in pvs.keys():
            if prop == 'Node' or pv_utils.is_valid_property(prop,
                                                            schemaless=False):
                continue
            if pv_utils.is_valid_property(
                    prop, schemaless=True) or prop.startswith('# '):
                # TODO: skip internal props '#...' instead of checking prefix '# '
                schemaless_props.append(prop)
        return schemaless_props

    def _construct_new_statvar_dcid(self, pvs: dict,
                                    dcid_ignore_props: list) -> str:
        """Constructs a new StatVar DCID string from property-values.

        This method is called when a DCID is not provided by other means (e.g.,
        from input, existing StatVar, or the external `get_statvar_dcid` generator).

        The DCID is built by concatenating terms derived from property-value pairs.
        The order of terms is influenced by `default_statvar_pvs`.
        Properties in `dcid_ignore_props` and values in `statvar_dcid_ignore_values`
        are excluded.
        Special handling exists for `measurementDenominator`.

        Args:
            pvs: The dictionary of property-values for the StatVar.
            dcid_ignore_props: A list of properties to ignore during DCID construction.

        Returns:
            The generated DCID string (without dc: namespace).
        """
        dcid_terms = []
        props = list(pvs.keys())
        dcid_ignore_values = self._config.get('statvar_dcid_ignore_values', [])
        for p in self._config.get('default_statvar_pvs', {}).keys():
            if p in props and p not in dcid_ignore_props:
                props.remove(p)
                value = strip_namespace(pvs[p])
                if value and value not in dcid_ignore_values:
                    dcid_terms.append(self._get_dcid_term_for_pv(p, value))
        dcid_suffixes = []
        if 'measurementDenominator' in props:
            dcid_suffixes.append('AsAFractionOf')
            dcid_suffixes.append(strip_namespace(pvs['measurementDenominator']))
            props.remove('measurementDenominator')
        for p in sorted(props, key=str.casefold):
            if p not in dcid_ignore_props:
                value = pvs[p]
                if pv_utils.is_valid_property(
                        p, self._config.get(
                            'schemaless',
                            False)) and pv_utils.is_valid_value(value):
                    dcid_terms.append(self._get_dcid_term_for_pv(p, value))
        dcid_terms.extend(dcid_suffixes)
        dcid = re.sub(r'[^A-Za-z_0-9/_-]+', '_', '_'.join(dcid_terms))
        dcid = re.sub(r'_$', '', dcid)
        return dcid

    def generate_statvar_dcid(self, pvs: dict) -> str:
        """Return the dcid for the statvar.

    Args:
      pvs: dictionary of property:values

    Returns:
      dcid string.
    For normal statvars, uses statvar_dcid_generator.py
    For schameless statvars, uses the local implementation to add prop and
    value.
    """
        dcid = pvs.get('dcid', pvs.get('Node', ''))
        if dcid:
            return dcid
        # Check if a statvar already exists.
        pvs = self._get_exisisting_statvar(pvs)
        dcid = pvs.get('dcid', pvs.get('Node', ''))
        if dcid:
            logging.level_debug() and logging.log(
                2, f'Reusing existing statvar {dcid} for {pvs}')
            return dcid

        # Use the statvar_dcid_generator for statvars with defined properties.
        dcid_ignore_props = self._config.get(
            'statvar_dcid_ignore_properties',
            [
                'description', 'name', 'nameWithLanguage', 'descriptionUrl',
                'alternateName'
            ],
        )
        if not self._config.get(
                'schemaless',
                False) or not self._get_schemaless_statvar_props(pvs):
            try:
                dcid = get_statvar_dcid(pvs, ignore_props=dcid_ignore_props)
                dcid = re.sub(r'[^A-Za-z_0-9/_\.-]+', '_', dcid)
            except TypeError as e:
                logging.error(
                    f'Failed to generate dcid for statvar:{pvs}, error: {e}')
                dcid = ''
        if not dcid:
            dcid = self._construct_new_statvar_dcid(pvs, dcid_ignore_props)

        # Check if the dcid is remapped.
        remap_dcid = self._statvar_dcid_remap.get(strip_namespace(dcid), '')
        if remap_dcid:
            logging.level_debug() and logging.log(
                2, f'Remapped {dcid} to {remap_dcid} for {pvs}')
            self._counters.add_counter(f'remapped-statvar-dcid', 1, remap_dcid)
            dcid = remap_dcid
        pvs['Node'] = add_namespace(dcid)
        logging.level_debug() and logging.log(
            2, f'Generated dcid {dcid} for {pvs}')
        return dcid

    def remove_undefined_properties(
        self,
        pv_map_dict: dict,
        ignore_props: list = [],
        comment_removed_props: bool = False,
    ) -> list:
        """Remove any property:value tuples with undefined property or values

    Returns list of properties removed.
    Args:
      pv_map_dict: dictionary of dcids mapped to a dictionary of property:values
      ignore_props: ignore any of these properties
      comment_removed_props: if set to True, any property not defined in schema
        is commented out. This is useful for a schemaless statvar with a mix of
        defined and undefined properties.

    Returns:
      list of properties removed.
      the pv_map_dict is also updated in place.

    Batches property and values to be looked up in the DC API.
    """
        # Collect all property and values to be checked in schema.
        props_removed = []
        lookup_dcids = set()
        for namespace, pv_map in pv_map_dict.items():
            for key, pvs in pv_map.items():
                # Add Node dcids as defined in cache.
                dcid = pvs.get('Node', '')
                dcid = pvs.get('dcid', dcid)
                if dcid:
                    dcid = strip_namespace(dcid)
                    self._dc_api_ids_cache[dcid] = True
                # Collect property and values not in cache and to be looked up.
                for prop, value in pvs.items():
                    if value:
                        value = strip_namespace(value)
                    if prop in ignore_props:
                        continue
                    if pv_utils.is_valid_property(
                            prop, self._config.get('schemaless', False)):
                        lookup_dcids.add(prop)
                        if pv_utils.is_schema_node(value):
                            lookup_dcids.add(value)

        # Lookup new Ids on the DC API.
        if lookup_dcids:
            api_lookup_dcids = [
                dcid for dcid in lookup_dcids
                if dcid not in self._dc_api_ids_cache
            ]
            if api_lookup_dcids:
                logging.level_debug() and logging.log(
                    2,
                    f'Looking up DC API for dcids: {api_lookup_dcids} from PV map.'
                )
                schema_nodes = dc_api_is_defined_dcid(
                    api_lookup_dcids, self._config.get_configs())
                # Update cache
                self._dc_api_ids_cache.update(schema_nodes)
                logging.level_debug() and logging.log(
                    2,
                    f'Got {len(schema_nodes)} of {len(api_lookup_dcids)} dcids from DC'
                    ' API.')

        # Remove any PVs not in schema.
        counter_prefix = 'error-pvmap-dropped'
        if comment_removed_props:
            counter_prefix = 'warning-commented-pvmap'
        for namespace, pv_map in pv_map_dict.items():
            for key, pvs in pv_map.items():
                for prop in list(pvs.keys()):
                    if prop in ignore_props:
                        continue
                    value = pvs[prop]
                    # Remove property looked up in schema but not defined.
                    if prop in lookup_dcids and not self._dc_api_ids_cache.get(
                            prop, False):
                        logging.error(
                            f'Removing undefined property "{prop}" from PV'
                            f' Map:{namespace}:{key}:{prop}:{value}')
                        value = pvs.pop(prop)
                        if comment_removed_props:
                            pvs[f'# {prop}: '] = value
                        self._counters.add_counter(
                            f'{counter_prefix}-undefined-property', 1, prop)
                    # Remove value looked up in schema but not defined.
                    if value in lookup_dcids and not self._dc_api_ids_cache.get(
                            value, False):
                        logging.error(
                            f'Removing undefined value "{value}" from PV'
                            f' Map:{namespace}:{key}:{prop}:{value}')
                        if prop in pvs:
                            pvs.pop(prop)
                        if comment_removed_props:
                            pvs[f'# {prop}: '] = value
                            props_removed.append(prop)
                        self._counters.add_counter(
                            f'{counter_prefix}-undefined-value', 1, prop)
                self._counters.add_counter(f'pvmap-defined-properties',
                                           len(pvs))
        return props_removed

    def convert_to_schemaless_statvar(self, pvs: dict) -> dict:
        """Returns the property:values dictionary after converting to schemaless statvar.

      If there are any properties starting with capital letters,
      they are commented and measuredProperty is set to the statvar dcid.
    Args:
      pvs: dictionary of property:values that is modified.

    Returns:
      True if the pvs were converted to schemaless.
    """
        logging.level_debug() and logging.log(
            2, f'Converting to schemaless statvar {pvs}')
        schemaless_props = self._get_schemaless_statvar_props(pvs)

        # Got some capitalized properties.
        # Convert to schemaless PV:
        # - set measuredProperty to the dcid.
        # - comment out any capitalized (invalid) property
        dcid = self.generate_statvar_dcid(pvs)
        for prop in schemaless_props:
            if prop[0] != '#':
                value = pvs.pop(prop)
                pvs[f'# {prop}: '] = value
        # Comment out any PVs with undefined property or value.
        if self._config.get('schemaless_statvar_comment_undefined_pvs', False):
            schemaless_props.extend(
                self.remove_undefined_properties(
                    {'StatVar': {
                        'SV': pvs
                    }},
                    ignore_props=['Node'],
                    comment_removed_props=True,
                ))
        if schemaless_props:
            # Found some schemaless properties. Change mProp to statvar dcid.
            if 'measuredProperty' in pvs:
                pvs['# measuredProperty:'] = pvs.pop('measuredProperty')
            pvs['measuredProperty'] = add_namespace(dcid)
        logging.level_debug() and logging.log(
            2, f'Generated schemaless statvar {pvs}')
        return len(schemaless_props) > 0

    def add_statvar(self, statvar_dcid: str, statvar_pvs: dict) -> bool:
        """Returns True if the statvar pvs are valid and is added to the map.

    Args:
      statvar_pvs: dictionary of property:values for the statvar

    Returns:
      True if statvar is valid, not a duplicate and was added to the map.
      The pvs may also be modified.
      A dcid is added to the statvar if not already set.
    """
        pvs = self.get_valid_pvs(statvar_pvs)
        if not statvar_dcid:
            statvar_dcid = strip_namespace(self.generate_statvar_dcid(pvs))
        pvs['Node'] = add_namespace(statvar_dcid)
        is_schemaless = False
        if self._config.get('schemaless', False):
            is_schemaless = self.convert_to_schemaless_statvar(pvs)
        # Check if all the required statvar properties are present.
        if pvs:
            missing_props = set(
                self._config.get('required_statvar_properties',
                                 [])).difference(set(pvs.keys()))
            if missing_props:
                logging.error(
                    f'Missing statvar properties {missing_props} in {pvs}')
                self._counters.add_counter(
                    f'error-statvar-missing-property',
                    1,
                    f'{statvar_dcid}:missing-{missing_props}',
                )
                pvs['#ErrorMissingStatVarProperties'] = missing_props
                return False
        if not self.add_dict_to_map(
                statvar_dcid,
                pvs,
                self._statvars_map,
                self._config.get('duplicate_statvars_key'),
                allow_equal_pvs=True,
                ignore_props=self._config.get(
                    'statvar_dcid_ignore_properties',
                    [
                        'typeOf', 'description', 'name', 'nameWithLanguage',
                        'descriptionUrl', 'alternateName'
                    ],
                ),
        ):
            logging.error(
                f'Cannot add duplicate statvars for {statvar_dcid}: old:'
                f' {self._statvars_map[statvar_dcid]}, new: {pvs}')
            self._counters.add_counter(f'error-duplicate-statvars', 1,
                                       statvar_dcid)
            return False
        logging.level_debug() and logging.debug(f'Adding statvar {pvs}')
        self._counters.add_counter('generated-statvars', 1, statvar_dcid)
        self._counters.set_counter('generated-unique-statvars',
                                   len(self._statvars_map))
        if is_schemaless:
            self._counters.add_counter('generated-statvars-schemaless', 1,
                                       statvar_dcid)
        return True

    def get_svobs_key(self, pvs: dict) -> str:
        """Returns the key for SVObs concatenating all PVs, except value.

    Args:
      pvs: dictionary of property:values for the statvar obs.

    Returns
      string fingerprint for the SVobs.
    """
        key_pvs = [
            f'{p}={pvs[p]}' for p in sorted(pvs.keys())
            if pv_utils.is_valid_property(
                p, self._config.get('schemaless', False)) and pv_utils.
            is_valid_value(pvs[p]) and p not in self._IGNORE_SVOBS_KEY_PVS
        ]
        return ';'.join(key_pvs)

    def aggregate_value(
        self,
        aggregation_type: str,
        current_pvs: str,
        new_pvs: dict,
        aggregate_property: str,
    ):
        """Aggregate values for the given aggregate_property from new_pvs into current_pvs.

    Args:
      aggregation_type: string which is one of the supported aggregation types:
        sum, min, max, list, first, last
      current_pvs: Existing property:values in the map.
      new_pvs: New pvs not in the map.
      aggregate_property: property whoese values are to be aggregated.

    Returns:
      True if aggregation was successful.
    """
        current_value = get_numeric_value(current_pvs.get(
            aggregate_property, 0))
        new_value = get_numeric_value(new_pvs.get(aggregate_property, 0))
        if current_value is None or new_value is None:
            logging.error(
                f'Invalid values to aggregate in {current_pvs}, {new_pvs}')
            self._counters.add_counter(f'error-aggregate-invalid-values', 1)
            return False
        aggregation_funcs = {
            'sum': lambda a, b: a + b,
            'min': lambda a, b: min(a, b),
            'max': lambda a, b: max(a, b),
            'list': lambda a, b: f'{a},{b}',
            'first': lambda a, b: a,
            'last': lambda a, b: b,
        }
        if aggregation_type:
            aggregation_type = aggregation_type.lower()
        if aggregation_type == 'mean':
            count_property = f'#Count-{aggregate_property}'
            current_count = current_pvs.get(count_property, 1)
            updated_value = (new_value + current_value * current_count) / (
                current_count + 1)
            current_pvs[aggregate_property] = updated_value
            current_pvs[count_property] = current_count + 1
            current_pvs['statType'] = 'dcs:meanValue'
        elif aggregation_type in aggregation_funcs:
            updated_value = aggregation_funcs[aggregation_type](current_value,
                                                                new_value)
            current_pvs[aggregate_property] = updated_value
        else:
            logging.error(
                f'Unsupported aggregation {aggregation_type} for {current_pvs},'
                f' {new_pvs}')
            self._counters.add_counter(
                f'error-aggregate-unsupported-{aggregation_type}', 1)
            return False
        merged_pvs_prop = self._config.get('merged_pvs_property',
                                           '#MergedSVObs')
        if merged_pvs_prop:
            if merged_pvs_prop not in current_pvs:
                current_pvs[merged_pvs_prop] = []
            current_pvs[merged_pvs_prop].append(new_pvs)
        # Set measurement method
        mmethod = strip_namespace(current_pvs.get('measurementMethod', ''))
        if not mmethod:
            current_pvs['measurementMethod'] = 'dcs:DataCommonsAggregate'
        elif not mmethod.startswith(
                'dcAggregate/') and mmethod != 'DataCommonsAggregate':
            current_pvs['measurementMethod'] = f'dcs:dcAggregate/{mmethod}'
        dup_svobs_key = self._config.get('duplicate_svobs_key')
        if dup_svobs_key in current_pvs:
            # Dups have been merged for this SVObs.
            # Remove #Error tag so it is not flagged as an error.
            current_pvs.pop(dup_svobs_key)
        self._counters.add_counter(f'aggregated-pvs-{aggregation_type}', 1)
        logging.level_debug() and logging.log(
            2, f'Aggregation: {aggregation_type}:{aggregate_property}: ' +
            f'value {current_value}, {new_value} into {updated_value} ' +
            f'from {current_pvs} and {new_pvs}')
        return True

    def set_statvar_dup_svobs(self, svobs_key: str, svobs: dict):
        """Add a duplicate SVObs for a statvar.

    Statvars with duplicate observations are likely missing constraint
    properties. The statvar and related observations will be dropped from the
    output.
    """
        # Check if SVObs aggregation is enabled.
        if svobs_key not in self._statvar_obs_map:
            # Corrected log.error to logging.error
            logging.error(f'Unexpected missing SVObs: {svobs_key}:{svobs}')
            statvar_dcid = strip_namespace(svobs.get(
                'variableMeasured', ''))  # Define statvar_dcid for counter
            self._counters.add_counter(
                'error-statvar-obs-missing-for-dup-svobs', 1, statvar_dcid)
            return
        existing_svobs = self._statvar_obs_map.get(svobs_key, None)
        if not existing_svobs:
            logging.error(f'Missing duplicate svobs for key {svobs_key}')
            return
        dup_svobs_key = self._config.get('duplicate_svobs_key')
        if dup_svobs_key not in existing_svobs:
            existing_svobs[dup_svobs_key] = []
        # Add the duplicate SVObs to the original SVObs.
        existing_svobs[dup_svobs_key].append(svobs)
        statvar_dcid = strip_namespace(svobs.get('variableMeasured', None))
        if not statvar_dcid:
            logging.error(f'Missing Statvar dcid for duplicate svobs {svobs}')
            self._counters.add_counter(
                'error-statvar-dcid-missing-for-dup-svobs', 1, statvar_dcid)
            return
        if statvar_dcid not in self._statvars_map:
            logging.error(
                f'Missing Statvar {statvar_dcid} for duplicate svobs {svobs}')
            self._counters.add_counter('error-statvar-missing-for-dup-svobs', 1,
                                       statvar_dcid)
            return
        # Add the duplicate SVObs to the statvar
        if self._config.get('drop_statvars_with_dup_svobs', True):
            statvar = self._statvars_map[statvar_dcid]
            if dup_svobs_key not in statvar:
                statvar[dup_svobs_key] = []
                self._counters.add_counter('error-statvar-with-dup-svobs', 1,
                                           statvar_dcid)
            if not svobs_key:
                svobs_key = self.get_svobs_key(svobs)
            statvar[dup_svobs_key].append(svobs_key)
            logging.level_debug() and logging.log(
                2, f'Added duplicate SVObs to statvar {statvar_dcid}:'
                f' {statvar[dup_svobs_key]}')

    def add_statvar_obs(self, pvs: dict, has_output_column: bool = False):
        # Check if the required properties are present.
        missing_props = set(
            self._config.get('required_statvarobs_properties',
                             [])).difference(set(pvs.keys()))
        if missing_props and not has_output_column:
            logging.error(f'Missing SVObs properties {missing_props} in {pvs}')
            self._counters.add_counter(f'error-svobs-missing-property', 1,
                                       f'{missing_props}')
            return False
        # Check if the SVObs already exists.
        allow_equal_pvs = True
        svobs_aggregation = self._config.get('aggregate_duplicate_svobs', None)
        svobs_aggregation = pvs.get(
            self._config.get('aggregate_key', '#Aggregate'), svobs_aggregation)
        if svobs_aggregation:
            # PVs with same value are not considered same, need to be aggregated.
            allow_equal_pvs = False
        svobs_key = self.get_svobs_key(pvs)
        if not self.add_dict_to_map(
                svobs_key,
                pvs,
                self._statvar_obs_map,
                self._config.get('duplicate_svobs_key'),
                allow_equal_pvs=allow_equal_pvs,
        ):
            existing_svobs = self._statvar_obs_map.get(svobs_key, None)
            if not existing_svobs:
                logging.error(f'Missing duplicate svobs for key {svobs_key}')
                return False
            if svobs_aggregation and self.aggregate_value(
                    svobs_aggregation, existing_svobs, pvs, 'value'):
                self._counters.add_counter(
                    f'aggregated-svobs-{svobs_aggregation}',
                    1,
                    pvs.get('variableMeasured', ''),
                )
                return True

            logging.error('Duplicate SVObs with mismatched values:'
                          f' {self._statvar_obs_map[svobs_key]} != {pvs}')
            self._counters.add_counter(f'error-mismatched-svobs', 1,
                                       pvs.get('variableMeasured', ''))
            self.set_statvar_dup_svobs(svobs_key, pvs)
            return False
        self._counters.add_counter('svobs-added', 1,
                                   pvs.get('variableMeasured', ''))

        # Count distinct values for each svobs prop.
        all_svobs_props = set(self._statvar_obs_props.keys())
        all_svobs_props.update(pvs.keys())
        for prop in all_svobs_props:
            value = pvs.get(prop, '')
            if prop not in self._statvar_obs_props:
                self._statvar_obs_props[prop] = []
            value_list = self._statvar_obs_props[prop]
            if value not in value_list and len(value_list) < 2:
                value_list.append(value)
        return True

    def is_valid_pvs(self, pvs: dict) -> bool:
        """Returns True if there are no error PVs."""
        dup_svobs_key = self._config.get('duplicate_svobs_key')
        dup_statvars_key = self._config.get('duplicate_statvars_key')
        for prop in pvs.keys():
            if prop in [dup_svobs_key, dup_statvars_key]:
                logging.error(f'Error duplicate property {prop} in {pvs}')
                return False
            if prop.startswith('#Error'):
                logging.error(f'Error property {prop} in {pvs}')
                return False
        return True

    def is_valid_statvar(self, pvs: dict) -> bool:
        """Returns True if the statvar is valid."""
        # Check if there are any duplicate StatVars or SVObs or errors.
        if not self.is_valid_pvs(pvs):
            logging.error(f'Invalid StatVar: {pvs}')
            return False
        # Check if the statvar has all mandatory properties.
        missing_props = set(self._config.get('required_statvar_properties',
                                             [])).difference(set(pvs.keys()))
        if missing_props:
            logging.error(
                f'Missing properties {missing_props} for statvar {pvs}')
            return False

        statvar_dcid = pvs.get('Node', None)
        statvar_dcid = pvs.get('dcid', statvar_dcid)
        if not statvar_dcid:
            statvar_dcid = self.generate_statvar_dcid(pvs)
        if not statvar_dcid:
            logging.error(f'Missing dcid for statvar {pvs}')
            return False
        pvs['Node'] = add_namespace(statvar_dcid)

        # Check if the statvar has any error properties.
        error_props = [
            f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')
        ]
        if error_props:
            logging.error(f'Statvar {pvs} with error properties {error_props}')
            return False

        # TODO: Check if the statvar has any blocked properties
        return True

    def is_valid_svobs(self, pvs: dict) -> bool:
        """Returns True if the SVObs is valid and refers to an existing StatVar."""
        if not self.is_valid_pvs(pvs):
            logging.error(f'Invalid SVObs: {pvs}')
            return False
        # Check if the StatVar exists.
        statvar_dcid = strip_namespace(pvs.get('variableMeasured', ''))
        if not statvar_dcid and not _pvs_has_any_prop(
                pvs, self._config.get('output_columns')):
            logging.error(f'Missing statvar_dcid for SVObs {pvs}')
            return False
        if statvar_dcid not in self._statvars_map:
            logging.log(
                2, f'Missing {statvar_dcid} in StatVarMap for SVObs {pvs}')
        # Check if the statvarobs has any error properties.
        error_props = [
            f'{p}:{v}' for p, v in pvs.items() if p.startswith('#Err')
        ]
        if error_props:
            logging.error(
                f'StatvarObs {pvs} with error properties {error_props}')
        return True

    def drop_statvars_without_svobs(self):
        """Drop any Statvars without any observations."""
        # Get statvars with observations
        statvars_with_obs = set()
        for svobs_key, pvs in self._statvar_obs_map.items():
            statvar_dcid = strip_namespace(pvs.get('variableMeasured', None))
            if statvar_dcid:
                statvars_with_obs.add(statvar_dcid)
        # Get any references to other statvars from stavtars with obs.
        for statvar in statvars_with_obs:
            pvs = self._statvars_map.get(statvar, {})
            for prop, value in pvs.items():
                if value in self._statvars_map:  # Check if value is a dcid of another statvar
                    statvars_with_obs.add(
                        strip_namespace(value))  # Add referenced statvar
                    break
        # Drop statvars without observations or references.
        drop_statvars = set(
            self._statvars_map.keys()).difference(statvars_with_obs)
        for statvar_dcid in drop_statvars:
            pvs = self._statvars_map.pop(statvar_dcid)
            logging.error(
                f'Dropping statvar {statvar_dcid} without SVObs {pvs}')
            self._counters.add_counter('dropped-statvars-without-svobs', 1,
                                       statvar_dcid)
        return

    def drop_invalid_statvars(self):
        """Drop invalid statvars and corresponding SVObs.

    Statvars dropped include: - statvars with missing required properties -
    statvars with duplicate SVObs. - statvars with any dropped properties
    """
        # Collect valid statvars
        valid_statvars = {}
        for statvar, pvs in self._statvars_map.items():
            if self.is_valid_statvar(pvs):
                valid_statvars[statvar] = pvs
            else:
                self._counters.add_counter(f'dropped-invalid-statvars', 1,
                                           statvar)
        self._statvars_map = valid_statvars

        # Collect valid SVObs with valid statvars.
        valid_svobs = {}
        for svobs_key, pvs in self._statvar_obs_map.items():
            if self.is_valid_svobs(pvs):
                valid_svobs[svobs_key] = pvs
            else:
                self._counters.add_counter(f'dropped-invalid-svobs', 1,
                                           svobs_key)
        self._statvar_obs_map = valid_svobs

        # Drop any statvars without any observations.
        if self._config.get('drop_statvars_without_svobs', True):
            self.drop_statvars_without_svobs()

    def write_statvars_mcf(
        self,
        filename: str,
        mode: str = 'w',
        stat_var_nodes: dict = None,
        header: str = None,
    ):
        """Save the statvars into an MCF file."""
        if not stat_var_nodes:
            stat_var_nodes = self._statvars_map
        if self._config.get('output_only_new_statvars', False):
            num_statvars = len(stat_var_nodes)
            stat_var_nodes = drop_existing_mcf_nodes(
                stat_var_nodes,
                self._config.get(
                    'statvar_diff_config',
                    {
                        # Ignore properties that don't affect statvar dcid.
                        'ignore_property': [
                            'constraintProperties',
                            'memberOf',
                            'member',
                            'provenance',
                            'relevantVariable',
                        ],
                        # Retain SVs with new PVs like name
                        'output_nodes_with_additions': True,
                    },
                ),
                self._counters,
            )
            removed_statvars = num_statvars - len(stat_var_nodes)
            self._counters.add_counter('dropped-output-statvars-mcf',
                                       removed_statvars)
            logging.info(f'Removed {removed_statvars} existing nodes from'
                         f' {num_statvars} statvars')

        if not stat_var_nodes:
            # No new statvars to output.
            return

        # Generate statvar names
        if self._config.get('google_api_key', '') and self._config.get(
                'llm_generate_statvar_name', False):
            pass
            # TODO: uncomment once LLM tools are merged.
            # Generate names using LLM
            # llm_statvar_name_generator.llm_generate_names(
            #    stat_var_nodes, '', self._config, self._counters)
        if self._config.get('generate_statvar_name', False):
            # Generate name from PVs
            for dcid, pvs in stat_var_nodes.items():
                if 'name' not in pvs and 'alternateName' not in pvs:
                    self._counters.add_counter('statvar-names-generated', 1,
                                               dcid)
                    generate_statvar_name(pvs, self._config.get_configs())

        commandline = ' '.join(sys.argv)
        if not header:
            header = (f'# Auto generated using command: "{commandline}" on'
                      f' {datetime.datetime.now()}\n')
        logging.info(
            f'Generating {len(stat_var_nodes)} statvars into {filename}')

        write_mcf_nodes(
            [stat_var_nodes],
            filename=filename,
            mode=mode,
            ignore_comments=not self._config.get('schemaless', False),
            sort=True,
            header=header,
        )
        self._counters.add_counter(
            'output-statvars-mcf',
            len(self._statvars_map
               ),  # Should be len(stat_var_nodes) if only outputting a subset
            os.path.basename(filename),
        )

        # Sanity check nodes
        sanity_errors = sanity_check_nodes(stat_var_nodes,
                                           config=self._config,
                                           counters=self._counters)

        # Generate new schema MCF
        if self._config.get('generate_schema_mcf', False):
            schema_mcf_file = self._config.get(
                'output_schema_mcf',
                file_util.file_get_name(filename,
                                        suffix='_schema',
                                        file_ext='.mcf'))
            new_schema_nodes = generate_schema_nodes(
                stat_var_nodes,
                self._config.get('existing_schema_mcf'),
                schema_mcf_file,
                self._config.get_configs(),
            )
            if new_schema_nodes:
                logging.info(
                    f'Generating new schema for {len(new_schema_nodes)} nodes into'
                    f' {schema_mcf_file}')
                write_mcf_nodes([new_schema_nodes],
                                filename=schema_mcf_file,
                                mode='w')
                new_schema_errors = sanity_check_nodes(new_schema_nodes,
                                                       config=self._config,
                                                       counters=self._counters)
                for err_key, err_val in new_schema_errors.items(
                ):  # Iterate through items
                    sanity_errors[len(
                        sanity_errors)] = err_val  # Append error correctly
            self._counters.add_counter(
                'output-new-schema-mcf',
                len(new_schema_nodes),
                os.path.basename(schema_mcf_file),
            )

        # Write any schema sanity errors
        if sanity_errors:
            error_output = self._config.get(
                'output_sanity_check',
                file_util.file_get_name(filename, '_sanity_errors', '.txt'))
            num_errors = len(sanity_errors)
            if not error_output:
                logging.info(f'Got {num_errors} errors: {sanity_errors}')
            else:
                logging.info(f'Writing {num_errors} errors into {error_output}')
                file_util.file_write_py_dict(sanity_errors, error_output)

    def get_constant_svobs_pvs(self) -> dict:
        """Return PVs that have a fixed value across SVObs."""
        if len(self._statvar_obs_map) < 2:
            return {'typeOf': 'dcs:StatVarObservation'}
        pvs = {}
        for prop, value_list in self._statvar_obs_props.items():
            if len(value_list) == 1:
                pvs[prop] = value_list[0]
        return pvs

    def get_multi_value_svobs_pvs(self) -> dict:
        """Return SVObs properties that have multiple values."""
        svobs_pvs = set(self._statvar_obs_props)
        return list(svobs_pvs.difference(self.get_constant_svobs_pvs().keys()))

    def get_statvar_obs_columns(self) -> list:
        """Returns the list of columns for statvar Obs."""
        columns = self._config.get('output_columns', None)
        if not columns:
            if self._config.get('skip_constant_csv_columns', False):
                columns = self.get_multi_value_svobs_pvs()
            else:
                columns = list(self._statvar_obs_props)
            if not self._config.get('debug', False):
                # Remove debug columns.
                columns_to_remove = []
                for col in columns:
                    if not pv_utils.is_valid_property(
                            col, self._config.get('schemaless', False)):
                        columns_to_remove.append(col)
                for col in columns_to_remove:
                    columns.remove(col)

                input_column = self._config.get('input_reference_column')
                if input_column in columns:
                    columns.remove(input_column)
        # Return output columns in order configured.
        output_columns = []
        for col in self._config.get('default_svobs_pvs', {}).keys():
            if col in columns:
                output_columns.append(col)
        # Add any additional valid columns.
        debug_columns = []
        for col in columns:
            if col not in output_columns:
                if pv_utils.is_valid_property(
                        col, self._config.get('schemaless', False)):
                    output_columns.append(col)
                else:
                    debug_columns.append(col)
        output_columns.extend(debug_columns)
        return output_columns

    def format_svobs(self, svobs: dict) -> dict:
        """Returns dict for SVObs with formatted values."""
        formatted_svobs = {}
        for prop, value in svobs.items():
            formatted_value = value
            numeric_value = get_numeric_value(value)
            if numeric_value is not None:  # Check if conversion was successful
                formatted_value = _str_from_number(
                    numeric_value,
                    precision_digits=self._config.get('output_precision_digits',
                                                      5),
                )
            elif isinstance(value, str) and value:
                value_stripped = value.strip()  # Use a different variable
                if value_stripped and value_stripped[0] != '"':
                    if ' ' in value_stripped or ',' in value_stripped:
                        # Add quote for values with spaces.
                        formatted_value = f'"{value_stripped}"'
                    else:
                        formatted_value = value_stripped  # Use stripped if no quotes needed
                elif not value_stripped:  # Handle empty string after strip
                    formatted_value = value_stripped

            formatted_svobs[prop] = formatted_value
        return formatted_svobs

    def filter_svobs(self):
        """Filter SVObs to remove outliers."""
        filter_data_svobs(self._statvar_obs_map, self._config, self._counters)

    def write_statvar_obs_csv(
        self,
        output_csv: str,
        mode: str = 'w',
        columns: list = None,
        output_tmcf_file: str = '',
    ):
        """Save the StatVar observations into a CSV file and tMCF."""
        if not columns:
            columns = self.get_statvar_obs_columns()

        logging.info(
            f'Writing {len(self._statvar_obs_map)} SVObs  into {output_csv} with'
            f' {columns}')
        svobs_unique_values = {}
        with file_util.FileIO(output_csv, mode, newline='') as f_out_csv:
            csv_writer = csv.DictWriter(
                f_out_csv,
                fieldnames=columns,
                extrasaction='ignore',
                doublequote=False,
                escapechar='\\',
                lineterminator='\n',
            )
            if mode == 'w':
                csv_writer.writeheader()
            for key, svobs in self._statvar_obs_map.items():
                format_svobs = self.format_svobs(svobs)
                csv_writer.writerow(format_svobs)
                for p, v in svobs.items():
                    if p in columns or pv_utils.is_valid_property(
                            p, self._config.get('schemaless', False)):
                        if p not in svobs_unique_values:
                            svobs_unique_values[p] = set()
                        svobs_unique_values[p].add(v)

        self._counters.add_counter('output-svobs-csv-rows',
                                   len(self._statvar_obs_map), output_csv)
        for p, s in svobs_unique_values.items():
            self._counters.add_counter(f'output-svobs-unique-{p}', len(s))

        if output_tmcf_file:
            self.write_statvar_obs_tmcf(output_tmcf_file, columns=columns)

    def write_statvar_obs_tmcf(
        self,
        filename: str,
        mode: str = 'w',
        columns: list = None,
        constant_pvs: dict = None,
        dataset_name: str = None,
    ):
        """Generate the tMCF for the listed StatVar observation columns."""
        output_tmcf = self._config.get('output_tmcf', None)
        if not output_tmcf:
            if not dataset_name:
                if file_util.file_is_local(filename):
                    dataset, ext = os.path.splitext(filename)
                    dataset_name = os.path.basename(dataset)
                else:
                    dataset_name = 'Data'
            if not columns:
                columns = self.get_multi_value_svobs_pvs()
            if not constant_pvs and self._config.get(
                    'skip_constant_csv_columns', True):
                constant_pvs = self.get_constant_svobs_pvs()

            logging.info(
                f'Writing SVObs tmcf {filename} with {columns} into {filename}.'
            )

            tmcf = [f'Node: E:{dataset_name}->E0']
            default_svobs_pvs = dict(self._config.get('default_svobs_pvs', {}))
            for prop in columns:
                # Emit any SVObs columns. Others are ignored.
                if prop in default_svobs_pvs:
                    tmcf.append(f'{prop}: C:{dataset_name}->{prop}')
                    default_svobs_pvs.pop(prop)
                    if constant_pvs and prop in constant_pvs:
                        constant_pvs.pop(prop)
            if constant_pvs:
                for prop, value in constant_pvs.items():
                    tmcf.append(f'{prop}: {value}')
                    if prop in default_svobs_pvs:
                        default_svobs_pvs.pop(prop)
            # Add any remaining default PVs
            for prop, value in default_svobs_pvs.items():
                if value:
                    tmcf.append(f'{prop}: {value}')
            output_tmcf = '\n'.join(tmcf) + '\n'

        with file_util.FileIO(filename, mode, newline='') as f_out_tmcf:
            f_out_tmcf.write(output_tmcf)

    def _load_existing_statvars(self, mcf_file: list) -> dict:
        fp_nodes = {}
        if mcf_file:
            statvar_nodes = load_mcf_nodes(mcf_file)
            fp_nodes = fingerprint_mcf_nodes(
                statvar_nodes,
                self._config.get('statvar_fingerprint_ignore_props', []),
                self._config.get('statvar_fingerprint_include_props', []),
            )
            logging.info(
                f'Loaded {len(fp_nodes)} existing statvars from {mcf_file}')
        return fp_nodes

    def _get_exisisting_statvar(self, pvs: dict) -> dict:
        """Returns an existing statvar with the same PVs.

    Args:
      pvs: dictionary of statvar property:values

    Returns:
      updated dictionary of statvar pvs if one exists already.
    """
        existing_node = self._statvar_resolver.resolve_node(pvs)
        if existing_node:
            logging.level_debug() and logging.log(
                2, f'Reusing existing statvar {existing_node} for {pvs}')
            for prop, value in existing_node.items():
                if prop not in pvs:
                    pvs[prop] = value
            self._counters.add_counter(f'existing-statvars-from-mcf', 1,
                                       pvs.get('dcid'))
        else:
            logging.level_debug() and logging.log(
                2, f'No existing statvar for :{pvs}')
        return pvs
