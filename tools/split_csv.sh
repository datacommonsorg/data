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

if [ $# -lt 1 ]; then
  echo "Usage: $0 <csv_to_split> [num_lines_per_shard]"
  exit 1
fi

HEADER=$(head -1 $1)
if [ -n "$2" ]; then
  LINES_PER_SHARD=$2
else
  LINES_PER_SHARD=10000
fi
FNAME=$(echo "$1" | sed 's/\.csv$//')
tail -n +2 $1 | \
  split -l $LINES_PER_SHARD - ${FNAME}_shard_ --additional-suffix=.csv
for i in ${FNAME}_shard_*; do
  sed -i -e "1i$HEADER" "$i"
done
