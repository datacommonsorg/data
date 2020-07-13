import logging
import os
import subprocess
import shutil

from flask import Flask, request

from app.executor import executor

app = Flask(__name__)


@app.route('/', methods=['POST'])
def execute_imports():
    task_info = None
    try:
        task_info = request.json
    except Exception as e:
        err = 'Failed to parse commit info'
        logging.critical('%s: %s', err, e)
        return 'Failed to parse commit info'

    repo_name = task_info['REPO_NAME']
    commit_sha = task_info['COMMIT_SHA']
    branch_name = task_info['BRANCH_NAME']
    pr_number = task_info['PR_NUMBER']

    return executor.execute_imports(task_info)


@app.route('/update', methods=['POST'])
def scheduled_updates():
    task_info = None
    try:
        task_info = request.json
    except Exception as e:
        err = 'Failed to parse commit info'
        logging.critical('%s: %s', err, e)
        return 'Failed to parse commit info'

    return executor.execute_import_on_update(task_info['absolute_import_name'])

def main():
    app.run(host='127.0.0.1', port=8080, debug=True)

