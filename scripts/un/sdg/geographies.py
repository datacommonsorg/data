import csv
import os
import sys
import collections

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import util

'''
19	Americas    undata-geo:G00134000
199	Least Developed Countries (LDCs)    undata-geo:G00404000
722	Small island developing States (SIDS)   undata-geo:G00405000
432	Landlocked developing countries (LLDCs) undata-geo:G00403000
514	Developed regions (Europe, Cyprus, Israel, Northern America, Japan, Australia & New Zealand)
515	Developing regions
127	Southern Asia (excluding India) undata-geo:G00800130
135	Caucasus and Central Asia   undata-geo:G00800100
198	Organisation for Economic Co-operation and Development (OECD) Member States undata-geo:G00406000
223	Eastern Asia (excluding Japan and China)    undata-geo:G00800150
485	Western Asia (exc. Armenia, Azerbaijan, Cyprus, Israel and Georgia) undata-geo:G00800370
513	Europe and Northern America undata-geo:G00126000
518	Eastern Asia (excluding Japan)  undata-geo:G00800160
543	Oceania (exc. Australia and New Zealand)    undata-geo:G00145000
593	Development Assistance Committee members (DAC)  undata-geo:G00500200
738	Sub-Saharan Africa (inc. Sudan) undata-geo:G00800500
746	Northern Africa (exc. Sudan)    undata-geo:G00800480
747	Northern Africa and Western Asia    undata-geo:G00103000
753	Eastern and South-Eastern Asia  undata-geo:G00122000
889	World Trade Organization (WTO) Member States    undata-geo:G00600700
901	Africa (ILO) DUPLICATE - africa
902	Asia and the Pacific (ILO)
903	Central and Eastern Europe (ILO)
904	Middle East and North Africa (ILO)
905	Middle East (ILO)
906	North America (ILO) DUPLICATE - northamerica
907	Other regions (ILO)
908	Western Europe (ILO) DUPLICATE - WesternEurope
910	High income economies (WB)
911	Low income economies (WB)
912	Lower middle economies (WB)
913	Low and middle income economies (WB)
914	Upper middle economies (WB)
915	WTO Developing Member States    undata-geo:G00600710
916	WTO Developed Member States undata-geo:G00600720
917	International Centers (FAO) undata-geo:G00600110
918	European Union (EU) Institutions    undata-geo:G00500360
97	European Union
919	Regional Centres (FAO)  undata-geo:G00600120
921	ODA residual
922	Custom groupings of data providers
99042	WHO Africa  undata-geo:G00600410
99043	WHO Americas    undata-geo:G00600420
99044	WHO South-East Asia undata-geo:G00600430
99045	WHO Europe  undata-geo:G00600440
99046	WHO Eastern Mediterranean
99047	WHO Western Pacific undata-geo:G00600450
99048	WHO Global  undata-geo:G00600400
909	Eastern Southern South-Eastern Asia and Oceania (MDG)
923	LLDC Africa undata-geo:G00403100
924	LLDC Americas   undata-geo:G00403200
925	LLDC Asia   undata-geo:G00403300
926	LLDC Europe undata-geo:G00403500
927	LDC Africa  undata-geo:G00404100
928	LDC Americas    undata-geo:G00404200
929	LDC Asia    undata-geo:G00404300
930	LDC Oceania undata-geo:G00404400
931	SIDS Africa undata-geo:G00405100
932	SIDS Americas   undata-geo:G00405200
933	SIDS Asia   undata-geo:G00405300
934	SIDS Oceania    undata-geo:G00405400
935	World (total) by SDG regions DUPLICATE Earth
936	World (total) by continental regions DUPLICATE Earth
937	World (total) by MDG regions DUPLICATE Earth
938	Member States   undata-geo:G00600000
'''

code2name = {}
name2code = {}
countries = {}
with open('sdg-dataset/output/SDG_geographies.csv') as f:
    reader = csv.DictReader(f)
    for row in reader: 
        if row['GEOGRAPHY_TYPE'] == 'Region':
            if row['GEOGRAPHY_CODE'] in code2name:
                print(row)
            code2name[row['GEOGRAPHY_CODE']] = row['GEOGRAPHY_NAME']
            if row['GEOGRAPHY_NAME'] in name2code:
                print(row)
            name2code[row['GEOGRAPHY_NAME']] = row['GEOGRAPHY_CODE']
        elif row['GEOGRAPHY_TYPE'] == 'Country':
            countries[row['GEOGRAPHY_NAME']] = row['GEOGRAPHY_CODE'] 
