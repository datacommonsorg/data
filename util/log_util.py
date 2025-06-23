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
    """Logs a structured message suitable for creating log-based metrics.
        In GCP Log Explorer, the labels will appear under `jsonPayload`.

        Guidelines for GCP log-based metrics:
        - Keep logging queries simple and focused.
            - More query fields might increase the chances of false negatives.
            - Filter logs by resource.type to focus on specific resources. This is auto populated by 
                GCP and does not need to be set here.
        - The same log can be used to create multiple log-based metrics, 
            especially when it contains multiple metric values (e.g. count, latency)
            - If so, metric_labels can be used as additional filtering criteria.       
    Args:
        log_type: Log type identifier; used for filtering log lines when creating log-based metrics.
            - Published as `log_type` label in structured log.
            - Use a unique log_type to filter log entries when creating log-based metrics. 
            - Reduces the number of fields required in the filtering query. This simplifies the query.
            - This method is more robust and easier to maintain than relying on labels, 
                which might be shared by other, unrelated log entries.
        level: Log level ("INFO", "WARNING", "ERROR").
        message: Log message. Provides a summary for display in the log explorer
            but should not be used for log queries or metric label derivation.  Use `metric_labels` instead.
        metric_labels: Labels for the metric. Might not be required for counter metrics when log_type alone might be sufficient.
            - Used to derive metric label values and metric value. Also used in logging queries,
                 especially when creating multiple log-based metrics from the same logs.
            - For metric labels, use scalar values (string, number, boolean) whenever possible.
            - This allows direct assignment to metric labels, avoiding the need for regular expressions.  
            - When using the same `log_type` in different parts of your code,
              maintain consistency in the labels used to guarantee correct population of log labels.
    """
    log_struct(level, message, {"log_type": log_type, **metric_labels})
