#!/bin/bash

DIR=scratch/AR6_Projections

# Generate Stat Vars.  This needs all files to cover all confidence-levels/SSPs.
mkdir -p $DIR/generated
python3 process.py \
  --generate_what=sv \
  --in_pattern=$DIR/*/*/ssp*/total_*.nc \
  --out_dir=$DIR/generated

# Generate Global Stats
mkdir -p $DIR/Global/generated
python3 process.py \
  --generate_what=stat \
  --in_pattern=$DIR/Global/*/ssp*/total_*.nc \
  --out_dir=$DIR/Global/generated

# Generate Regional Stats.  For now skip low-confidence
mkdir -p $DIR/Regional/generated
python3 process.py \
  --generate_what=stat \
  --in_pattern=$DIR/Regional/medium_confidence/ssp*/total_*.nc \
  --out_dir=$DIR/Regional/generated

# Generate Places (one file is sufficient!)
python3 process.py \
  --generate_what=place \
  --in_pattern=$DIR/Regional/medium_confidence/ssp245/total_ssp245_medium_confidence_values.nc \
  --out_dir=$DIR/generated
