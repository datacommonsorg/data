# Default configuration settings for events_pipeline.py.
# Includes static settings for each stage of processing.
{
    # Defaults applied to configs of all stages
    'defaults': {
        # Change to import specific name
        'import_name': 'SampleImport',

        # Date from which to process files.
        'start_date': '',
        'time_period': 'P1M',

        # GCS folder settings for output files
        # outputs will be in: gs://<gcs_bucket>/<gcs_folder>/*
        'gcs_project': '',
        'gcs_bucket': 'datcom-prod-imports',
        'gcs_folder': '{import_name}',
    },

    # Sequence of stages with configs.
    'stages': [
        # stage config for EarthEngineRunner
        # Settings to fetch geotiff from earth engine
        # See earthentine_image.py:EE_DEFAULT_CONFIG for config parameters
        {
            'stage': 'earthengine',

            # Date from which to process files.
            # Images are generated from start_date until now
            # with one image for each time period, say month.
            'start_date': '',
            'time_period': 'P1M',

            # Image settings
            # Use the pre-configured data set in
            # earthengine_image.py:_DEFAULT_DATASETS
            # For example, use the image collection: 'DynamicWorld'
            'ee_dataset': 'dynamic-world',
            # Band in the image collection to extract as output.
            # Should be one of the bands in the image collection chosen above.
            'band': 'water',

            # reducer to aggregate band value for each point across images
            # in the image collection into a single value in the output image.
            'ee_reducer': 'max',

            # Filter by band value to generate output with points having
            # interesting values.
            'band_min': 0.7,
            # Apply a mask to include values for places where mask is set to 1
            'ee_mask': 'land',

            # Output settings
            # Output pixel resolution in meters.
            # Generates a value in the output for a region of 1000x1000m.
            'scale': 1000,
            # Export geoTif to 'gs://{gcs_bucket}/gcs_folder}/ee_image*.tif'
            'gcs_folder': '{import_name}/{stage}/{year}',

            # Wait for EE tasks to complete
            'ee_wait_task': True,

            # Generate new images only since last run.
            # Skip image generation for existing outputs generated previously.
            'skip_existing_output': True,
        },

        # stage config for DownloadRunner
        # Settings to download source data from a list of URLs.
        {
            'stage':
                'download',

            # List of URLs to download
            'url': [],

            # URL parameters for GET or POST requests
            'url_params': {},
            'http_method':
                'GET',

            # Regular expression pattern to check in the URL response.
            # Requests with responses not matching the regex are considered
            # unsuccessful and will be retried.
            # For example, look for a date column in the response CSV.
            'successful_response_regex':
                ',[0-9]{4}-[0-9]{2}-[0-9]{2},',

            # Dates to download files
            # URL is downloaded for dates from start_date to now
            # with a request made for each time_period.
            'start_date':
                '',
            'time_period':
                'P1D',

            # Retry settings.
            # Timeout in seconds for HTTP requests.
            'timeout':
                60,
            # Number of times to retry the HTTP request
            'retry_count':
                10,
            # Interval in seconds between retries for HTTP requests
            'retry_interval':
                60,

            # Output file name for file downloaded from the URL.
            # In case multiple requests are made for different dates,
            # add the date to the file name.
            'output_file':
                'gs://{gcs_bucket}/{gcs_folder}/{stage_name}/{year}/{import_name}-{stage_name}-{start_date}-{time_period}.csv',

            # Skip download if the output file exists.
            'skip_existing_output':
                True,
        },

        # stage config for RasterCSVRunner
        # Settings to convert source input data to csv
        # See raster_to_csv.py:_DEFAULT_CONFIG for config settings
        {
            'stage': 'raster_csv',

            # Input: process output from previous stage
            'input_files': '',
            'gs://{gcs_bucket}/{gcs_folder}/download/{year}/*.csv,gs://{gcs_bucket}/{gcs_folder}/earthengine/{year}/*.tif'

            # Processing parameters
            # Rename columns from input to output.
            # rename columns <input-name>: <output-name>
            # to the expected columns for processing: date, latitude, longitude
            'rename_columns': {
                # Rename columns in CSV
                'acq_date': 'date',
                'lat': 'latitude',
                'lng': 'longitude',

                # Rename bands in geoTif
                'band:0': 'water',
            },
            # Add an S2 cell of the given level for each input point.
            # For GeoTif inputs, use the lat/lng of each data value,
            # for CSV inputs, use the columns 'latitude' and 'longitude'.
            # Generate data points for leve 10 S2 cells (10x10km)
            's2_level': 10,

            # Default aggregation for data values mapped to the same s2_cell+date
            # that can be one of: min, max, mean, sum.
            # For columns specific aggregation methods,
            # use the config:'input_data_filter'.
            'aggregate': 'sum',
            # Default area for input CSVs.
            # For raster inputs, the cell area is computed from the input.
            # Use one the area or width/height options.
            # Default input point area in sqkm if constant for the whole data set.
            'default_cell_area': 0,
            # Default point/cell width/height in degrees
            # Use ~1sqkm at equator, lower near poles.
            'default_cell_width': 0.009,
            'default_cell_height': 0.009,

            # filter settings per column for data
            # input (pre-aggregation) and output (post-aggregation) of the form:
            # {
            #   '<column>' : {
            #     'min': <NN.NNN>, # Minimum value for <column>
            #     'max': <NN.NNN>, # Maximum value for <column>
            #     'aggregate': 'sum', # one of 'min','max','sum','mean'
            #   },
            #   ...
            # }
            'input_data_filter': {
                # Add up area for points added to an s2cell.
                'area': {
                    'aggregate': 'sum',
                },
                # Pick rows with confidence column set to 'n' or 'h'.
                # 'confidence': {
                #     'regex': r'[nh]',  # pick normal or high
                # }
                # 'water': {  # band:0
                #     'min': 1.0
                # },
            },
            'output_data_filter': {
                #   'area': {
                #       'min': 1.0,  # Minimum area in sqkm after aggregation
                #   },
            },

            # Output settings
            # Generate an output file in the folder for each input file
            'output_dir': 'gs://{gcs_bucket}/{gcs_folder}/{stage_name}/{year}',
            # Skip re-processing of existing output files.
            'skip_existing_output': True,
        },

        # stage config for EventsRunner
        # Settings to process data into events
        # See event_config.py for config settings.
        {
            'stage':
                'events',

            # EventType used for StatVars and tMCFs
            'event_type':
                'FloodEvent',

            # Input: use CSV generated from raster_csv
            # re-generating events for the current year.
            'input_files':
                'gs://{gcs_bucket}/{gcs_folder}/raster_csv/{year}/*.csv',

            # Output file name prefix for events, svobs CSV and tMCF
            'output_dir':
                'gs://{gcs_bucket}/{gcs_folder}/{stage}/{year}/{import_name}_',

            ### Input settings.

            # Map to rename input columns to output columns with entries as:
            #   '<input-column>': '<output-column>'
            # Rest of the configs below refer to the renamed columns.
            # Only output columns starting with lower case are added to tmcf.
            'input_rename_columns': {
                'date': 'observationDate',
            },

            # Columms of input_csv (after renaming) that are added as event properties
            'input_columns': ['area'],

            # Input CSV column (after renaming) that contain the place,
            # such as, s2 cell id generated by raster_csv
            'place_column':
                's2CellId',

            # Input CSV column (after renaming) for date.
            'date_column':
                'observationDate',

            ### Processing settings

            # Maximum distance between places that are merged into the same event.
            'max_overlap_distance_km':
                10,

            # S2 level to which data is aggregated.
            # In case input place is an S2 cell of higher level, it is aggregated into
            # a parent S2 cell of this level.
            's2_level':
                10,  # Events at level-10 S2 cells, roughly 10x10km.

            # Event property settings.
            # Default aggregation for all event properties
            'aggregate':
                'sum',
            # Per property filter params for input data.
            'input_filter_config': {
                # '<prop>' : {
                #   'min': <min>,
                #   'max': <max>,
                #   'regex': '<regex>',
                # },
                # For example: 'area': { 'min': 1 },
            },
            # Per property filter params for output events
            # Applied when output_events is True
            # Event is dropped if any property fails the filter.
            'output_events_filter_config': {
                # '<prop>' : {
                #   'min': <min>,
                #   'max': <max>,
                #   'regex': '<regex>',
                # },
                # For example: to generate events with area of atleast 10sqkm,
                # 'area' { 'min': 10 }
            },
            # Per property aggregation settings for an event across places and dates.
            # For different  per-date and per-place aggregations, use the settings
            # 'property_config_per_date' and 'property_config_across_dates'.
            'property_config': {
                'aggregate': 'max',
                'area': {
                    'aggregate': 'sum',
                    'unit': 'SquareKilometer',
                },
                'affectedPlace': {
                    'aggregate': 'list',
                },
            },
            # Per property aggregation settings for a date across multiple places.
            # Falls back to 'property_config' if not set.
            'property_config_per_date': {
                # Default aggregation for all properties: pick max value across places.
                'aggregate': 'max',
                'area': {
                    'aggregate': 'sum',
                    'unit': 'SquareKilometer',
                },
                'affectedPlace': {
                    'aggregate': 'list',
                },
            },
            # Per property aggregation settings across multiple dates.
            # Falls back to 'property_config' if not set.
            'property_config_across_dates': {
                # Default aggregation for all properties: pick max value across dates.
                'aggregate': 'max',
                'area': {
                    'aggregate': 'max',
                    'unit': 'SquareKilometer',
                },
                'affectedPlace': {
                    'aggregate': 'list',
                },
            },
            # Threshold for dates and places added to an event
            # Treat incidents at the same location more than 90 days apart as separate events.
            'max_event_interval_days':
                90,
            # Treat incidents after 90 days from start as a seperate event.
            'max_event_duration_days':
                90,
            # Treat incidents at more than 10000 places into seperate events.
            'max_event_places':
                10000,

            # Generate property aggregations by containedInPlaces such as
            # country, continent
            'aggregate_by_contained_in_place':
                True,
            # Disable parent place lookups for place dcids added to the event.
            # When disabled, parent places could be looked up using the
            # place_property_cache.
            'lookup_contained_for_place':
                False,
            # Cache file with properties for places including
            # 'name', 'containedInPlace', 'latitude' and 'longitude'.
            # It is a pickle file with a dictionary of the form:
            # {
            #   '<prop>' : {
            #     '<place-dcid>': '<place-property-value>'
            #     ...
            #   },
            #   ...
            # }
            # For example:
            # {
            #   'containedInPlace' : {
            #     'geoId/06': ['Earth', 'northamerica', 'country/USA', 'usc/PacificDivision' ]
            #   }
            #   'latitude': {
            #     'geoId/06': 37.148
            #   },
            #   'longitude': {
            #     'geoId/06': -119.540
            #   }
            # }
            'place_property_cache_file':
                'gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl',

            ### Output settings.

            # CSV delimiter for outputs
            'output_delimiter':
                ',',

            # Settings for event boundary polygons.
            # Add event boundary polygon covering all event affectedPlaces
            # as value for the property: geoJsonCoordinatesDP1
            # To skip generating event polygons, set it to None.
            'output_affected_place_polygon':
                'geoJsonCoordinatesDP1',
            # Simplify the output polygons to 0.1 degrees.
            # To disable simplification, set it to None.
            'polygon_simplification_factor':
                0.1,

            # Output svobs CSV per place
            'output_place_svobs':
                True,

            # List of properties for SVObs
            'output_place_svobs_properties': ['area', 'count'],
            # Date formats to whcih SVObs are aggregated
            'output_place_svobs_format': ['YYYY-MM-DD', 'YYYY-MM'],

            # Enable/Disable events SVObs with eventId as observationAbout
            # Disable until it is used in the UI
            'output_svobs':
                False,
            'output_active_svobs':
                False,
        },
    ],

    # File with the state from the last pipeline run
    'pipeline_state_file': ''
}
