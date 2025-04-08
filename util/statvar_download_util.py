"""
statvar_download_util.py

Python utility to download files dynamically from given URLs.

USAGE(as import):
-----------------
from statvar_download_util import StatVarDownloader

downloader = StatVarDownloader()

urls = [
    "https://example.com/data.csv",
    "https://example.com/data/report.csv"
]

downloader.download_files(urls, "/your/output/folder")

-----------------
Requirements:
- absl-py(pip install absl-py)
"""

import os
import time
import hashlib
import zipfile
from io import BytesIO
from typing import List
from urllib.parse import urlparse
import requests
import pandas as pd
from absl import logging

class StatVarDownloader:
    def __init__(self, retry_count: int = 3, timeout: int = 10):
        self.retry_count = retry_count
        self.timeout = timeout
        
    def _generate_unique_filename(self, url: str, existing_filenames: set) -> str:
        base_name = os.path.basename(urlparse(url).path) or "downloaded_file"
        name, ext = os.path.splitext(base_name)
        
        #If filename already used, append hash for uniqueness
        if base_name in existing_filenames:
            hash_suffix = hashlib.md5(url.encode()).hexdigest()[:6]
            base_name = f"{name}_{hash_suffix}{ext}"
        existing_filenames.add(base_name)
        return base_name
        
    def _download_file(self, url: str, output_path: str):
        for attempt in range(self.retry_count):
            try:
                logging.info(f"Downloading: {url}")
                response = requests.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    #Only create output folder after successful request
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logging.info(f"Saved to: {output_path}")
                    return
                else:
                    logging.warning(f"Attempt {attempt+1} failed: Status{response.status_code}")
            except Exception as e:
                logging.warning(f"Attempt {attempt+1} failed: {e}")
        raise RuntimeError(f"Failed to download after {self.retry_count} attempts: {url}")
    
    def download_files(self, urls: list, output_dir: str):
        if not isinstance(urls, list):
            raise ValueError("'urls' should be a list of URL strings.")
        if not output_dir:
            raise ValueError("'output_dir' should be a valid directory path.")
        
        existing_filenames = set()
        for url in urls:
            try:
                filename = self._generate_unique_filename(url, existing_filenames)
                output_path = os.path.join(output_dir, filename)
                self._download_file(url, output_path)
            except Exception as e:
                logging.error(f"Error downloading {url}: {e}")