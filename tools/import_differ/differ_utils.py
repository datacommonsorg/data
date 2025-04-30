import glob
import fnmatch
import os
import pandas as pd
import re

from absl import logging
from google.cloud.storage import Client


def load_mcf_file(file: str) -> pd.DataFrame:
    """ Reads an MCF text file and returns it as a dataframe."""
    mcf_file = open(file, 'r', encoding='utf-8')
    mcf_contents = mcf_file.read()
    mcf_file.close()
    # nodes separated by a blank line
    mcf_nodes_text = mcf_contents.split('\n\n')
    # lines seprated as property: constraint
    mcf_line = re.compile(r'^(\w+)\s*:\s*(.*)$')
    mcf_nodes = []
    for node in mcf_nodes_text:
        current_mcf_node = {}
        for line in node.split('\n'):
            parsed_line = mcf_line.match(line)
            if parsed_line is not None:
                current_mcf_node[parsed_line.group(1)] = parsed_line.group(2)
        if current_mcf_node:
            if current_mcf_node['typeOf'] == 'dcid:StatVarObservation':
                mcf_nodes.append(current_mcf_node)
            else:
                logging.warning(
                    f'Ignoring node of type:{current_mcf_node["typeOf"]}')
    df = pd.DataFrame(mcf_nodes)
    return df


def load_mcf_files(path: str) -> pd.DataFrame:
    """ Loads all sharded mcf files in the given directory and 
    returns a single combined dataframe."""
    df_list = []
    filenames = glob.glob(path)
    for filename in filenames:
        df = load_mcf_file(filename)
        df_list.append(df)
    result = pd.concat(df_list, ignore_index=True)
    return result


def write_data(df: pd.DataFrame, path: str, file: str):
    """ Writes a dataframe to a CSV file with the given path."""
    out_file = open(os.path.join(path, file), mode='w', encoding='utf-8')
    df.to_csv(out_file, index=False, mode='w')
    out_file.close()


def load_data(path: str, tmp_dir: str) -> pd.DataFrame:
    """ Loads data from the given path and returns as a dataframe.
    Args:
      path: local or gcs path (single file or wildcard format)
      tmp_dir: destination folder
    Returns:
      dataframe with the input data
    """
    if path.startswith('gs://'):
        path = get_gcs_data(path, tmp_dir)
    return load_mcf_files(path)


def get_gcs_data(uri: str, tmp_dir: str) -> str:
    """ Downloads files from GCS and copies them to local.
    Args:
      uri: single file path or wildcard format 
      tmp_dir: destination folder
    Returns:
      path to the output file/folder
    """

    client = Client()
    bucket = client.get_bucket(uri.split('/')[2])
    if '*' in uri:
        file_pat = uri.split(bucket.name, 1)[1][1:]
        dirname = os.path.dirname(file_pat)
        for blob in bucket.list_blobs(prefix=dirname):
            if fnmatch.fnmatch(blob.name, file_pat):
                path = os.path.join(tmp_dir, blob.name.replace('/', '_'))
                blob.download_to_filename(path)
        return os.path.join(tmp_dir, '*')
    else:
        file_name = uri.split('/')[3]
        blob = bucket.get_blob(file_name)
        path = os.path.join(tmp_dir, blob.name.replace('/', '_'))
        blob.download_to_filename(path)
        return path
