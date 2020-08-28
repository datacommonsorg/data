from Config import config
from WikiParser import parse_time_series_chart
import pandas as pd

for country in config:
    data = parse_time_series_chart(country['url'])
    table = pd.DataFrame(data).T
    table['geoId'] = country['geoId']
    print(table)