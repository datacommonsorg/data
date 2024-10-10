# Config to generate FloodEvent through the script: events_pipeline.py
{
    'defaults': {
        'import_name': 'DynamicWorldFloods',
        # Set start_date to start of year to be processed.
        # Defaults to Jan 1 of current year if left empty.
        'start_date': '',
        'time_period': 'P1M',

        # GCS settings
        'gcs_project': 'datcom',
        'gcs_bucket': 'datcom-prod-imports',
        'gcs_folder': 'scripts/floods',
    },
    # State of previous run of the pipeline with input/output for each stage.
    'pipeline_state_file':
        'gs://datcom-prod-imports/scripts/floods/flood_event_pipeline_state_{year}.py',

    # Pipeline stages to generate flood events.
    'stages': [
        # Generate geoTiff from EarthEngine Dynamic World data set.
        {
            'stage': 'earthengine',

            # Image loading settings.
            'ee_dataset': 'dynamic_world',
            # Image processing settings.
            'ee_reducer': 'max',
            'band': 'water',

            # Filter by band value and remove permanent water
            'band_min': 0.7,
            'ee_mask': 'land',

            # Output image settings
            'scale': 1000,
            'gcs_folder': 'scripts/floods/{stage}',
            'ee_export_image': True,
            # Generate monthly images for a year at a time.
            # Events are processed annually from Jan-Dec.
            'ee_image_count': 12,
            'skip_existing_output': True,
        },

        # Convert geoTiff to CSV with S2 cells.
        {
            'stage':
                'raster_csv',
            's2_level':
                13,
            'aggregate':
                None,
            'input_data_filter': {
                'area': {
                    # pick max area for s2 cell.
                    # each fire in input is a fixed region.
                    'aggregate': 'max'
                },
            },

            # use output from download stage as input
            'input_files':
                'gs://{gcs_bucket}/{gcs_folder}/earthengine/*{year}*.tif',
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/{stage}',
            'skip_existing_output':
                True,
        },

        # Generate events from the CSV with flooded S2 cells per month.
        {
            'stage':
                'events',

            # Process all data files for the whole year.
            'input_files':
                'gs://{gcs_bucket}/{gcs_folder}/raster_csv/*{year}*raster_csv.csv',
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/{stage}/{import_name}-{stage}-{year}-',
            'event_type':
                'FloodEvent',

            # Input settings.
            # Columms of input_csv that are added as event properties
            'data_columns': ['area'],
            'input_rename_columns': {
                'date': 'observationDate',
            },
            # Input column for date.
            'date_column':
                'observationDate',
            # Columns of input_csv that contains the s2 cell id.
            'place_column':
                's2CellId',

            # Processing settings
            # Maximum distance within which 2 events are merged.
            'max_overlap_distance_km':
                0,
            # Maximum number of cells of same level in between 2 events to be merged.
            'max_overlap_place_hop':
                2,
            # S2 level to which data is aggregated.
            's2_level':
                10,  # Events are at resolution of level-10 S2 cells.
            'aggregate':
                'sum',  # default aggregation for all properties
            # Per property settings
            'property_config': {
                'area': {
                    'aggregate': 'sum',
                    'unit': 'SquareKilometer',
                },
                'affectedPlace': {
                    'aggregate': 'list',
                },
            },
            # Treat events at the same location more than 45 days apart as separate events.
            'max_event_interval_days':
                45,

            # Enable DC API lookup for place properties
            'dc_api_enabled':
                False,
            'dc_api_batch_size':
                200,
            # Cache file for place properties like name, location, typeOf
            # Cache is updated with new places looked up.
            'place_property_cache_file':
                'gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl',

            # Output settings.
            #'output_delimiter': ';',
            'output_delimiter':
                ',',
            'output_svobs':
                True,
            'output_affected_place_polygon':
                'geoJsonCoordinates',
            'polygon_simplification_factor':
                None,
            'output_geojon_string':
                False,

            # Output svobs per place
            'output_place_svobs':
                True,
            'output_place_svobs_properties': ['area', 'count'],
            'output_place_svobs_dates': ['YYYY-MM-DD', 'YYYY-MM', 'YYYY'],
            # Generate stats for all containedInPlaces for the event.
            # Uses the containedInPlace property in the
            # place_property_cache_file.
            'aggregate_by_contained_in_place':
                True,
        },
    ],
}
