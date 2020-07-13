import os
import subprocess
from unittest import mock

import psutil
from google.auth import credentials
from google.cloud import datastore
from google.cloud import exceptions

from app import utils
from app.model import import_attempt_model
from app.model import system_run_model

_ATTEMPT = import_attempt_model.ImportAttemptModel
_RUN = system_run_model.SystemRunModel()

PARSE_ARGS = 'flask_restful.reqparse.RequestParser.parse_args'


class LogMessageManagerMock:
    def __init__(self):
        self.data = {}

    def load_message(self, log_id):
        message = self.data.get(log_id)
        if not message:
            raise exceptions.NotFound(
                f'message of log {log_id} has never been saved.')
        return self.data[log_id]

    def save_message(self, message, log_id):
        self.data[log_id] = message
        return log_id


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
        namespace=utils.get_id(),
        credentials=credentials.AnonymousCredentials())


def ingest_import_attempts(
        run_list_resource, attempt_list_resource, attempts, system_run=None):
    with mock.patch(PARSE_ARGS) as parse_args:
        if system_run:
            parse_args.side_effect = [system_run] + attempts
            run_id = system_run[_RUN.run_id]
        else:
            parse_args.side_effect = [{}] + attempts
            run_id = run_list_resource.post()[_RUN.run_id]
        for i, attempt in enumerate(attempts):
            attempt[_ATTEMPT.run_id] = run_id
            attempts[i] = attempt_list_resource.post()
    return attempts


def ingest_system_runs(list_resource, runs):
    with mock.patch(PARSE_ARGS) as parse_args:
        parse_args.side_effect = runs
        runs = [list_resource.post() for _ in runs]
        return runs
