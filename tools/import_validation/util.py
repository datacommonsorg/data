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


def filter_dataframe(df: pd.DataFrame,
                     statvar_dcids: list[str] = None,
                     regex_patterns: list[str] = None,
                     contains_all: list[str] = None) -> pd.DataFrame:
    """Filters a DataFrame based on a set of explicit, disjunctive criteria.

    This function selects rows from a DataFrame where the 'StatVar' column
    matches AT LEAST ONE of the provided filtering conditions. The results of
    applying each filter are combined using a logical OR (union).

    Args:
        df: The DataFrame to filter. It must contain a 'StatVar' column.
        statvar_dcids: A list of exact StatVar DCIDs to match.
        regex_patterns: A list of regex patterns to match against the 'StatVar'
          column.
        contains_all: A list of substrings that must ALL be present in the
          'StatVar' DCID for it to be considered a match.

    Returns:
        A new DataFrame containing only the rows that match at least one of
        the filter criteria.

    Examples:
        >>> df = pd.DataFrame({
        ...     'StatVar': [
        ...         'Count_Person_Male',
        ...         'Count_Person_Female',
        ...         'Count_Person_U18_Female',
        ...         'Amount_Debt_Government'
        ...     ]
        ... })

        **Single Filter Examples:**

        >>> # 1. Filter by a specific DCID
        >>> filter_dataframe(df, statvar_dcids=['Count_Person_Male'])
                      StatVar
        0  Count_Person_Male

        >>> # 2. Filter by a regex pattern
        >>> filter_dataframe(df, regex_patterns=['^Amount_.*'])
                               StatVar
        3  Amount_Debt_Government

        >>> # 3. Filter by substrings (all must be present)
        >>> filter_dataframe(df, contains_all=['Person', 'Female'])
                           StatVar
        1      Count_Person_Female
        2  Count_Person_U18_Female

        **Multiple Filter Example (Union):**

        >>> # 4. Filter by DCID OR regex (union of results)
        >>> filter_dataframe(
        ...     df,
        ...     statvar_dcids=['Count_Person_Male'],
        ...     regex_patterns=['^Amount_.*']
        ... )
                               StatVar
        0           Count_Person_Male
        3      Amount_Debt_Government
    """
    if not statvar_dcids and not regex_patterns and not contains_all:
        return df

    # This will hold the indices of all rows that match at least one filter
    matching_indices = set()

    if statvar_dcids:
        matching_indices.update(df[df['StatVar'].isin(statvar_dcids)].index)

    if regex_patterns:
        for pattern in regex_patterns:
            try:
                regex = re.compile(pattern)
                matches = df['StatVar'].str.match(regex, na=False)
                matching_indices.update(df[matches].index)
            except re.error:
                # If it's not a valid regex, it won't match anything.
                # We could log a warning here if needed.
                pass

    if contains_all:
        # Start with a mask of all True and progressively filter it
        combined_condition = pd.Series(True, index=df.index)
        for substring in contains_all:
            combined_condition &= df['StatVar'].str.contains(substring,
                                                             case=False)
        matching_indices.update(df[combined_condition].index)

    return df.loc[sorted(list(matching_indices))]
