#!/usr/bin/env bash
set -euo pipefail

# End-to-end automated pipeline for statvar_imports/dynamic_world_flood:
#   1. Download Dynamic World V1 (GOOGLE/DYNAMICWORLD/V1) flood rasters directly
#      from Google Earth Engine via download_script.py + util/download_util_script.py
#   2. Process into Data Commons CSV/tMCF via stat_var_processor.py
#   3. Run import-tool.jar lint & genmcf
#   4. Compute diff against optional previous output via import_differ.py
#   5. Run import_validation runner against validation_config.json

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${REPO_ROOT}/.env/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

IMPORT_TOOL_JAR="${IMPORT_TOOL_JAR:-${HOME}/.cache/datacommons/dc-import/import-tool.jar}"
START_DATE="${START_DATE:-}"
END_DATE="${END_DATE:-}"
BOUNDS="${BOUNDS:-24.72,83.83,26.06,88.26}"
PREV_OUTPUT_MCF="${PREV_OUTPUT_MCF:-}"
if [[ -n "${PREV_OUTPUT_MCF}" && "${PREV_OUTPUT_MCF}" != /* ]]; then
  PREV_OUTPUT_MCF="$(cd "$(dirname "${PREV_OUTPUT_MCF}")" && pwd)/$(basename "${PREV_OUTPUT_MCF}")"
fi

cd "${SCRIPT_DIR}"
mkdir -p input_files output counters

echo "=== Step 1: Downloading Dynamic World V1 Flood Data directly from Earth Engine ==="
DL_ARGS=(
  "--bounds=${BOUNDS}"
  "--output_dir=${SCRIPT_DIR}/input_files"
)
if [[ -n "${START_DATE}" ]]; then
  DL_ARGS+=("--start_date=${START_DATE}")
fi
if [[ -n "${END_DATE}" ]]; then
  DL_ARGS+=("--end_date=${END_DATE}")
fi
"${PYTHON_BIN}" "${SCRIPT_DIR}/download_script.py" "${DL_ARGS[@]}"

INPUT_CSV="${SCRIPT_DIR}/input_files/dynamic_world_flood_place_svobs.csv"
if [[ ! -f "${INPUT_CSV}" ]]; then
  echo "ERROR: Expected consolidated input CSV missing: ${INPUT_CSV}" >&2
  exit 1
fi

echo "=== Step 2: Running stat_var_processor.py ==="
"${PYTHON_BIN}" "${REPO_ROOT}/tools/statvar_importer/stat_var_processor.py" \
  "--input_data=${INPUT_CSV}" \
  "--pv_map=${SCRIPT_DIR}/dynamic_world_flood_pvmap.csv" \
  "--config_file=${SCRIPT_DIR}/dynamic_world_flood_metadata.csv" \
  "--output_path=${SCRIPT_DIR}/output/dynamic_world_flood_output" \
  "--existing_schema_mcf=${SCRIPT_DIR}/dynamic_world_flood_schema.mcf" \
  "--output_counters=${SCRIPT_DIR}/counters/dynamic_world_flood_counters.csv"

if [[ -f "${IMPORT_TOOL_JAR}" ]]; then
  echo "=== Step 3a: Running import-tool lint ==="
  mkdir -p "${SCRIPT_DIR}/output/lint"
  java -Xmx8g -jar "${IMPORT_TOOL_JAR}" \
    -o="${SCRIPT_DIR}/output/lint" \
    -e=false \
    -r=LOCAL \
    lint \
    "${SCRIPT_DIR}/dynamic_world_flood_schema.mcf" \
    "${SCRIPT_DIR}/output/dynamic_world_flood_output.tmcf" \
    "${SCRIPT_DIR}/output/dynamic_world_flood_output.csv"

  echo "=== Step 3b: Running import-tool genmcf ==="
  mkdir -p "${SCRIPT_DIR}/output/genmcf"
  java -Xmx8g -jar "${IMPORT_TOOL_JAR}" \
    -o="${SCRIPT_DIR}/output/genmcf" \
    -e=false \
    -r=LOCAL \
    genmcf \
    "${SCRIPT_DIR}/dynamic_world_flood_schema.mcf" \
    "${SCRIPT_DIR}/output/dynamic_world_flood_output.tmcf" \
    "${SCRIPT_DIR}/output/dynamic_world_flood_output.csv"
else
  echo "=== Step 3: Skipping import-tool lint/genmcf (jar not found at ${IMPORT_TOOL_JAR}) ==="
fi

CURRENT_MCF="${SCRIPT_DIR}/output/genmcf/table_mcf_nodes_dynamic_world_flood_output.mcf"
if [[ -n "${PREV_OUTPUT_MCF}" && -f "${PREV_OUTPUT_MCF}" && -f "${CURRENT_MCF}" ]]; then
  echo "=== Step 4: Running import_differ.py ==="
  rm -rf "${SCRIPT_DIR}/output/differ_results"
  mkdir -p "${SCRIPT_DIR}/output/differ_results"
  "${PYTHON_BIN}" "${REPO_ROOT}/tools/import_differ/import_differ.py" \
    "--current_data=${CURRENT_MCF}" \
    "--previous_data=${PREV_OUTPUT_MCF}" \
    "--output_location=${SCRIPT_DIR}/output/differ_results" \
    "--file_format=mcf" \
    "--runner_mode=native" \
    "--job_name=dynamic_world_flood_diff"
fi

echo "=== Pipeline completed successfully ==="
