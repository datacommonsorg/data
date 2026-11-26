# Dictionary of config parameters and values.
{
    # Keep False: stat_var_processor.py:978 (`statvars_with_obs.add(statvar)`)
    # fails to retain referenced `Count_Student_*` denominator StatVars that
    # lack direct observations (and denominators use `dcid:` prefix).
    'drop_statvars_without_svobs': False,
    'header_columns': 0,
    'header_rows': 1,
    'mapped_columns': '6,7,9,10,14',
    # Keep False: enabling `output_only_new_statvars` causes mcf_filter.py:109
    # -> mcf_file_util.py:375 (`check_nodes_can_merge`) to increment
    # `error-node-merge-conflict` and fail because `/v2/node` returns
    # `definition` absent from local nodes and `_STATVAR_DCID_IGNORE_PROPS`.
    'output_only_new_statvars': False,
    'output_precision_digits': None,
    # Keep False to preserve the fixed 8-column CSV/TMCF contract rather than
    # folding shard-constant columns (such as `observationAbout`) into TMCF.
    'skip_constant_csv_columns': False,
    'spell_allow_words': ['std', 'performa'],
    'word_delimiter': '',
}