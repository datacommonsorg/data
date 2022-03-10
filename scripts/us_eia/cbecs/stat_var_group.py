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
'''
Utilities to create StatVarGroups.
'''

_SVG_ROOT = 'dcid:dc/g/Energy'  # or 'dcid:eia/g/Root'
_SVG_GROUP = 'dcid:eia/g/cbes'

_DEFAULT_IGNORE_PROPS = [
    'Node',
    'typeOf',
    'measuredProperty',
    'populationType',
    'statType',
    'measurementDenominator',
    'measurementQualifier',
    'description',
    'name',
    'dcid',
    'scalingFactor',
    # properties from StatVarObs
    'observationDate',
    'observationAbout',
    'variableMeasured',
    'value',
    'unit',
    # properties from StatVarGroups
    'specializationOf',
    'memberOf',
]


def _strip_namespace(dcid: str) -> str:
    '''Returns the dcid without the namespace.'''
    return dcid[dcid.find(':') + 1:]


def _strip_nonalpha(name: str) -> str:
    '''Returns a string without any alphanumeric characters.'''
    # TODO(ajaits): handle quantity ranges with '-'
    return ''.join([x for x in name if x.isalnum()])


def _get_all_permutations(items: list) -> list:
    '''Returns a list of lists containing all permitations of items
    by recursively generating permutations of smaller lists.
    
    Args:
        items: List of items.
    Returns a list where each element is a permutation of items.
    '''
    if len(items) == 1:
        return [items]
    permutations = []
    for i in range(len(items)):
        sub_items = list(items[:i])
        sub_items.extend(items[i + 1:])
        sub_perms = _get_all_permutations(sub_items)
        for perm in sub_perms:
            perm.append(items[i])
            permutations.append(perm)
    return permutations


def _get_prop_name(text: str) -> str:
    '''Return space separated capitalized words from a camelCase string.'''
    # TODO: handle acronyms and digits like 'abcDEF123'
    chars = [' ' + x.upper() if x.isupper() else x for x in text]
    text = ''.join(chars).replace('  ', ' ').strip()
    return ' '.join([x.capitalize() for x in text.split(' ')])


def _add_stat_var_group(svg_id: str, name: str, svg_parent_id: str,
                        svg_map: dict):
    '''Add a statvar to the group. '''
    if svg_id not in svg_map:
        svg_map[svg_id] = {
            'Node': svg_id,
            'name': f'"{name}"',
            'typeOf': 'dcs:StatVarGroup',
        }
    svg_node = svg_map[svg_id]
    prop = 'specializationOf'
    if prop in svg_node:
        if svg_parent_id != '' and svg_parent_id not in svg_node[prop]:
            svg_node[prop] = f'{svg_node[prop]}, {svg_parent_id}'
    else:
        svg_node[prop] = svg_parent_id


def _add_group_to_stat_var(sv_id: str, svg_id: str, svg_map: dict):
    '''Add a statvar group as a 'memberOf' to the statvar. '''
    sv_id = _strip_namespace(sv_id)
    if sv_id not in svg_map:
        svg_map[sv_id] = {
            'Node': f'dcid:{sv_id}',
            'typeOf': 'dcs:StatisticalVariable',
        }
    sv = svg_map[sv_id]
    if 'memberOf' not in sv:
        sv['memberOf'] = []
    sv['memberOf'].append('dcid:' + _strip_namespace(svg_id))


def add_stat_var_groups(svg_root: str,
                        svg_prefix: str,
                        stat_vars: dict,
                        stat_var_groups: dict,
                        stat_var_members: dict = None,
                        properties=None,
                        ignore_props=_DEFAULT_IGNORE_PROPS,
                        ignore_default_pvs={},
                        min_values=0):
    '''Add a set of statvar groups for each property of the statvars.'''
    # Get all properties for the statvar heirarchy.
    # prop_dcids = get_statvar_properties(statvars, properties, min_values)

    if stat_var_members is None:
        # Add 'memberOf' properties to the statvar groups.
        stat_var_members = stat_var_groups
    # Generate all permutations of properties in each statvar.
    # Add the statvar to each of the groups in all permutations.
    for dcid, sv in stat_vars.items():
        pop_suffix = ''
        if 'populationType' in sv:
            # Generate statvar group for the population type
            pop_suffix = _strip_namespace(sv['populationType'])
            svg_id = svg_prefix + pop_suffix
            svg_name = _get_prop_name(pop_suffix)
            _add_stat_var_group(svg_id, svg_name, svg_root,
                                stat_var_groups)
            svg_root = svg_id
        # Collect all properties to be used for stat var groups.
        sv_props = []
        for p in sv.keys():
            if properties is not None and p not in properties:
                continue
            if p in ignore_props:
                continue
            if p in ignore_default_pvs:
                if sv[p] == ignore_default_pvs[p]:
                    continue
            sv_props.append(p)
        svg = []
        # Generate stat var group heirarchy for each permutation or properties.
        prop_perms = _get_all_permutations(sv_props)
        for perm in prop_perms:
            svg_parent_id = svg_root
            svg_id = svg_prefix + pop_suffix
            svg_name = _get_prop_name(pop_suffix) + ' with '
            for prop in perm:
                prop_name = _strip_nonalpha(prop)
                val = _strip_namespace(sv[prop])
                val_name = _strip_nonalpha(val)
                # Create svg with the added property
                svg_id = svg_id + '_' + prop_name
                sep = ', '
                if svg_name.endswith('with '):
                    sep = ''
                svg_name = svg_name + sep + _get_prop_name(prop)
                _add_stat_var_group(svg_id, svg_name, svg_parent_id,
                                    stat_var_groups)
                # Create a child svg with the added property and value
                svg_parent_id = svg_id
                svg_id = svg_id + '-' + val_name
                svg_name = svg_name + ' = ' + _get_prop_name(val)
                _add_stat_var_group(svg_id, svg_name, svg_parent_id,
                                    stat_var_groups)
                svg_parent_id = svg_id

            sv_id = sv['Node']
            _add_group_to_stat_var(sv_id, svg_id, stat_var_members)
    return stat_var_groups
