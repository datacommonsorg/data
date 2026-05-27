import json
import os
import pandas as pd
import re

from absl import logging
from util.file_util import FileIO
from util.file_util import file_get_matching


def load_mcf_file(file: str):
    """ Reads an MCF text file and returns mcf nodes."""
    with FileIO(file, 'r', encoding='utf-8') as mcf_file:
        mcf_contents = mcf_file.read()
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
    filenames = file_get_matching(path)
    logging.info(f'Loading {len(filenames)} files from path {path}')
    for filename in filenames:
        nodes = load_mcf_file(filename)
        node_list.extend(nodes)
    return node_list


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
