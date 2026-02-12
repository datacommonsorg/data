import glob
import fnmatch
import json
import os
import pandas as pd
import re

from absl import logging
from google.cloud import storage


def load_mcf_file(file: str):
    """ Reads an MCF text file and returns mcf nodes."""
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
            mcf_nodes.append(current_mcf_node)

    logging.info(f'Loaded {len(mcf_nodes)} nodes from file {file}')
    return mcf_nodes


def load_mcf_files(path: str) -> pd.DataFrame:
    """ Loads all sharded mcf files in the given directory and 
    returns a combined MCF node list."""
    node_list = []
    filenames = glob.glob(path)
    logging.info(f'Loading {len(filenames)} files from path {path}')
    for filename in filenames:
        nodes = load_mcf_file(filename)
        node_list.extend(nodes)
    return node_list


def load_csv_data(path: str, tmp_dir: str) -> pd.DataFrame:
    """ Loads all matched files in the given path and 
    returns a single combined dataframe."""
    df_list = []
    pattern = path
    if path.startswith('gs://'):
        pattern = get_gcs_data(path, tmp_dir)

    filenames = glob.glob(pattern)
    for filename in filenames:
        df = pd.read_csv(filename)
        df_list.append(df)
    result = pd.concat(df_list, ignore_index=True)
    return result


def write_csv_data(df: pd.DataFrame, dest: str, file: str, tmp_dir: str):
    """ Writes a dataframe to a CSV file with the given path."""
    if dest.startswith('gs://'):
        path = os.path.join(tmp_dir, file)
    else:
        path = os.path.join(dest, file)
    with open(path, mode='w', encoding='utf-8') as out_file:
        df.to_csv(out_file, index=False, mode='w', header=True)
    if dest.startswith('gs://'):
        upload_output_data(path, dest)


def write_json_data(data, dest: str, file: str, tmp_dir: str):
    """ Writes data to a JSON file with the given path."""
    if dest.startswith('gs://'):
        path = os.path.join(tmp_dir, file)
    else:
        path = os.path.join(dest, file)
    with open(path, mode='w', encoding='utf-8') as out_file:
        json.dump(data, out_file, indent=4)
    if dest.startswith('gs://'):
        upload_output_data(path, dest)


def upload_output_data(src: str, dest: str):
    client = storage.Client()
    bucket_name = dest.split('/')[2]
    bucket = client.get_bucket(bucket_name)
    for filepath in glob.iglob(src):
        filename = os.path.basename(filepath)
        logging.info('Uploading %s to %s', filename, dest)
        blobname = dest[len('gs://' + bucket_name + '/'):] + '/' + filename
        blob = bucket.blob(blobname)
        blob.upload_from_filename(filepath)


def get_gcs_data(uri: str, dest_dir: str) -> str:
    """ Downloads files from GCS and copies them to local.
    Args:
      uri: single file path or wildcard format 
      dest_dir: destination folder
    Returns:
      path to the output file/folder
    """
    client = storage.Client()
    bucket = client.get_bucket(uri.split('/')[2])
    file_pat = uri.split(bucket.name, 1)[1][1:]
    dirname = os.path.dirname(file_pat)
    for blob in bucket.list_blobs(prefix=dirname):
        if fnmatch.fnmatch(blob.name, file_pat):
            dest_file = os.path.join(dest_dir, blob.name)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            blob.download_to_filename(dest_file)
    return os.path.join(dest_dir, file_pat)


def load_data(path: str, tmp_dir: str) -> list:
    """ Loads data from the given path and returns dataframe.
    Args:
      path: local or gcs path (single file or wildcard format)
      tmp_dir: temporary folder
    Returns:
      combined list of mcf nodes
    """
    if path.startswith('gs://'):
        os.makedirs(tmp_dir, exist_ok=True)
        path = get_gcs_data(path, tmp_dir)

    mcf_nodes = load_mcf_files(path)
    return mcf_nodes
