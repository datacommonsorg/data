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

# Wrapper script for the Data Commons import tool (dc-import).
#
# Reuses the locally cached import-tool.jar if it was fetched or verified
# within the last hour. If the cached JAR is older than an hour, checks Google
# Cloud Storage (GCS) for a newer version, updates the cache if a newer build
# exists, and executes `java -jar` with all provided arguments.
#
# ==============================================================================
# 1. Permanent Alias Setup (~/.bashrc)
# ==============================================================================
# Run the following commands once to permanently add the `dc-import` alias to
# your ~/.bashrc and apply it to your current session. Replace
# <path-to-data-repo> with the absolute path to your local checkout of the
# `data` repository (e.g., ~/projects/data):
#
#   echo "alias dc-import='<path-to-data-repo>/tools/scripts/run_import_tool.sh'" >> ~/.bashrc
#   source ~/.bashrc
#
# Note: Aliases are not available in non-interactive shells (e.g., coding agents
# or scripts). In those cases, call the script directly:
#
#   <path-to-data-repo>/tools/scripts/run_import_tool.sh lint ...
#
# Note: Set `export DC_API_KEY="<your-key>"` if running existence or resolution
# checks against the Data Commons API.
#
# ==============================================================================
# 2. Usage Examples (after setting up the alias)
# ==============================================================================
#   # View help and all supported flags:
#   dc-import --help
#
#   # Lint TMCF, CSV, and MCF files:
#   dc-import lint path/to/data.tmcf path/to/data.csv path/to/schema.mcf
#
#   # Generate instance MCF files from TMCF + CSV files:
#   dc-import genmcf path/to/data.tmcf path/to/data.csv
#
# ==============================================================================
# 3. Optional Environment Variables
# ==============================================================================
#   DC_IMPORT_JAR_URL       Override the GCS URL for import-tool.jar.
#   DC_IMPORT_CACHE_DIR     Override the local cache directory
#                           (default: ${XDG_CACHE_HOME:-~/.cache}/datacommons/dc-import,
#                           or ${TMPDIR:-/tmp}/dc-import-<uid> if HOME is unset).
#   DC_IMPORT_JAVA_OPTS     Extra JVM flags (e.g., "-Xmx8g").
#   DC_IMPORT_FORCE_UPDATE  Set to "1" or "true" to check for a newer version
#                           immediately, even if the cached JAR was checked
#                           within the last hour.
#
#   Set a variable for a single run by putting it before the command, e.g.:
#
#     DC_IMPORT_JAVA_OPTS="-Xmx8g" dc-import genmcf path/to/data.tmcf path/to/data.csv

set -euo pipefail

readonly DEFAULT_JAR_URL="https://storage.googleapis.com/datacommons_public/import_tools/import-tool.jar"
readonly CHECK_INTERVAL_MINUTES=60

# Pick a default cache directory. Fall back to a per-user directory under /tmp
# when neither XDG_CACHE_HOME nor HOME is set (e.g., minimal agent or CI shells).
USING_TMP_CACHE_FALLBACK=0
if [[ -n "${XDG_CACHE_HOME:-}" ]]; then
  DEFAULT_CACHE_DIR="${XDG_CACHE_HOME}/datacommons/dc-import"
elif [[ -n "${HOME:-}" ]]; then
  DEFAULT_CACHE_DIR="${HOME}/.cache/datacommons/dc-import"
else
  DEFAULT_CACHE_DIR="${TMPDIR:-/tmp}/dc-import-$(id -u)"
  USING_TMP_CACHE_FALLBACK=1
fi
readonly DEFAULT_CACHE_DIR

readonly JAR_URL="${DC_IMPORT_JAR_URL:-${DEFAULT_JAR_URL}}"
readonly CACHE_DIR="${DC_IMPORT_CACHE_DIR:-${DEFAULT_CACHE_DIR}}"
readonly CACHED_JAR="${CACHE_DIR}/import-tool.jar"
readonly JAVA_BIN="${JAVA_BIN:-java}"
if [[ -n "${DC_IMPORT_CACHE_DIR:-}" ]]; then
  USING_TMP_CACHE_FALLBACK=0
fi
readonly USING_TMP_CACHE_FALLBACK

log_info() {
  echo "[dc-import] $*" >&2
}

