# Copyright 2025 Google LLC
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

import os, shutil
from absl import logging, app

def move_latest_files(inputdir, inputdir_latest):
    if not os.path.exists(inputdir_latest):        
        os.makedirs(inputdir_latest, exist_ok=True)
        logging.info(f"Created download directory: {inputdir_latest}")
    max_digit_male,max_digit_female = -1,-1
    for filename in os.listdir(inputdir):
        filename_last_digit = int(filename.split(".")[0].split("_")[-1])
        if "40" in filename and filename_last_digit > max_digit_male:
            max_digit_male = filename_last_digit
        elif "50" in filename and filename_last_digit > max_digit_female:
            max_digit_female = filename_last_digit
    for filename in os.listdir(inputdir):
        if str(max_digit_male) in filename or str(max_digit_female) in filename:
            src_filepath = os.path.join(inputdir, filename)
            dest_filepath = os.path.join(inputdir_latest, filename)
            shutil.move(src_filepath, dest_filepath)
            logging.info(f"Successfully moved the latest file {filename} from {inputdir} to {inputdir_latest}.")

def main(_):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")
    input_dir_latest = os.path.join(script_dir, "input_files_latest")
    try:
        move_latest_files(input_dir,input_dir_latest)
    except Exception as e:
        logging.fatal(f"A critical error prevented pre process the data from  completing: {e}")

if __name__ == "__main__":
   app.run(main)

