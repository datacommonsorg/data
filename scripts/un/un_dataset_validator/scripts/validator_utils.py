import os
import glob
import csv
import re

def to_canonical_format(text: str) -> str:
    """Removes quotes, spaces, underscores, and converts to lowercase for alignment matching."""
    return re.sub(r'[^a-z0-9]', '', text.strip('"').lower())

def load_multipliers(pvmap_dir: str) -> dict:
    """Loads the UNIT_MULT multipliers from the PV map."""
    mult_file = os.path.join(pvmap_dir, "CL_MULT_pvmap_multiply.csv")
    
    # If not found in agency pvmap, try global pvmap (for ILO it might be there, or SDG)
    if not os.path.exists(mult_file):
        # Look in the parent directory's pvmap
        global_pvmap = os.path.join(os.path.dirname(os.path.dirname(pvmap_dir)), "pvmap", "CL_MULT_pvmap_multiply.csv")
        if os.path.exists(global_pvmap):
            mult_file = global_pvmap
        else:
            return {} # No multiplier file

    multipliers = {}
    with open(mult_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#') or row[0] == 'UnCodeKey':
                continue
            # format: UNIT_MULT:-15,#Multiply,1.00E-15
            if len(row) >= 3 and row[0].startswith("UNIT_MULT:"):
                key = row[0].split(":", 1)[1]
                try:
                    multipliers[key] = float(row[2])
                except ValueError:
                    continue
    return multipliers

def get_input_file_path(dataset_name: str, filename: str, input_data_dir: str) -> str:
    """Finds the absolute path to the raw input DATA file."""
    if not input_data_dir:
        return None
    full_path = os.path.join(input_data_dir, filename)
    if os.path.exists(full_path):
        return full_path
        
    # Check inside DATA subdirectory
    data_path = os.path.join(input_data_dir, "DATA", filename)
    if os.path.exists(data_path):
        return data_path
        
    return None
