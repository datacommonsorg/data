#!/bin/bash
# Post-process generated stat vars MCFs to append required provisional schema/nodes and clean names
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Append OutstandingPerformance provisional enum to egdxgkd_stat_vars.mcf (idempotent)
EG_PATH="${SCRIPT_DIR}/output/egdxgkd_stat_vars.mcf"
if [ -f "$EG_PATH" ] && ! grep -q "Node: dcid:OutstandingPerformance" "$EG_PATH" 2>/dev/null; then
cat << 'EOF' >> "$EG_PATH"

Node: dcid:OutstandingPerformance
typeOf: dcid:PerformanceLevelEnum
name: "Outstanding Performance"
isProvisional: dcs:True
EOF
fi

# 2. Normalize and clean names in xszlbb_stat_vars.mcf
python3 -c "
import os, re

mcf_path = '${SCRIPT_DIR}/output/xszlbb_stat_vars.mcf'
if os.path.exists(mcf_path):
    with open(mcf_path) as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.startswith('name:'):
            raw = line[5:].strip()
            m = re.match(r'^\s*\"([^\"]+)\"', raw)
            if m:
                clean_name = m.group(1)
            else:
                clean_name = raw.replace('\"', '').replace('dcid:', '').split(',')[0].strip()
            clean_name = clean_name.replace('dcid:', '').strip()
            new_lines.append(f'name: \"{clean_name}\"\n')
        else:
            new_lines.append(line)

    with open(mcf_path, 'w') as f:
        f.writelines(new_lines)
    print('Successfully normalized xszlbb_stat_vars.mcf names')
"
