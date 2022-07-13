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
"""
This function is called inorder to check if some Stat Vars are already present
in the DataCommons present MCF files, so that one SV is not added again.
"""
import datacommons


def check_dcid_existance(nodes):
    nodes_response = datacommons.get_property_values(
        nodes,
        "typeOf",
        out=True,
        value_type=None,
        limit=datacommons.utils._MAX_LIMIT)
    node_status = {}
    for node, value in nodes_response.items():
        if value == []:
            node_status[node] = False
        else:
            node_status[node] = True
    return node_status
