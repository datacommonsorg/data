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
"""Module for the Validator class."""

import duckdb
import pandas as pd
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from result import ValidationResult, ValidationStatus


class Validator:
    """
  Contains the core logic for all validation rules.
  This class is stateless and does not interact with the filesystem.
  """

    def validate_sql(self, stats_df: pd.DataFrame, differ_df: pd.DataFrame,
                     params: dict) -> ValidationResult:
        """Runs a SQL query to validate the data.

    Args:
        stats_df: A DataFrame containing the summary statistics.
        differ_df: A DataFrame containing the differ output.
        params: A dictionary containing the validation parameters, which must
          have 'query' and 'condition' keys.

    Returns:
        A ValidationResult object.
    """
        if 'query' not in params or 'condition' not in params:
            return ValidationResult(
                ValidationStatus.CONFIG_ERROR,
                'SQL_VALIDATOR',
                message=
                "Configuration error: 'query' and 'condition' must be specified for SQL_VALIDATOR."
            )

        try:
            con = duckdb.connect(database=':memory:', read_only=False)
            con.register('stats', stats_df)
            con.register('differ', differ_df)

            final_query = f"""
            WITH data_to_validate AS (
                {params['query']}
            )
            SELECT *
            FROM data_to_validate
            WHERE NOT ({params['condition']})
            """
            failing_df = con.execute(final_query).fetchdf()

            if failing_df.empty:
                return ValidationResult(ValidationStatus.PASSED,
                                        'SQL_VALIDATOR')

            return ValidationResult(
                ValidationStatus.FAILED,
                'SQL_VALIDATOR',
                message=f"{len(failing_df)} rows failed the SQL validation.",
                details={'failing_rows': failing_df.to_dict('records')})

        except duckdb.Error as e:
            return ValidationResult(ValidationStatus.CONFIG_ERROR,
                                    'SQL_VALIDATOR',
                                    message=f"SQL Error: {e}")

    def validate_max_date_latest(self, stats_df: pd.DataFrame,
                                 params: dict) -> ValidationResult:
        """Checks that the MaxDate in the stats summary is from the current year.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'MaxDate' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'MaxDate' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MAX_DATE_LATEST',
                message="Input data is missing required column: 'MaxDate'.")

        rows_processed = len(stats_df)
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MAX_DATE_LATEST',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        stats_df['MaxDate'] = pd.to_datetime(stats_df['MaxDate'])
        max_date_year = stats_df['MaxDate'].dt.year.max()
        current_year = pd.to_datetime('today').year

        if max_date_year < current_year:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MAX_DATE_LATEST',
                message=
                f"Latest date found was {max_date_year}, expected {current_year}.",
                details={
                    'latest_date_found': int(max_date_year),
                    'expected_latest_date': int(current_year),
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'MAX_DATE_LATEST',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_deleted_count(self, differ_df: pd.DataFrame,
                               params: dict) -> ValidationResult:
        """Checks if the total number of deleted points is within a threshold.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have a
        'DELETED' column.
      params: A dictionary containing the validation parameters, which may
        have a 'threshold' key.

    Returns:
      A ValidationResult object.
    """
        if differ_df.empty:
            deleted_count = 0
            threshold = params.get('threshold', 0)
            if deleted_count > threshold:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    'DELETED_COUNT',
                    message=
                    f"Found {deleted_count} deleted points, which is over the threshold of {threshold}.",
                    details={
                        'deleted_count': int(deleted_count),
                        'threshold': threshold,
                        'rows_processed': 0,
                        'rows_succeeded': 0,
                        'rows_failed': 0
                    })
            return ValidationResult(ValidationStatus.PASSED,
                                    'DELETED_COUNT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        if 'DELETED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'DELETED_COUNT',
                message="Input data is missing required column: 'DELETED'.")

        rows_processed = len(differ_df)
        threshold = params.get('threshold', 0)
        deleted_count = differ_df['DELETED'].sum()

        if deleted_count > threshold:
            return ValidationResult(
                ValidationStatus.FAILED,
                'DELETED_COUNT',
                message=
                f"Found {deleted_count} deleted points, which is over the threshold of {threshold}.",
                details={
                    'deleted_count': int(deleted_count),
                    'threshold': threshold,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'DELETED_COUNT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_modified_count(self, differ_df: pd.DataFrame,
                                params: dict) -> ValidationResult:
        """Checks if the number of modified points is the same for all StatVars.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have a
        'MODIFIED' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if differ_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MODIFIED_COUNT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        if 'MODIFIED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MODIFIED_COUNT',
                message="Input data is missing required column: 'MODIFIED'.")

        rows_processed = len(differ_df)
        unique_counts = differ_df['MODIFIED'].nunique()

        if unique_counts > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MODIFIED_COUNT',
                message=
                "The number of modified data points is not consistent across all StatVars",
                details={
                    'distinct_statvar_count': differ_df['StatVar'].nunique(),
                    'distinct_modified_counts': unique_counts,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'MODIFIED_COUNT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_added_count(self, differ_df: pd.DataFrame,
                             params: dict) -> ValidationResult:
        """Checks if the number of added points is the same for all StatVars.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have an
        'ADDED' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if differ_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'ADDED_COUNT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        if 'ADDED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'ADDED_COUNT',
                message="Input data is missing required column: 'ADDED'.")

        rows_processed = len(differ_df)
        unique_counts = differ_df['ADDED'].nunique()

        if unique_counts > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'ADDED_COUNT',
                message=
                "The number of added data points is not consistent across all StatVars.",
                details={
                    'distinct_statvar_count': differ_df['StatVar'].nunique(),
                    'distinct_added_counts': unique_counts,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'ADDED_COUNT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_num_places_consistent(self, stats_df: pd.DataFrame,
                                       params: dict) -> ValidationResult:
        """Checks if the number of places is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'NumPlaces' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'NumPlaces' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'NUM_PLACES_CONSISTENT',
                message="Input data is missing required column: 'NumPlaces'.")

        rows_processed = len(stats_df)
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'NUM_PLACES_CONSISTENT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        unique_counts = stats_df['NumPlaces'].nunique()

        if unique_counts > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'NUM_PLACES_CONSISTENT',
                message=
                "The number of places is not consistent across all StatVars.",
                details={
                    'distinct_statvar_count': stats_df['StatVar'].nunique(),
                    'distinct_place_counts': unique_counts,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'NUM_PLACES_CONSISTENT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_num_places_count(self, stats_df: pd.DataFrame,
                                  params: dict) -> ValidationResult:
        """Checks if the number of places for each StatVar is within a defined range.

    The range can be specified using 'minimum', 'maximum', or an exact 'value'
    in the params.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'NumPlaces' and 'StatVar' columns.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'NumPlaces' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'NUM_PLACES_COUNT',
                message="Input data is missing required column: 'NumPlaces'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'NUM_PLACES_COUNT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        min_val = params.get('minimum')
        max_val = params.get('maximum')
        exact_val = params.get('value')

        rows_processed = len(stats_df)
        rows_failed = 0
        failed_rows_details = []

        for _, row in stats_df.iterrows():
            value = row['NumPlaces']
            stat_var = row.get('StatVar', 'Unknown')
            failed = False

            if exact_val is not None and value != exact_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'expected_value': exact_val,
                    'reason': f"Expected exactly {exact_val}"
                })
            elif min_val is not None and value < min_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'minimum': min_val,
                    'reason': f"Below minimum of {min_val}"
                })
            elif max_val is not None and value > max_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'maximum': max_val,
                    'reason': f"Above maximum of {max_val}"
                })

            if failed:
                rows_failed += 1

        rows_succeeded = rows_processed - rows_failed

        if rows_failed > 0:
            return ValidationResult(
                ValidationStatus.FAILED,
                'NUM_PLACES_COUNT',
                message=
                f"{rows_failed} out of {rows_processed} rows failed the range check.",
                details={
                    'failed_rows': failed_rows_details,
                    'rows_processed': rows_processed,
                    'rows_succeeded': rows_succeeded,
                    'rows_failed': rows_failed
                })

        return ValidationResult(ValidationStatus.PASSED,
                                'NUM_PLACES_COUNT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_succeeded,
                                    'rows_failed': rows_failed
                                })

    def validate_min_value_check(self, stats_df: pd.DataFrame,
                                 params: dict) -> ValidationResult:
        """Checks if the MinValue for each StatVar is not below a defined minimum.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'MinValue' and 'StatVar' columns.
      params: A dictionary containing the validation parameters, which must
        have a 'minimum' key.

    Returns:
      A ValidationResult object.
    """
        if 'minimum' not in params:
            return ValidationResult(
                ValidationStatus.CONFIG_ERROR,
                'MIN_VALUE_CHECK',
                message="Configuration error: 'minimum' key not specified.")
        if 'MinValue' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MIN_VALUE_CHECK',
                message="Input data is missing required column: 'MinValue'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MIN_VALUE_CHECK',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        min_val = params['minimum']
        rows_processed = len(stats_df)
        rows_failed = 0
        failed_rows_details = []

        for _, row in stats_df.iterrows():
            min_value = row['MinValue']
            stat_var = row.get('StatVar', 'Unknown')

            if min_value < min_val:
                rows_failed += 1
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_min_value': min_value,
                    'minimum': min_val
                })

        rows_succeeded = rows_processed - rows_failed

        if rows_failed > 0:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MIN_VALUE_CHECK',
                message=
                f"{rows_failed} out of {rows_processed} StatVars failed the minimum value check.",
                details={
                    'failed_rows': failed_rows_details,
                    'rows_processed': rows_processed,
                    'rows_succeeded': rows_succeeded,
                    'rows_failed': rows_failed
                })

        return ValidationResult(ValidationStatus.PASSED,
                                'MIN_VALUE_CHECK',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_succeeded,
                                    'rows_failed': rows_failed
                                })

    def validate_max_date_consistent(self, stats_df: pd.DataFrame,
                                     params: dict) -> ValidationResult:
        """Checks if the MaxDate is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'MaxDate' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'MaxDate' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MAX_DATE_CONSISTENT',
                message="Input data is missing required column: 'MaxDate'.")

        rows_processed = len(stats_df)
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MAX_DATE_CONSISTENT',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        unique_dates = stats_df['MaxDate'].nunique()

        if unique_dates > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MAX_DATE_CONSISTENT',
                message="The MaxDate is not consistent across all StatVars.",
                details={
                    'distinct_statvar_count': stats_df['StatVar'].nunique(),
                    'distinct_max_date_counts': unique_dates,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'MAX_DATE_CONSISTENT',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_num_observations_check(self, stats_df: pd.DataFrame,
                                        params: dict) -> ValidationResult:
        """Checks if the number of observations for each StatVar is within a defined range.

    The range can be specified using 'minimum', 'maximum', or an exact 'value'
    in the params.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'NumObservations' and 'StatVar' columns.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'NumObservations' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'NUM_OBSERVATIONS_CHECK',
                message=
                "Input data is missing required column: 'NumObservations'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'NUM_OBSERVATIONS_CHECK',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        min_val = params.get('minimum')
        max_val = params.get('maximum')
        exact_val = params.get('value')

        rows_processed = len(stats_df)
        rows_failed = 0
        failed_rows_details = []

        for _, row in stats_df.iterrows():
            value = row['NumObservations']
            stat_var = row.get('StatVar', 'Unknown')
            failed = False

            if exact_val is not None and value != exact_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'expected_value': exact_val,
                    'reason': f"Expected exactly {exact_val}"
                })
            elif min_val is not None and value < min_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'minimum': min_val,
                    'reason': f"Below minimum of {min_val}"
                })
            elif max_val is not None and value > max_val:
                failed = True
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_value': value,
                    'maximum': max_val,
                    'reason': f"Above maximum of {max_val}"
                })

            if failed:
                rows_failed += 1

        rows_succeeded = rows_processed - rows_failed

        if rows_failed > 0:
            return ValidationResult(
                ValidationStatus.FAILED,
                'NUM_OBSERVATIONS_CHECK',
                message=
                f"{rows_failed} out of {rows_processed} rows failed the range check.",
                details={
                    'failed_rows': failed_rows_details,
                    'rows_processed': rows_processed,
                    'rows_succeeded': rows_succeeded,
                    'rows_failed': rows_failed
                })

        return ValidationResult(ValidationStatus.PASSED,
                                'NUM_OBSERVATIONS_CHECK',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_succeeded,
                                    'rows_failed': rows_failed
                                })

    def validate_unit_consistency(self, stats_df: pd.DataFrame,
                                  params: dict) -> ValidationResult:
        """Checks if the unit is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'Units' column.
      params: A dictionary containing the validation parameters.

    Returns:
      A ValidationResult object.
    """
        if 'Units' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'UNIT_CONSISTENCY_CHECK',
                message="Input data is missing required column: 'Units'.")

        rows_processed = len(stats_df)
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'UNIT_CONSISTENCY_CHECK',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        unique_units = stats_df['Units'].nunique()

        if unique_units > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'UNIT_CONSISTENCY_CHECK',
                message="The unit is not consistent across all StatVars.",
                details={
                    'distinct_statvar_count': stats_df['StatVar'].nunique(),
                    'distinct_unit_counts': unique_units,
                    'rows_processed': rows_processed,
                    'rows_succeeded': 0,
                    'rows_failed': rows_processed
                })
        return ValidationResult(ValidationStatus.PASSED,
                                'UNIT_CONSISTENCY_CHECK',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_processed,
                                    'rows_failed': 0
                                })

    def validate_max_value_check(self, stats_df: pd.DataFrame,
                                 params: dict) -> ValidationResult:
        """Checks if the MaxValue for each StatVar is not above a defined maximum.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'MaxValue' and 'StatVar' columns.
      params: A dictionary containing the validation parameters, which must
        have a 'maximum' key.

    Returns:
      A ValidationResult object.
    """
        if 'maximum' not in params:
            return ValidationResult(
                ValidationStatus.CONFIG_ERROR,
                'MAX_VALUE_CHECK',
                message="Configuration error: 'maximum' key not specified.")
        if 'MaxValue' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MAX_VALUE_CHECK',
                message="Input data is missing required column: 'MaxValue'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MAX_VALUE_CHECK',
                                    details={
                                        'rows_processed': 0,
                                        'rows_succeeded': 0,
                                        'rows_failed': 0
                                    })

        max_val = params['maximum']
        rows_processed = len(stats_df)
        rows_failed = 0
        failed_rows_details = []

        for _, row in stats_df.iterrows():
            max_value = row['MaxValue']
            stat_var = row.get('StatVar', 'Unknown')

            if max_value > max_val:
                rows_failed += 1
                failed_rows_details.append({
                    'stat_var': stat_var,
                    'actual_max_value': max_value,
                    'maximum': max_val
                })

        rows_succeeded = rows_processed - rows_failed

        if rows_failed > 0:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MAX_VALUE_CHECK',
                message=
                f"{rows_failed} out of {rows_processed} StatVars failed the maximum value check.",
                details={
                    'failed_rows': failed_rows_details,
                    'rows_processed': rows_processed,
                    'rows_succeeded': rows_succeeded,
                    'rows_failed': rows_failed
                })

        return ValidationResult(ValidationStatus.PASSED,
                                'MAX_VALUE_CHECK',
                                details={
                                    'rows_processed': rows_processed,
                                    'rows_succeeded': rows_succeeded,
                                    'rows_failed': rows_failed
                                })
