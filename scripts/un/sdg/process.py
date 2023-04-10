import csv
import os
import re

places = {}
with open('m49.csv') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if not row['ISO-alpha3 code']:  # only countries for now
            continue
        places[int(row['M49 code'])] = row['ISO-alpha3 code']

# remove a bunch of the attributes for now (no units)
with open('attributes_filtered') as f:
    lines = f.read().splitlines()
    attributes = {l.split(':')[0] for l in lines}

attr = {}
with open('attribute.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['code_id'] not in attr:
            attr[row['code_id']] = row['code_description']

template = '''
Node: dcid:{dcid}
typeOf: dcs:StatisticalVariable
measuredProperty: dcid:{dcid}
memberOf: dcs:{svg}
name: {name}
populationType: dcs:Thing
statType: dcs:measuredValue
'''

with open('sv.mcf', 'w') as f_out:
    svs = set()
    for file in sorted(os.listdir('input')):
        code = file.removesuffix('.csv')
        print(f'Starting {code}')
        with open('input/' + file) as f_in:
            reader = csv.DictReader(f_in)
            properties = sorted([
                field for field in reader.fieldnames
                if field[0] == '[' and field in attributes
            ])
            try:
                for row in reader:
                    if not int(row['GeoAreaCode']) in places:
                        continue
                    sv = 'sdg/' + '_'.join([row['SeriesCode']] + [
                        row[i].replace('<', 'lt').replace('=', 'e').replace(
                            '+', 'gte').replace(' ', '')
                        for i in properties
                        if row[i]
                    ])
                    if sv in svs:
                        continue
                    svs.add(sv)
                    description = re.sub(
                        '[\(\[].*?[\)\]]', '',
                        row['SeriesDescription']).split(', by')[0].replace(
                            ' , ', ', ').strip().removesuffix(',')
                    pvs = ', '.join(
                        attr[row[i]] for i in properties if row[i] in attr)
                    if pvs:
                        description += ': ' + pvs
                    f_out.write(
                        template.format_map({
                            'dcid': sv,
                            'svg': 'sdg/g/' + row['SeriesCode'],
                            'name': '"' + description + '"'
                        }))
            except:
                print(f'Finished processing {code}')
