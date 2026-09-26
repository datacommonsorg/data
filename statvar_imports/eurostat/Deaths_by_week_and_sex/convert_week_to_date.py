# Copyright 2026 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import pandas as pd
import os
from datetime import datetime

# Get the absolute path of the directory where this script is located
# (Which is now the Deaths_by_week_and_sex folder)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Since the data is in the same folder as the script, we just append the filenames
input_file = os.path.join(script_dir, 'Deaths_by_week_and_sex_data_raw.csv')
output_file = os.path.join(script_dir, 'Deaths_by_week_and_sex_data_raw_processed.csv')

# Load your raw data
df = pd.read_csv(input_file)

# Convert YYYY-Wxx to the Sunday of that week (ISO format: %G = Year, %V = Week, %u = Day of Week)
df['CALENDAR_DATE'] = df['TIME_PERIOD'].apply(
    lambda x: datetime.strptime(x + '-7', "%G-W%V-%u").strftime("%Y-%m-%d")
)

# Save the updated CSV to use in your importer
df.to_csv(output_file, index=False)

print(f"Data successfully processed and saved to:\n{output_file}")