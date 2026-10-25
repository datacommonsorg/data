"""
Contains the recurring functions of other files
"""
import io
import json
import os
import re
import tempfile
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from retry import retry
from urllib3.util.retry import Retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_raw_data_dir():
    """Ensures the raw_data directory exists inside the module directory."""
    raw_dir = os.path.join(_MODULE_DIR, "raw_data")
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir


def _create_retry_session(retries=5, backoff_factor=2):
    """Creates a requests.Session with automatic retry on transient HTTP errors."""
    session = requests.Session()
    session.headers.update({
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) DataCommonsImport/1.0 (https://datacommons.org)',
        'Accept':
            '*/*',
    })
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['HEAD', 'GET'],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def _is_html_response(content_type, first_bytes=b''):
    """Returns True if the response headers or body indicate an HTML/WAF error page."""
    if 'html' in (content_type or '').lower():
        return True
    if first_bytes:
        head = first_bytes[:512].lstrip().lower()
        if (head.startswith(b'<html') or head.startswith(b'<!doctype html') or
                b'<title>request rejected</title>' in head or
                b'the requested url was rejected' in head):
            return True
    return False


@retry(tries=3, delay=5, backoff=2)
def _head_with_html_retry(session, url, timeout=30):
    """Performs a HEAD request with retry when the server returns HTML for a non-HTML URL."""
    response = session.head(url, timeout=timeout, allow_redirects=True)
    content_type = response.headers.get('Content-Type', '').lower()
    if (response.status_code == 200 and 'html' in content_type and
            not url.lower().endswith(('.html', '.htm'))):
        raise ValueError(
            f'Server returned HTML (Content-Type: {content_type}) for non-HTML URL: {url}'
        )
    return response


@retry(tries=5, delay=5, backoff=2)
def download_with_retry(session, url, dest_path):
    """Downloads a URL to dest_path atomically, retrying on HTTP errors or HTML/WAF pages."""
    with session.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(dest_path))
        try:
            first_chunk = b''
            with os.fdopen(fd, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        if not first_chunk:
                            first_chunk = chunk[:512]
                            if (not url.lower().endswith(
                                ('.html', '.htm')) and _is_html_response(
                                    content_type, first_chunk)):
                                raise ValueError(
                                    f'Server returned HTML/WAF response (Content-Type: {content_type}) for non-HTML URL: {url}'
                                )
                        f.write(chunk)
            if not first_chunk:
                raise ValueError(f'Downloaded empty file from URL: {url}')
            os.replace(tmp_path, dest_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


@retry(tries=5, delay=5, backoff=2)
def _fetch_url_bytes(url: str) -> bytes:
    """Fetches URL content with retries and WAF/HTML rejection."""
    session = _create_retry_session()
    try:
        with session.get(url, timeout=60) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            content = response.content
            if not content:
                raise ValueError(f'Downloaded empty response from URL: {url}')
            if (not url.lower().endswith(('.html', '.htm')) and
                    _is_html_response(content_type, content[:512])):
                raise ValueError(
                    f'Server returned HTML/WAF response (Content-Type: {content_type}) for non-HTML URL: {url}'
                )
            return content
    finally:
        session.close()


def load_url_or_path(url_or_path: str):
    """Returns a BytesIO buffer for HTTP/HTTPS URLs (with retries and WAF checks) or the local path."""
    ensure_raw_data_dir()
    if isinstance(url_or_path, str):
        if url_or_path.lower().startswith(('http://', 'https://')):
            return io.BytesIO(_fetch_url_bytes(url_or_path))
        if not os.path.isabs(url_or_path) and not os.path.exists(url_or_path):
            candidate = os.path.join(_MODULE_DIR, url_or_path)
            if os.path.exists(candidate):
                return candidate
    return url_or_path


def input_url(file_name: str, key_name: str):
    """
    Take the File Name and Key as input
    and provide the URLs of the specified year/geo as output.
    """
    ensure_raw_data_dir()
    _URLS_JSON_PATH = os.path.join(_MODULE_DIR, file_name)
    _URLS_JSON = None
    with open(_URLS_JSON_PATH, encoding="UTF-8") as file:
        _URLS_JSON = json.load(file)
    _url = _URLS_JSON[key_name]
    return _url


def replace_age(df: pd.DataFrame):
    """
    Replaces the columns of DF as per metadata
    """
    df.rename(columns={
        0: '0To4Years',
        1: '5To9Years',
        2: '10To14Years',
        3: '15To19Years',
        4: '20To24Years',
        5: '25To29Years',
        6: '30To34Years',
        7: '35To39Years',
        8: '40To44Years',
        9: '45To49Years',
        10: '50To54Years',
        11: '55To59Years',
        12: '60To64Years',
        13: '65To69Years',
        14: '70To74Years',
        15: '75To79Years',
        16: '80To84Years',
        17: '85OrMoreYears'
    },
              inplace=True)
    return df


def replace_agegrp(df: pd.DataFrame, inp_flag: int):
    if inp_flag == 1:
        df = df.replace({"AGEGRP": {'1': '0To4Years'}})
    else:
        df = df.replace({"AGEGRP": {
            '0': '0Years',
            '1': '1To4Years',
        }})
    df = df.replace({
        "AGEGRP": {
            '2': '5To9Years',
            '3': '10To14Years',
            '4': '15To19Years',
            '5': '20To24Years',
            '6': '25To29Years',
            '7': '30To34Years',
            '8': '35To39Years',
            '9': '40To44Years',
            '10': '45To49Years',
            '11': '50To54Years',
            '12': '55To59Years',
            '13': '60To64Years',
            '14': '65To69Years',
            '15': '70To74Years',
            '16': '75To79Years',
            '17': '80To84Years',
            '18': '85OrMoreYears'
        }
    })
    return df


def gender_based_grouping(df: pd.DataFrame):
    """
    Aggregates the columns based on gender by removing race from SV
    """
    df['SVs'] = df['SVs'].str.replace('_WhiteAlone', '')
    df['SVs'] = df['SVs'].str.replace('_BlackOrAfricanAmericanAlone', '')
    df['SVs'] = df['SVs'].str.replace('_OtherRaces', '')
    df['SVs'] = df['SVs'].str.replace('_AmericanIndianAndAlaskaNativeAlone', '')
    df['SVs'] = df['SVs'].str.replace('_AsianOrPacificIslander', '')
    df['SVs'] = df['SVs'].str.replace('_AsianAlone', '')
    df['SVs'] = df['SVs'].str.replace\
        ('_NativeHawaiianAndOtherPacificIslanderAlone', '')
    df['SVs'] = df['SVs'].str.replace('_TwoOrMoreRaces', '')
    df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey'
    df = df.groupby(['Year', 'geo_ID', 'SVs',
                     'Measurement_Method']).sum().reset_index()

    return df


def race_based_grouping(df: pd.DataFrame):
    """
    Aggregates the columns based on race by removing gender from SV
    """
    df['SVs'] = df['SVs'].str.replace('_Male', '')
    df['SVs'] = df['SVs'].str.replace('_Female', '')
    df['Measurement_Method'] = 'dcAggregate/CensusPEPSurvey'
    df = df.groupby(['Year', 'geo_ID', 'SVs',
                     'Measurement_Method']).sum().reset_index()
    return df


def extract_year(year_str):
    match = re.search(r'\d{4}', year_str)
    if match:
        return match.group()
    else:
        return None