countries['Côte d’Ivoire'] = '384'


name2un = {}
un2name = {}
with open('geographies.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        #if int(row['subject_id'][12:]) >=  100000:
        #    continue
        #if row['subject_label'] in name2un:
        #    print(row['subject_label'])
        name2un[row['subject_label']] = row['subject_id']
        un2name[row['subject_id']] = row['subject_label']

REGION_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:GeoRegion
containedInPlace: dcs:Earth
name: "{name}"
unDataCode: "{code}"
unDataLabel: "{name}"
'''

'''
with open('geographies/regions.csv') as f_in:
    with open('geographies/regions.mcf', 'w') as f_out:
        reader = csv.DictReader(f_in)
        for row in reader:
            f_out.write(REGION_TEMPLATE.format_map({
                'dcid': row['un_code'].replace(':', '/'),
                'code': row['un_code'],
                'name': un2name[row['un_code']]
            }))
'''


'''
subjects = []
with open('geographies/regions.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subjects.append(row['un_code'])

with open('geographies/subjects', 'w') as f:
    for s in subjects:
        f.write(s + ',' + s.replace(':', '/') + '\n')
'''




'''
subjects = {}
with open('geographies/subjects.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        subjects[row['code']] = row['dcid']

# un code -> name
objects = {}
with open('partof.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['pa'] in subjects:
            objects[row['object_id']] = row['object_label']

# un code -> iso3
objects_filtered = {}
for x in objects:
    if objects[x] in countries:
        objects_filtered[x] = countries[objects[x]]
    #else:
    #    print('Missing: ', objects[x])

# m49 -> iso3
m49 = {}
with open('m49.csv') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        m49[str(int(row['M49 code']))] = row['ISO-alpha3 code']

# un code -> iso3
o = {}
for x in objects_filtered:
    if objects_filtered[x]  in m49 and m49[objects_filtered[x]]:
        o[x] = m49[objects_filtered[x]]
    #else:
    #    print('Missing: ', objects_filtered[x])

with open('geographies/objects.csv', 'w') as f:
    for x in o:
        f.write(x + ',country/' + o[x] + '\n')
'''



S = {}
S2 = {}
with open('geographies/subjects.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        S[row['code']] = row['dcid']
        S2[row['dcid']] = row['code']

O = {}
O2 = {}
with open('geographies/objects.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        O[row['code']] = row['dcid']
        O2[row['dcid']] = row['code']

# un code for country -> [un code for region]
part_of = collections.defaultdict(list)
part_of2 = collections.defaultdict(list)
with open('geography_hierarchy_new.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if 'undata-geo:' + row['subject_id'] in O and 'undata-geo:' + row['object_id'] in S:
            part_of[O['undata-geo:' + row['subject_id']]].append(S['undata-geo:' + row['object_id']])
        #if 'undata-geo:' + row['subject_id'] in S and 'undata-geo:' + row['object_id'] in S:
        #    part_of2[S['undata-geo:' + row['subject_id']]].append(S['undata-geo:' + row['object_id']])
#for x in part_of2:
#    print(x, part_of2[x])

COUNTRY_TEMPLATE = '''
Node: dcid:{dcid}
typeOf: dcs:Country
unDataCode: "{code}"
unDataLabel: "{label}"{containedInPlace}
'''

with open('geographies/countries.mcf', 'w') as f:
    for x in sorted(part_of):
        contained_in_place = ''
        for y in (part_of[x]):
            contained_in_place += '\ncontainedInPlace: dcs:' + y
        f.write(COUNTRY_TEMPLATE.format_map({
            'dcid': x,
            'code': O2[x],
            'label': un2name[O2[x]],
            'containedInPlace': contained_in_place,
        }))

'''
dcids = set()
dupes = set()
with open('cities_test.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row['dcid']:
            continue
        if row['dcid'] in dcids:
           dupes.add(row['dcid'])
        dcids.add(row['dcid'])


with open('cities_test.csv') as f_in:
    with open('cities_filtered.csv', 'w') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=['name', 'dcid'])
        writer.writeheader()
        for row in reader:
            if row['dcid'] in dupes:
                writer.writerow({
                    'name': row['name'],
                    'dcid': ''
                })
            else:
                writer.writerow(row)
'''
