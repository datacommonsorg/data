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

set -uo pipefail

# Add required executables here; the generic loop checks each with command -v.
REQUIRED_COMMANDS=(
  bash
  bq
  curl
  git
  gcloud
  jq
  python3
  realpath
  sed
)

# Add exact gcloud operations here; the generic loop appends --help.
GCLOUD_COMMANDS=(
  'artifacts docker images describe'
  'auth list'
  'auth print-access-token'
  'auth application-default print-access-token'
  'batch jobs describe'
  'batch tasks list'
  'logging read'
  'scheduler jobs describe'
  'spanner databases execute-sql'
  'storage cat'
  'storage objects list'
)

function usage {
  printf '%s\n' \
    'Usage: ./agents/check_dependencies.sh [--local|--help]' \
    '' \
    'With no flag, run local dependency checks followed by authentication checks.' \
    'Use --local to skip authentication checks.'
}

run_auth=true
if [[ $# -eq 1 && "$1" == '--local' ]]; then
  run_auth=false
elif [[ $# -eq 1 && "$1" == '--help' ]]; then
  usage
  exit 0
elif [[ $# -ne 0 ]]; then
  usage >&2
  exit 2
fi

repo_root="$PWD"
for required_path in statvar_imports scripts import-automation requirements_all.txt run_tests.sh; do
  if [[ ! -e "$repo_root/$required_path" ]]; then
    echo 'Run this command from the Data Commons data repository root.' >&2
    exit 2
  fi
done

local_failures=0
gcloud_available=true

for command_name in "${REQUIRED_COMMANDS[@]}"; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "MISSING  command $command_name" >&2
    echo "SEE      agents/dependency-setup.md#system-tools" >&2
    local_failures=$((local_failures + 1))
    case "$command_name" in
      gcloud) gcloud_available=false ;;
    esac
  fi
done

if [[ $local_failures -eq 0 ]]; then
  echo 'PASS     Required command-line tools'
fi

if [[ "$gcloud_available" == true ]]; then
  gcloud_version=''
  if gcloud_version="$(gcloud version 2>/dev/null)"; then
    gcloud_version="${gcloud_version%%$'\n'*}"
    if [[ -n "$gcloud_version" ]]; then
      echo "PASS     $gcloud_version"
    else
      echo 'FAILED   gcloud version returned no output' >&2
      local_failures=$((local_failures + 1))
    fi
  else
    echo 'FAILED   gcloud version' >&2
    echo 'SEE      agents/dependency-setup.md#gcloud-cli' >&2
    local_failures=$((local_failures + 1))
  fi

  gcloud_command_failures=0
  for command_spec in "${GCLOUD_COMMANDS[@]}"; do
    command_parts=()
    read -r -a command_parts <<< "$command_spec"
    if ! gcloud "${command_parts[@]}" --help >/dev/null 2>&1; then
      echo "MISSING  gcloud $command_spec" >&2
      echo 'SEE      agents/dependency-setup.md#gcloud-cli' >&2
      gcloud_command_failures=$((gcloud_command_failures + 1))
    fi
  done
  if [[ $gcloud_command_failures -eq 0 ]]; then
    echo 'PASS     Required gcloud commands'
  else
    local_failures=$((local_failures + gcloud_command_failures))
  fi
else
  echo 'NOT_RUN  gcloud version and command checks' >&2
fi

python_bin="$repo_root/.env/bin/python"
python_checker="$repo_root/agents/common/scripts/check_python_dependencies.py"
if [[ ! -x "$python_bin" ]]; then
  echo 'MISSING  Python agent environment' >&2
  echo 'RUN      ./run_tests.sh -r' >&2
  local_failures=$((local_failures + 1))
elif [[ ! -f "$python_checker" ]]; then
  echo 'MISSING  agents/common/scripts/check_python_dependencies.py' >&2
  local_failures=$((local_failures + 1))
elif ! "$python_bin" "$python_checker"; then
  local_failures=$((local_failures + 1))
fi

if [[ $local_failures -ne 0 ]]; then
  echo 'NOT_RUN  Authentication checks' >&2
  exit 1
fi

if [[ "$run_auth" != true ]]; then
  echo 'NOT_RUN  Authentication checks (--local)'
  exit 0
fi

function has_nonempty_output {
  "$@" --quiet 2>/dev/null |
    "$python_bin" -c \
      'import sys; raise SystemExit(0 if sys.stdin.read().strip() else 1)'
}

auth_failures=0
if has_nonempty_output gcloud auth list \
    --filter='status:ACTIVE' --format='value(account)'; then
  if has_nonempty_output gcloud auth print-access-token; then
    echo 'PASS     gcloud CLI authentication'
  else
    echo 'FAILED   gcloud CLI authentication' >&2
    echo 'SEE      agents/dependency-setup.md#gcloud-cli-authentication' >&2
    auth_failures=$((auth_failures + 1))
  fi
else
  echo 'FAILED   No active gcloud account' >&2
  echo 'SEE      agents/dependency-setup.md#gcloud-cli-authentication' >&2
  auth_failures=$((auth_failures + 1))
fi

if has_nonempty_output gcloud auth application-default print-access-token; then
  echo 'PASS     Application Default Credentials'
else
  echo 'FAILED   Application Default Credentials' >&2
  echo 'SEE      agents/dependency-setup.md#application-default-credentials' >&2
  auth_failures=$((auth_failures + 1))
fi

if [[ $auth_failures -ne 0 ]]; then
  exit 1
fi

echo 'NOT_RUN  Cloud resource permissions'
