import csv
import io

pvmap = []
deterministic_file = "/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_EN_MAR_TP/deterministic_pvmap.csv"
metadata_file = "/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_EN_MAR_TP/input/metadata.csv"

# Read deterministic pvmap
with open(deterministic_file, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        pvmap.append(row)

# Read metadata.csv and convert to pvmap entries
# metadata format: column_name,value,DC_PV_PAIR
with open(metadata_file, 'r') as f:
    reader = csv.reader(f)
    next(reader) # skip header
    for row in reader:
        if len(row) < 3: continue
        col_name = row[0].strip()
        val = row[1].strip()
        dc_pv = row[2].strip()
        if not dc_pv: continue
        
        # Parse dc_pv (comma separated, then colon separated)
        # e.g., "populationType:WaterBody, chemicalConcentration:TotalPhosphorus"
        pairs = [p.strip() for p in dc_pv.split(',') if p.strip()]
        
        pv_row = [f"{col_name}:{val}"]
        for p in pairs:
            if ':' in p:
                k, v = p.split(':', 1)
                pv_row.extend([k.strip(), v.strip()])
            else:
                pv_row.extend([p, ""])
                
        # check if this key is already in deterministic pvmap
        # if so, maybe skip or merge?
        existing = False
        for i, existing_row in enumerate(pvmap):
            if existing_row and existing_row[0] == pv_row[0]:
                existing = True
                # Merge logic if needed, but let's just replace or assume deterministic is better
                # Wait, deterministic might be missing some properties that are in metadata.
                # Actually, deterministic_pvmap already has SERIES:EN_MAR_TP etc.
                break
        if not existing:
            pvmap.append(pv_row)

# Ensure measuredProperty and statType are present somewhere
has_measured_property = False
has_stat_type = False
for row in pvmap:
    for i in range(1, len(row), 2):
        if row[i] == 'measuredProperty': has_measured_property = True
        if row[i] == 'statType': has_stat_type = True

if not has_measured_property or not has_stat_type:
    # Let's add them to OBS_VALUE which is the global value column
    for row in pvmap:
        if row[0] == 'OBS_VALUE':
            if not has_measured_property:
                row.extend(['measuredProperty', 'concentration'])
            if not has_stat_type:
                row.extend(['statType', 'measuredValue'])

# Pad rows to max length
max_len = max(len(r) for r in pvmap)
header = ['key']
for i in range(1, max_len, 2):
    header.extend([f'prop{i//2+1}', f'val{i//2+1}'])

with open('merged_pvmap.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    for row in pvmap:
        padded = list(row) + [''] * (max_len - len(row))
        writer.writerow(padded)

