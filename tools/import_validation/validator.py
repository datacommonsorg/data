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

import pandas as pd
from .result import ValidationResult, ValidationStatus


class Validator:
    """
  Contains the core logic for all validation rules.
  This class is stateless and does not interact with the filesystem.
  """

    def validate_max_date_latest(self, stats_df: pd.DataFrame,
                                 config: dict) -> ValidationResult:
        """Checks that the MaxDate in the stats summary is from the current year.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'MaxDate' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'MaxDate' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MAX_DATE_LATEST',
                message="Input data is missing required column: 'MaxDate'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED, 'MAX_DATE_LATEST')

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
                    'expected_latest_date': int(current_year)
                })
        return ValidationResult(ValidationStatus.PASSED, 'MAX_DATE_LATEST')

    def validate_deleted_count(self, differ_df: pd.DataFrame,
                               config: dict) -> ValidationResult:
        """Checks if the total number of deleted points is within a threshold.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have a
        'DELETED' column.
      config: A dictionary containing the validation configuration, which may
        have a 'threshold' key.

    Returns:
      A ValidationResult object.
    """
        if 'DELETED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'DELETED_COUNT',
                message="Input data is missing required column: 'DELETED'.")
        if differ_df.empty:
            return ValidationResult(ValidationStatus.PASSED, 'DELETED_COUNT')
        threshold = config.get('threshold', 0)
        deleted_count = differ_df['DELETED'].sum()
        if deleted_count > threshold:
            return ValidationResult(
                ValidationStatus.FAILED,
                'DELETED_COUNT',
                message=
                f"Found {deleted_count} deleted points, which is over the threshold of {threshold}.",
                details={
                    'deleted_count': int(deleted_count),
                    'threshold': threshold
                })
        return ValidationResult(ValidationStatus.PASSED, 'DELETED_COUNT')

    def validate_modified_count(self, differ_df: pd.DataFrame,
                                config: dict) -> ValidationResult:
        """Checks if the number of modified points is the same for all StatVars.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have a
        'MODIFIED' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'MODIFIED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MODIFIED_COUNT',
                message="Input data is missing required column: 'MODIFIED'.")
        if differ_df.empty:
            return ValidationResult(ValidationStatus.PASSED, 'MODIFIED_COUNT')
        unique_counts = differ_df['MODIFIED'].nunique()
        if unique_counts > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MODIFIED_COUNT',
                message=
                f"Found {unique_counts} unique modified counts where 1 was expected.",
                details={'unique_counts': list(differ_df['MODIFIED'].unique())})
        return ValidationResult(ValidationStatus.PASSED, 'MODIFIED_COUNT')

    def validate_added_count(self, differ_df: pd.DataFrame,
                             config: dict) -> ValidationResult:
        """Checks if the number of added points is the same for all StatVars.

    Args:
      differ_df: A DataFrame containing the differ output, expected to have an
        'ADDED' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'ADDED' not in differ_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'ADDED_COUNT',
                message="Input data is missing required column: 'ADDED'.")
        if differ_df.empty:
            return ValidationResult(ValidationStatus.PASSED, 'ADDED_COUNT')
        unique_counts = differ_df['ADDED'].nunique()
        if unique_counts != 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'ADDED_COUNT',
                message=
                f"Found {unique_counts} unique added counts where 1 was expected.",
                details={'unique_counts': list(differ_df['ADDED'].unique())})
        return ValidationResult(ValidationStatus.PASSED, 'ADDED_COUNT')

    def validate_unmodified_count(self, differ_df: pd.DataFrame,
                                  config: dict) -> ValidationResult:
        """Checks if the number of unmodified points is the same for all StatVars.

    Note: The logic for this validation is currently disabled.

    Args:
      differ_df: A DataFrame containing the differ output.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object, which is always PASSED.
    """
        # The logic for this validation is currently disabled.
        # This method is a placeholder to ensure the validation "passes".
        return ValidationResult(ValidationStatus.PASSED, 'UNMODIFIED_COUNT')

    def validate_num_places_consistent(self, stats_df: pd.DataFrame,
                                       config: dict) -> ValidationResult:
        """Checks if the number of places is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'NumPlaces' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'NumPlaces' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'NUM_PLACES_CONSISTENT',
                message="Input data is missing required column: 'NumPlaces'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'NUM_PLACES_CONSISTENT')
        unique_counts = stats_df['NumPlaces'].nunique()
        if unique_counts > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'NUM_PLACES_CONSISTENT',
                message=
                f"Found {unique_counts} unique place counts where 1 was expected.",
                details={'unique_counts': list(stats_df['NumPlaces'].unique())})
        return ValidationResult(ValidationStatus.PASSED,
                                'NUM_PLACES_CONSISTENT')

    def _validate_range(self, df: pd.DataFrame, column_name: str, config: dict,
                        validation_name: str) -> ValidationResult:
        """Helper function to check if values in a column are within a defined range.

    Args:
        df: The DataFrame to validate.
        column_name: The name of the column to check.
        config: A dictionary containing the validation configuration, which may
          have 'minimum', 'maximum', or 'value' keys.
        validation_name: The name of the validation rule.

    Returns:
        A ValidationResult object.
    """
        if column_name not in df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                validation_name,
                message=
                f"Input data is missing required column: '{column_name}'.")
        if df.empty:
            return ValidationResult(ValidationStatus.PASSED, validation_name)

        min_val = config.get('minimum')
        max_val = config.get('maximum')
        exact_val = config.get('value')

        for _, row in df.iterrows():
            value = row[column_name]
            stat_var = row.get(
                'StatVar', 'Unknown'
            )  # Assuming StatVar column exists for better error messages

            if exact_val is not None and value != exact_val:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    validation_name,
                    message=
                    f"StatVar '{stat_var}' has {value} for {column_name}, but expected exactly {exact_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': value,
                        'expected_count': exact_val
                    })
            if min_val is not None and value < min_val:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    validation_name,
                    message=
                    f"StatVar '{stat_var}' has {value} for {column_name}, which is below the minimum of {min_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': value,
                        'minimum': min_val
                    })
            if max_val is not None and value > max_val:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    validation_name,
                    message=
                    f"StatVar '{stat_var}' has {value} for {column_name}, which is above the maximum of {max_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_count': value,
                        'maximum': max_val
                    })

        return ValidationResult(ValidationStatus.PASSED, validation_name)

    def validate_num_places_count(self, stats_df: pd.DataFrame,
                                  config: dict) -> ValidationResult:
        """Checks if the number of places for each StatVar is within a defined range.

    The range can be specified using 'minimum', 'maximum', or an exact 'value'
    in the config.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'NumPlaces' and 'StatVar' columns.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        return self._validate_range(stats_df, 'NumPlaces', config,
                                    'NUM_PLACES_COUNT')

    def validate_min_value_check(self, stats_df: pd.DataFrame,
                                 config: dict) -> ValidationResult:
        """Checks if the MinValue for each StatVar is not below a defined minimum.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'MinValue' and 'StatVar' columns.
      config: A dictionary containing the validation configuration, which must
        have a 'minimum' key.

    Returns:
      A ValidationResult object.
    """
        if 'minimum' not in config:
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
            return ValidationResult(ValidationStatus.PASSED, 'MIN_VALUE_CHECK')

        min_val = config['minimum']
        for _, row in stats_df.iterrows():
            min_value = row['MinValue']
            stat_var = row.get('StatVar', 'Unknown')

            if min_value < min_val:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    'MIN_VALUE_CHECK',
                    message=
                    f"StatVar '{stat_var}' has a minimum value of {min_value}, which is below the required minimum of {min_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_min_value': min_value,
                        'minimum': min_val
                    })
        return ValidationResult(ValidationStatus.PASSED, 'MIN_VALUE_CHECK')

    def validate_max_date_consistent(self, stats_df: pd.DataFrame,
                                     config: dict) -> ValidationResult:
        """Checks if the MaxDate is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'MaxDate' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'MaxDate' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'MAX_DATE_CONSISTENT',
                message="Input data is missing required column: 'MaxDate'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'MAX_DATE_CONSISTENT')
        unique_dates = stats_df['MaxDate'].nunique()
        if unique_dates > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'MAX_DATE_CONSISTENT',
                message=
                f"Found {unique_dates} unique MaxDates where 1 was expected.",
                details={'unique_dates': list(stats_df['MaxDate'].unique())})
        return ValidationResult(ValidationStatus.PASSED, 'MAX_DATE_CONSISTENT')

    def validate_num_observations_check(self, stats_df: pd.DataFrame,
                                        config: dict) -> ValidationResult:
        """Checks if the number of observations for each StatVar is within a defined range.

    The range can be specified using 'minimum', 'maximum', or an exact 'value'
    in the config.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'NumObservations' and 'StatVar' columns.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        return self._validate_range(stats_df, 'NumObservations', config,
                                    'NUM_OBSERVATIONS_CHECK')

    def validate_unit_consistency(self, stats_df: pd.DataFrame,
                                  config: dict) -> ValidationResult:
        """Checks if the unit is the same for all StatVars.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        a 'Units' column.
      config: A dictionary containing the validation configuration.

    Returns:
      A ValidationResult object.
    """
        if 'Units' not in stats_df.columns:
            return ValidationResult(
                ValidationStatus.DATA_ERROR,
                'UNIT_CONSISTENCY_CHECK',
                message="Input data is missing required column: 'Units'.")
        if stats_df.empty:
            return ValidationResult(ValidationStatus.PASSED,
                                    'UNIT_CONSISTENCY_CHECK')
        unique_units = stats_df['Units'].nunique()
        if unique_units > 1:
            return ValidationResult(
                ValidationStatus.FAILED,
                'UNIT_CONSISTENCY_CHECK',
                message=
                f"Found {unique_units} unique units where 1 was expected.",
                details={'unique_units': list(stats_df['Units'].unique())})
        return ValidationResult(ValidationStatus.PASSED,
                                'UNIT_CONSISTENCY_CHECK')

    def validate_max_value_check(self, stats_df: pd.DataFrame,
                                 config: dict) -> ValidationResult:
        """Checks if the MaxValue for each StatVar is not above a defined maximum.

    Args:
      stats_df: A DataFrame containing the summary statistics, expected to have
        'MaxValue' and 'StatVar' columns.
      config: A dictionary containing the validation configuration, which must
        have a 'maximum' key.

    Returns:
      A ValidationResult object.
    """
        if 'maximum' not in config:
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
            return ValidationResult(ValidationStatus.PASSED, 'MAX_VALUE_CHECK')

        max_val = config['maximum']
        for _, row in stats_df.iterrows():
            max_value = row['MaxValue']
            stat_var = row.get('StatVar', 'Unknown')

            if max_value > max_val:
                return ValidationResult(
                    ValidationStatus.FAILED,
                    'MAX_VALUE_CHECK',
                    message=
                    f"StatVar '{stat_var}' has a maximum value of {max_value}, which is above the allowed maximum of {max_val}.",
                    details={
                        'stat_var': stat_var,
                        'actual_max_value': max_value,
                        'maximum': max_val
                    })
        return ValidationResult(ValidationStatus.PASSED, 'MAX_VALUE_CHECK')
