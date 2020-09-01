from ConfigWikiId import config
from WikiParser import parse_time_series_chart
import pandas as pd
from typing import Dict, List

# Stores a list of all the tables, for each place.
tables: List[pd.DataFrame] = []

for place in config:
    url: str = place['url']
    # Parse the Wikipedia Page's table.
    data: Dict[str, int] = parse_time_series_chart(url)
    # Flip the table.
    table: pd.DataFrame = pd.DataFrame(data).T
    table['wikiId'] = place['wikiId']

    # Store the table.
    tables.append(table)    

# Create one big table from the list of tables.
main_table = pd.concat(tables)

# Cases = Active Cases + Recoveries OR Confirmed Cases
main_table['cases'] = main_table['active cases'] + main_table['recoveries'] + main_table['confirmed cases']
# Get rid of any unecessary columns.
main_table = main_table[['recoveries', 'active cases', 'deaths', 'cases', 'wikiId']]
# Export table to CSV.
main_table.to_csv('output.csv', mode="w+")