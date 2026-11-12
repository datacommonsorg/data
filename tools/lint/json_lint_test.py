# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from tools.lint import json_lint


class LintFileTest(unittest.TestCase):

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)

    def _write(self, name, content):
        path = os.path.join(self._tmp_dir.name, name)
        mode = 'wb' if isinstance(content, bytes) else 'w'
        encoding = None if isinstance(content, bytes) else 'utf-8'
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return path

    def test_valid_json_passes(self):
        path = self._write('ok.json', '{"a": [1, 2.5, null, true], "b": "é"}')
        self.assertEqual(json_lint.lint_file(path), [])

    def test_utf8_bom_passes(self):
        path = self._write('bom.json', b'\xef\xbb\xbf{"a": 1}')
        self.assertEqual(json_lint.lint_file(path), [])

    def test_same_key_in_different_objects_passes(self):
        path = self._write('nested.json', '[{"a": 1}, {"a": 2}]')
        self.assertEqual(json_lint.lint_file(path), [])

    def test_lfs_pointer_is_skipped(self):
        path = self._write(
            'lfs.json', 'version https://git-lfs.github.com/spec/v1\n'
            'oid sha256:abc\nsize 123\n')
        self.assertIsNone(json_lint.lint_file(path))

    def test_syntax_error_reports_line_and_column(self):
        path = self._write('bad.json', '{\n  "a": 1,\n}')
        errors = json_lint.lint_file(path)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith('3:1: '), errors[0])

    def test_merge_conflict_markers_fail(self):
        path = self._write(
            'conflict.json', '{\n<<<<<<< HEAD\n"a": 1\n=======\n"a": 2\n'
            '>>>>>>> other\n}')
        self.assertEqual(len(json_lint.lint_file(path)), 1)

    def test_duplicate_keys_fail(self):
        path = self._write('dup.json', '{"x": {"a": 1, "b": 2, "a": 3}}')
        self.assertEqual(json_lint.lint_file(path), ["duplicate keys: 'a'"])

    def test_nan_fails(self):
        path = self._write('nan.json', '{"a": NaN}')
        self.assertEqual(json_lint.lint_file(path), ['NaN is not valid JSON'])

    def test_infinity_fails(self):
        path = self._write('inf.json', '[-Infinity]')
        self.assertEqual(json_lint.lint_file(path),
                         ['-Infinity is not valid JSON'])

    def test_invalid_utf8_fails(self):
        path = self._write('latin1.json', b'{"a": "\xe9"}')
        errors = json_lint.lint_file(path)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith('not valid UTF-8'), errors[0])


class FindJsonFilesTest(unittest.TestCase):

    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.root = self._tmp_dir.name

    def _touch(self, rel_path):
        path = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('{}')

    def _find(self, paths=None):
        found = json_lint.find_json_files(paths or [self.root],
                                          repo_root=self.root)
        return sorted(os.path.relpath(p, self.root) for p in found)

    def test_finds_json_and_geojson_only(self):
        self._touch('a.json')
        self._touch('sub/b.geojson')
        self._touch('sub/c.csv')
        self._touch('sub/d.jsonl')
        self.assertEqual(self._find(), ['a.json', 'sub/b.geojson'])

    def test_skips_excluded_dirs(self):
        self._touch('keep/a.json')
        self._touch('.env/lib/site-packages/pkg/data.json')
        self._touch('.git/x.json')
        self._touch('scripts/foo/scratch/out.json')
        self._touch('node_modules/pkg/package.json')
        self.assertEqual(self._find(), ['keep/a.json'])

    def test_skips_excluded_files(self):
        excluded = next(iter(json_lint.EXCLUDED_FILES))
        self._touch(excluded)
        self._touch('a.json')
        self.assertEqual(self._find(), ['a.json'])

    def test_accepts_explicit_files(self):
        self._touch('a.json')
        self._touch('b.json')
        self.assertEqual(self._find([os.path.join(self.root, 'b.json')]),
                         ['b.json'])


class MainTest(unittest.TestCase):

    def test_summary_counts_checked_failed_and_skipped(self):
        with tempfile.TemporaryDirectory() as root:
            files = {
                'ok.json': '{"a": 1}',
                'bad.json': '{"a": 1,}',
                'lfs.json': 'version https://git-lfs.github.com/spec/v1\n',
                'excluded.json': 'not json',
            }
            for name, content in files.items():
                with open(os.path.join(root, name), 'w', encoding='utf-8') as f:
                    f.write(content)
            excluded = os.path.relpath(os.path.join(root, 'excluded.json'),
                                       json_lint._REPO_ROOT)
            stdout = io.StringIO()
            with mock.patch.object(json_lint, 'EXCLUDED_FILES',
                                   frozenset({excluded})), \
                    contextlib.redirect_stdout(stdout), \
                    contextlib.redirect_stderr(io.StringIO()):
                exit_code = json_lint.main(['json_lint.py', root])

        self.assertEqual(exit_code, 1)
        self.assertIn(
            'Checked 2 JSON files, 1 failed, 2 skipped '
            '(1 in EXCLUDED_FILES, 1 Git LFS pointers).', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
