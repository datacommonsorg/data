# Copyright 2020 Google LLC
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

from __future__ import absolute_import
import unittest

from mcf_dict_util import *


class TestMCFDict(unittest.TestCase):

    def test_mcf_to_dict_list(self):
        node1_str = """Node: node1
        a: v1
        b: dcs:v2
        c : l: v3
        d: schema:  v4
        e:   dcid: v5
        """
        node1_dict = OrderedDict({
            'Node': {
                'value': 'node1',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })

        node2_str = """Node: dcid:node2
        a: v1
        b: dcs:v2
        c : l: v3
        d: schema:  v4
        e:   dcid: v5
        """
        node2_dict = OrderedDict({
            'Node': {
                'value': 'node2',
                'namespace': 'dcid'
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })

        node3_str = """Node: node3
        a: v1
        b: dcs:v2
        c : l: v3
        d: schema:  v4
        e:   dcid: v5
        dcid: node3
        """
        node3_dict = OrderedDict({
            'Node': {
                'value': 'node3',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            },
            'dcid': {
                'value': 'node3',
                'namespace': ''
            },
        })

        node4_str = """Node: node3
        a: v1
        b: dcs:v2
        #c : l: v3
        d: schema:  v4
        e:   dcid: v5
        dcid: node3
        """
        node4_dict = OrderedDict({
            'Node': {
                'value': 'node3',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            '__comment1': '#c : l: v3',
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            },
            'dcid': {
                'value': 'node3',
                'namespace': ''
            },
        })

        self.assertEqual(list(mcf_to_dict_list(node1_str)[0].values()),
                         list(node1_dict.values()))
        self.assertEqual(list(mcf_to_dict_list(node2_str)[0].values()),
                         list(node2_dict.values()))
        self.assertEqual(list(mcf_to_dict_list(node3_str)[0].values()),
                         list(node3_dict.values()))

    def test_mcf_dict_rename_prop(self):
        node1_str = """Node: node1
        a: v1
        b: dcs:v2
        c : l: v3
        d: schema:  v4
        e:   dcid: v5
        """
        node1_dict = OrderedDict({
            'Node': {
                'value': 'node1',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b2': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })
        node_list = mcf_to_dict_list(node1_str)
        ret_node = mcf_dict_rename_prop(node_list[0], 'b', 'b2')
        self.assertEqual(list(ret_node.values()), list(node1_dict.values()))

    def test_mcf_dict_rename_namespace(self):
        node1_str = """Node: node1
        a: v1
        b: dcs:v2
        c : l: v3
        d: schema:  v4
        e:   dcid: v5
        """
        node1_dict = OrderedDict({
            'Node': {
                'value': 'node1',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'dcs'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })
        node_list = mcf_to_dict_list(node1_str)
        ret_node = mcf_dict_rename_namespace(node_list[0], 'schema', 'dcs')
        self.assertEqual(list(ret_node.values()), list(node1_dict.values()))

    def test_mcf_dict_rename_prop_value(self):
        node1_str = """Node: node1
        a: v1
        b: dcs:v2
        c : l: v2
        d: schema:  v4
        e:   dcid: v5
        """
        node1_dict = OrderedDict({
            'Node': {
                'value': 'node1',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v22',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v2',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })
        node_list = mcf_to_dict_list(node1_str)
        ret_node = mcf_dict_rename_prop_value(node_list[0], 'b', 'v2', 'v22')
        self.assertEqual(list(ret_node.values()), list(node1_dict.values()))

    def test_get_dcid_node(self):
        node1_str = """Node: node1
a: v1
b: dcs:v2
c : l: v3
d: schema:  v4
e:   dcid: v5

Node: dcid:node2
a: v1
b: dcs:v2
c : l: v3
d: schema:  v4
e:   dcid: v5

Node: node3
a: v1
b: dcs:v2
c : l: v3
d: schema:  v4
e:   dcid: v5
dcid: node3
"""

        node_list = mcf_to_dict_list(node1_str)
        self.assertEqual(get_dcid_node(node_list[0]), '')
        self.assertEqual(get_dcid_node(node_list[1]), 'node2')
        self.assertEqual(get_dcid_node(node_list[2]), 'node3')

    def test_drop_nodes(self):
        node1_str = """Node: node1
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: dcid:node2
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: node3
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5
    dcid: node3
    """

        node_list = mcf_to_dict_list(node1_str)
        node_list2 = drop_nodes(node_list, ['node2', 'node3'])

        self.assertEqual(node_list2, [node_list[0]])

    def test_node_list_check_existence_dc(self):
        node1_str = """Node: dcid:node1
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: dcid:Count_Person
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: Person
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5
    dcid: Person
    """

        node_list = mcf_to_dict_list(node1_str)
        node_list2 = node_list_check_existence_dc(node_list)

        self.assertEqual(node_list2, {
            'node1': False,
            'Person': True,
            'Count_Person': True
        })

    def test_node_list_check_existence_node_list(self):
        node1_str = """Node: dcid:node1
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: dcid:Count_Person
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5

    Node: Person
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5
    dcid: Person
    """

        node2_str = """Node: Person
    a: v1
    b: dcs:v2
    c : l: v3
    d: schema:  v4
    e:   dcid: v5
    dcid: Person
    """

        node_list = mcf_to_dict_list(node1_str)
        node_list2 = mcf_to_dict_list(node2_str)
        node_list3 = node_list_check_existence_node_list(node_list, node_list2)

        self.assertEqual(node_list3, {
            'node1': False,
            'Person': True,
            'Count_Person': False
        })

    def test_dict_list_to_mcf_str(self):
        node1_str = """Node: node1
a: v1
b: dcs:v2
c: l:v3
#c1: l:v31
d: schema:v4
e: dcid:v5

"""
        node1_dict = OrderedDict({
            'Node': {
                'value': 'node1',
                'namespace': ''
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            '__comment1': '#c1: l:v31',
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })

        node2_str = """Node: dcid:node2
a: v1
b: dcs:v2
c: l:v3
d: schema:v4
e: dcid:v5

"""
        node2_dict = OrderedDict({
            'Node': {
                'value': 'node2',
                'namespace': 'dcid'
            },
            'a': {
                'value': 'v1',
                'namespace': ''
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            }
        })

        node3_str = """Node: node3
a: [v1 v8 v7]
b: dcs:v2
c: l:v3
d: schema:v4
e: dcid:v5
dcid: node3

"""
        node3_dict = OrderedDict({
            'Node': {
                'value': 'node3',
                'namespace': ''
            },
            'a': {
                'value': '[v1 v6 v7]',
                'namespace': '',
                'complexValue': ['v1', 'v8', 'v7']  # value v6 renamed to v8
            },
            'b': {
                'value': 'v2',
                'namespace': 'dcs'
            },
            'c': {
                'value': 'v3',
                'namespace': 'l'
            },
            'd': {
                'value': 'v4',
                'namespace': 'schema'
            },
            'e': {
                'value': 'v5',
                'namespace': 'dcid'
            },
            'dcid': {
                'value': 'node3',
                'namespace': ''
            },
        })

        self.assertEqual(dict_list_to_mcf_str([node1_dict]), node1_str)
        self.assertEqual(dict_list_to_mcf_str([node2_dict], sort_keys=True),
                         node2_str)
        self.assertEqual(
            dict_list_to_mcf_str([node3_dict], regen_complex_vals=True),
            node3_str)


if __name__ == '__main__':
    unittest.main()
