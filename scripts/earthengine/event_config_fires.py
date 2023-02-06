# Config settings for event aggregations.
{
    # Input settings.
    # Columms of input_csv that are added as event properties
    'data_columns': ['area', 'frp', 'bright_ti4', 'bright_ti5', 'confidence'],
    # Columns of input_csv that contains the s2 cell id.
    's2_cell_column': 's2CellId',
    # Input column for date.
    'date_column': 'date',

    # Processing settings
    # Maximum distance within which 2 events are merged.
    'max_overlap_distance_km': 0,
    # Maximum number of cells of same level in between 2 events to be merged.
    'max_overlap_distance_cell': 1,
    # S2 level to which data is aggregated.
    's2_level': 10,  # Events are at resolution of level-10 S2 cells.
    'aggregate': 'sum',  # default aggregation for all properties
    # Per property filter params for input data.
    'input_filter_config': {
        'confidence': {
            'regex': '[nh]',
        }
    },
    'output_events_filter_config': {
        'area': {
            # Only allow fire events with atleast 4sqkm (10%) of events.
            'min': 4.0,
        },
    },
    # Per property settings
    'property_config': {
        'area': {
            'aggregate': 'sum',
            'unit': 'SquareKilometer',
        },
    },
    # Treat events at the same location beyond 10 days as separate events.
    'max_event_interval_days': 10,
    # Limit time range for an event to 3 months, roughly a season
    'max_event_duration_days': 90,
    # Limit event affected region to 1000 L10 s2 cells, roughly 100K sqkm.
    'max_event_places': 1000,

    # Output settings.
    'event_type': 'FireEvent',
}
