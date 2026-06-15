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

import os
import pandas as pd
import re


def filter_dataframe(df: pd.DataFrame,
                     dcids: list[str] = None,
                     regex_patterns: list[str] = None,
                     contains_all: list[str] = None) -> pd.DataFrame:
    """Filters a DataFrame based on a set of explicit, disjunctive criteria.

    This function selects rows from a DataFrame where the 'StatVar' column
    matches AT LEAST ONE of the provided filtering conditions. The results of
    applying each filter are combined using a logical OR (union).

    Args:
        df: The DataFrame to filter. It must contain a 'StatVar' column.
        dcids: A list of exact StatVar DCIDs to match.
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

        >>> # 1. Filter by a specific StatVar DCID
        >>> filter_dataframe(df, dcids=['Count_Person_Male'])
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

        >>> # 4. Filter by StatVar DCID OR regex (union of results)
        >>> filter_dataframe(
        ...     df,
        ...     dcids=['Count_Person_Male'],
        ...     regex_patterns=['^Amount_.*']
        ... )
                               StatVar
        0           Count_Person_Male
        3      Amount_Debt_Government
    """
    if not dcids and not regex_patterns and not contains_all:
        return df

    # This will hold the indices of all rows that match at least one filter
    matching_indices = set()

    if dcids:
        matching_indices.update(df[df['StatVar'].isin(dcids)].index)

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


def _is_relative_local(path_val: str) -> bool:
    """Checks if a path is a relative, local file path.

    This function identifies path strings that represent local relative files
    (e.g., 'golden_data/un_wpp.csv') as opposed to absolute paths. It filters
    out non-strings, empty strings, and absolute local paths.

    Args:
        path_val: The file path string to evaluate.

    Returns:
        True if the path represents a relative, local file path; False otherwise.
    """
    if not isinstance(path_val, str) or not path_val:
        return False
    return not os.path.isabs(path_val)


def _find_base_dir(start_path: str, target_sub_path: str) -> str | None:
    """Helper to find a base directory containing a target sub-path by walking up.

    Starting from the absolute directory of `start_path`, this function recursively
    checks if `target_sub_path` exists in the current folder. If not, it walks up the 
    parent directory tree up to 8 levels. This is crucial for resolving paths relative 
    to import-specific golden directories when tests/validation are run from
    different working directories (such as the repository root in CI/CD).

    Args:
        start_path: The file or directory path to start the upward search from.
        target_sub_path: The name of the subdirectory or file (e.g., 'golden_data')
            to search for within the parent tree.

    Returns:
        The absolute path of the directory containing `target_sub_path` if found,
        or None if the root was reached or the 8-level limit was exceeded.
    """
    if not start_path:
        return None
    curr = os.path.abspath(start_path)
    for _ in range(8):  # limit to 8 levels up
        if os.path.exists(os.path.join(curr, target_sub_path)):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return None
