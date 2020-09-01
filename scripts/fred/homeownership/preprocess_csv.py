import pandas as pd

df = pd.read_csv('MNHOWN.csv')

# Preprocessing
del df['realtime_start']
del df['realtime_end']
df['GeoId'] = 'dcid:geoId/27' # this can be modified to import additional data
df['Percent_Population_Homeowners']=df['value']
del df['value']

df.to_csv(path_or_buf='mn_homeownership.csv')