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
"""_summary_
Script to check the property/dcid/nodes existance in datacommons.org.
"""
import datacommons


def check_dcid_existence(nodes: list) -> dict:
    """
    Checks the existance of dcid nodes in autopush.
    True: Available
    False: Unavailable

    Args:
        nodes (list): Dcid Nodes List

    Returns:
        dict: Status dictionary.
    """
    # pylint: disable=protected-access
    nodes_response = datacommons.get_property_values(
        nodes,
        "typeOf",
        out=True,
        value_type=None,
        limit=datacommons.utils._MAX_LIMIT)
    # pylint: enable=protected-access
    node_status = {}
    for node, value in nodes_response.items():
        if value == []:
            node_status[node] = False
        else:
            node_status[node] = True
    return node_status
