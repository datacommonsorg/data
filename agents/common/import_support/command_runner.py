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
"""Runs an allowlisted set of read-only gcloud operations."""

from collections.abc import Sequence
import json
from pathlib import Path
import re
import subprocess
from typing import Any

_ALLOWED_GCLOUD_PREFIXES = (
    ('scheduler', 'jobs', 'describe'),
    ('scheduler', 'jobs', 'list'),
    ('workflows', 'describe'),
    ('batch', 'jobs', 'describe'),
    ('batch', 'jobs', 'list'),
    ('batch', 'tasks', 'list'),
    ('logging', 'read'),
    ('run', 'services', 'describe'),
    ('storage', 'objects', 'list'),
    ('storage', 'cat'),
    ('builds', 'list'),
)
_SENSITIVE_KEY = re.compile(
    r'(access.?token|api.?key|authorization|credential|oauth|password|private.?key|secret)',
    re.IGNORECASE)
_MAX_ERROR_LENGTH = 2000


class CommandError(RuntimeError):
    """A safe error returned by a read-only command."""

    def __init__(self, message: str, returncode: int | None = None):
        super().__init__(message)
        self.returncode = returncode


def redact(value: Any) -> Any:
    """Recursively redacts common credential-bearing fields."""
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            result[key] = '<redacted>' if _SENSITIVE_KEY.search(
                str(key)) else redact(child)
        return result
    if isinstance(value, list):
        return [redact(child) for child in value]
    return value


def _has_flag(args: Sequence[str], flag: str) -> bool:
    return flag in args or any(arg.startswith(f'{flag}=') for arg in args)


def _validate_gcloud_args(args: Sequence[str], expect_json: bool) -> None:
    if not args or args[0] != 'gcloud':
        raise CommandError('Only gcloud commands are accepted.')
    operation = tuple(args[1:])
    if not any(operation[:len(prefix)] == prefix
               for prefix in _ALLOWED_GCLOUD_PREFIXES):
        raise CommandError(
            f'Operation is not in the read-only allowlist: {" ".join(args[:4])}'
        )
    if not _has_flag(args, '--project'):
        raise CommandError('Every gcloud operation must specify --project.')
    if expect_json and not any(
            arg == '--format=json' or arg.startswith('--format=json')
            for arg in args):
        raise CommandError('JSON operations must specify --format=json.')
    forbidden_flags = ('--access-token-file', '--impersonate-service-account',
                       '--log-http')
    for flag in forbidden_flags:
        if _has_flag(args, flag):
            raise CommandError(f'Forbidden credential-sensitive flag: {flag}')


def _safe_error(stderr: str, stdout: str) -> str:
    message = stderr.strip() or stdout.strip() or 'Command failed.'
    message = re.sub(r'ya29\.[A-Za-z0-9._-]+', '<redacted-token>', message)
    return message[:_MAX_ERROR_LENGTH]


class ReadOnlyCommandRunner:
    """Executes validated gcloud commands without a shell."""

    def __init__(self, repo_root: Path, default_timeout: int = 90):
        self._repo_root = repo_root.resolve()
        self._default_timeout = default_timeout

    def _run(self,
             args: Sequence[str],
             expect_json: bool,
             timeout: int | None = None) -> str:
        _validate_gcloud_args(args, expect_json)
        try:
            process = subprocess.run(list(args),
                                     cwd=self._repo_root,
                                     check=False,
                                     capture_output=True,
                                     text=True,
                                     timeout=timeout or self._default_timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CommandError(f'Unable to execute gcloud: {exc}') from exc
        if process.returncode:
            raise CommandError(_safe_error(process.stderr, process.stdout),
                               process.returncode)
        return process.stdout

    def run_json(self, args: Sequence[str], timeout: int | None = None) -> Any:
        """Returns parsed JSON for one allowlisted operation."""
        output = self._run(args, expect_json=True, timeout=timeout)
        try:
            return json.loads(output or 'null')
        except json.JSONDecodeError as exc:
            raise CommandError('gcloud returned invalid JSON.') from exc

    def run_text(self, args: Sequence[str], timeout: int | None = None) -> str:
        """Returns text for an allowlisted operation such as storage cat."""
        return self._run(args, expect_json=False, timeout=timeout)