log_warn() {
  echo "[dc-import] [WARN] $*" >&2
}

log_error() {
  echo "[dc-import] [ERROR] $*" >&2
}

is_force_update() {
  [[ "${DC_IMPORT_FORCE_UPDATE:-0}" == "1" || "${DC_IMPORT_FORCE_UPDATE:-false}" == "true" ]]
}

ensure_latest_jar() {
  if [[ "${USING_TMP_CACHE_FALLBACK}" -eq 1 ]]; then
    # /tmp is shared by all users, so create the directory as private and make
    # sure it belongs to the current user before trusting a JAR inside it.
    mkdir -p -m 700 "${CACHE_DIR}"
    if [[ ! -O "${CACHE_DIR}" || -L "${CACHE_DIR}" ]]; then
      log_error "Cache directory ${CACHE_DIR} is a symlink or not owned by the current user. Set DC_IMPORT_CACHE_DIR to a private directory."
      exit 1
    fi
  else
    mkdir -p "${CACHE_DIR}"
  fi

  # Reuse the local JAR without checking GCS if it was fetched or verified
  # within the last hour, unless a forced update is requested.
  if ! is_force_update && [[ -s "${CACHED_JAR}" ]] \
      && [[ -n "$(find "${CACHED_JAR}" -mmin "-${CHECK_INTERVAL_MINUTES}" 2>/dev/null)" ]]; then
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    log_error "curl executable not found in PATH. Please install curl."
    exit 1
  fi

  local tmp_jar
  tmp_jar="$(mktemp "${CACHE_DIR}/import-tool.jar.tmp.XXXXXX")"

  # Clean up any leftover temp file on unexpected exit.
  trap 'rm -f "${tmp_jar:-}"' EXIT

  if [[ ! -s "${CACHED_JAR}" ]]; then
    log_info "Downloading import-tool.jar from ${JAR_URL} ..."
    if curl -fsSL --connect-timeout 5 -o "${tmp_jar}" "${JAR_URL}" && [[ -s "${tmp_jar}" ]]; then
      mv -f "${tmp_jar}" "${CACHED_JAR}"
      log_info "Downloaded import-tool.jar to ${CACHED_JAR}."
    else
      rm -f "${tmp_jar}"
      log_error "Failed to download import-tool.jar from ${JAR_URL}."
      exit 1
    fi
  else
    # Conditional GET: only downloads if remote Last-Modified is newer than CACHED_JAR.
    # On HTTP 304 (Not Modified), tmp_jar remains 0 bytes (`[[ -s "${tmp_jar}" ]]` is false).
    if curl -fsSL --connect-timeout 5 -z "${CACHED_JAR}" -o "${tmp_jar}" "${JAR_URL}"; then
      if [[ -s "${tmp_jar}" ]]; then
        mv -f "${tmp_jar}" "${CACHED_JAR}"
        log_info "Updated import-tool.jar to latest version."
      else
        rm -f "${tmp_jar}"
        # Update timestamp so we don't check GCS again for another hour.
        touch "${CACHED_JAR}"
      fi
    else
      rm -f "${tmp_jar}"
      log_warn "Could not check for updates from ${JAR_URL}; using cached JAR."
      # Update timestamp to avoid retrying the network request on every run when offline.
      touch "${CACHED_JAR}"
    fi
  fi

  rm -f "${tmp_jar}"
  trap - EXIT
}

main() {
  if ! command -v "${JAVA_BIN}" >/dev/null 2>&1; then
    log_error "Java executable '${JAVA_BIN}' not found in PATH. Please install Java 17+."
    exit 1
  fi

  ensure_latest_jar

  # Disable Log4j2 JMX by default to avoid cgroupv2 NullPointerException noise on Cloudtop JDKs.
  local java_opts=("-Dlog4j2.disable.jmx=true")
  if [[ -n "${DC_IMPORT_JAVA_OPTS:-}" ]]; then
    local extra_java_opts=()
    read -r -a extra_java_opts <<< "${DC_IMPORT_JAVA_OPTS}"
    java_opts+=("${extra_java_opts[@]}")
  fi

  exec "${JAVA_BIN}" "${java_opts[@]}" -jar "${CACHED_JAR}" "$@"
}

main "$@"
