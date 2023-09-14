import collections
import csv
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from un.sdg import util

directory = 'sdg-dataset/output/observations'


def fix(s):
    try:
        return s.encode('latin1').decode('utf8')
    except:
        return s.encode('utf8').decode('utf8')

sources = collections.defaultdict(set)
for filename in sorted(os.listdir(directory)):
    file = os.path.join(directory, filename)
    print(file)
    with open(file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dcid = 'sdg/' + util.format_variable_code(row['VARIABLE_CODE'])
            if row['SOURCE']:
                sources[dcid].add(fix(row['SOURCE']).removesuffix('.').strip().replace('"', "'").replace('\n', '').replace('\t', '').replace('__', '_'))

with open('schema/sv.mcf') as f_in:
    with open('sv_footnote.mcf', 'w') as f_out:
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
            f_out.write('\n\n')

