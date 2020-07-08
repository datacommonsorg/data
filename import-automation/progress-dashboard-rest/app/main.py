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
Entry point of the API.
When deployed on App Engine, gunicorn will serve the FLASK_APP variable,
which is a Flask object.
"""

import os

import flask
import flask_restful

from app.resource import import_attempt, import_log
from app import utils


def create_app(logging=True):
    """Creates the Flask app.

    Args:
        logging: Whether to set up Google Cloud Logging.
    """
    if logging:
        utils.setup_logging()
    return flask.Flask(__name__)


def create_api(app):
    """Creates the REST API on top of the Flask app."""
    api = flask_restful.Api(app)
    api.add_resource(import_attempt.ImportAttemptByID,
                     '/import/<string:attempt_id>')
    api.add_resource(import_attempt.ImportAttemptList,
                     '/imports')
    api.add_resource(import_log.ImportLog,
                     '/import/<string:attempt_id>/logs')
    return api


def main():
    """Runs the Flask app locally."""
    FLASK_APP.run(debug=True, port=8080)


FLASK_APP = create_app('DASHBOARD_PRODUCTION' in os.environ)
FLASK_API = create_api(FLASK_APP)
