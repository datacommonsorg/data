import csv
import os

REF_FILE = "/usr/local/google/home/nehil/Downloads/UN_DATA_ Codelist Geography - CL_GEOGRAPHY.csv"
OUT_FILE = "undata/cl_reviewed/CL_GEOGRAPHY.csv"

def fix_geography():
    if not os.path.exists(REF_FILE):
        print(f"Error: Reference file not found at {REF_FILE}")
        return

    with open(REF_FILE, mode='r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader)
        
        # Indices based on observation:
        # 0: CONCEPT
        # 1: CODE
        # 2: NAME_EN
        # 3: PARENT
        # 5: SORT_ORDER (sometimes empty)
        # 6: dcid
        # 7: dcid_from_un_places
        # 9: parent_dcid
        
        output_rows = []
        for row in reader:
            if not row or len(row) < 10:
                continue
                
            concept = row[0]
            code = row[1]
            name = row[2]
            parent = row[3]
            sort_order = row[5]
            
            dcid_primary = row[6].strip()
            dcid_fallback = row[9].strip()
            dcid_unplaces = row[7].strip()
            
            # Selection logic
            final_dcid = ""
            if dcid_primary and not dcid_primary.startswith("undata-geo/") and dcid_primary != "N":
                final_dcid = dcid_primary
            elif dcid_fallback and not dcid_fallback.startswith("undata-geo/") and dcid_fallback != "N":
                final_dcid = dcid_fallback
            elif dcid_unplaces and not dcid_unplaces.startswith("undata-geo/") and dcid_unplaces != "N":
                final_dcid = dcid_unplaces
            
            if final_dcid:
                # Format as property, value
                # We'll use geographyCounterpart as the default property
                dc_pv_pair = f"geographyCounterpart, {final_dcid}"
                output_rows.append([concept, code, name, parent, sort_order, dc_pv_pair])
            else:
                # Still include the row but without a mapping if none found
                output_rows.append([concept, code, name, parent, sort_order, ""])

    with open(OUT_FILE, mode='w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(["CONCEPT", "CODE", "NAME_EN", "PARENT", "SORT_ORDER", "DC_PV_PAIR"])
        writer.writerows(output_rows)

    print(f"Successfully reconstructed {OUT_FILE} with {len(output_rows)} rows.")

if __name__ == "__main__":
    fix_geography()
