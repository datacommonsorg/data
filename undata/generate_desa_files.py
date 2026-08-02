import csv
import collections
import os

data_file = '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/data/DESA-GENDER_2025_OBS_MAT_WAGE.csv'
cl_dir = '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed'
output_pvmap = '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/unreviewed/DESA-GENDER_2025_OBS_MAT_WAGE/output_pvmap.csv'
output_metadata = '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/unreviewed/DESA-GENDER_2025_OBS_MAT_WAGE/output_metadata.csv'

# Ensure output directory exists
os.makedirs(os.path.dirname(output_pvmap), exist_ok=True)

# 1. Collect unique values from data
unique_values = collections.defaultdict(set)
with open(data_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        for col, val in row.items():
            unique_values[col].add(val)

# 2. Map columns to codelists
col_to_cl = {
    'SERIES': 'CL_SERIES.csv',
    'GEOGRAPHY': 'CL_GEOGRAPHY.csv',
    'VALUE_CATEGORY': 'CL_VALUE_CATEGORY.csv',
    'UNIT_MEASURE': 'CL_UNIT_MEASURE.csv',
    'UNIT_MULT': 'CL_UNIT_MULT.csv',
    'CENSORED_VALUE_TYPE': 'CL_CENSORED_VALUE_TYPE.csv',
    'FREQUENCY': 'CL_FREQUENCY.csv',
    'OBSERVATION_STATUS': 'CL_OBSERVATION_STATUS.csv'
}

pv_mappings = collections.defaultdict(list)

for col, cl_file in col_to_cl.items():
    cl_path = os.path.join(cl_dir, cl_file)
    if not os.path.exists(cl_path):
        continue
    
    with open(cl_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        try:
            code_idx = header.index('CODE')
            pv_idx = header.index('DC_PV_PAIR')
        except ValueError:
            continue
            
        for row in reader:
            if not row or len(row) <= code_idx:
                continue
            code = row[code_idx]
            if code in unique_values[col]:
                # Take all values from pv_idx onwards
                parts = []
                for val in row[pv_idx:]:
                    if val.strip():
                        # If a value contains a comma, it might be a single string from a quoted field
                        # or it might be multiple fields. csv.reader handles quoting.
                        # We want to split by comma if it's a single string like "p, v"
                        if ',' in val:
                            parts.extend([p.strip() for p in val.split(',')])
                        else:
                            parts.append(val.strip())
                
                pairs = []
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        p, v = parts[i], parts[i+1]
                        if p == 'geographyCounterpart':
                            p = 'observationAbout'
                        pairs.append((p, v))
                
                if pairs:
                    key = f"{col}:{code}"
                    for p, v in pairs:
                        pv_mappings[key].extend([p, v])

# 3. Add mandatory properties for SERIES:MAT_WAGE
if 'SERIES:MAT_WAGE' in pv_mappings:
    pvs = pv_mappings['SERIES:MAT_WAGE']
    has_pop = False
    has_mp = False
    has_st = False
    for i in range(0, len(pvs), 2):
        if pvs[i] == 'populationType': has_pop = True
        if pvs[i] == 'measuredProperty': has_mp = True
        if pvs[i] == 'statType': has_st = True
    
    if not has_pop: pvs.extend(['populationType', 'MaternityLeave'])
    if not has_mp: pvs.extend(['measuredProperty', 'count'])
    if not has_st: pvs.extend(['statType', 'measuredValue'])
else:
    pv_mappings['SERIES:MAT_WAGE'] = ['benefitType', 'MaternityLeaveWages', 'populationType', 'MaternityLeave', 'measuredProperty', 'count', 'statType', 'measuredValue']

# 4. Add global mappings
pv_mappings['TIME_PERIOD'] = ['observationDate', '{Data}']
pv_mappings['OBS_VALUE'] = ['value', '{Number}']

# 5. Write output_pvmap.csv
with open(output_pvmap, 'w') as f:
    writer = csv.writer(f)
    for key, pvs in pv_mappings.items():
        writer.writerow([key] + pvs)

# 6. Write output_metadata.csv
with open(output_metadata, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['parameter', 'value'])
    writer.writerow(['header_rows', '1'])
