import csv

def generate_pvmap():
    pvmap = []
    pvmap.append(['key', 'property1', 'value1', 'property2', 'value2', 'property3', 'value3', 'property4', 'value4', 'property5', 'value5', 'property6', 'value6', 'property7', 'value7', 'property8', 'value8'])

    # SERIES
    pvmap.append(['SERIES:NEET_RATE', 'populationType', 'dcs:Person', 'measuredProperty', 'dcs:count', 'statType', 'dcs:measuredValue', 'employmentStatus', 'dcs:NotInEducationEmploymentOrTraining'])

    codelists = [
        ('GEOGRAPHY', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_GEOGRAPHY.csv'),
        ('AGE', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_AGE.csv'),
        ('SEX', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_SEX.csv'),
        ('UNIT_MEASURE', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_UNIT_MEASURE.csv'),
        ('UNIT_MULT', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_UNIT_MULT.csv'),
        ('CENSORED_VALUE_TYPE', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_CENSORED_VALUE_TYPE.csv'),
        ('FREQUENCY', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_FREQUENCY.csv'),
        ('OBSERVATION_STATUS', '/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/cl_reviewed/CL_OBSERVATION_STATUS.csv'),
    ]

    for prefix, path in codelists:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            # Find DC_PV_PAIR index
            try:
                pv_idx = header.index('DC_PV_PAIR')
            except ValueError:
                continue
                
            for row in reader:
                if not row or len(row) <= pv_idx:
                    continue
                
                code = row[1]
                pv_parts = row[pv_idx:]
                # Join and re-split to handle commas inside columns or extra columns
                pv_str = ",".join(pv_parts).strip()
                if not pv_str:
                    if code == '_T' and prefix in ['AGE', 'SEX']:
                        prop = 'age' if prefix == 'AGE' else 'gender'
                        pvmap.append([f"{prefix}:{code}", prop, '""'])
                    continue
                
                pairs = []
                if ':' in pv_str:
                    # Format: prop: val, prop: val
                    items = [item.strip() for item in pv_str.split(',')]
                    for item in items:
                        if ':' in item:
                            k, v = item.split(':', 1)
                            val = v.strip()
                            if not val.startswith('dcs:') and not val.startswith('[') and not val.startswith('"') and val != '""':
                                val = 'dcs:' + val
                            pairs.extend([k.strip(), val])
                else:
                    # Format: prop, val, prop, val
                    items = [item.strip() for item in pv_str.split(',')]
                    for i in range(0, len(items), 2):
                        if i + 1 < len(items):
                            k, v = items[i], items[i+1]
                            if not k or not v: continue
                            val = v.strip()
                            if not val.startswith('dcs:') and not val.startswith('[') and not val.startswith('"') and val != '""':
                                val = 'dcs:' + val
                            pairs.extend([k, val])
                
                if prefix == 'GEOGRAPHY':
                    if 'geographyCounterpart' in pairs:
                        idx = pairs.index('geographyCounterpart')
                        pvmap.append([f"GEOGRAPHY:{code}", 'observationAbout', pairs[idx+1]])
                elif prefix == 'UNIT_MULT':
                    if '#Multiply' in pairs:
                        idx = pairs.index('#Multiply')
                        pvmap.append([f"UNIT_MULT:{code}", 'scalingFactor', pairs[idx+1]])
                elif prefix == 'FREQUENCY':
                    if 'measurementQualifier' in pairs:
                        idx = pairs.index('measurementQualifier')
                        if pairs[idx+1] == 'dcs:Annual':
                            pairs.extend(['observationPeriod', 'P1Y'])
                    pvmap.append([f"FREQUENCY:{code}"] + pairs)
                else:
                    if pairs:
                        pvmap.append([f"{prefix}:{code}"] + pairs)

    pvmap.append(['TIME_PERIOD', 'observationDate', '{Data}'])
    pvmap.append(['OBS_VALUE', 'value', '{Number}'])

    with open('/usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/unreviewed/DESA-GENDER_2025_OBS_NEET_RATE/output_pvmap.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(pvmap)

if __name__ == "__main__":
    generate_pvmap()
