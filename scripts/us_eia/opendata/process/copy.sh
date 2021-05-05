#!/bin/bash

# Directory names
ELEC=electricity
NG=natural_gas
PET=petroleum
INTL=international
SEDS=seds
TOTAL=total_energy

if [[ "$#" -ne 1 ]]; then
  echo "Usage: $0 <dataset>"
  exit 1
fi

function copy() {
  dataset=$1
  src=tmp_raw_data/${dataset}/${dataset}
  dst=${!dataset}

  if [[ -z "$dst" ]]; then
    echo "ERROR: Incorrect dataset"
    exit 1
  fi

  set -x
  fileutil cp -f --parallel_copy 3 ${src}.mcf ${src}.tmcf ${src}.csv /cns/jv-d/home/datcom/v3_mcf/us_eia/${dst}/
  fileutil cp -f ${src}.mcf /cns/jv-d/home/datcom/v3_resolved_mcf/us_eia/${dst}/
  set +x
}

if [[ "$1" == "all" ]]; then
  for d in ELEC NG PET INTL SEDS TOTAL; do
    copy $d
  done
else
  copy $1
fi
