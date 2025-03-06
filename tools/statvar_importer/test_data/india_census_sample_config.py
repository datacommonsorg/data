{
    'match_substring_word_boundary': False,
    'required_statvar_properties': [
        'measuredProperty',
        'populationType',
    ],
    # Disable matching by words in the columns header
    # 'word_delimiter': '',
    # Suppress columns with constant values in csv, use value directly in tmcf
    'skip_constant_csv_columns': True,
    'pv_map_drop_undefined_nodes': False,  # Drop undefined properties/values

    # Generate old and new statvars into MCF
    # so test outputs don't have to change even if prod schems is updated.
    'output_only_new_statvars': False,
}
