import csv
import os
import re

from attribute import *

def format_description(s):
    # Remove <=2 levels of ().
    formatted = re.sub('\((?:[^)(]|\([^)(]*\))*\)', '', s)
    # Remove <=2 levels of [].
    formatted = re.sub('\[(?:[^)(]|\[[^)(]*\])*\]', '', formatted)
    # Remove attributes indicated with 'by'.
    formatted = formatted.split(', by')[0]
    # Remove references indicated by 'million USD'.
    formatted = formatted.split(', million USD')[0]
    # Remove extra spaces
    formatted = formatted.replace(' , ', ', ').replace('  ', ' ').strip()
    # Remove trailing commas
    return formatted.removesuffix(',')

places = {}
with open('m49.csv') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if not row['ISO-alpha3 code']:  # only countries for now
            continue
        places[int(row['M49 code'])] = row['ISO-alpha3 code']

template = '''
Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
measuredProperty: dcs:{mprop}
name: {name}
populationType: dcs:Thing
statType: dcs:measuredValue{cprops}
'''

with open('attribute.csv') as f:
    reader = csv.DictReader(f)
    concepts = collections.defaultdict(dict)
    for row in reader:
        # Skip since these will be modeled diffferently.
        if row['concept_id'] in skipped_attributes:
            continue
        # Skip totals.
        if row['code_sdmx'] == '_T':
            continue
        concepts[row['concept_id']][row['code_id']] = (row['code_description'], make_value(row['code_id']))

with open('sv.mcf', 'w') as f_out:
    svs = set()
    for file in sorted(os.listdir('input')):
        code = file.removesuffix('.csv')
        print(f'Starting {code}')
        with open('input/' + file) as f_in:
            reader = csv.DictReader(f_in)
            properties = sorted([
                field for field in reader.fieldnames
                if field[0] == '[' and field[1:-1] not in skipped_attributes
            ])
            try:
                for row in reader:
                    if not int(row['GeoAreaCode']) in places:
                        continue
                    value_ids = []
                    value_descriptions = []
                    cprops = ''
                    for i in properties: 
                        field = i[1:-1]
                        if not row[i] or field not in concepts or row[i] not in concepts[field]:
                            continue
                        value_ids.append(concepts[field][row[i]][1])
                        value_descriptions.append(concepts[field][row[i]][0])
                        enum = make_property(field)
                        if field in mapped_attributes:
                            prop = mapped_attributes[field]
                        else:
                            prop = 'sdg_' + enum[0].lower() + enum[1:]
                        val = enum + 'Enum_' + concepts[field][row[i]][1]
                        cprops += f'\n{prop}: dcs:SDG_{val}'
                    sv = 'sdg/' + '_'.join([row['SeriesCode']] + value_ids)
                    if sv in svs:
                        continue
                    svs.add(sv)
                    description = format_description(row['SeriesDescription'])
                    pvs = ', '.join(value_descriptions)
                    if pvs:
                        description += ': ' + pvs
                    f_out.write(
                        template.format_map({
                            'dcid': sv,
                            'mprop': 'sdg_' + row['SeriesCode'],
                            'name': '"' + description + '"',
                            'cprops': cprops,
                        }))
            except:
                print(f'Finished processing {code}')
