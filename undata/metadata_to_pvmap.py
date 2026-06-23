import os
import csv
import glob
from pathlib import Path
import collections

METADATA_DIR = "undata/SDG/metadata"
OUTPUT_DIR = "undata/SDG/output/deterministic_pvmap"

def normalize_geography(pairs):
    """Special normalization for geography properties."""
    normalized = []
    for p, v in pairs:
        if p == 'geographyCounterpart':
            if 'wikidataId/' in v:
                normalized.append(('observationAbout', f'dcid:{v.split("/")[-1]}'))
            elif 'country/' in v:
                normalized.append(('observationAbout', f'country/{v.split("/")[-1]}'))
            else:
                normalized.append(('observationAbout', v))
        else:
            normalized.append((p, v))
    return normalized

def process_metadata_to_pvmap():
    metadata_files = glob.glob(os.path.join(METADATA_DIR, "*_metadata.csv"))
    print(f"Found {len(metadata_files)} metadata files.")
    
    for meta_path in metadata_files:
        filename_stem = Path(meta_path).name.replace("_metadata.csv", "")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # Final PVMap filename
        output_pvmap = os.path.join(OUTPUT_DIR, f"{filename_stem}_pvmap.csv")
        # Separate Metadata filename if needed
        output_metadata = os.path.join(OUTPUT_DIR, f"{filename_stem}_metadata.csv")
        
        print(f"Processing metadata for {filename_stem}...")
        
        pv_mappings = collections.defaultdict(list)
        
        # Add Defaults
        pv_mappings['TIME_PERIOD'].append(('observationDate', '{Data}'))
        pv_mappings['OBS_VALUE'].append(('value', '{Number}'))
        
        try:
            with open(meta_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    col = row['column_name']
                    val = row['value']
                    key = f"{col}:{val}"
                    
                    extra_vals = []
                    for header, cell_val in row.items():
                        if header not in ['column_name', 'value'] and cell_val:
                            parts = [p.strip() for p in cell_val.split(',')]
                            extra_vals.extend(parts)
                    
                    all_pairs = []
                    if any(':' in v for v in extra_vals):
                        for v in extra_vals:
                            if ':' in v:
                                p, v_pv = v.split(':', 1)
                                all_pairs.append((p.strip(), v_pv.strip()))
                            elif ' ' in v:
                                p_v = v.split(' ', 1)
                                all_pairs.append((p_v[0].strip(), p_v[1].strip()))
                    else:
                        for i in range(0, len(extra_vals), 2):
                            if i + 1 < len(extra_vals):
                                p = extra_vals[i].strip()
                                v_pv = extra_vals[i+1].strip()
                                if p and v_pv:
                                    all_pairs.append((p, v_pv))
                    
                    if col == 'GEOGRAPHY':
                        all_pairs = normalize_geography(all_pairs)
                    
                    unique_pairs = {}
                    for p, v in all_pairs:
                        unique_pairs[p] = v
                    
                    for p, v in unique_pairs.items():
                        pv_mappings[key].append((p, v))
            
            for key in pv_mappings:
                if key.startswith('SERIES:'):
                    existing_props = [p for p, v in pv_mappings[key]]
                    if 'populationType' not in existing_props:
                        pv_mappings[key].append(('populationType', 'Person'))
                    if 'measuredProperty' not in existing_props:
                        pv_mappings[key].append(('measuredProperty', 'count'))
                    if 'statType' not in existing_props:
                        pv_mappings[key].append(('statType', 'measuredValue'))
            
            # Write pvmap.csv (without 1,2 rows)
            with open(output_pvmap, mode='w', encoding='utf-8', newline='') as out_f:
                writer = csv.writer(out_f)
                # PVMap starts with the key/property header
                writer.writerow(["key", "property1", "value1", "property2", "value2", "property3", "value3", "property4", "value4", "property5", "value5"])
                
                for key, pairs in pv_mappings.items():
                    row = [key]
                    for p, v in pairs:
                        row.extend([p, v])
                    
                    target_len = 11
                    if len(row) < target_len:
                        row.extend([''] * (target_len - len(row)))
                    else:
                        row = row[:target_len]
                    writer.writerow(row)

            # Write metadata.csv (with 1,2 rows)
            with open(output_metadata, mode='w', encoding='utf-8', newline='') as out_f:
                writer = csv.writer(out_f)
                writer.writerow(["parameter", "value"])
                writer.writerow(["header_rows", "1"])
                # Could add more parameters here if known
            
            print(f"  Saved: {output_pvmap} and {output_metadata}")
            
        except Exception as e:
            print(f"Error processing {meta_path}: {e}")

if __name__ == "__main__":
    process_metadata_to_pvmap()
