import pandas as pd
pd.DataFrame()

import pandas as pd
import numpy as np
import io
import csv

original_file = "demo_r_d3area_1_Data.csv"
cleaned_file = "PopulationDensity_Eurostat_NUTS3.csv"
tmcf= "PopulationDensity_Eurostat_NUTS3.tmcf"
df = pd.read_csv(original_file)
df.head()

# Get a list of column names:
df.columns

output_columns = ['Date', 'GeoId',
                  'PopulationDensity',
                 ]
with open(cleaned_file, 'w', newline='') as f_out:
  writer = csv.DictWriter(f_out, fieldnames=output_columns, lineterminator='\n')
  with open(original_file) as response:
    reader = csv.DictReader(response)

    writer.writeheader()
    for row_dict in reader:
      processed_dict = {
          'Date': '%s' % (row_dict['TIME'][:4]),
          'GeoId': 'dcid:nuts/%s' % row_dict['GEO'],
          'PopulationDensity': row_dict['Value'],
      }   

      writer.writerow(processed_dict)

# View the result:
df_cleaned = pd.read_csv(cleaned_file)
df_cleaned.head()

# Automate Template MCF generation since there are many Statistical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:PopulationDensity_Eurostat_NUTS3->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
observationAbout: C:PopulationDensity_Eurostat_NUTS3->GeoId
observationDate: C:PopulationDensity_Eurostat_NUTS3->Dates
value: C:PopulationDensity_Eurostat_NUTS3->{stat_var}
"""

stat_vars = output_columns[2:]
with open(tmcf, 'w', newline='') as f_out:
  for i in range(len(stat_vars)):
    f_out.write(TEMPLATE_MCF_TEMPLATE.format_map({'index': i, 'stat_var': output_columns[2:][i]}))

# View the result:
df_cleaned = pd.read_csv(tmcf)
df_cleaned.head()


# Uncomment the following to download to your local computer.
# files.download(tmcf)