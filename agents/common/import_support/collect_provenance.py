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
"""Collects bounded read-only runtime source provenance."""

from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from absl import app
from absl import flags

from agents.common.import_support.command_runner import CommandError
from agents.common.import_support.command_runner import ReadOnlyCommandRunner
from agents.common.import_support.resolve_import import find_repository_root

_FLAGS = flags.FlagValues()
_IMAGE_URI = flags.DEFINE_string('image_uri',
                                 None,
                                 'Batch runnable container image URI.',
                                 flag_values=_FLAGS)
_TASK_START_TIME = flags.DEFINE_string(
    'task_start_time',
    None,
    'RFC3339 task start time used to bound builds.',
    flag_values=_FLAGS)
_WORKFLOW_REVISION_ID = flags.DEFINE_string('workflow_revision_id',
                                            '',
                                            'Historical Workflow revision ID.',
                                            flag_values=_FLAGS)
_BUILD_PROJECT = flags.DEFINE_string(
    'build_project',
    '',
    'Cloud Build project; defaults to image project.',
    flag_values=_FLAGS)
_BUILD_REGION = flags.DEFINE_string('build_region',
                                    'global',
                                    'Cloud Build region.',
                                    flag_values=_FLAGS)
_BUILD_LIMIT = flags.DEFINE_integer('build_limit',
                                    20,
                                    'Maximum build candidates to inspect.',
                                    flag_values=_FLAGS)

_IMAGE_PATTERN = re.compile(
    r'^(?P<host>[^/]+)/(?P<project>[^/]+)/(?:(?P<repository>[^/]+)/)?'
    r'(?P<image>[^:@]+)(?::(?P<tag>[^@]+))?(?:@(?P<digest>sha256:[a-fA-F0-9]+))?$'
)
_MAX_BUILD_LIMIT = 50


class ProvenanceError(ValueError):
    """Raised when provenance input is invalid."""


def parse_image_uri(image_uri: str) -> dict[str, str | None]:
    """Parses Artifact Registry and legacy GCR image URIs."""
    match = _IMAGE_PATTERN.match(image_uri)
    if not match:
        raise ProvenanceError(f'Unsupported image URI: {image_uri}')
    return match.groupdict()


def _run_git(repo_root: Path, args: list[str]) -> str:
    process = subprocess.run(['git', *args],
                             cwd=repo_root,
                             check=False,
                             capture_output=True,
                             text=True,
                             timeout=20)
    if process.returncode:
        raise ProvenanceError(process.stderr.strip() or 'git command failed')
    return process.stdout.strip()


def collect_local_repository_state(repo_root: Path) -> dict[str, Any]:
    """Returns the local commit and dirty state without changing Git."""
    return {
        'commit': _run_git(repo_root, ['rev-parse', 'HEAD']),
        'dirty': bool(_run_git(repo_root, ['status', '--short'])),
    }


def _safe_build(build: dict[str, Any]) -> dict[str, Any]:
    substitutions = build.get('substitutions', {})
    source = build.get('sourceProvenance', {})
    resolved_source = source.get('resolvedRepoSource', {})
    images = []
    for image in build.get('results', {}).get('images', []):
        images.append({
            'name': image.get('name'),
            'digest': image.get('digest'),
        })
    for image in build.get('images', []):
        if isinstance(image, str):
            images.append({'name': image, 'digest': None})
    return {
        'id':
            build.get('id'),
        'status':
            build.get('status'),
        'create_time':
            build.get('createTime'),
        'finish_time':
            build.get('finishTime'),
        'trigger_id':
            build.get('buildTriggerId'),
        'commit_sha':
            substitutions.get('COMMIT_SHA') or resolved_source.get('commitSha'),
        'declared_image':
            substitutions.get('_DOCKER_IMAGE'),
        'images':
            images,
    }


def _matching_builds(builds: list[dict[str, Any]],
                     image_uri: str) -> list[dict[str, Any]]:
    parsed = parse_image_uri(image_uri)
    image_base = image_uri.split('@', 1)[0].rsplit(':', 1)[0]
    matches = []
    for build in builds:
        safe = _safe_build(build)
        declared_image = str(safe.get('declared_image') or '')
        declared_base = declared_image.split('@', 1)[0].rsplit(':', 1)[0]
        if declared_base == image_base and not parsed.get('digest'):
            matches.append(safe)
            continue
        for image in safe['images']:
            name = image.get('name') or ''
            digest = image.get('digest')
            if image_base not in name:
                continue
            requested_digest = parsed.get('digest')
            if requested_digest and digest != requested_digest:
                continue
            matches.append(safe)
            break
    return matches


