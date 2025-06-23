# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
The script is created for one particular file in rwanda dataset.
File name: 'qavhudd'
The data is for lower level geos and the places to be mapped come from two
different columns.
Hence creating a new column based on the available of the two columns
'''

import pandas as pd
import numpy as np

# Reading the input file to make changes.
df_input = pd.read_csv("gcs_output/input_files/qavhudd.csv")

#  Creating columns to keep all the places to be mapped under one column
df_input["TMP_PLC"] = np.where((df_input["ID_DISTRICTS"]=="D"),
                             df_input["REGIONID_PROVINCE"],
                            df_input["REGIONID_DISTRICTS"]
)

df_input["PLACE"] = np.where( pd.isna(df_input['TMP_PLC']),
                            df_input["ID_DISTRICTS"],
                            df_input["TMP_PLC"]
)

df_input=df_input[["PROVINCE","ID_PROVINCE","REGIONID_PROVINCE",
                   "DISTRICTS","ID_DISTRICTS","REGIONID_DISTRICTS",
                   "TMP_PLC","PLACE","INDICATOR","ID_INDICATOR","FREQ",
                   "TIME_PERIOD","OBS_VALUE"]]

# Writing to output
df_input.to_csv("gcs_output/input_files/qavhudd_modified.csv",
                index=False)
