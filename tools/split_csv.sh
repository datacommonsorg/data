#!/bin/bash
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Utility to split a single CSV file into chunks with header replicated in each
# of the outputs. Produces shards in the same directory as input CSV.  For
# example, /path/to/dir/input.csv produces /path/to/dir/input_shard_*.csv files.

if [ $# -lt 1 ]; then
  echo "Usage: $0 <csv_to_split> [row_size_per_chunk]"
  exit 1
fi

HEADER=$(head -1 $1)
if [ -n "$2" ]; then
  CHUNK=$2
else
  CHUNK=1000
fi
FNAME=$(echo "$1" | sed 's/\.csv$//')
tail -n +2 $1 | split -l $CHUNK - ${FNAME}_shard_ --additional-suffix=.csv
for i in ${FNAME}_shard_*; do
  sed -i -e "1i$HEADER" "$i"
done
