#!/bin/bash

if [[ "$#" -ne 1 ]]; then
  echo "Usage: $0 <dataset>|all"
  exit 1
fi

set -x
if [[ "$1" == "all" ]]; then
  python3 ../download_bulk.py --datasets=ELEC,NG,PET,INTL,SEDS,TOTAL --data_dir=tmp_raw_data/
  for d in ELEC NG PET INTL SEDS TOTAL; do
    python3 main.py --dataset="$d" --data_dir=tmp_raw_data/"$d"
  done
else
  python3 ../download_bulk.py --datasets=$1 --data_dir=tmp_raw_data/
  python3 main.py --dataset="$1" --data_dir=tmp_raw_data/"$1"
fi
