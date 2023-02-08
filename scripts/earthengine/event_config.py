# Config settings for event aggregations.
{
    # Input settings.
    # Columms of input_csv that are added as event properties
    'data_columns': ['area'],
    'input_rename_columns': {
        'date': 'observationDate',
    },
    # Input column for date.
    'date_column': 'observationDate',
    # Columns of input_csv that contains the s2 cell id.
    'place_column': 's2CellId',

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 0,
    # Maximum number of cells of same level in between 2 events to be merged.
    'max_overlap_place_hop': 2,
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
    # Treat events at the same location more than 45 days apart as separate events.
    'max_event_interval_days': 45,

    # Output settings.
    'event_type': 'FloodEvent',
    'output_svobs': True,
    'output_active_svobs': True,
    'output_affected_place_polygon': 'geoJsonCoordinatesDP1',
}
