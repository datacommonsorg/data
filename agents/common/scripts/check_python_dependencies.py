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
"""Checks that registered Python dependencies for agent tooling import."""

import importlib
import sys
from typing import Callable

# Keep distribution names synchronized with agents/requirements.txt.
REQUIRED_MODULES = (
    ('absl-py', 'absl'),
    ('google-api-core', 'google.api_core'),
    ('google-auth', 'google.auth'),
    ('google-cloud-storage', 'google.cloud.storage'),
    ('pyopenssl', 'OpenSSL'),
    ('pyyaml', 'yaml'),
)


def find_unavailable_modules(
    importer: Callable[[str], object] = importlib.import_module,
) -> list[tuple[str, str, str]]:
    """Returns all registered modules that cannot be imported."""
    unavailable = []
    for distribution, module in REQUIRED_MODULES:
        try:
            importer(module)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            unavailable.append((distribution, module, type(exc).__name__))
    return unavailable


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print('Usage: check_python_dependencies.py', file=sys.stderr)
        return 2

    unavailable = find_unavailable_modules()
    if unavailable:
        for distribution, module, error_type in unavailable:
            print(f'MISSING  {distribution} (import {module}; {error_type})',
                  file=sys.stderr)
        print('RUN      ./run_tests.sh -r', file=sys.stderr)
        return 1

    print('PASS     Python agent dependencies')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
