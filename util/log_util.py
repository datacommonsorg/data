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
import logging
import os
import sys

from absl import flags

from google.cloud.logging.handlers import StructuredLogHandler
from functools import wraps

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

from timer import Timer

flags.DEFINE_integer('funcion_call_log_level', logging.INFO,
                     'Log level for function call logs.')

_FLAGS = flags.FLAGS


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


def configure_cloud_logging():
    """Configure a structured log handler to send logs to stdout.

    This is the standard way to get structured logs with correct severity
    in Google Cloud environments like Cloud Run, Cloud Functions, and Batch.
    The logs are captured from stdout by the environment's logging agent.

    It also removes any existing handlers to prevent log duplication.
    """
    # Remove all existing handlers from the root logger.
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # Add a handler that formats logs as JSON and sends them to stdout.
    handler = StructuredLogHandler(stream=sys.stdout)

    root.addHandler(handler)
    root.setLevel(logging.INFO)  # Set root logger level


def running_on_cloud() -> bool:
    """Check if running on Cloud.
    
    Returns:
        bool: True if running on Cloud services or jobs, False otherwise.
    """
    return bool(os.getenv('K_SERVICE')) or bool(
        os.getenv('CLOUD_RUN_JOB')) or bool(os.getenv('BATCH_JOB_UID'))


def configure_logging(enable_cloud_logging: bool):
    running_on_cloud_result = running_on_cloud()
    if running_on_cloud_result:
        if enable_cloud_logging:
            configure_cloud_logging()
            logging.info("Google Cloud Logging configured.")
        else:
            logging.info(f'Not enabling cloud logging')
    else:
        logging.info(f'Not running on cloud, using default logging')


def log_function_call(func):
    """
    A decorator to log function entry and exit.

    To log a function, add the @log_function_call before it.
    Example:
      @log_function_call
      def my_function():
         ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        log_level = logging.INFO
        if _FLAGS.is_parsed():
            log_level = _FLAGS.funcion_call_log_level
        logging.log(log_level, f"Function start: {func_name}")
        timer = Timer()
        try:
            result = func(*args, **kwargs)
            logging.log(
                log_level,
                f"Function end: {func_name}, time: {timer.time():.4f}s")
            return result
        except Exception as e:
            logging.log(
                log_level - 1,
                f"Function error: {func_name}: {e}, time: {timer.time():.4f}s",
                exc_info=True)
            raise  # Re-raise the exception after logging

    return wrapper
