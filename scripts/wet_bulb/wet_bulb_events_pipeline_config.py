# Config to generate WetBulbTemperatureEvent through the script: events_pipeline.py
{
    'defaults': {
        'import_name': 'NASAWetBulb',
        # Set start_date to start of year to be processed.
        # Defaults to Jan 1 of current year if left empty.
        'start_date': '',
        'end_date': '',
        'time_period': 'P1D',

        # GCS settings
        'gcs_project': 'datcom',
        'gcs_bucket': 'datcom-prod-imports',
        'gcs_folder': 'scripts/wet_bulb',
    },
    # State of previous run of the pipeline with input/output for each stage.
    'pipeline_state_file':
        'gs://datcom-prod-imports/scripts/wet_bulb/wet_bulb_event_pipeline_state_{year}.py',

    # Pipeline stages to generate wet_bulb events.
    'stages': [
        # Generate geoTiff from EarthEngine Dynamic World data set.
        {
            'stage': 'earthengine',

            # EE dataset from NASA/GSFC/MERRA
            # https://developers.google.com/earth-engine/datasets/catalog/NASA_GSFC_MERRA_slv_2#description
            'ee_image_collection': 'NASA/GSFC/MERRA/slv/2',
            # Image processing settings.
            'ee_reducer': 'max',

            # Filter by min web bulb temperature of 32 deg C
            'band': 'T2MWET',
            'band_min': 303,  # 273.15(K) + 30,
            # preserve the original temp after filtering by min threshold.
            'ee_band_bool': False,
            'ee_mask': 'land',

            # Output image settings
            'ee_output_data_type': 'float',
            'scale': 10000,
            'gcs_folder': 'scripts/wet_bulb/{stage}/{year}',
            'ee_export_image': True,
            # Generate daily images for a year at a time.
            # Events are processed annually from Jan-Dec.
            'ee_image_count': 365,
            # 'ee_image_count': 31,
            'skip_existing_output': True,
        },

        # Convert geoTiff to CSV with S2 cells.
        {
            'stage':
                'raster_csv',
            # debug
            #'debug': True,
            #'limit_points': 10,
            's2_level':
                10,
            'aggregate':
                'max',
            'rename_columns': {
                'band:1': 'T2MWET',
            },
            'input_data_filter': {
                # Convert WetBulbTemperature to Celsius
                'area': {
                    # pick max area for s2 cell.
                    'aggregate': 'max'
                },
                'T2MWET': {
                    # convert value from Kelvin to Celsius
                    'eval': '{T2MWET}-273.15',
                    # Pick s2Cells with a min wetBulbTemperature
                    'min': 28,
                    'aggregate': 'max',
                }
            },

            # use output from download stage as input
            'input_files':
                'gs://{gcs_bucket}/{gcs_folder}/earthengine/*{year}*.tif',
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/{stage}/{year}',
            'skip_existing_output':
                True,
        },

        # Generate events from the CSV with wet_bulbed S2 cells per month.
        {
            'stage':
                'events',

            # Process all data files for the whole year.
            'input_files':
                'tmp/fixed-temp/*.csv',
            #'input_files':
            #    'gs://{gcs_bucket}/{gcs_folder}/raster_csv/{year}/*{year}*raster_csv.csv',
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/{stage}/{import_name}-{stage}-{year}-',
            'event_type':
                'WetBulbTemperatureEvent',

            # Input settings.
            # Columms of input_csv that are added as event properties
            'data_columns': ['area', 'T2MWET'],
            'input_rename_columns': {
                'date': 'observationDate',
                'T2MWET': 'wetBulbTemperature',
            },
            # Input column for date.
            'date_column':
                'observationDate',
            # Columns of input_csv that contains the s2 cell id.
            'place_column':
                's2CellId',
            'input_filter_config': {
                'wetBulbTemperature': {
                    'min': 30,
                },
            },

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
                'max',  # default aggregation for all properties
            # Per property settings
            'property_config': {
                'area': {
                    'aggregate': 'sum',
                    'unit': 'SquareKilometer',
                },
                'wetBulbTemperature': {
                    'aggregate': 'max',
                    'unit': 'Celsius',
                },
                'affectedPlace': {
                    'aggregate': 'list',
                },
            },
            # Treat events at the same location more than 7 days apart as separate events.
            'max_event_interval_days':
                7,

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
                True,

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
