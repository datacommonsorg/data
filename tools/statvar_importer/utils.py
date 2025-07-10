# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for the StatVar importer.

This module provides helper functions used across the StatVar import process.
"""

import os
import logging
import re
import sys
import tempfile
from typing import Union, Optional, Dict, List

import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import file_util

from download_util import download_file_from_url


def capitalize_first_char(string: str) -> str:
    """Capitalizes the first character of a string.

    If the input is not a string, or is an empty string, it's returned as is.

    Args:
        string: The input string.

    Returns:
        The string with its first character capitalized, or the original input
        if it cannot be capitalized.

    Examples:
        >>> capitalize_first_char("hello")
        'Hello'
        >>> capitalize_first_char("World")
        'World'
        >>> capitalize_first_char("")
        ''
        >>> capitalize_first_char("1st")
        '1st'
        >>> capitalize_first_char(None)

    """
    if not string or not isinstance(string, str):
        return string
    return string[0].upper() + string[1:]


def str_from_number(number: Union[int, float],
                    precision_digits: Optional[int] = None) -> str:
    """Converts a number (int or float) to its string representation.

    Integers and floats that are whole numbers (e.g., 10.0) are returned as
    integer strings (e.g., "10").
    Floats are rounded to the specified number of precision digits if provided.

    Args:
        number: The number to convert.
        precision_digits: Optional number of decimal places to round a float to.

    Returns:
        The string representation of the number.

    Examples:
        >>> str_from_number(123)
        '123'
        >>> str_from_number(123.0)
        '123'
        >>> str_from_number(123.456)
        '123.456'
        >>> str_from_number(123.456, precision_digits=2)
        '123.46'
        >>> str_from_number(123.451, precision_digits=2)
        '123.45'
    """
    # Check if number is an integer or float without any decimals.
    if int(number) == number:
        number_int = int(number)
        return f'{number_int}'
    # Return float rounded to precision digits.
    if precision_digits is not None:
        number = round(number, precision_digits)
    return f'{number}'


def pvs_has_any_prop(pvs: Optional[Dict[str, any]],
                     columns: Optional[List[str]] = None) -> bool:
    """Checks if a dictionary of Property-Values (PVs) contains any of the specified columns (properties).

    This function iterates through the provided PVs dictionary and checks if any of its
    keys (properties) are present in the `columns` list and have a non-empty value.

    Args:
        pvs: A dictionary where keys are properties and values are their corresponding values.
        columns: A list of column names (properties) to check for in the PVs.

    Returns:
        True if any property in `pvs` is also in `columns` and has a truthy value,
        False otherwise.

    Examples:
        >>> pvs_has_any_prop({'name': 'Test', 'age': 30}, ['age', 'city'])
        True
        >>> pvs_has_any_prop({'name': 'Test', 'age': None}, ['age'])
        False
        >>> pvs_has_any_prop({'name': 'Test'}, ['city'])
        False
        >>> pvs_has_any_prop({}, ['name'])
        False
        >>> pvs_has_any_prop(None, ['name'])
        False
        >>> pvs_has_any_prop({'name': 'Test'}, None)
        False
    """
    if pvs and columns:
        for prop, value in pvs.items():
            if value and prop in columns:
                return True
    return False


def is_place_dcid(place: str) -> bool:
    """Heuristically checks if a string is a Data Commons ID (DCID).

    This function serves as a fast, local workaround to avoid making slow,
    sequential API calls to validate DCIDs during data processing. It is
    intended to quickly identify strings that are already resolved DCIDs,
    thus skipping unnecessary place resolution steps.

    The heuristic works as follows:
    1.  If the string starts with a `dcid:` or `dcs:` prefix, it is
        assumed to be a valid DCID. This assumption is based on the
        convention that these prefixes are typically present in configured
        PV maps for already-resolved places.
    2.  If no prefix is present, the function performs a basic structural
        check. It verifies that the string contains a '/' and consists only
        of alphanumeric characters, underscores, and slashes.

    Note: This check is not exhaustive and may not cover all valid DCID
    formats. Its primary purpose is to optimize the import process by
    reducing external API calls.

    Examples:
        >>> is_place_dcid("dcid:country/USA")
        True
        >>> is_place_dcid("dcs:country/USA")
        True
        >>> is_place_dcid("country/USA")
        True
        >>> is_place_dcid("dcid:!@#") # Assumed valid due to prefix
        True
        >>> is_place_dcid("countryUSA") # Fails due to missing slash
        False
        >>> is_place_dcid("country/USA!") # Fails due to invalid character
        False
    """
    if not place or not isinstance(place, str):
        return False
    if place.startswith('dcid:') or place.startswith('dcs:'):
        return True

    # For non-prefixed DCIDs, check for a slash and valid characters.
    if '/' not in place:
        return False
    for c in place:
        if not c.isalnum() and c not in ['_', '/']:
            return False
    return True


def get_observation_period_for_date(date_str: str,
                                    default_period: str = '') -> str:
    """Determines the observation period (e.g., P1Y, P1M, P1D) based on the date string format.

    It counts the number of hyphens ('-') in the date string to infer the period:
    - 0 hyphens: Assumes yearly (P1Y), e.g., "2023".
    - 1 hyphen: Assumes monthly (P1M), e.g., "2023-01".
    - 2 hyphens: Assumes daily (P1D), e.g., "2023-01-15".
    If the hyphen count is not 0, 1, or 2, the `default_period` is returned.
    Note: This function does not validate the actual date components.

    Args:
        date_str: The date string to analyze.
        default_period: The default period to return if the hyphen count
                        does not match yearly, monthly, or daily patterns.

    Returns:
        The determined observation period string ('P1Y', 'P1M', 'P1D') or the `default_period`.

    Examples:
        >>> get_observation_period_for_date("2023")
        'P1Y'
        >>> get_observation_period_for_date("2023-05")
        'P1M'
        >>> get_observation_period_for_date("2023-05-10")
        'P1D'
        >>> get_observation_period_for_date("2023/05/10", "P1D") # No hyphens
        'P1Y'
        >>> get_observation_period_for_date("invalid-date-string", "PXY") # Two hyphens
        'P1D'
        >>> get_observation_period_for_date("invalid", "PXY") # Zero hyphens
        'P1Y'
    """
    date_parts = date_str.count('-')
    if date_parts == 0:  # YYYY
        return 'P1Y'
    if date_parts == 1:  # YYYY-MM
        return 'P1M'
    if date_parts == 2:  # YYYY-MM-DD
        return 'P1D'
    return default_period


def get_observation_date_format(date_str: str) -> str:
    """Determines a Python strftime date format string based on the structure of the date_str.

    This function infers the format by counting the number of hyphens ('-')
    separating parts of the date string:
    - "YYYY" (0 hyphens) -> "%Y"
    - "YYYY-MM" (1 hyphen) -> "%Y-%m"
    - "YYYY-MM-DD" (2 hyphens) -> "%Y-%m-%d"

    Args:
        date_str: The date string (e.g., "2023", "2023-01", "2023-01-15").

    Returns:
        A Python strftime format string.

    Examples:
        >>> get_observation_date_format("2023")
        '%Y'
        >>> get_observation_date_format("2023-07")
        '%Y-%m'
        >>> get_observation_date_format("2023-07-15")
        '%Y-%m-%d'
        >>> get_observation_date_format("2023/07/15") # Relies on hyphens
        '%Y'
    """
    # Get the date format based on number of tokens in date string.
    date_format = '%Y'
    date_tokens = date_str.split('-')
    num_tokens = len(date_tokens)
    if num_tokens > 1:
        date_format += '-%m'
    if num_tokens > 2:
        date_format += '-%d'

    return date_format


def get_filename_for_url(url: str, path: str) -> str:
    """Generates a safe local filename from a URL, ensuring uniqueness in the given path.

    It extracts the filename from the last segment of the URL path, removing query
    parameters and fragments. If a file with the generated name already exists in the
    specified path, it appends a unique numerical suffix (e.g., "-1", "-2").

    Args:
        url: The URL to derive the filename from.
        path: The directory path where the file will be saved, used to check for
              existing files to ensure uniqueness.

    Returns:
        A unique, safe filename string to be used locally.

    Examples:
        >>> get_filename_for_url("http://example.com/data/my_file.csv", "/tmp")
        '/tmp/my_file.csv'
        >>> get_filename_for_url("http://example.com/data/report.pdf?v=2#page3", "/docs")
        '/docs/report.pdf'
    """
    # Remove URL arguments separated by '?' or '#'
    url_path = url.split('?', maxsplit=1)[0].split('#', maxsplit=1)[0]
    # Get the last component URL as the filename
    filename = url_path[url_path.rfind('/') + 1:]
    filename, ext = os.path.splitext(filename)
    existing_files = file_util.file_get_matching(os.path.join(path, '*'))
    count = 0
    file = os.path.join(path, filename + ext)
    while file in existing_files:
        count += 1
        file = os.path.join(path, f'{filename}-{count}{ext}')
    return file


def download_csv_from_url(urls: Union[str, List[str]],
                          download_files: Optional[Union[str,
                                                         List[str]]] = None,
                          overwrite: bool = False) -> List[str]:
    """Downloads data from one or more URLs and saves it to specified files.

    If `download_files` are provided, they are used as the destination paths for
    the corresponding URLs. If not, filenames are automatically generated based
    on the URL.

    Args:
        urls: A single URL string or a list of URL strings to download from.
        download_files: A single destination file path or a list of paths.
                        If provided, the number of files must match the number of URLs.
                        If None, filenames are generated automatically.
        overwrite: If True, existing files will be overwritten.
                   Defaults to False.

    Returns:
        A list of file paths for the successfully downloaded files.
        Returns an empty list if any download fails or if inputs are invalid.

    Examples:
        >>> download_csv_from_url("http://example.com/data.csv")
        ['./data.csv']
        >>> download_csv_from_url(["http://example.com/data1.csv", "http://example.com/data2.csv"],
        ...                       ['/tmp/d1.csv', '/tmp/d2.csv'])
        ['/tmp/d1.csv', '/tmp/d2.csv']
        >>> download_csv_from_url([])
        []
    """
    data_files = []
    if not isinstance(urls, list):
        urls = [urls]
    if download_files and not isinstance(download_files, list):
        download_files = [download_files]
    if download_files:
        data_path = os.path.dirname(download_files[0])
    else:
        data_path = './'
    for index in range(len(urls)):
        url = urls[index]
        if download_files and index < len(download_files):
            filename = download_files[index]
        else:
            filename = get_filename_for_url(url, data_path)
        logging.info(f'Downloading {url} into {filename}')
        output_file = download_file_from_url(url=url,
                                             output_file=filename,
                                             overwrite=False)
        if output_file:
            data_files.append(output_file)
    logging.info(f'Downloaded {urls} into {data_files}.')
    return data_files


def shard_csv_data(
    files: List[str],
    column: Optional[str] = None,
    prefix_len: int = sys.maxsize,
    keep_existing_files: bool = True,
) -> List[str]:
    """Shards one or more CSV files into multiple smaller CSV files based on the unique values in a specified column.

    This function reads one or more CSVs, concatenates them, and then splits the
    resulting DataFrame into new CSV files. Each new file contains all rows that
    share the same unique value (or a common prefix of that value) in the
    specified `column`.

    If no `column` is specified, the first column of the DataFrame is used for sharding.

    Args:
        files: A list of paths to the input CSV files.
        column: The name of the column to shard by. If None, the first column is used.
        prefix_len: The number of characters of the column value to use for grouping.
                    Defaults to the full length of the value.
        keep_existing_files: If True, existing shard files will not be overwritten.
                             Defaults to True.

    Returns:
        A list of file paths for the generated shard files.

    Examples:
        >>> shard_csv_data(['my_data.csv'], column='country')
        ['my_data-country-00000-of-00002.csv', 'my_data-country-00001-of-00002.csv']
        >>> shard_csv_data([], column='country')
        []
    """
    logging.info(
        f'Loading data files: {files} for sharding by column: {column}...')
    if not files:
        return []
    dfs = []
    for file in files:
        dfs.append(
            pd.read_csv(file_util.FileIO(file), dtype=str, na_filter=False))
    df = pd.concat(dfs)
    if not column:
        # Pick the first column.
        column = list(df.columns)[0]
    # Convert nan to empty string so sharding doesn't drop any rows.
    # df[column] = df[column].fillna('')
    # Get unique shard prefix values from column.
    shards = list(
        sorted(set([str(x)[:prefix_len] for x in df[column].unique()])))
    if file_util.file_is_local(file):
        (file_prefix, file_ext) = os.path.splitext(file)
    else:
        fd, file_prefix = tempfile.mkstemp()
        file_ext = '.csv'
    column_suffix = re.sub(r'[^A-Za-z0-9_-]', '-', column)
    output_path = f'{file_prefix}-{column_suffix}'
    logging.info(f'Sharding {files} into {len(shards)} shards by column'
                 f' {column}:{shards} into {output_path}-*.csv.')
    output_files = []
    num_shards = len(shards)
    for shard_index in range(num_shards):
        shard_value = shards[shard_index]
        output_file = f'{output_path}-{shard_index:05d}-of-{num_shards:05d}.csv'
        logging.info(
            f'Sharding by {column}:{shard_value} into {output_file}...')
        if not os.path.exists(output_file) or not keep_existing_files:
            if shard_value:
                df[df[column].str.startswith(shard_value)].to_csv(output_file,
                                                                  index=False)
            else:
                df[df[column] == ''].to_csv(output_file, index=False)
        output_files.append(output_file)
    return output_files


def convert_xls_to_csv(filenames: List[str],
                       sheets: Optional[List[str]] = None) -> List[str]:
    """Converts specified sheets from Excel files (.xls, .xlsx) into CSV files.

    For each file in `filenames`, if it has an Excel extension, this function
    iterates through its sheets. If `sheets` is specified, only the sheets
    named in the list are converted. If `sheets` is None, all sheets in the
    Excel file are converted.

    Each converted sheet is saved as a new CSV file with a name derived from the
    original Excel file and the sheet name. Non-Excel files in the `filenames`
    list are passed through unchanged.

    Args:
        filenames: A list of file paths, which can include Excel and other file types.
        sheets: An optional list of sheet names to convert. If None, all sheets
                in the Excel files are converted.

    Returns:
        A list of file paths, including the newly created CSV files and any
        non-Excel files from the input.

    Examples:
        >>> convert_xls_to_csv(['my_data.xlsx'])
        ['my_data_Sheet1.csv', 'my_data_Sheet2.csv']
        >>> convert_xls_to_csv(['my_data.xlsx'], sheets=['Sheet1'])
        ['my_data_Sheet1.csv']
        >>> convert_xls_to_csv([])
        []
    """
    csv_files = []
    for file in filenames:
        filename, ext = os.path.splitext(file)
        logging.info(f'Converting {filename}{ext} into csv for {sheets}')
        if '.xls' in ext:
            # Convert the xls file into csv file per sheet.
            xls = pd.ExcelFile(file)
            for sheet in xls.sheet_names:
                # Read each sheet as a Pandas DataFrame and save it as csv
                if not sheets or sheet in sheets:
                    df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
                    csv_filename = re.sub('[^A-Za-z0-9_.-]+', '_',
                                          f'{filename}_{sheet}.csv')
                    df.to_csv(csv_filename, index=False)
                    logging.info(
                        f'Converted {file}:{sheet} into csv {csv_filename}')
                    csv_files.append(csv_filename)
        else:
            csv_files.append(file)
    return csv_files


def prepare_input_data(config: Dict) -> List[str]:
    """Prepares input data for processing by downloading, converting, and sharding files as needed.

    This function orchestrates the initial data preparation steps based on the provided
    configuration dictionary. The steps are:
    1.  If `input_data` is not found locally, it attempts to download from `data_url`.
    2.  Converts any Excel files (`.xls`, `.xlsx`) to CSV format.
    3.  If `parallelism` is enabled and a `shard_input_by_column` is specified,
        it shards the CSV files into smaller chunks.

    Args:
        config: A dictionary containing configuration parameters, such as:
                - `input_data` (str): Path to the input data file(s).
                - `data_url` (str): URL to download data from if `input_data` is not found.
                - `input_xls` (list): A list of sheets to convert from Excel files.
                - `shard_input_by_column` (str): The column to shard by.
                - `parallelism` (int): The number of parallel processes to use.

    Returns:
        A list of file paths for the prepared data files.

    Raises:
        RuntimeError: If no input data is found locally and no `data_url` is provided.

    Examples:
        >>> # Basic case: local CSV file is found and returned.
        >>> config = {'input_data': 'my_data.csv'}
        >>> prepare_input_data(config)
        ['my_data.csv']

        >>> # Download case: local file not found, download from URL.
        >>> config = {'data_url': 'http://example.com/data.csv'}
        >>> prepare_input_data(config)
        ['./data.csv']

        >>> # XLS conversion: local .xlsx file is converted to CSV.
        >>> config = {'input_data': 'my_data.xlsx', 'input_xls': ['Sheet1']}
        >>> prepare_input_data(config)
        ['my_data_Sheet1.csv']

        >>> # Sharding case: CSV is sharded by a column.
        >>> config = {
        ...     'input_data': 'my_data.csv',
        ...     'shard_input_by_column': 'country',
        ...     'parallelism': 2
        ... }
        >>> prepare_input_data(config)
        ['my_data-country-00000-of-00002.csv', 'my_data-country-00001-of-00002.csv']

        >>> # Negative case: no input data or URL.
        >>> config = {}
        >>> prepare_input_data(config)
        Traceback (most recent call last):
            ...
        RuntimeError: Provide data with --data_url or --input_data.
    """
    input_data = config.get('input_data', '')
    input_files = file_util.file_get_matching(input_data)
    if not input_files:
        # Download input data from the URL.
        data_url = config.get('data_url', '')
        if not data_url:
            raise RuntimeError(f'Provide data with --data_url or --input_data.')
        input_files = download_csv_from_url(data_url, input_data)
    input_files = convert_xls_to_csv(input_files, config.get('input_xls', []))
    shard_column = config.get('shard_input_by_column', '')
    if config.get('parallelism', 0) > 0 and shard_column:
        return shard_csv_data(
            input_files,
            shard_column,
            config.get('shard_prefix_length', sys.maxsize),
            True,
        )
    return input_files
