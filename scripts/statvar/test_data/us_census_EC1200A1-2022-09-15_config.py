{
    'match_substring_word_boundary':
        False,
    'data_key': 'Data',
    'numeric_data_key': 'Number',
    'multiply_factor': 'MultiplyFactor',
    'required_statvar_properties': [
        'measuredProperty',
        'populationType',
    ],
    # Suppress columns with constant values in csv, use value directly in tmcf
    'skip_constant_csv_columns':
        True,
    'pv_map_drop_undefined_nodes':
        False,  # Drop undefined properties/values

}
