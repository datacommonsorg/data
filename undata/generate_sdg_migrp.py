import csv

metadata_in = "/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_SG_CPA_MIGRP/input/metadata.csv"
pvmap_out = "/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_SG_CPA_MIGRP/generated/new_pvmap.csv"
metadata_out = "/usr/local/google/home/nehil/datacommons/import/git/data/undata/SDG/output/agentic/SDG_q4-2025_OBS_SG_CPA_MIGRP/generated/new_metadata.csv"

# First, construct the PV map rows
pv_map = {}

# Standard global column mappings
pv_map["TIME_PERIOD"] = ["observationDate", "{Data}"]
pv_map["OBS_VALUE"] = ["value", "{Number}"]
pv_map["UNIT_MULT"] = ["IgnoredUnitMult", "''"]
pv_map["FOOTNOTE"] = ["IgnoredFootnote", "''"]
pv_map["SOURCE"] = ["IgnoredSource", "''"]
pv_map["VALUE_TYPE"] = ["IgnoredValueType", "''"]
pv_map["TIME_DETAIL"] = ["IgnoredTimeDetail", "''"]

with open(metadata_in, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        col = row["column_name"].strip()
        val = row["value"].strip()
        pv_pair_str = row["DC_PV_PAIR"].strip()
        
        # Build key
        if val:
            key = f"{col}:{val}"
        else:
            key = col
            
        # Parse PV pairs
        pvs = []
        if pv_pair_str:
            # Special cleanups for malformed inputs
            if "G00116000" in key:
                pvs = ["geographyCounterpart", "CentralAndSouthAmerica", "incomeLevel", "LowerMiddleIncome"]
            elif "G00126000" in key:
                pvs = ["geographyCounterpart", "MiddleEastNotElsewhereSpecified"]
            else:
                # Split by comma but handle cases where values are quoted or have colons
                parts = pv_pair_str.split(",")
                for part in parts:
                    part = part.strip()
                    if ":" in part:
                        # Split on the first colon
                        subparts = part.split(":", 1)
                        prop = subparts[0].strip()
                        val_prop = subparts[1].strip()
                        pvs.extend([prop, val_prop])
        
        # Specials/Custom mappings
        if col == "REPORTING_LEVEL" and val == "G":
            # Must set observationAbout to Earth/Global
            pvs = ["observationAbout", "wikidataId/Q2", "reportingLevel", "Global"]
        elif col == "POLICY_DOMAINS" and val == "_T":
            pvs = ["IgnoredPolicyDomainTotal", "''"]
        elif col == "UNIT_MULT" and val == "0":
            pvs = ["IgnoredUnitMult", "''"]
            
        if pvs:
            pv_map[key] = pvs

# Write PV map to CSV
header = ["key"]
max_props = max(len(pvs) // 2 for pvs in pv_map.values())
for i in range(1, max_props + 1):
    header.extend([f"prop{i}", f"val{i}"])

rows = [header]
for key in sorted(pv_map.keys()):
    row = [key] + pv_map[key]
    row += [""] * (len(header) - len(row))
    rows.append(row)

with open(pvmap_out, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print(f"Generated {pvmap_out}")

# Write metadata.csv
with open(metadata_out, "w") as f:
    f.write("parameter,value\n")
    f.write("header_rows,1\n")
    f.write('output_columns,"observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor,#input"\n')
    f.write("output_only_new_statvars,0\n")

print(f"Generated {metadata_out}")
