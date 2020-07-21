import os
import subprocess
from unittest import mock
import atexit

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
        return message

    def save_message(self, message, log_id):
        self.data[log_id] = message
        return log_id


class DatastoreEmulator:
    def __init__(self):
        self.process = None

    def start_emulator(self):
        if self.process is not None:
            return

        # bufsize=1 means that stderr will be line buffered
        self.process = subprocess.Popen(
            'gcloud beta emulators datastore start --no-store-on-disk'.split(),
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1)

        # Wait for the emulator to fully start up
        while True:
            line = self.process.stderr.readline()
            if 'Dev App Server is now running' in line:
                break
        env_process = subprocess.run(
            'gcloud beta emulators datastore env-init'.split(),
            capture_output=True,
            text=True)

        # Set environmental variables for the emulator
        for line in env_process.stdout.splitlines():
            prefix = 'export '
            if line.startswith(prefix):
                line = line.strip(prefix)
                name, val = line.split('=')
                os.environ[name] = val

    def terminate_emulator(self):
        assert self.process is not None
        parent = psutil.Process(self.process.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        self.process.stderr.close()
        self.process.terminate()
        self.process.wait()

        self.process = None


EMULATOR = DatastoreEmulator()
atexit.register(EMULATOR.terminate_emulator)


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
