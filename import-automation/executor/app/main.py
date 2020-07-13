import logging

from flask import Flask, request

from app.executor import executor

app = Flask(__name__)


@app.route('/', methods=['POST'])
def execute_imports():
    task_info = request.get_json(force=True)
    repo_name = task_info['REPO_NAME']
    commit_sha = task_info['COMMIT_SHA']
    branch_name = task_info['BRANCH_NAME']
    pr_number = task_info['PR_NUMBER']

    return executor.execute_imports_on_commit(
        commit_sha, repo_name, branch_name, pr_number)


@app.route('/update', methods=['POST'])
def scheduled_updates():
    task_info = request.get_json(force=True)
    return executor.execute_import_on_update(task_info['absolute_import_name'])


@app.route('/_ah/start')
def start():
    return ''


def main():
    app.run(host='127.0.0.1', port=8080, debug=True)
