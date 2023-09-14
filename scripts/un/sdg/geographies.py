import collections 
import csv 
import json

FIXED = {
    'africa': '2',
    'undata-geo/G99999999': '952',
}

def should_include_containment(s, s_dcid, o, o_dcid):
    if (s == 'GeoRegion' or s == 'UNGeoRegion') and o_dcid == 'Earth':
        return True
    elif (s == 'GeoRegion' or s == 'UNGeoRegion') and o == 'Continent':
        return True
    elif (s == 'GeoRegion' or s == 'UNGeoRegion') and (o == 'GeoRegion' or o =='UNGeoRegion'):
        return True
    elif s == 'Country' and (o == 'GeoRegion' or o =='UNGeoRegion'):
        return True
    elif s == 'SamplingStation' and o == 'Country':
        return True
    elif s == 'City' and s_dcid.startswith('undata-geo') and o == 'Country':
        return True
    return False

sdg2type = {}
with open('sdg-dataset/output/SDG_geographies.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sdg2type[row['GEOGRAPHY_CODE']] = row['GEOGRAPHY_TYPE']

sdg2un = {}
un2sdg = {}
with open('sssom-mappings/output_mappings/undata-geo__sdg-geo.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row['\ufeffsubject_id'] or not row['object_id']:
            continue
        sdg2un[row['object_id'].removeprefix('sdg-geo:')] = row['\ufeffsubject_id']
        un2sdg[row['\ufeffsubject_id']] = row['object_id'].removeprefix('sdg-geo:')

# un -> (dcid, type, name)
un2dc = {}
with open('geography/places.csv') as f:
    reader = csv.DictReader(f)
    for row in reader: 
        if row['unDataCode'] == 'x':
            continue
        if row['dcid'] == 'NorthernEurope':
            type = 'UNGeoRegion'
        else:
            type = json.loads(row['typeOf'].replace("'", '"'))[0]['dcid']
        un2dc[row['unDataCode']] = (row['dcid'], type, row['dc_name'])

# write base place mcf
PLACE_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:{type}
name: "{name}"
unDataCode: "{code}"
unDataLabel: "{label}"
'''
un2dc2 = {}
subjects = set()
with open('geography/geographies.csv') as f_in:
    with open('geography/un_places.mcf', 'w') as f_out:
        reader = csv.DictReader(f_in)
        for row in reader:
            subject = row['subject_id']
            if subject in un2dc:
                dcid = un2dc[subject][0]
                type = un2dc[subject][1]
                name = un2dc[subject][2]
            else:
                dcid = row['subject_id'].replace(':', '/')
                if row['subject_id'] in un2sdg and un2sdg[row['subject_id']] in sdg2type:
                    sdg_type = sdg2type[un2sdg[row['subject_id']]]
                    if sdg_type == 'SamplingStation' or sdg_type == 'City':
                        type = sdg_type
                    else:
                        type = 'GeoRegion'
                else:
                    type = 'GeoRegion'
                name = row['subject_label'].split('_')[-1]
            un2dc2[subject] = (dcid, type, name)
            if type == 'GeoRegion' or type == 'UNGeoRegion' or type == 'SamplingStation' or (type == 'City' and dcid.startswith('undata-geo')):
                subjects.add((dcid, type))
            f_out.write(PLACE_TEMPLATE.format_map({
                'dcid': dcid,
                'type': type,
                'name': name,
                'code': row['subject_id'],
                'label': row['subject_label']
            }))

# dcid -> [parent dcids]
containment = collections.defaultdict(list)
with open('sssom-mappings/data/enumerations/undata/geography_hierarchy.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subject = 'undata-geo:' + row['\ufeffsubject_id']
        if subject in un2dc:
            s_dcid = un2dc[subject][0]
            s_type = un2dc[subject][1]
        elif subject in un2dc2:
            s_dcid = un2dc2[subject][0]
            s_type = un2dc2[subject][1]
        else:
            print('Missing subject: ', subject)
        object = 'undata-geo:' + row['object_id']
        if object in un2dc:
            o_dcid = un2dc[object][0]
            o_type = un2dc[object][1]
        elif object in un2dc2:
            o_dcid = un2dc2[object][0]
            o_type = un2dc2[object][1]
        else:
            print('Missing object: ', object)
        if should_include_containment(s_type, s_dcid, o_type, o_dcid):
            containment[(s_dcid, s_type)].append(o_dcid)

CONTAINMENT_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcid:{type}{containment}
'''
with open('geography/un_containment.mcf', 'w') as f:
    for s in sorted(containment):
        c = ''
        for o in containment[s]:
            c += '\ncontainedInPlace: dcs:' + o
        f.write(CONTAINMENT_TEMPLATE.format_map({
            'dcid': s[0],
            'type': s[1],
            'containment': c
        }))
    for s in sorted(subjects):
        if s in containment:
            continue
        c = '\ncontainedInPlace: dcs:Earth'
        f.write(CONTAINMENT_TEMPLATE.format_map({
            'dcid': s[0],
            'type': s[1],
            'containment': c
        }))
    
with open('geography/place_mappings.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['sdg', 'dcid'])
    writer.writeheader()
    for s in sdg2un:
        un = sdg2un[s]
        if un in un2dc:
            dcid = un2dc[un][0]
        elif un in un2dc2:
            dcid = un2dc2[un][0]
        else:
            continue
        
        # Filter duplicates.
        if dcid in FIXED and s != FIXED[dcid]:
            continue

        writer.writerow({
            'sdg': s,
            'dcid': dcid
        })