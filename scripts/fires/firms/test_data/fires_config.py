# Config for processing fires data from FIRMS.
{
    # Get a KEY from https://firms.modaps.eosdis.nasa.gov/api/data_availability/
    # and set it in place of 'YOUR_KEY' below.
    # To process multiple days data, add a list of URLs with the date suffix.
    'url': [
        # URL for the latesr NASA FIRMS data set for 1 day.
        'https://firms.modaps.eosdis.nasa.gov/api/area/csv/TEST_KEY/VIIRS_SNPP_NRT/world/10'
    ],
    # File to save data downloaded from the URLs above.
    'csv_data': 'sample-fires.csv',
    's2_level': 13,
    'rename_columns': {
        'acq_date': 'date',
    },

    # Output settings.
    # Output csv with statvar obs for file area in s2 cells.
    'output_csv': 'firms_fires_s2_cell_areas.csv',
    # Output prefix for S2 cell place csv and tmcf.
    'output_s2_place': 's2_cell_places',
}
