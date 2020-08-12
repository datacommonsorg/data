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
Data Commons importer client.
"""

import os
import time
import logging
import dataclasses
from typing import Dict, Iterable

import requests
from google.cloud import storage

from app.executor import import_target

_PROXY_HOST = 'https://datcom-api-key-sandbox.uc.r.appspot.com'
_PROXY_IMPORT_TABLE = f'{_PROXY_HOST}/ImportTable'
_PROXY_IMPORT_NODE = f'{_PROXY_HOST}/ImportNode'
_PROXY_GET_IMPORT_LOG = f'{_PROXY_HOST}/GetImportLog'
_PROXY_IMPORT_DELETE = f'{_PROXY_HOST}/ImportDelete'


@dataclasses.dataclass
class ImportInputs:
    # Path to the CSV, relative to the root directory of the bucket in which
    # the CSV is stored, e.g.,
    # scripts/us_fed/treasury/2020_07_15T12_07_17_365264_07_00/data.csv
    cleaned_csv: str = None
    # Path to the template MCF, relative to the root directory of the bucket
    template_mcf: str = None
    # Path to the node MCF, relative to the root directory of the bucket
    node_mcf: str = None


class PreviousImportNotFinishedError(Exception):
    """Exception thrown if an import with the same import name and the
    same email is still queued or running.

    Attributes:
        import_name: Import name submitted to the importer as a string.
        curator_email: Email submitted to the importer as a string.
    """

    def __init__(self, import_name: str, curator_email: str):
        import_info = _format_import_info(import_name, curator_email)
        super().__init__(f'Previous import {import_info} '
                         'is still queued or running')
        self.import_name = import_name
        self.curator_email = curator_email


class ImportNotFoundError(Exception):
    """Exception thrown if an import is expected to be found in the import
    logs but not.

    Attributes:
        import_name: Import name submitted to the importer as a string.
        curator_email: Email submitted to the importer as a string.
        import_id: ID assigned by the importer, if applicable.
    """

    def __init__(self,
                 import_name: str,
                 curator_email: str,
                 import_id: str = None):
        import_info = _format_import_info(import_name, curator_email, import_id)
        super().__init__(f'Import <{import_info}> not found in import logs')
        self.import_name = import_name
        self.curator_email = curator_email
        self.import_id = import_id


class ImportFailedError(Exception):
    """Exception thrown if an import fails on the importer's side, i.e.,
    state != SUCCESSFUL.

    Attributes:
        log: Log entry created by the importer for the import.
    """

    def __init__(self, log: Dict):
        import_info = _format_import_info(log['importName'], log['userEmail'],
                                          log['id'])
        super().__init__(f'Import <{import_info}> failed: {log}')
        self.log = log


class ImportServiceClient:
    """Data Commons importer client."""
    # Number of seconds between each get_import_log call for
    # blocking on imports.
    _SLEEP_DURATION: float = 60
    # Enum value for ImportLogEntry.BIGQUERY
    _BIGQUERY = 2
    # Enum value for ResolutionNeed.LOCAL_RES_BY_ID
    _LOCAL_RES_BY_ID = 2
    # Enum value for NodeFormat.MCF
    _MCF = 1

    def __init__(self, project_id: str, unresolved_mcf_bucket_name: str,
                 resolved_mcf_bucket_name: str, importer_output_prefix: str,
                 executor_output_prefix: str):
        """Constructs an ImportServiceClient.

        Args:
            project_id: project_id: ID of the Google Cloud project that hosts
                the bucket, as a string.
            unresolved_mcf_bucket_name: Name of the Cloud Storage bucket the
                the generated data files are uploaded to, as a string.
            resolved_mcf_bucket_name: Name of the Cloud Storage bucket the
                Data Commons importer outputs to, as a string.
            importer_output_prefix: Output prefix in the
                unresolved_mcf_bucket_name bucket, as a string.
            executor_output_prefix: Output prefix in the
                resolved_mcf_bucket_name bucket, as a string.
        """
        client = storage.Client(project=project_id)
        self.unresolved_bucket = client.bucket(unresolved_mcf_bucket_name)
        self.resolved_bucket = client.bucket(resolved_mcf_bucket_name)
        self.unresolved_mcf_bucket_name = unresolved_mcf_bucket_name
        self.resolved_mcf_bucket_name = resolved_mcf_bucket_name
        self.importer_output_prefix = importer_output_prefix
        self.executor_output_prefix = executor_output_prefix

    def smart_import(self,
                     import_dir: str,
                     import_inputs: ImportInputs,
                     import_spec: dict,
                     block: bool = False,
                     timeout: float = None) -> Dict:
        """Performs a table import or node import depending on the
        import_inputs parameter.

        In import_inputs, if cleaned_csv and template_mcf are both set, performs
        a table import. If only node_mcf is set, performs a node import.

        Args:
            import_dir: Path to the directory with the manifest, relative to
                the root directory of the repository, as a string.
            import_inputs: ImportInputs object containing input paths.
            import_spec: Import specification as a dict.
            block: Whether to block the calling thread until the import succeeds
                or fails, as a boolean.
            timeout: If block is set, the maximum time in seconds to block, as
                a float.

        Returns:
            Log entry created by the importer for the import. If block is set,
            log['state'] is one of FAILED, SUCCESSFUL, PREEMPTED_WHILE_RUNNING,
            or PREEMPTED_WHILE_QUEUED. Otherwise, it could also be QUEUED and
            RUNNING.

        Raises:
            ValueError: import_inputs does not match any condition, i.e., no
                import performed.
            PreviousImportNotFinishedError: An import with the same absolute
                import name and the same email as the first email in the
                curator_email list in the import specification is still queued
                or running.
            requests.HTTPError: The importer returns a status code that is
                larger than or equal to 400.
            ImportFailedError: Import fails on the importer's side.
            TimeoutError: Timeout expired.
        """
        if import_inputs.cleaned_csv and import_inputs.template_mcf:
            return self.import_table(import_dir, import_inputs, import_spec,
                                     block, timeout)
        if (import_inputs.node_mcf and not import_inputs.cleaned_csv and
                not import_inputs.template_mcf):
            return self.import_node(import_dir, import_inputs, import_spec,
                                    block, timeout)
        raise ValueError(f'Invalid import inputs {import_inputs}')

    def import_table(self,
                     import_dir: str,
                     import_inputs: ImportInputs,
                     import_spec: dict,
                     block: bool = False,
                     timeout: float = None) -> Dict:
        """Imports a CSV table with template MCF and node MCF.
        See smart_import."""
        absolute_import_name = _get_fixed_absolute_import_name(
            import_dir, import_spec['import_name'])
        curator_email = import_spec['curator_emails'][0]
        request = {
            'manifest': {
                'importName': absolute_import_name,
                'curatorEmail': curator_email,
                'table': {
                    'tableName':
                        absolute_import_name,
                    'csvPath':
                        self._fix_input_path(import_inputs.cleaned_csv),
                    'mappingPath':
                        self._fix_input_path(import_inputs.template_mcf),
                    'fieldDelim':
                        ','
                },
                'provenanceUrl': import_spec['provenance_url'],
                'provenanceDescription': import_spec['provenance_description'],
                'mcfUrl': [self._fix_input_path(import_inputs.node_mcf)],
            },
            'useFlume': False,
            'dbType': ImportServiceClient._BIGQUERY,
            'resolutionNeed': ImportServiceClient._LOCAL_RES_BY_ID,
            'skipCsvValueChecks': True,
            'writeToDb': True
        }
        return self._import_helper(_PROXY_IMPORT_TABLE, request,
                                   absolute_import_name, curator_email, block,
                                   timeout)

    def import_node(self,
                    import_dir: str,
                    import_inputs: ImportInputs,
                    import_spec: dict,
                    block: bool = False,
                    timeout: float = None) -> Dict:
        """Imports a node MCF file. See smart_import."""
        absolute_import_name = _get_fixed_absolute_import_name(
            import_dir, import_spec['import_name'])
        curator_email = import_spec['curator_emails'][0]
        request = {
            'nodeFilePattern': self._fix_input_path(import_inputs.node_mcf),
            'nodeFormat': ImportServiceClient._MCF,
            'importName': absolute_import_name,
            'useFlume': False,
            'sanityCheckOnly': False,
            'userEmail': curator_email,
            'provenanceUrl': import_spec['provenance_url'],
            'provenanceDescription': import_spec['provenance_description'],
            'dbType': ImportServiceClient._BIGQUERY,
            'resolutionNeed': ImportServiceClient._LOCAL_RES_BY_ID,
            'writeToDb': True,
            'generateDcidsForNewPlaces': False
        }
        return self._import_helper(_PROXY_IMPORT_NODE, request,
                                   absolute_import_name, curator_email, block,
                                   timeout)

    def delete_import(self,
                      import_dir: str,
                      import_spec: Dict,
                      block: bool = False,
                      timeout: float = None) -> Dict:
        """Deletes an import.

        Args:
            import_dir: Path to the directory containing the manifest for the
                import, relative to the root directory of the repository.
            import_spec: Specification of the import parsed from the manifest.
            block: Whether to block the calling thread until the deletion is
                failed or finished.
            timeout: If block is set, the maximum time to block in seconds.

        Returns:
            The response from the importer as a dict.

        Raises:
            requests.HTTPError: The importer returns a status code that is
                larger than or equal to 400.
        """
        absolute_import_name = _get_fixed_absolute_import_name(
            import_dir, import_spec['import_name'])
        curator_email = import_spec['curator_emails'][0]
        request = {
            'importName': absolute_import_name,
            'userEmail': curator_email,
            'dbType': ImportServiceClient._BIGQUERY
        }
        return self._import_helper(_PROXY_IMPORT_DELETE, request,
                                   absolute_import_name, curator_email, block,
                                   timeout)

    def delete_previous_output(self, import_dir: str,
                               import_spec: dict) -> None:
        """Deletes artifacts generated by the previous import, such as
        the resolved MCF.

        Args:
            import_dir: Path to the directory containing the manifest for the
                import, relative to the root directory of the repository.
            import_spec: Specification of the import parsed from the manifest.
        """
        absolute_import_name = _get_fixed_absolute_import_name(
            import_dir, import_spec['import_name'])

        for bucket in (self.unresolved_bucket, self.resolved_bucket):
            blobs = bucket.list_blobs(prefix=os.path.join(
                self.importer_output_prefix, absolute_import_name))
            for blob in blobs:
                blob.delete()

    def get_import_log(self, curator_email: str) -> Dict:
        """Gets import logs.

        Args:
            curator_email: Email submitted to the importer.

        Returns:
            The response from the importer as a dict.

        Raises:
            requests.HTTPError: The importer returns a status code that is
                larger than or equal to 400.
        """
        request = {'userEmail': curator_email}
        logging.info(f'ImportServiceClient: Sending request {request} '
                     'to {_PROXY_GET_IMPORT_LOG}')
        response = requests.post(_PROXY_GET_IMPORT_LOG, json=request)
        logging.info(f'ImportServiceClient: Received response {response.text} '
                     'from {_PROXY_GET_IMPORT_LOG}')
        response.raise_for_status()
        return response.json()

    def _import_helper(self,
                       url: str,
                       import_request: Dict,
                       import_name: str,
                       curator_email: str,
                       block: bool = False,
                       timeout: float = None) -> Dict:
        """Sends an import request to the importer and optionally wait for
        its completion.

        Args:
            url: Importer endpoint address.
            import_request: Import request to be sent.
            import_name: Import name to be submitted as part of the request.
                This must match the import_name in the request.
            curator_email: Email to be submitted as part of the request.
                This must match the curator_email or user_email in the request.
            block: Whether to block the calling thread until the import is
                failed or finished.
            timeout: If block is set, the maximum time to block in seconds.

        Returns:
            See smart_import.

        Raises:
            PreviousImportNotFinishedError: An import with the same absolute
                import name and the same email as the first email in the
                curator_email list in the import specification is still queued
                or running.
            requests.HTTPError: The importer returns a status code that is
                larger than or equal to 400.
            Same exceptions as _are_imports_finished.
            If block is set, Same exceptions as _block_on_import.
        """
        logs_before = self.get_import_log(curator_email)['entry']
        if not _are_imports_finished(logs_before, import_name, curator_email):
            raise PreviousImportNotFinishedError(import_name, curator_email)

        response = requests.post(url, json=import_request)
        response.raise_for_status()

        logs_after = self.get_import_log(curator_email)['entry']
        import_id = _get_import_id(import_name, curator_email, logs_before,
                                   logs_after)
        log = _get_log(import_id, import_name, curator_email, logs_after)
        if block:
            self._block_on_import(import_id, import_name, curator_email,
                                  timeout)
        return log

    def _fix_input_path(self, path: str) -> str:
        """Fixes the path to a CSV or MCF to be the desirable path in the
        executor output bucket."""
        return os.path.join('/bigstore', self.unresolved_mcf_bucket_name,
                            self.executor_output_prefix, path)

    def _block_on_import(self,
                         import_id: str,
                         import_name: str,
                         curator_email: str,
                         timeout: float = None) -> Dict:
        """Blocks the calling thread until the import fails or succeeds.

        Args:
            import_id: ID of the import request assigned by the importer.
            import_name: Import name submitted to the importer.
            curator_email: Email submitted to the importer.
            timeout: Maximum time to block in seconds.

        Returns:
            Log entry for the import.

        Raises:
            Same exceptions as ImportServiceClient.get_import_log.
            ImportFailedError: Import fails on the importer's side.
            TimeoutError: Timeout expired.
        """
        start = time.time()
        while True:
            log = _get_log(import_id, import_name, curator_email,
                           self.get_import_log(curator_email)['entry'])
            if _is_import_finished(log):
                if log['state'] != 'SUCCESSFUL':
                    raise ImportFailedError(log)
                return log
            if timeout is not None and time.time() - start > timeout:
                raise TimeoutError('Timeout expired blocking on '
                                   f'{import_name} ({curator_email})')
            time.sleep(ImportServiceClient._SLEEP_DURATION)


def _get_fixed_absolute_import_name(import_dir: str, import_name: str) -> str:
    """Returns the absolute import name with colons and backslashes
    replaced with underscores."""
    return _fix_absolute_import_name(
        import_target.get_absolute_import_name(import_dir, import_name))


def _fix_absolute_import_name(name: str) -> str:
    """Replaces colons and backslashes with underscores."""
    return name.replace(':', '_').replace('/', '_')


def _get_import_id(import_name: str, curator_email: str,
                   logs_before: Iterable[Dict],
                   logs_after: Iterable[Dict]) -> str:
    """Finds the ID assigned to an import request by the importer.

    This function looks for a new log entry between logs_before and logs_after
    with the import_name and curator_email. The assumption is that between
    logs_before and logs_after, no import request with the same import name and
    email is submitted to the importer.

    Args:
        import_name: Import name submitted to the importer.
        curator_email: Email submitted to the importer.
        logs_before: Collection of logs before the import request is submitted.
        logs_after: Collection of logs after the import request is submitted.

    Returns:
        ID assigned to the import.

    Raises:
        ImportNotFoundError: Import not found in the import logs.
    """
    ids_before = set(log['id'] for log in logs_before)
    ids_after = set(log['id'] for log in logs_after)
    new_ids = ids_after - ids_before
    for log in logs_after:
        import_id = log['id']
        if (import_id in new_ids and log['importName'] == import_name and
                log['userEmail'] == curator_email):
            return import_id
    raise ImportNotFoundError(import_name, curator_email)


def _get_log(import_id: str, import_name, curator_email,
             logs: Iterable[Dict]) -> Dict:
    """Finds the log entry with the import_id in the logs."""
    for log in logs:
        if log['id'] == import_id:
            return log
    raise ImportNotFoundError(import_name, curator_email, import_id)


def _are_imports_finished(logs: Iterable[Dict], import_name: str,
                          curator_email: str) -> bool:
    """Checks if all import or deletion requests with the import_name and
    curator_email have finished (succeeded or failed) on the importer's side.

    Pairs of <import_name, curator_email> are not unique on the importer
    side. This function returns False if there is any import with the
    import_name and curator_email that has not finished.

    Args:
        logs: Collection of log entrties.
        import_name: Import name submitted to the importer.
        curator_email: Email submitted to the importer.

    Returns:
        Whether the import has finished.

    Raises:
        ImportNotFoundError: Import not found in the import logs.
    """
    found = False
    for log in logs:
        if (log['userEmail'] == curator_email and
                log['importName'] == import_name):
            found = True
            finished = _is_import_finished(log)
            if not finished:
                return False
    if not found:
        raise ImportNotFoundError(import_name, curator_email)
    return True


def _is_import_finished(log: Dict) -> bool:
    """Returns whether the import has finished (failed or succeeded)."""
    return log['state'] not in ('QUEUED', 'RUNNING')


def _format_import_info(import_name: str,
                        curator_email: str,
                        import_id: str = None) -> str:
    """Formats a string identifying an import request."""
    import_info = (f'import_name: {import_name}, '
                   f'curator_email: {curator_email}')
    if import_id:
        import_info += f', import_id: {import_id}'
    return import_info
