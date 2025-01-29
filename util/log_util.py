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
"""Utility functions for logging."""

import json


def log_struct(level: str, message: str, labels: dict):
    """Logs a structured message. In GCP Log Explorer, the labels will appear under `jsonPayload`.
    
    Args:
        level: Log level (e.g., "INFO", "WARNING", "ERROR").
        message: Log message.
        labels: Additional labels to include in the log.
    """
    # With Python logging lib, json is interpreted as text (populates textPayload field).
    # Using print to populate json as structured logs (populate jsonPayload field).
    # Ref: https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
    print(json.dumps({"message": message, "severity": level, **labels}))


def log_metric(log_type: str, level: str, message: str, metric_labels: dict):
    """Logs a structured message which can be used to create a log-based metric.
        In GCP Log Explorer, the labels will appear under `jsonPayload`.

    Args:
        log_type: Log type identifier; used for filtering log lines when creating log-based metrics.
            Published as `log_type` label in structured log.
        level: Log level ("INFO", "WARNING", "ERROR").
        message: Log message.
        metric_labels: Labels for the metric.
    """
    log_struct(level, message, {"log_type": log_type, **metric_labels})
