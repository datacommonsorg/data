import collections
import csv
import os

directory = 'sdg-dataset/output/observations'

def get_dcid(code):
    return 'sdg/' + code.replace('@', '.').replace(' ', '')

def fix(s):
    try:
        return s.encode('latin1').decode('utf8')
    except:
        return s.encode('utf8').decode('utf8')

sources = collections.defaultdict(set)
footnotes = collections.defaultdict(set)
for filename in os.listdir(directory):
#for file in [os.path.join(directory, 'observations_SP_PSR_OSATIS_PRM.csv')]:
    file = os.path.join(directory, filename)
    print(file)
    with open(file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dcid = get_dcid(row['VARIABLE_CODE'])
            if row['SOURCE']:
                sources[dcid].add(fix(row['SOURCE']).removesuffix('.').strip().replace('"', "'").replace('\n', '').replace('\t', '').replace('__', '_'))
            #if row['FOOT_NOTE']:
            #    footnotes[dcid].add(row['FOOT_NOTE'].encode("iso-8859-1").decode('utf8').removesuffix('.').strip().replace('"', "'").replace('\n', ''))

with open('schema/sv.mcf') as f_in:
    with open('sv2.mcf', 'w') as f_out:
        nodes = f_in.read().split('Node: ')[1:]
        for node in nodes:
            lines = node.split('\n')
            for line in lines:
                if line.startswith('dcid:'):
                    dcid = line.removeprefix('dcid:')
            if not dcid:
                continue
            f_out.write('Node: ' + node.removesuffix('\n\n'))
            if dcid in sources:
                f_out.write('\nfootnote: "Includes data from the following sources: ' + '; '.join(sorted(sources[dcid])) + '"')
            #if dcid in footnotes:
            #    f_out.write('\nfootnote: "Footnotes: ' + '; '.join(sorted(footnotes[dcid])) + '"')
            f_out.write('\n\n')

