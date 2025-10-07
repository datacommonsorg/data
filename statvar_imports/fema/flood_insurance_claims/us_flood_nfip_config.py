{
    # NFIP Insurance claims data url
    'data_url':
        'https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv',
    # Shard files by state to allow aggregations by time, place, statvar.
    #'shard_input_by_column':
    #    'state',
    #'shard_prefix_length':
    #    2,
    # Process shards in parallel
    #'parallelism':
    #    16,
    'schemaless':
        False,
    'schemaless_statvar_comment_undefined_pvs':
        False,
    'required_statvar_properties': [
        'measuredProperty',
        'populationType',
    ],
    'data_key':
        'Data',
    'numeric_data_key':
        'Number',
    # Suppress columns with constant values in csv, use value directly in tmcf
    'skip_constant_csv_columns':
        True,
    'pv_map_drop_undefined_nodes':
        False,  # Drop undefined properties/values
    'required_statvar_properties': [
        'measuredProperty',
        #'populationType',
    ],

    # Input settings.
    # PV mappings only for 1 header row.
    # Rest of the file is data values with no PV lookup required.
    'header_rows':
        1,
    'header_columns':
        0,
    # Aggregation settings
    'merged_pvs_property':
        '',  # Don't save list of merged SVObs.

    # Output settings.
    # Output all SVobs columns even if it has a constant value
    # so a single tmcf can be used with multiple csv files.
    'output_csv_columns': [
        'observationDate',
        'observationAbout',
        'value',
        'unit',
        'observationPeriod',
        'variableMeasured',
    ],

    # Value in a row is applicale to multiple places: Census tract, County,
    # and State as well as multiple dates: Month and Year.
    'multi_value_properties': [
        'observationAbout', 'observationDate', 'floodZoneType'
    ],

    # DC API settings.
    'dc_api_retries':
        3,
    'dc_api_retry_secs':
        5,
    'dc_api_use_cache':
        True,
    #'dc_api_root': 'http://autopush.api.datacommons.org',
    'dc_api_root':
        'http://api.datacommons.org',
}
