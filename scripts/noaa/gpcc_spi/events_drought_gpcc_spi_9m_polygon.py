{
    # input columns
    'input_rename_columns': {
        'spi': 'standardizedPrecipitationIndex',
    },
    'date_column': 'time',
    'place_column': 'place',
    'data_columns': [
        'area',  # area not in input, computed dynamically from the grid
    ],

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 0,
    # Maximum number of cells of same level in between 2 events to be merged.
    'max_overlap_place_hop': 1,
    # S2 level to which data is aggregated.
    #'s2_level': 10, # Events are at resolution of level-10 S2 cells.
    'aggregate': 'sum',  # default aggregation for all properties
    # Per property filter params for input data.
    'input_filter_config': {
        'standardizedPrecipitationIndex': {
            'max': -1.5,
        },
        #'time': {
        #    'min': '2020',
        #},
    },
    'output_events_filter_config': {
        #'area': {
        #    # Only allow fire events with atleast 4sqkm (10%) of events.
        #    'min': 4.0,
        #},
    },
    # Per property settings
    'property_config': {
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
        'standardizedPrecipitationIndex': {
            'aggregate': 'min',
        },
    },
    # Treat events at the same location beyond 180 days as separate events.
    'max_event_interval_days': 180,
    # Limit time range for an event to be 1 year
    'max_event_duration_days': 30,
    # Limit event affected region to 1000 places, roughly 100K sqkm.
    'max_event_places': 100,

    # Output settings.
    'event_type': 'DroughtEvent',
    'output_svobs': True,
    'output_place_svobs': True,
    'aggregate_by_contained_in_place': True,
    'output_affected_place_polygon': 'geoJsonCoordinates',
    'polygon_simplification_factor': 0.1,
    'output_geojson_string': False,  # output json dump instead of string
    'output_delimiter': ',',

    # Enable DC API lookup for place properties
    'dc_api_enabled': False,
    'dc_api_batch_size': 200,
    # Cache file for place properties like name, location, typeOf
    # Cache is updated with new places looked up.
    'place_property_cache_file': 'grid_1_place_property_cache.pkl',
}
