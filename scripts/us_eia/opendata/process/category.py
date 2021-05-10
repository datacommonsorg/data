# Copyright 2021 Google LLC
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
"""Helper functions to deal with category hierarchy."""

_DCID_PREFIX = 'dcid:'


def _strip_dcid_prefix(id):
    return id[len(_DCID_PREFIX):] if id.startswith(_DCID_PREFIX) else id


def _svg_dcid(dataset, cat_id):
    return f'dcid:eia/g/{dataset}.{cat_id}'


def _get_dataset_root(svg_info):
    dataset_root = ''
    for _, (parent, _) in svg_info.items():
        if parent in svg_info or dataset_root == parent:
            continue
        assert not dataset_root, f'Two roots found: {dataset_root}, {parent}'
        dataset_root = parent

    return dataset_root


def generate_svg_nodes(dataset, dataset_name, svg_info):
    """Generates MCF nodes for StatVarGroups.

    Args:
        dataset: Dataset code
        dataset_name: Dataset name
        svg_info: Dict of SVG-ID -> (parent SVG-ID, name)

    Returns a list of MCF nodes as strings.
    """

    nodes = []

    if not svg_info:
        return nodes

    # EIA SVG root
    pvs = [
        'Node: dcid:eia/g/Root', 'typeOf: dcs:StatVarGroup',
        'name: "Other Data (eia.gov)"', 'specializationOf: dcid:dc/g/Energy'
    ]
    nodes.append('\n'.join(pvs))

    # EIA Dataset root
    dataset_root = _get_dataset_root(svg_info)
    if dataset_root:
        pvs = [
            f'Node: dcid:{dataset_root}', 'typeOf: dcs:StatVarGroup',
            f'name: "{dataset_name}"', 'specializationOf: dcid:eia/g/Root'
        ]
        nodes.append('\n'.join(pvs))

    # Category SVGs
    for svg, (parent, name) in svg_info.items():
        svg = _strip_dcid_prefix(svg)
        parent = _strip_dcid_prefix(parent)
        pvs = [
            f'Node: dcid:{svg}', 'typeOf: dcs:StatVarGroup', f'name: "{name}"',
            f'specializationOf: dcid:{parent}'
        ]
        nodes.append('\n'.join(pvs))

    return nodes


def trim_area_categories(svg_info, counters):
    """Given a category hierarchy, trims all "by Area" categories and its
       children.  Like https://www.eia.gov/opendata/qb.php?category=457053.

    Args:
        svg_info: Dict of SVG-ID -> (parent SVG-ID, name)
        counters: Dict of counters

    On success, updates svg_info.
    """
    dataset_root = _get_dataset_root(svg_info)

    # Delete "area" categories.
    for svg, (_, name) in list(svg_info.items()):
        if name and name.lower() == 'by area':
            counters['info_deleted_area_categories'] += 1
            del svg_info[svg]

    # Trim orphans, except for dataset_root.
    run_again = True
    while run_again:
        run_again = False
        for svg, (parent, _) in list(svg_info.items()):
            if parent != dataset_root and parent not in svg_info:
                run_again = True
                counters['info_deleted_orphan_categories'] += 1
                del svg_info[svg]


def process_category(dataset, data, extract_place_statvar_fn, svg_info,
                     sv_membership_map, counters):
    """Process a category line, compute StatVarGroups (SVG) and update results.

    Args:
        dataset: Dataset code
        data: JSON category data from source
        extract_place_statvar_fn: Function to extract raw place and stat-var
                                  from series_id
        svg_info: Dict from SVG-ID -> (parent SVG-ID, name)
        sv_membership_map: Dict from Raw-SV -> set(SVG-IDs)
        counters: Dict for counters

    On success, updates svg_info and sv_membership_map.
    """

    cat_id = data.get('category_id', None)
    parent_cat_id = data.get('parent_category_id', None)
    name = data.get('name', None)
    if not cat_id or not parent_cat_id:
        return
    svg_id = _svg_dcid(dataset, cat_id)
    svg_info[svg_id] = (_svg_dcid(dataset, parent_cat_id), name)

    child_series = data.get('childseries', [])
    for series in child_series:
        (_, raw_sv, _) = extract_place_statvar_fn(series, counters)
        if not raw_sv:
            counters['error_extract_place_sv_for_category'] += 1
            continue

        if raw_sv not in sv_membership_map:
            sv_membership_map[raw_sv] = set([svg_id])
        else:
            sv_membership_map[raw_sv].add(svg_id)
