{
    'defaults': {
        'import_name': 'Sample',
        'start_date': '2023-01-01',
        'time_period': 'P1Y',
        'tmp_dir': '',  # Filled in by the test
        'place_property_cache_file': 'test_data/test_s2_cells_properties.pkl',
    },
    'pipeline_state_file':
        '',  # Set by the test
    'stages': [
        {
            'stage': 'download',
            'url': 'http://sample_test.com/data/{year}',
            'output_file': '{tmp_dir}/{stage}/{year}/fire_input_data.csv',
            'skip_existing_output': 0,
        },
        # convert lat/longs to s2 cells.
        {
            'stage': 'raster_csv',
            'time_period': 'P1D',
            's2_level': 13,
            'aggregate': None,
            'input_data_filter': {
                'area': {
                    # pick max area for s2 cell.
                    # each fire in input is a fixed region.
                    'aggregate': 'max'
                },
            },
            'input_files': '{tmp_dir}/download/{year}/*.csv',
            'output_dir': '{tmp_dir}/{stage}/{year}',
        },
        {
            'stage': 'events',

            # Process all data files for the whole year.
            'input_files': '{tmp_dir}/raster_csv/{year}/*raster_csv.csv',
            'output_dir': '{tmp_dir}/{stage}/{year}/sample_fires_',
            'event_type': 'FireEvent',

            # Input settings.
            # Columms of input_csv that are added as event properties
            'data_columns': [
                'area', 'frp', 'bright_ti4', 'bright_ti5', 'confidence'
            ],
            # Columns of input_csv that contains the s2 cell id.
            'place_column': 's2CellId',
            # Input column for date.
            'date_column': 'acq_date',

            # Processing settings
            # Maximum distance within which 2 events are merged.
            'max_overlap_distance_km': 0,
            # Maximum number of cells of same level in between 2 events to be merged.
            'max_overlap_place_hop': 1,
            # S2 level to which data is aggregated.
            's2_level': 10,  # Events are at resolution of level-10 S2 cells.
            'aggregate': 'sum',  # default aggregation for all properties
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
            # Per property filter params for input data.
            'input_filter_config': {
                'confidence': {
                    'regex': '[nh]',
                }
            },
            'output_events_filter_config': {
                'AreaSqKm': {
                    # Only allow fire events with atleast 4sqkm (10%) of events.
                    'min': 2.0,
                },
            },
            # Per property settings
            'property_config': {
                'area': {
                    'aggregate': 'sum',
                    'unit': 'SquareKilometer',
                },
            },
            # Treat events at the same location beyond 3 days as separate events.
            'max_event_interval_days': 3,
            # Limit time range for an event to 3 months, roughly a season
            'max_event_duration_days': 90,
            # Limit event affected region to 1000 L10 s2 cells, roughly 100K sqkm.
            'max_event_places': 1000,

            # Enable DC API lookup for place properties
            'dc_api_enabled': False,
            'dc_api_batch_size': 200,

            # Output settings.
            'output_svobs': True,
            'output_delimiter': ',',
            'output_affected_place_polygon': 'geoJsonCoordinatesDP1',
            'polygon_simplification_factor': None,
            'output_geojson_string': True,

            # Output svobs per place
            'output_place_svobs': True,
            'output_place_svobs_properties': ['area', 'count'],
            'output_place_svobs_dates': ['YYYY-MM-DD', 'YYYY-MM', 'YYYY'],
        },
    ]
}
