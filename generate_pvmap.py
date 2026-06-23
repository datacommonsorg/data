import csv
import re

metadata_file = '/usr/local/google/home/nehil/datacommons/import/git/data/isolated_test_DESA_2/input/metadata/DESA-GENDER_2025_OBS_ICT_SKILL_RT_metadata.csv'
output_pvmap = '/usr/local/google/home/nehil/datacommons/import/git/data/isolated_test_DESA_2/output_pvmap.csv'

pv_rows = []

# Base mappings for column headers
pv_rows.append(["SERIES:ICT_SKILL_RT", "populationType", "Person", "measuredProperty", "informationAndCommunicationsTechnologySkill", "statType", "measuredValue"])
pv_rows.append(["TIME_PERIOD", "observationDate", "{Data}"])
pv_rows.append(["OBS_VALUE", "value", "{Number}"])

# Handle UNIT_MULT using #Eval correctly
# Format: key, #Eval, "prop=expression"
pv_rows.append(["UNIT_MULT", "#Eval", "scalingFactor=10**int('{Data}') if '{Data}'.strip() else 1"])

# Handle FREQUENCY using #Eval correctly
pv_rows.append(["FREQUENCY", "#Eval", "observationPeriod='P1Y' if '{Data}' == 'A' else ('P1M' if '{Data}' == 'M' else ('P3M' if '{Data}' == 'Q' else ''))"])
pv_rows.append(["FREQUENCY", "#Eval", "measurementQualifier='Annual' if '{Data}' == 'A' else ('Monthly' if '{Data}' == 'M' else ('Quarterly' if '{Data}' == 'Q' else ''))"])

def clean_pv(pv_str):
    # Remove 'dcs:' or 'dcs, ' or 'dcs: '
    pv_str = pv_str.replace('dcs:', '').replace('dcs, ', '').replace('dcs: ', '')
    # Remove quotes if they wrap the whole value
    if pv_str.startswith('"') and pv_str.endswith('"'):
        pv_str = pv_str[1:-1]
    return pv_str.strip()

with open(metadata_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        col = row['column_name']
        val = row['value']
        pv_pair = row['DC_PV_PAIR']
        
        # Qualify key
        key = f"{col}:{val}"
        
        # Special case for UNIT_MULT and FREQUENCY - we already handled them generally
        if col in ['UNIT_MULT', 'FREQUENCY', 'UNIT_MEASURE']:
            continue

        parts = []
        # Split by comma followed by a space (heuristic)
        raw_parts = re.split(r', (?=[a-z])', pv_pair)
        for p in raw_parts:
            if ':' in p:
                prop, value = p.split(':', 1)
                prop = prop.strip()
                value = clean_pv(value)
                
                # Special handling for geographyCounterpart etc.
                if prop in ['geographyCounterpart', 'counterpartLocation', 'counterpartPlace', 'geographicalCounterpart', 'counterpartArea', 'locationCounterpart']:
                    prop = 'observationAbout'
                
                if value in ['TotalAge', 'TotalPlaceOfResidence', 'TotalSubject']:
                    # Use empty string to omit constraint
                    value = ""
                
                parts.extend([prop, value])
        
        if parts:
            pv_rows.append([key] + parts)
        else:
            pv_rows.append([key, "SkipProp", ""])

# Special case for UNIT_MEASURE:PT -> unit,Percent
pv_rows.append(["UNIT_MEASURE:PT", "unit", "Percent"])

with open(output_pvmap, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(pv_rows)

print(f"Generated {len(pv_rows)} rows in {output_pvmap}")
