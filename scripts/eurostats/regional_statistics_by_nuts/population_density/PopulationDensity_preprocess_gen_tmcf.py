# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import csv

# data_url = "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/demo_r_d3area.tsv.gz"
source_tsv = "demo_r_d3dens.tsv"
source_csv_long = "demo_r_d3dens.csv"
cleaned_csv = "PopulationDensity_Eurostat_NUTS3.csv"
tmcf= "PopulationDensity_Eurostat_NUTS3.tmcf"

df = pd.read_csv(source_tsv, delimiter='\t')
assert df.head!=[]
print(df.head())
header = list(df.columns.values)
years = header[1:]

# Pandas.melt() unpivots a DataFrame from wide format to long format
df = pd.melt(df, id_vars =header[0], value_vars =years, 
              var_name ='time', value_name ='value') 


# separate geo and unit columns
new = df[header[0]].str.split(",", n = 1, expand = True) 
df['geo']= new[1] 
df['unit']= new[0]    
df.drop(columns =[header[0]], inplace = True) 

# remove empty rows, clean values to have all digits
df = df[df.value.str.contains('[0-9]')]
possible_flags=[' ', ':', 'b', 'e']
for flag in possible_flags:
  df['value'] = df['value'].str.replace(flag,'')

print(df.head())
df.to_csv(source_csv_long, index=False)
print(df.columns)

output_columns = ['Date', 'GeoId',
                  'Count_Person_AsAFractionOfArea',
                 ]
with open(cleaned_csv, 'w', newline='') as f_out:
  writer = csv.DictWriter(f_out, fieldnames=output_columns, lineterminator='\n')
  with open(source_csv_long) as response:
    reader = csv.DictReader(response)

    writer.writeheader()
    for row_dict in reader:
      assert not row_dict['value'].isdigit()
      assert not row_dict['time'].isdigit()
      processed_dict = {
              # 'Date': '%s-%s-%s' % (row_dict['TIME'][:4], '01', '01'),
              'Date': '%s' % (row_dict['time'][:4]),
              'GeoId': 'dcid:nuts/%s' % row_dict['geo'],
              'Count_Person_AsAFractionOfArea': float(row_dict['value']),
      }    
      writer.writerow(processed_dict)

# View the result:
df_cleaned = pd.read_csv(cleaned_csv)
print(df_cleaned.head())
