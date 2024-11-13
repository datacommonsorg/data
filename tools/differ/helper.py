import glob
import os
import pandas as pd
import re

from google.cloud.storage import Client


def load_mcf_file(file: str) -> pd.DataFrame:
    """ Reads an MCF text file and returns it as a dataframe."""
    mcf_file = open(file, 'r', encoding='utf-8')
    mcf_contents = mcf_file.read()
    mcf_file.close()
    # nodes separated by a blank line
    mcf_nodes_text = mcf_contents.split('\n\n')
    # lines seprated as property: constraint
    mcf_line = re.compile(r'^(\w+): (.*)$')
    mcf_nodes = []
    for node in mcf_nodes_text:
        current_mcf_node = {}
        for line in node.split('\n'):
            parsed_line = mcf_line.match(line)
            if parsed_line is not None:
                current_mcf_node[parsed_line.group(1)] = parsed_line.group(2)
        if current_mcf_node and current_mcf_node[
                'typeOf'] == 'dcid:StatVarObservation':
            mcf_nodes.append(current_mcf_node)
    df = pd.DataFrame(mcf_nodes)
    return df


def load_mcf_files(path: str) -> pd.DataFrame:
    """ Loads all sharded mcf files in the given directory and 
    returns a single combined dataframe."""
    df = pd.DataFrame()
    filenames = glob.glob(path + '.mcf')
    for filename in filenames:
        df2 = load_mcf_file(filename)
        # Merge data frames, expects same headers
        df = pd.concat([df, df2])
    return df


def write_data(df: pd.DataFrame, path: str, file: str):
    """ Write a dataframe to a CSV file with the given path."""
    out_file = open(os.path.join(path, file), mode='w', encoding='utf-8')
    df.to_csv(out_file, index=False, mode='w')
    out_file.close()


def load_data(path: str, tmp_dir: str) -> pd.DataFrame:
    """ Loads data from the given path and returns as a dataframe.
    Args:
      path: local or gcs path (single file or folder/* format)
    Returns:
      dataframe with the input data
    """
    if path.startswith('gs://'):
        path = get_gcs_data(path, tmp_dir)

    if path.endswith('*'):
        return load_mcf_files(path)
    else:
        return load_mcf_file(path)


def get_gcs_data(uri: str, tmp_dir: str) -> str:
    """ Downloads files form GCS and copies them to local.
    Args:
      uri: single file path or folder/* format 
    Returns:
      path to the output file/folder
    """

    client = Client()
    bucket = client.get_bucket(uri.split('/')[2])
    if uri.endswith('*'):
        blobs = client.list_blobs(bucket)
        for blob in blobs:
            path = os.path.join(os.getcwd(), tmp_dir, blob.name)
            blob.download_to_filename(path)
        return os.path.join(os.getcwd(), tmp_dir, '*')
    else:
        file_name = uri.split('/')[3]
        blob = bucket.get_blob(file_name)
        path = os.path.join(os.getcwd(), tmp_dir, file_name)
        blob.download_to_filename(path)
        return path
