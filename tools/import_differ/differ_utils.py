import glob
import fnmatch
import os
import pandas as pd
import re
import shutil

from absl import logging
from google.cloud.storage import Client
from googleapiclient.discovery import build


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


def load_csv_data(path: str, column_list: list, tmp_dir: str) -> pd.DataFrame:
    """ Loads all matched files in the given path and 
    returns a single combined dataframe."""
    df_list = []
    pattern = path
    if path.startswith('gs://'):
        pattern = get_gcs_data(path, tmp_dir)

    filenames = glob.glob(pattern)
    for filename in filenames:
        df = pd.read_csv(filename, names=column_list, header=None)
        df_list.append(df)
    result = pd.concat(df_list, ignore_index=True)
    return result


def write_csv_data(df: pd.DataFrame, dest: str, file: str, tmp_dir: str):
    """ Writes a dataframe to a CSV file with the given path."""
    tmp_file = os.path.join(tmp_dir, file)
    with open(tmp_file, mode='w', encoding='utf-8') as out_file:
        df.to_csv(out_file, index=False, mode='w', header=True)
    upload_output_data(tmp_file, dest)


def launch_dataflow_job(project: str, job: str, current_data: str,
                        previous_data: str, file_format: str,
                        output_location: str) -> str:
    parameters = {
        'currentData': current_data,
        'previousData': previous_data,
        'outputLocation': output_location + '/diff',
    }
    if file_format == 'mcf':
        logging.info('Using mcf file format')
        template = 'gs://datcom-dataflow/templates/differ-mcf'
    else:
        logging.info('Using tfrecord file format')
        template = 'gs://datcom-dataflow/templates/differ-tfr'
        parameters['useOptimizedGraphFormat'] = 'true'

    dataflow = build("dataflow", "v1b3")
    request = (dataflow.projects().templates().launch(
        projectId=project,
        gcsPath=template,
        body={
            "jobName": job,
            "parameters": parameters,
        },
    ))
    response = request.execute()
    job_id = response['job']['id']
    return f'https://pantheon.corp.google.com/dataflow/jobs/{job_id}?project={project}'


def get_job_status(project: str, job: str) -> str:
    dataflow = build("dataflow", "v1b3")
    request = (dataflow.projects().jobs().list(projectId=project, name=job))
    response = request.execute()
    return response['jobs'][0]['currentState']


def upload_output_data(src: str, dest: str):
    if dest.startswith('gs://'):
        client = Client()
        bucket_name = dest.split('/')[2]
        bucket = client.get_bucket(bucket_name)
        for filepath in glob.iglob(src):
            filename = os.path.basename(filepath)
            logging.info('Uploading %s to %s', filename, dest)
            blobname = dest[len('gs://' + bucket_name + '/'):] + '/' + filename
            blob = bucket.blob(blobname)
            blob.upload_from_filename(filepath)
    else:
        os.makedirs(dest, exist_ok=True)
        for filepath in glob.iglob(src):
            shutil.copyfile(filepath,
                            os.path.join(dest, os.path.basename(filepath)))


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
    file_pat = uri.split(bucket.name, 1)[1][1:]
    dirname = os.path.dirname(file_pat)
    for blob in bucket.list_blobs(prefix=dirname):
        if fnmatch.fnmatch(blob.name, file_pat):
            path = blob.name.replace('/', '_')
            blob.download_to_filename(os.path.join(tmp_dir, path))
    return os.path.join(tmp_dir, file_pat.replace('/', '_'))
