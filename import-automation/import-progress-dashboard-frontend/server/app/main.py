# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Frontend server for the import progress dashboard.
"""

import os
import json

import flask

from server.app import configs
from server.app.service import dashboard_api

DASHBOARD_API = dashboard_api.DashboardAPI(
    configs.get_dashboard_oauth_client_id())


def create_app():
    """Creates the Flask app."""
    return flask.Flask(__name__,
                       static_folder='../../client/build/static',
                       template_folder='../../client/build')


FLASK_APP = create_app()


@FLASK_APP.route('/')
def serve_index():
    """Serves index.html."""
    return flask.render_template('index.html')


@FLASK_APP.route('/<path:path>')
def serve_file(path):
    """Serves static files."""
    return flask.send_from_directory(FLASK_APP.template_folder, path)


@FLASK_APP.route('/system_runs')
def get_system_runs():
    """Returns all the system runs."""
    # TODO(intrepiditee): Limit number returned
    return flask.Response(json.dumps(DASHBOARD_API.get_system_runs()),
                          mimetype='application/json')


@FLASK_APP.route('/import_attempts/<string:attempt_id>')
def get_import_attempt(attempt_id):
    """Returns the import attempt with the attempt_id."""
    return DASHBOARD_API.get_import_attempt(attempt_id)


@FLASK_APP.route('/import_attempts/<string:attempt_id>/logs')
def get_logs_by_attempt_id(attempt_id):
    """Returns the logs of an import attempt with the attempt_id."""
    return flask.Response(json.dumps(
        DASHBOARD_API.get_logs_by_attempt_id(attempt_id)),
                          mimetype='application/json')


@FLASK_APP.route('/system_runs/<string:run_id>/logs')
def get_logs_by_run_id(run_id):
    """Returns the logs of a system run with the run_id."""
    return flask.Response(json.dumps(DASHBOARD_API.get_logs_by_run_id(run_id)),
                          mimetype='application/json')


def main():
    """Runs the app locally."""
    FLASK_APP.run(host='127.0.0.1', port=8080, debug=True)
