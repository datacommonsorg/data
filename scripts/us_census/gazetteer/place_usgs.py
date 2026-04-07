"""
Standardized 2025 USGS Containment Linker.
Generates a separate MCF file matching the 2022 format.
"""

import os
import glob
from collections import defaultdict


class Config:
    usgs_file = 'gazetteer/FederalCodes_National.txt'
    mcf_folder = 'gazetteer/merged_mcf'
    output_file = 'gazetteer/merged_files/NationalFedCodes_place_containment.mcf'


_MCF_STR = """
Node: dcid:geoId/{pid}
typeOf: schema:City
dcid: "geoId/{pid}"
containedInPlace: {cid_list}
"""


def main():
    whitelist_ids = set()

    # 1. Build Whitelist from ALL MCF files in output_mcf
    mcf_files = glob.glob(os.path.join(Config.mcf_folder, '*.mcf'))

    if not mcf_files:
        print(f"ERROR: No MCF files found in {Config.mcf_folder}")
        return

    print(f'Building whitelist from {len(mcf_files)} MCF files...')

    for mcf_path in mcf_files:
        # Avoid self-referencing the output file
        if os.path.basename(mcf_path) == os.path.basename(Config.output_file):
            continue

        with open(mcf_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # FIX: Look for both dcid:geoId/ AND geoId/
                if line.startswith('Node: geoId/') or line.startswith(
                        'Node: dcid:geoId/'):
                    # Split 'Node: dcid:geoId/01234' -> '01234'
                    parts = line.strip().split('/')
                    if len(parts) >= 2:
                        geoid = parts[-1].replace('"', '').strip()
                        whitelist_ids.add(geoid)

    print(f'Built master whitelist of {len(whitelist_ids)} total IDs.')

    # 2. Verify USGS input file
    if not os.path.exists(Config.usgs_file):
        print(f"ERROR: USGS file '{Config.usgs_file}' not found.")
        return

    count_found = 0

    # 3. Aggregate Counties per Place
    print(f'Processing {Config.usgs_file}...')
    place_to_counties = defaultdict(set)

    with open(Config.usgs_file, 'r', encoding='utf-8-sig',
              errors='ignore') as f_in:
        for line in f_in:
            parts = line.strip().split('|')
            if len(parts) < 12 or parts[0] == 'feature_id':
                continue

            # Place ID = State(8) + Place(3)
            # County ID = State(8) + County(11)
            place_id = parts[8] + parts[3]
            county_id = parts[8] + parts[11]

            if place_id in whitelist_ids:
                place_to_counties[place_id].add(county_id)

    # 4. Generate the Final Containment File
    print('Writing aggregated MCF file...')
    with open(Config.output_file, 'w', encoding='utf-8') as f_out:
        for place_id, counties in place_to_counties.items():
            # Format as: dcid:geoId/36033,dcid:geoId/36031
            cid_list = ','.join(
                [f"dcid:geoId/{cid}" for cid in sorted(counties)])

            # Write a single block for this place
            f_out.write(_MCF_STR.format(pid=place_id, cid_list=cid_list))
            count_found += len(counties)

    print('--- Finished ---')
    print(f'Total Links Created: {count_found}')
    print(f'Total Unique Places Updated: {len(place_to_counties)}')
    print(f'Output saved to: {Config.output_file}')


if __name__ == '__main__':
    main()
