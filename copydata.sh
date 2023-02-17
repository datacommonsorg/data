#!/bin/bash

# Copyright 2023 Google LLC
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

# A list of folders that we watch for data update and copy to GCS in Custom DC
# The layout under each folder should match the storage layout in
# https://docs.datacommons.org/custom_dc/upload_data.html


set -x

# Define a map from folder path under this repo, to the GCS path to copy data to.
declare -A foldermap
foldermap["scripts/stanford"]="gs://datcom-stanford-resources/imports"


# This function run "git diff" between latest and the previous commit on the
# specified folder (from function argument $1) and output a list of file names.
changes() {
  git diff --name-only --diff-filter=AMDR --cached HEAD^ $1
}

# Iterate target folder
for folder in ${!foldermap[@]}; do
  # Get the GCS path to copy data to
  gcs_path=${foldermap[$folder]}
  # If the current commit touches files in the target folder, copy data.
  if [[ $(changes "$folder") != "" ]];  then
    echo "Copy data to $gcs_path"
    for dir in $(find $folder -type d -maxdepth 1 -mindepth 1)
    do
      import_group=$(basename $dir)
      echo $import_group
      # Should only copy content under /data folder for each import group.
      # In GCS, there are /internal folders that should not be overwritten.
      # TODO(shifucun): Handle copy GCS reference. In this case, user would
      # store a link but not actual data in this repo.
      gsutil cp -r "$folder/$import_group/data/*" "$gcs_path/$import_group/data/"
    done
  fi
done

