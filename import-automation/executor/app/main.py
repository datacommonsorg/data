import logging

import flask

from app import utils
from app import configs
from app.executor import executor
from app.executor import update_scheduler


def create_app(logging=True):
    """Creates the Flask app.
    Args:
        logging: Whether to set up Google Cloud Logging.
    """
    if logging:
        utils.setup_logging()
    return flask.Flask(__name__)


FLASK_APP = create_app(configs.production())


@FLASK_APP.route('/', methods=['POST'])
def execute_imports():
    task_info = flask.request.get_json(force=True)
    commit_sha = task_info['COMMIT_SHA']
    repo_name = task_info.get('REPO_NAME')
    branch_name = task_info.get('BRANCH_NAME')
    pr_number = task_info.get('PR_NUMBER')

    return executor.execute_imports_on_commit(
        commit_sha, repo_name, branch_name, pr_number)


@FLASK_APP.route('/update', methods=['POST'])
def scheduled_updates():
    task_info = flask.request.get_json(force=True)
    return executor.execute_imports_on_update(task_info['absolute_import_name'])


@FLASK_APP.route('/schedule', methods=['POST'])
def schedule_crons():
    task_info = flask.request.get_json(force=True)



@FLASK_APP.route('/_ah/start')
def start():
    return ''


def main():
    FLASK_APP.run(host='127.0.0.1', port=8080, debug=True)
