# Config settings for generating events with process_events.py
{
    # EventType used for StatVars and tMCFs
    'event_type': 'FloodEvent',

    ### Input settings.

    # Delimiter in the input CSV
    'input_delimiter': ',',

    # Map to rename input columns to output columns with entries as:
    #   '<input-column>': '<output-column>'
    # Rest of the configs below refer to the renamed columns.
    # Only output columns starting with lower case are added to tmcf.
    'input_rename_columns': {
        'date': 'observationDate',
    },

    # Columms of input_csv (after renaming) that are added as event properties
    'input_columns': ['area'],

    # Input CSV column (after renaming) that contain the place, such as, s2 cell id.
    'place_column': 's2CellId',

    # Input CSV column (after renaming) for date.
    'date_column': 'observationDate',

    ### Processing settings

    # Maximum distance between places that are merged into the same event.
    'max_overlap_distance_km': 10,

    # S2 level to which data is aggregated.
    # In case input place is an S2 cell of higher level, it is aggregated into
    # a parent S2 cell of this level.
    's2_level': 10,  # Events at level-10 S2 cells, roughly 10x10km.

    # Event property settings.
    # Default aggregation for all event properties
    'aggregate': 'sum',
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
    'max_event_interval_days': 90,
    # Treat incidents after 90 days from start as a seperate event.
    'max_event_duration_days': 90,
    # Treat incidents at more than 10000 places into seperate events.
    'max_event_places': 10000,

    # Generate property aggregations by containedInPlaces such as
    # country, continent
    'aggregate_by_contained_in_place': True,
    # Disable parent place lookups for place dcids added to the event.
    # When disabled, parent places could be looked up using the
    # place_property_cache.
    'lookup_contained_for_place': False,
    # Cache file with properties for places.
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
    'place_property_cache_file': '',

    ### Output settings.

    # CSV delimiter for outputs
    'output_delimiter': ',',

    # Settings for event boundary polygons.
    # Add event boundary polygon covering all event affectedPlaces
    # as value for the property: geoJsonCoordinatesDP1
    # To skip generating event polygons, set it to None.
    'output_affected_place_polygon': 'geoJsonCoordinatesDP1',
    # Simplify the output polygons to 0.1 degrees.
    # To disable simplification, set it to None.
    'polygon_simplification_factor': 0.1,

    # Output svobs CSV per place
    'output_place_svobs': True,

    # List of properties for SVObs
    'output_place_svobs_properties': ['area', 'count'],
    # Date formats to whcih SVObs are aggregated
    'output_place_svobs_format': ['YYYY-MM-DD', 'YYYY-MM'],

    # Enable/Disable events SVObs with eventId as observationAbout
    # Disable until it is used in the UI
    'output_svobs': False,
    'output_active_svobs': False,
}
