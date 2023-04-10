import collections
import csv

property_template = '''
Node: dcid:{dcid}
typeOf: schema:Property
domainIncludes: dcs:Thing
rangeIncludes: dcs:{enum}
name: "{dcid}"
description: "{name}"
'''

enum_template = '''
Node: dcid:{enum}
typeOf: schema:Class
subClassOf: schema:Enumeration
name: "{enum}"
'''

value_template = '''
Node: dcid:{enum}_{dcid}
typeOf: dcs:{enum}
name: "{name}"
'''

skipped_attributes = {
    'Cities', 'Freq', 'Nature', 'Observation Status', 'Report Ordinal',
    'Reporting Type', 'UnitMultiplier', 'Units'
}

# Use existing property enums when they exist.
# Ideally the enum values should also be mapped to existing ones,
# but currently always generate a new node.
mapped_attributes = {
    'Age': 'AgeStatusEnum',
    'Cause of death': 'CauseOfDeathAndDisabilityEnum',
    'Disability status': 'USC_DisabilityStatusEnum',
    'Education level': 'SchoolGradeLevelEnum',
    'Sex': 'GenderType'
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
        # Skip attributes that swill be modeled differently.
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
        if concept in mapped_attributes:
            enum = mapped_attributes[concept]
        else:
            prop = make_property(concept)
            enum = prop + 'Enum'
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
