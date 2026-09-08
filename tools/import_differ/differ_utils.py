import json
import os
import pandas as pd
import re

from absl import logging
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.join(_DATA_DIR, 'util'))
sys.path.append(os.path.join(_DATA_DIR, 'tools', 'statvar_importer'))

from file_util import FileIO
from file_util import file_get_matching
from mcf_file_util import load_mcf_nodes


def load_mcf_file(file: str) -> list:
    """ Reads an MCF text file and returns mcf nodes."""
    nodes_dict = load_mcf_nodes(file)
    return list(nodes_dict.values())


def load_mcf_files(path: str) -> list:
    """ Loads all sharded mcf files in the given directory and 
    returns a combined MCF node list."""
    nodes_dict = load_mcf_nodes(path)
    return list(nodes_dict.values())


def load_csv_data(path: str, tmp_dir: str) -> pd.DataFrame:
    """ Loads all matched files in the given path and 
    returns a single combined dataframe."""
    df_list = []
    filenames = file_get_matching(path)
    for filename in filenames:
        with FileIO(filename, mode='r') as in_file:
            df = pd.read_csv(in_file)
            df_list.append(df)
    result = pd.concat(df_list, ignore_index=True)
    return result


def write_csv_data(df: pd.DataFrame, dest: str, file: str, tmp_dir: str):
    """ Writes a dataframe to a CSV file with the given path."""
    path = os.path.join(dest, file)
    with FileIO(path, mode='w', encoding='utf-8') as out_file:
        df.to_csv(out_file, index=False, mode='w', header=True)


def write_json_data(data, dest: str, file: str, tmp_dir: str):
    """ Writes data to a JSON file with the given path."""
    path = os.path.join(dest, file)
    with FileIO(path, mode='w', encoding='utf-8') as out_file:
        json.dump(data, out_file, indent=4)


def write_mcf_nodes(nodes: list, dest: str, file: str, tmp_dir: str):
    """ Writes mcf nodes to a file with the given path."""
    path = os.path.join(dest, file)
    with FileIO(path, mode='w', encoding='utf-8') as out_file:
        for node in nodes:
            if 'Node' in node:
                out_file.write(f'Node: {node["Node"]}\n')
            elif 'dcid' in node:
                out_file.write(f'dcid: {node["dcid"]}\n')

            for key, value in node.items():
                if key in ['Node', 'dcid']:
                    continue
                out_file.write(f'{key}: {value}\n')
            out_file.write('\n')


def load_data(path: str, tmp_dir: str) -> list:
    """ Loads data from the given path and returns dataframe.
    Args:
      path: local or gcs path (single file or wildcard format)
      tmp_dir: temporary folder
    Returns:
      combined list of mcf nodes
    """
    mcf_nodes = load_mcf_files(path)
    return mcf_nodes
