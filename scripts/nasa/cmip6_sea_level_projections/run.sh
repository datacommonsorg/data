#!/bin/bash

# Generate Stat Vars.  This needs all files to cover all confidence-levels /
# SSPs.
python3 process.py \
  --generate_what=sv \
  --in_pattern=scratch/Regional/*/ssp*/total_*.nc \
  --out_dir=scratch

# Generate Places (one file is sufficient!)
python3 process.py \
  --generate_what=place \
  --in_pattern=scratch/Regional/medium_confidence/ssp245/total_ssp245_medium_confidence_values.nc \
  --out_dir=scratch

exit

# Generate Global Stats
mkdir -p scratch/Global/generated
python3 process.py \
  --generate_what=stat \
  --in_pattern=scratch/Global/*/ssp*/total_*.nc \
  --out_dir=scratch/Global/generated


# Generate Regional Stats.  For now skip low-confidence
mkdir -p scratch/Regional/generated
python3 process.py \
  --generate_what=stat \
  --in_pattern=scratch/Regional/medium_confidence/ssp*/total_*.nc \
  --out_dir=scratch/Regional/generated
