import os
import sys
import subprocess
import re
from collections import defaultdict

# --- 1. Setup Data Commons Environment Paths ---
py_script_path = os.path.expanduser('~/Desktop/data')
sys.path.append(os.path.join(py_script_path, 'tools', 'statvar_importer'))
sys.path.append(os.path.join(py_script_path, 'util'))

# (We no longer need mcf_file_util for merging, but keeping it in the path just in case)

# --- 2. Configuration & Directories ---
PROJECT_DIR = 'gazetteer'
DIRS = {
    'hist': os.path.join(PROJECT_DIR, 'hist_mcf'),
    'new': os.path.join(PROJECT_DIR, 'output_mcf'),
    'before_diff': os.path.join(PROJECT_DIR, 'before_merge_diff_mcf'),
    'merged': os.path.join(PROJECT_DIR, 'merged_mcf'),
    'after_diff': os.path.join(PROJECT_DIR, 'after_merge_diff_mcf'),
    'final': os.path.join(PROJECT_DIR, 'merged_files')
}

# Ensure all output directories exist
for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

# Map historical files to their corresponding new 2025 files
FILE_PAIRS = [('2018_2022_Gaz_116CDs_national.mcf',
               '2025_Gaz_119CDs_national.mcf', '119CDs_national'),
              ('2018_Gaz_cbsa_national.mcf', '2025_Gaz_cbsa_national.mcf',
               'cbsa_national'),
              ('2018_2022_Gaz_counties_national.mcf',
               '2025_Gaz_counties_national.mcf', 'counties_national'),
              ('2018_2022_Gaz_cousubs_national.mcf',
               '2025_Gaz_cousubs_national.mcf', 'cousubs_national'),
              ('2018_2022_Gaz_elsd_national.mcf', '2025_Gaz_elsd_national.mcf',
               'elsd_national'),
              ('2018_2022_Gaz_place_national.mcf',
               '2025_Gaz_place_national.mcf', 'place_national'),
              ('2018_2022_Gaz_scsd_national.mcf', '2025_Gaz_scsd_national.mcf',
               'scsd_national'),
              ('2018_2022_Gaz_sdadm_national.mcf',
               '2025_Gaz_sdadm_national.mcf', 'sdadm_national'),
              ('2018_2022_Gaz_tracts_national.mcf',
               '2025_Gaz_tracts_national.mcf', 'tracts_national'),
              ('2018_2022_Gaz_unsd_national.mcf', '2025_Gaz_unsd_national.mcf',
               'unsd_national'),
              ('2018_2022_Gaz_zcta_national.mcf', '2025_Gaz_zcta_national.mcf',
               'zcta_national')]

# --- 3. Helper Functions ---


def run_diff(mcf1, mcf2, output_txt):
    """Runs the Data Commons mcf_diff.py script via subprocess."""
    print(f"  -> Running Diff: Outputting to {output_txt}")
    cmd = [
        "python3", "tools/statvar_importer/mcf_diff.py", f"--mcf1={mcf1}",
        f"--mcf2={mcf2}", "--ignore_property="
    ]
    with open(output_txt, "w") as outfile:
        # Added stderr=subprocess.STDOUT to capture counters in the file
        subprocess.run(cmd,
                       stdout=outfile,
                       stderr=subprocess.STDOUT,
                       check=True)


def merge_mcfs(old_mcf, new_mcf, merged_mcf):
    """Merges historical and new MCFs using a pure text-block strategy to preserve prefixes."""
    print(f"  -> Merging files (Pure Text Mode)...")

    def load_text_blocks(filepath):
        blocks = {}
        current_id = None
        current_block = []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('Node:'):
                    # Save the previous block before starting a new one
                    if current_id:
                        blocks[current_id] = "".join(current_block)

                    current_block = [line]
                    # Extract a clean, prefix-free ID to use as the dictionary key for perfect matching
                    raw_node = line.split('Node:')[1]
                    current_id = raw_node.replace('dcid:',
                                                  '').replace('"', '').strip()

                elif current_id:
                    current_block.append(line)

            # Catch the very last block in the file
            if current_id:
                blocks[current_id] = "".join(current_block)

        return blocks

    # Load literal text blocks
    old_blocks = load_text_blocks(old_mcf)
    new_blocks = load_text_blocks(new_mcf)

    # Merge them (Last-Writer-Wins, meaning 2025 blocks overwrite 2022 blocks)
    merged_blocks = old_blocks
    merged_blocks.update(new_blocks)

    # Write the exact text blocks safely back to the new file
    with open(merged_mcf, 'w', encoding='utf-8') as f:
        for block_text in merged_blocks.values():
            f.write(block_text)
            # Ensure proper spacing between blocks
            if not block_text.endswith('\n\n'):
                if not block_text.endswith('\n'):
                    f.write('\n\n')
                else:
                    f.write('\n')


