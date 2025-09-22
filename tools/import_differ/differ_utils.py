# Copyright 2024 Google LLC
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
"""
Utility classes for handling file I/O for the import differ, abstracting
away the differences between local and GCS storage.
"""

import abc
import fnmatch
import glob
import os
import re
from typing import list

import pandas as pd
from absl import logging
from google.cloud import storage


class StorageStrategy(abc.ABC):
  """Abstract base class for storage strategies."""

  @abc.abstractmethod
  def load_mcf_nodes(self) -> list[dict]:
    pass

  @abc.abstractmethod
  def load_csv(self, filename_pattern: str) -> pd.DataFrame:
    pass

  @abc.abstractmethod
  def write_csv(self, df: pd.DataFrame, filename: str) -> None:
    pass


class LocalStrategy(StorageStrategy):
  """Storage strategy for the local filesystem."""

  def __init__(self, path: str):
    self._path = path

  def _load_mcf_file(self, file_path: str) -> list[dict]:
    """Reads a single MCF text file and returns a list of MCF nodes."""
    with open(file_path, 'r', encoding='utf-8') as mcf_file:
      mcf_contents = mcf_file.read()
    mcf_nodes_text = mcf_contents.split('\n\n')
    mcf_line = re.compile(r'^(\w+)\s*:\s*(.*)')
    mcf_nodes = []
    for node in mcf_nodes_text:
      current_mcf_node = {}
      for line in node.split('\n'):
        parsed_line = mcf_line.match(line)
        if parsed_line:
          current_mcf_node[parsed_line.group(1)] = parsed_line.group(2)
      if current_mcf_node:
        mcf_nodes.append(current_mcf_node)
    logging.info('Loaded %s nodes from file %s', len(mcf_nodes), file_path)
    return mcf_nodes

  def load_mcf_nodes(self) -> list[dict]:
    """Loads all sharded MCF files and returns a combined list of nodes."""
    node_list = []
    filenames = glob.glob(self._path)
    logging.info('Loading %s files from path %s', len(filenames), self._path)
    for filename in filenames:
      nodes = self._load_mcf_file(filename)
      node_list.extend(nodes)
    return node_list

  def load_csv(self, filename_pattern: str) -> pd.DataFrame:
    """Loads all CSV files matching a pattern and returns a DataFrame."""
    df_list = []
    full_pattern = os.path.join(self._path, filename_pattern)
    filenames = glob.glob(full_pattern)
    for filename in filenames:
      df = pd.read_csv(filename)
      df_list.append(df)
    return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

  def write_csv(self, df: pd.DataFrame, filename: str) -> None:
    """Writes a DataFrame to a CSV file."""
    path = os.path.join(self._path, filename)
    with open(path, mode='w', encoding='utf-8') as out_file:
      df.to_csv(out_file, index=False, mode='w', header=True)


class GCSStrategy(StorageStrategy):
  """Storage strategy for Google Cloud Storage."""

  def __init__(self, path: str, tmp_dir: str):
    self._gcs_uri = path
    self._tmp_dir = tmp_dir
    self._client = storage.Client()
    self._bucket_name = self._gcs_uri.split('/')[2]
    self._bucket = self._client.get_bucket(self._bucket_name)
    os.makedirs(self._tmp_dir, exist_ok=True)

  def _download_files(self, gcs_uri_pattern: str) -> str:
    """Downloads files from GCS to a local temporary directory."""
    file_pattern = gcs_uri_pattern.split(self._bucket.name, 1)[1][1:]
    dir_prefix = os.path.dirname(file_pattern)
    for blob in self._bucket.list_blobs(prefix=dir_prefix):
      if fnmatch.fnmatch(blob.name, file_pattern):
        dest_file = os.path.join(self._tmp_dir, blob.name)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        blob.download_to_filename(dest_file)
    return os.path.join(self._tmp_dir, file_pattern)

  def _upload_file(self, local_path: str, gcs_filename: str) -> None:
    """Uploads a local file to GCS."""
    logging.info('Uploading %s to %s', local_path, self._gcs_uri)
    blob_name = (
        self._gcs_uri[len(f'gs://{self._bucket_name}/') :] + f'/{gcs_filename}'
    )
    blob = self._bucket.blob(blob_name)
    blob.upload_from_filename(local_path)

  def load_mcf_nodes(self) -> list[dict]:
    """Downloads MCF files from GCS and loads them into a list of nodes."""
    local_path_pattern = self._download_files(self._gcs_uri)
    return LocalStrategy(local_path_pattern).load_mcf_nodes()

  def load_csv(self, filename_pattern: str) -> pd.DataFrame:
    """Downloads CSV files from GCS and loads them into a DataFrame."""
    gcs_path_pattern = os.path.join(self._gcs_uri, filename_pattern)
    local_path_pattern = self._download_files(gcs_path_pattern)
    return LocalStrategy(local_path_pattern).load_csv('')

  def write_csv(self, df: pd.DataFrame, filename: str) -> None:
    """Writes a DataFrame to a local CSV and uploads it to GCS."""
    local_path = os.path.join(self._tmp_dir, filename)
    LocalStrategy(self._tmp_dir).write_csv(df, filename)
    self._upload_file(local_path, filename)


class StorageClient:
  """
  A client for interacting with storage, abstracting away local vs. GCS.
  """

  def __init__(self, path: str, tmp_dir: str = None):
    if path.startswith('gs://'):
      if not tmp_dir:
        raise ValueError('tmp_dir is required for GCS paths.')
      self._strategy = GCSStrategy(path, tmp_dir)
    else:
      self._strategy = LocalStrategy(path)

  def load_mcf_nodes(self) -> list[dict]:
    return self._strategy.load_mcf_nodes()

  def load_csv(self, filename_pattern: str = '*.csv') -> pd.DataFrame:
    return self._strategy.load_csv(filename_pattern)

  def write_csv(self, df: pd.DataFrame, filename: str) -> None:
    self._strategy.write_csv(df, filename)
