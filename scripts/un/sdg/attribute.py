import collections
import csv

property_template = '''
Node: dcid:SDG_{dcid}
typeOf: schema:Property
domainIncludes: dcs:Thing
rangeIncludes: dcs:{enum}
name: "SDG_{dcid}"
description: "{name}"
isProvisional: dcs:True
'''

enum_template = '''
Node: dcid:SDG_{enum}
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "SDG_{enum}"
isProvisional: dcs:True
'''

value_template = '''
Node: dcid:SDG_{enum}_{dcid}
typeOf: dcs:SDG_{enum}
name: "{name}"
isProvisional: dcs:True
'''

skipped_attributes = {
    'Cities', 'Freq', 'Nature', 'Observation Status', 'Report Ordinal',
    'Reporting Type', 'UnitMultiplier', 'Units'
}

# Use existing properties when they exist.
# Ideally the enum values should also be mapped to existing ones,
# but currently always generate a new node.
mapped_attributes = {
    'Age',
    'Cause of death',
    'Disability status',
    'Education level',
    'Sex',
}


def make_property(s):
    return s.title().replace(' ', '').replace('-',
                                              '').replace('_',
                                                          '').replace('/', '')


def make_value(s):
    return s.replace('<=', 'LEQ').replace('<',
                                          'LT').replace('+',
                                                        'GEQ').replace(' ', '')


with open('attribute.csv') as f:
    reader = csv.DictReader(f)
    concepts = collections.defaultdict(set)
    for row in reader:
        # Skip since these will be modeled diffferently.
        if row['concept_id'] in skipped_attributes:
            continue
        # Skip totals.
        if row['code_sdmx'] == '_T':
            continue
        concepts[row['concept_id']].add(
            (row['code_id'], row['code_description'],
             make_value(row['code_id'])))

with open('schema.mcf', 'w') as f:
    for concept in concepts:
        prop = make_property(concept)
        enum = prop + 'Enum'
        if concept not in mapped_attributes:
            f.write(
                property_template.format_map({
                    'dcid': prop[0].lower() + prop[1:],
                    'name': concept,
                    'enum': enum
                }))
        f.write(enum_template.format_map({'enum': enum}))
        for v in sorted(concepts[concept]):
            f.write(
                value_template.format_map({
                    'dcid': v[2],
                    'enum': enum,
                    'name': v[1][0].upper() + v[1][1:],
                }))
