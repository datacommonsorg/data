set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

mkdir -p "input_files"

gsutil -m cp -r gs://unresolved_mcf/IPEDS/Enrollment_FTE_National/input_files/*.csv "$SCRIPT_PATH/input_files"