def normalize_node_id(node_str):
    """Removes 'dcid:', quotes, and whitespace to ensure perfect matching."""
    return node_str.replace('dcid:', '').replace('"', '').strip()


def add_alternate_names(diff_file, mcf_file, out_file):
    """Parses diff for deleted names and injects them as alternateName."""
    print(f"  -> Injecting alternate names from diff...")
    alt_names_to_add = defaultdict(set)
    current_diff_node = None

    # Find deleted names
    with open(diff_file, 'r', encoding='utf-8') as df:
        for line in df:
            line_str = line.strip()
            if line_str.startswith('Node:'):
                current_diff_node = normalize_node_id(
                    line_str.split('Node:')[1])
            elif line_str.startswith('-') and 'name:' in line_str:
                match = re.search(r'-\s*name:\s*(.+)', line_str)
                if match and current_diff_node:
                    alt_names_to_add[current_diff_node].add(
                        match.group(1).strip())

    # Inject into MCF
    out_lines = []
    current_mcf_node = None
    with open(mcf_file, 'r', encoding='utf-8') as mf:
        for line in mf:
            line_str = line.strip()
            if line_str.startswith('Node:'):
                current_mcf_node = normalize_node_id(line_str.split('Node:')[1])
                out_lines.append(line)
            elif not line_str:
                if current_mcf_node and current_mcf_node in alt_names_to_add:
                    for alt_name in alt_names_to_add[current_mcf_node]:
                        out_lines.append(f'alternateName: {alt_name}\n')
                    del alt_names_to_add[current_mcf_node]
                out_lines.append(line)
                current_mcf_node = None
            else:
                out_lines.append(line)

    if current_mcf_node and current_mcf_node in alt_names_to_add:
        for alt_name in alt_names_to_add[current_mcf_node]:
            out_lines.append(f'alternateName: {alt_name}\n')

    with open(out_file, 'w', encoding='utf-8') as out_f:
        out_f.writelines(out_lines)


# --- 4. Main Execution Loop ---


def main():
    print(f"Starting pipeline for {len(FILE_PAIRS)} geography types...\n" +
          "=" * 50)

    for hist_file, new_file, base_name in FILE_PAIRS:
        print(f"\nProcessing: {base_name}")

        hist_path = os.path.join(DIRS['hist'], hist_file)
        new_path = os.path.join(DIRS['new'], new_file)

        before_diff_path = os.path.join(DIRS['before_diff'], f"{base_name}.txt")
        merged_path = os.path.join(DIRS['merged'], f"merged_{base_name}.mcf")
        after_diff_path = os.path.join(DIRS['after_diff'], f"{base_name}.txt")
        final_path = os.path.join(DIRS['final'], f"merged_{base_name}.mcf")

        if not os.path.exists(hist_path) or not os.path.exists(new_path):
            print(f"  [!] Missing source files for {base_name}. Skipping.")
            continue

        # Step 1: Initial Diff
        run_diff(hist_path, new_path, before_diff_path)

        # Step 2: Merge the MCFs (Using the new Text Merger!)
        merge_mcfs(hist_path, new_path, merged_path)

        # Step 3: Second Diff (Old vs Merged)
        run_diff(hist_path, merged_path, after_diff_path)

        # Step 4: Add Alternate Names and finalize
        add_alternate_names(after_diff_path, merged_path, final_path)

        print(f"  -> {base_name} complete! Saved to {final_path}")

    print("\n" + "=" * 50 + "\nAll processes finished successfully!")


if __name__ == "__main__":
    main()
