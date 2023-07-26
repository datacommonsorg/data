import pandas as pd
import os

input_directory = r'scripts/us_epa/air_emissions_inventory/input_html_files/'
os.mkdir("scripts/us_epa/air_emissions_inventory/input_files")
output_directory = r'scripts/us_epa/air_emissions_inventory/input_files/'
for filename in os.listdir(input_directory):
    if filename.endswith('.html'):
        csv_filename = filename.replace('.html', '.csv')
        fname = os.path.join(input_directory, filename)
        table = pd.read_html(fname)[0]
        table.to_csv(output_directory + csv_filename, index=False)