def _confidence(image: dict[str, str | None],
                builds: list[dict[str, Any]]) -> tuple[str, str]:
    if image.get('digest') and len(builds) == 1:
        return 'exact', 'One build records the requested immutable digest.'
    if len(builds) == 1 and image.get('tag') not in ('stable', 'latest', None):
        return ('strongly_correlated',
                'One build matches the non-default tag before task start.')
    if builds and image.get('tag') in ('stable', 'latest'):
        return ('strongly_correlated',
                'The most recent matching successful build before task start '
                'is selected for the mutable image tag.')
    if len(builds) > 1:
        return 'ambiguous', 'More than one immutable-tag build remains.'
    if len(builds) == 1:
        return ('strongly_correlated',
                'One time-bounded build matches a mutable image tag.')
    return 'unknown', 'No matching build evidence was found.'


def collect_runtime_provenance(
        repo_root: Path,
        image_uri: str,
        task_start_time: str,
        workflow_revision_id: str = '',
        build_project: str = '',
        build_region: str = 'global',
        build_limit: int = 20,
        runner: ReadOnlyCommandRunner | None = None) -> dict[str, Any]:
    """Collects local, image, and Cloud Build provenance evidence."""
    if build_limit < 1 or build_limit > _MAX_BUILD_LIMIT:
        raise ProvenanceError(
            f'build_limit must be between 1 and {_MAX_BUILD_LIMIT}.')
    try:
        datetime.fromisoformat(task_start_time.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ProvenanceError(
            f'Invalid task_start_time: {task_start_time}') from exc
    image = parse_image_uri(image_uri)
    project = build_project or str(image['project'])
    command_runner = runner or ReadOnlyCommandRunner(repo_root)
    warnings: list[str] = []
    builds: list[dict[str, Any]] = []
    try:
        raw_builds = command_runner.run_json([
            'gcloud', 'builds', 'list', f'--project={project}',
            f'--region={build_region}',
            f'--filter=status="SUCCESS" AND finishTime<"{task_start_time}"',
            '--sort-by=~finishTime', f'--limit={build_limit}', '--format=json'
        ])
        if isinstance(raw_builds, list):
            builds = _matching_builds(raw_builds, image_uri)
    except CommandError as exc:
        warnings.append(f'Cloud Build provenance unavailable: {exc}')
    confidence, confidence_reason = _confidence(image, builds)
    local = collect_local_repository_state(repo_root)
    selected_build = (builds[0]
                      if confidence in ('exact', 'strongly_correlated') and
                      builds else None)
    return {
        'requested_image_uri':
            image_uri,
        'requested_image_digest':
            image.get('digest'),
        'cloud_build_id':
            selected_build.get('id') if selected_build else None,
        'cloud_build_source_commit':
            selected_build.get('commit_sha') if selected_build else None,
        'embedded_data_commit':
            None,
        'workflow_revision_id':
            workflow_revision_id or None,
        'local_data_commit':
            local['commit'],
        'local_checkout_dirty':
            local['dirty'],
        'confidence':
            confidence,
        'confidence_reason':
            confidence_reason,
        'build_candidates':
            builds,
        'warnings':
            warnings + [
                'The cloud Dockerfile clones /data separately; the embedded data '
                'commit is unknown unless runtime evidence records it.'
            ],
    }


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Unexpected positional arguments.')
    if not _IMAGE_URI.value or not _TASK_START_TIME.value:
        raise app.UsageError('--image_uri and --task_start_time are required.')
    try:
        repo_root = find_repository_root()
        result = collect_runtime_provenance(
            repo_root=repo_root,
            image_uri=_IMAGE_URI.value,
            task_start_time=_TASK_START_TIME.value,
            workflow_revision_id=_WORKFLOW_REVISION_ID.value,
            build_project=_BUILD_PROJECT.value,
            build_region=_BUILD_REGION.value,
            build_limit=_BUILD_LIMIT.value,
        )
    except (ProvenanceError, CommandError) as exc:
        print(json.dumps({'error': str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(3) from exc
    print(json.dumps(result, indent=2, sort_keys=True))


def _parse_flags(argv: list[str]) -> list[str]:
    remaining = flags.FLAGS(argv, known_only=True)
    return _FLAGS(remaining)


if __name__ == '__main__':
    app.run(main, flags_parser=_parse_flags)
