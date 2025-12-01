# Config to generate FireEvent through the script: events_pipeline.py
{
    "defaults": {
        "import_name": "FIRMSFires",
        # Set start_date to start of year to be processed.
        # Defaults to Jan 1 of current year if left empty.
        "start_date": "",
        # Aggregate events upto the end of the year from per-day source files.
        "end_date": "{year}-12-31",
        "batch_days": 1,
        "time_period": "P{batch_days}D",

        # GCS settings
        "gcs_project": "datcom",
        "gcs_bucket": "datcom-prod-imports",
        "gcs_folder": "scripts/fires/firms",
    },
    # State of previous run of the pipeline with input/output for each stage.
    "pipeline_state_file":
        "gs://datcom-prod-imports/scripts/fires/firms/flood_event_pipeline_state_{year}.py",

    # Pipeline stages to generate flood events.
    "stages": [
        # Download NASA FIRMS fires data using the API
        {
            "stage":
                "download",

            # API key for NASA FIRMS data download
            # Get a MAPS_KEY from https://firms.modaps.eosdis.nasa.gov/api/area/
            "nasa_firms_api_key":
                "<REPLACE_WITH_YOUR_KEY>",
            "nasa_data_source":
                "VIIRS_SNPP_NRT",  # upto last 60 days
            # Use this if processing data older than 60 days
            #"nasa_data_source": "VIIRS_SNPP_SP",
            "batch_days":
                1,
            "url":
                "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{nasa_firms_api_key}/{nasa_data_source}/world/{batch_days}/{start_date}",
            # API rate limits downloads.
            # retry downloads after 200 secs until a CSV with date is downloaded.
            "successful_response_regex":
                "{year}",
            "retry_interval":
                200,
            "retry_count":
                10,
            "output_file":
                "gs://{gcs_bucket}/{gcs_folder}/download/{year}/{import_name}-download-{start_date}-{time_period}.csv",
            "skip_existing_output":
                True,
        },

        # Add S2 cells to the downloaded CSV files.
        {
            "stage":
                "raster_csv",
            "time_period":
                "P{batch_days}D",
            "s2_level":
                10,
            "aggregate":
                None,
            "input_data_filter": {
                "area": {
                    # pick max area for s2 cell.
                    # each fire in input is a fixed region.
                    "aggregate": "max"
                },
            },
            "input_files":
                "gs://{gcs_bucket}/{gcs_folder}/download/{year}/{import_name}-download-{year}*.csv",
            "output_dir":
                "gs://{gcs_bucket}/{gcs_folder}/{stage}/{year}",
            "skip_existing_output":
                True,
        },

        # Generate events from the CSV with fires in S2 cells
        {
            "stage":
                "events",

            # Process all data files for the whole year.
            "input_files":
                "gs://{gcs_bucket}/{gcs_folder}/raster_csv/{year}/*{year}*.csv",
            # Output events csv into a common folder with a year in filename,
            # as the import automation can copy all files in a single folder.
            "output_dir":
                "gs://{gcs_bucket}/{gcs_folder}/{stage}/{import_name}-{stage}-{year}-without-usa-",
            "event_type":
                "FireEvent",

            # Input settings.
            # Columns of input_csv that are added as event properties
            "data_columns": [
                "area", "frp", "bright_ti4", "bright_ti5", "confidence"
            ],
            # Columns of input_csv that contains the s2 cell id.
            "place_column":
                "s2CellId",
            # Input column for date.
            "date_column":
                "acq_date",

            # Processing settings
            # Maximum distance within which 2 events are merged.
            "max_overlap_distance_km":
                0,
            # Maximum number of cells of same level in between 2 events to be merged.
            "max_overlap_place_hop":
                1,
            # S2 level to which data is aggregated.
            "s2_level":
                10,  # Events are at resolution of level-10 S2 cells.
            "aggregate":
                "sum",  # default aggregation for all properties
            # Per property settings
            "property_config": {
                "area": {
                    "aggregate": "sum",
                    "unit": "SquareKilometer",
                },
                "affectedPlace": {
                    "aggregate": "list",
                },
            },
            # Per property filter params for input data.
            "input_filter_config": {
                "confidence": {
                    "regex": "[nh]",
                }
            },
            "output_events_filter_config": {
                "AreaSqKm": {
                    # Only allow fire events with atleast 4sqkm (10%) of events.
                    "min": 4.0,
                },
                "affectedPlace": {
                    # Ignore fires in USA also generated by a different import
                    "ignore": "country/USA"
                }
            },
            # Per property settings
            "property_config": {
                "aggregate": "max",
                "area": {
                    "aggregate": "sum",
                    "unit": "SquareKilometer",
                },
            },
            # Treat events at the same location beyond 3 days as separate events.
            "max_event_interval_days":
                3,
            # Limit time range for an event to 3 months, roughly a season
            "max_event_duration_days":
                90,
            # Limit event affected region to 1000 L10 s2 cells, roughly 100K sqkm.
            "max_event_places":
                1000,

            # Enable DC API lookup for place properties
            "dc_api_enabled":
                False,
            "dc_api_batch_size":
                200,
            # Cache file for place properties like name, location, typeOf
            # Cache is updated with new places looked up.
            "place_property_cache_file":
                "gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl",

            # Output settings.
            "output_svobs":
                True,
            "output_delimiter":
                ",",
            "output_affected_place_polygon":
                "geoJsonCoordinates",
            "polygon_simplification_factor":
                None,
            "output_geojson_string":
                False,

            # Output svobs per place
            # Place svobs generated by entity aggregation pipeline
            "output_place_svobs":
                False,
            "output_place_svobs_properties": ["area", "count"],
            "output_place_svobs_dates": ["YYYY-MM-DD", "YYYY-MM", "YYYY"],
        },
    ],
}
