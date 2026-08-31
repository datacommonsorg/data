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

TESTED_GH_VERSION='2.74.2'

function fail {
  echo "FAILED   $1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail 'git is required'
command -v gh >/dev/null 2>&1 || fail 'GitHub CLI (gh) is required'

gh_version="$(gh --version 2>/dev/null)" || fail 'gh --version'
gh_version="${gh_version%%$'\n'*}"
[[ -n "$gh_version" ]] || fail 'gh --version returned no output'

api_help="$(gh api --help 2>&1)" || fail 'gh api --help'
for capability in '--paginate' '--jq'; do
  if [[ "$api_help" != *"$capability"* ]]; then
    fail "gh api does not support $capability"
  fi
done

search_help="$(gh search prs --help 2>&1)" || fail 'gh search prs --help'
for capability in '--merged' '--merged-at'; do
  if [[ "$search_help" != *"$capability"* ]]; then
    fail "gh search prs does not support $capability"
  fi
done

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  fail 'gh is not authenticated for github.com'
fi

echo 'PASS     git and GitHub CLI are available'
echo "PASS     $gh_version"
echo 'PASS     Required gh capabilities'
echo 'PASS     GitHub CLI authentication'
echo "INFO     Workflow tested with GitHub CLI $TESTED_GH_VERSION"
echo 'INFO     Standalone jq is not required; gh provides --jq'
