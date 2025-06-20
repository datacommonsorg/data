# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for the import validation tool."""

import pandas as pd
import re


def filter_dataframe(df: pd.DataFrame, filter_config: list) -> pd.DataFrame:
    """Filters a DataFrame based on a configuration.

    The filter configuration is a list that can contain:
    - Strings: Exact match on the 'StatVar' column.
    - Regex patterns: For partial or pattern matching on the 'StatVar' column.
    - Dictionaries: For matching specific property:value pairs in the StatVar DCID.

    Args:
        df: The DataFrame to filter.
        filter_config: The configuration defining the filters to apply.

    Returns:
        A new DataFrame containing only the rows that match the filter criteria.
    """
    if not filter_config:
        return df

    # This will hold the indices of all rows that match at least one filter
    matching_indices = set()

    for f in filter_config:
        if isinstance(f, str):
            # Handle both exact matches and regex patterns
            try:
                # Attempt to treat as regex
                regex = re.compile(f)
                matches = df['StatVar'].str.match(regex, na=False)
                matching_indices.update(df[matches].index)
            except re.error:
                # Treat as a literal string if regex is invalid
                matching_indices.update(df[df['StatVar'] == f].index)

        elif isinstance(f, dict):
            # Handle dictionary-based property matching
            # This is a simplified version. A more robust implementation might
            # parse the DCID into its component parts. For now, we'll use
            # string matching on the StatVar DCID.
            prop_conditions = []
            for prop, value in f.items():
                if value == '*':
                    # Match if the property exists
                    prop_conditions.append(
                        df['StatVar'].str.contains(f"{prop}="))
                else:
                    # Match the exact property:value pair
                    prop_conditions.append(
                        df['StatVar'].str.contains(f"{prop}={value}"))

            if prop_conditions:
                combined_condition = pd.concat(prop_conditions,
                                               axis=1).all(axis=1)
                matching_indices.update(df[combined_condition].index)

    return df.loc[list(matching_indices)]
