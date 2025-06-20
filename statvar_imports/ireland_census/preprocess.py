# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pandas as pd
from absl import app, logging

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")

# Removing state level data for the years 2008-2021 which was existing in the suicides.csv file.
def preprocess():
    try:
        for filename in os.listdir(INPUT_DIR):
            if "suicides_with_aa1_aa2" in filename:
                filepath = os.path.join(INPUT_DIR, filename)
                df = pd.read_csv(filepath)
                if 'Area of Residence' in df.columns and 'Year' in df.columns:
                    years_to_drop = range(2008, 2022)
                    mask = (df['Area of Residence'] == 'State') & (df['Year'].isin(years_to_drop))
                    df = df[~mask]
                df.to_csv(filepath, index=False)
                logging.info("Successfully dropped State level values for the years 2008 to 2021.")

    except Exception as e:
        logging.fatal(f"Failed to preprocess the file: {e}")


def main(argv):
    preprocess()

if __name__ == "__main__":
    app.run(main)
