# Config settings for event aggregations.
{
    # Input settings.
    # Columms of input_csv that are added as event properties
    'data_columns': ['area'],
    # Columns of input_csv that contains the s2 cell id.
    's2_cell_column': 's2CellId',
    # Input column for date.
    'date_column': 'date',

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 10,
    # S2 level to which data is aggregated.
    's2_level': 10,  # Events are at resolution of level-10 S2 cells.
    'aggregate': 'sum',  # default aggregation for all properties
    # Per property settings
    'property_config': {
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
    },
    # Treat events at the same location more than 90 days apart as separate events.
    'max_event_interval_days': 90,

    # Output settings.
    'event_type': 'FloodEvent',
}
