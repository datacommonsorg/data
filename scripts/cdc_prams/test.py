import pandas as pd
import numpy as np

data = [None, '45.1 (40.6-49.7)', '42.0 (36.9-47.2)']
data1 = [np.nan, np.nan, np.nan, '42.0 (36.9-47.2)']
df = pd.DataFrame(data1, columns=['values'])
df = df['values'].str.split(r"\s+|-", expand=True)
df = df.rename(columns={
    df.columns[1]: 'new',
    df.columns[0]: 'zero',
    df.columns[2]: 'hey'
})
print(df)
