import os
import subprocess
import logging

import psutil
from google.auth import credentials
from google.cloud import datastore

from app import utils

PARSE_ARGS = 'flask_restful.reqparse.RequestParser.parse_args'


def start_emulator():
    # bufsize=1 means that stderr will be line buffered
    process = subprocess.Popen(
        'gcloud beta emulators datastore start --no-store-on-disk'.split(),
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1)
    while True:
        line = process.stderr.readline()
        if 'Dev App Server is now running' in line:
            break
    p = subprocess.run('gcloud beta emulators datastore env-init'.split(),
                       capture_output=True, text=True)
    for line in p.stdout.splitlines():
        prefix = 'export '
        if line.startswith(prefix):
            line = line.strip(prefix)
            logging.warning(line)
            name, val = line.split('=')
            os.environ[name] = val
    return process


def terminate_emulator(process):
    parent = psutil.Process(process.pid)
    for child in parent.children(recursive=True):
        child.terminate()
    process.stderr.close()
    process.terminate()
    process.wait()


def create_test_datastore_client():
    return datastore.Client(
        project=utils.get_id(),
        namespace='namespace',
        credentials=credentials.AnonymousCredentials())


EXAMPLE_ATTEMPT = {
    'attempt_id': '0',
    'branch_name': 'branch',
    'repo_name': 'repo',
    'import_name': 'name',
    'time_created': '2020-06-30T04:28:53.717569+00:00',
    'logs': [],
    'status': 'created',
    'pr_number': 0
}
