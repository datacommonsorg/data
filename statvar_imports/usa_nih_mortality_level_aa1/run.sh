set -e

SCRIPT_PATH=$(realpath "$(dirname "$0")")

mkdir -p "input_files"

gsutil -m cp -r gs://unresolved_mcf/USA_Health_MortalityRate/input_files/*.csv "$SCRIPT_PATH/input_files"