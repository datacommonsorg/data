#!/bin/bash

for d in ELEC NG PET INTL SEDS TOTAL; do
  echo python3 main.py --dataset="$d" --data_dir=tmp_raw_data/"$d"
  python3 main.py --dataset="$d" --data_dir=tmp_raw_data/"$d"
done
