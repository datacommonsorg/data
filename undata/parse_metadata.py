import csv
with open('/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_SP_TRN_PUBL/input/metadata.csv', 'r') as f:
    reader = csv.DictReader(f)
    mappings = []
    for row in reader:
        col = row['column_name']
        val = row['value']
        dc_pv = row['DC_PV_PAIR']
        if col == 'GEOGRAPHY':
            # dc_pv looks like "geographyCounterpart:Charikar"
            if ':' in dc_pv:
                prop, pval = dc_pv.split(':', 1)
                mappings.append(f"{col}:{val},observationAbout,\"{pval}\"")

with open('/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_SP_TRN_PUBL/generated/new_pvmap.csv', 'a') as f:
    for m in mappings:
        f.write(m + '\n')
