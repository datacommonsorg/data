# Copyright 2026 Google LLC
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

import functions_framework
import logging
from flask import jsonify

logging.getLogger().setLevel(logging.INFO)

@functions_framework.http
def embedding_helper(request):
    """
    HTTP Cloud Function for handling embedding tasks.
    Takes request and argument actionType.
    """
    request_json = request.get_json(silent=True)
    if not request_json:
        return ('Request is not a valid JSON', 400)

    if 'actionType' not in request_json:
        return ("'actionType' parameter is missing", 400)

    action_type = request_json['actionType']
    logging.info(f"Received request for actionType: {action_type}")

    if action_type == 'initilization':
        return jsonify({
            "status": "success",
            "message": "initilization action triggered"
        }), 200
    elif action_type == 'incremental_update':
        return jsonify({
            "status": "success",
            "message": "incremental_update action triggered"
        }), 200
    elif action_type == 'manual_update':
        return jsonify({
            "status": "success",
            "message": "manual_update action triggered"
        }), 200
    else:
        logging.warning(f"Unknown actionType: {action_type}")
        return (f"Unknown actionType: {action_type}", 400)
