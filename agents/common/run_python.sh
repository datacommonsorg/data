#!/bin/bash

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

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repository-relative-python-script> [args...]" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" || "$PWD" != "$repo_root" ]]; then
  echo "Run this command from the data repository root." >&2
  exit 2
fi

for required_path in statvar_imports scripts import-automation requirements_all.txt run_tests.sh; do
  if [[ ! -e "$repo_root/$required_path" ]]; then
    echo "Current repository is not the Data Commons data repository: missing $required_path" >&2
    exit 2
  fi
done

python_bin="$repo_root/.env/bin/python"
if [[ ! -x "$python_bin" ]]; then
  echo "Python environment is missing. Run ./run_tests.sh -r first." >&2
  exit 3
fi

script_path="$repo_root/$1"
if [[ ! -f "$script_path" ]]; then
  echo "Python script does not exist: $1" >&2
  exit 2
fi

resolved_script="$(realpath "$script_path")"
case "$resolved_script" in
  "$repo_root"/*) ;;
  *)
    echo "Script must be contained in the data repository." >&2
    exit 2
    ;;
esac

shift
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
exec "$python_bin" "$resolved_script" "$@"
