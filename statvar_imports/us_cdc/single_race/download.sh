#!/bin/bash

set -e -o pipefail

mkdir -p input_files
gsutil -m cp gs://unresolved_mcf/cdc/UnderlyingCause/Single_Race/latest/input_files/*.csv input_files/
